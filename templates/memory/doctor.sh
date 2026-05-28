#!/usr/bin/env bash
# aims memory pipeline health summary.
# Prints a one-screen status of the memory subsystem:
#   - total nodes
#   - dirty count
#   - last-consolidated timestamp (or "never")
#   - lint summary
#   - count of nodes over the 4 KB soft limit (ADR-0008)
#
# Per ADR-0009 there is no API key field: consolidation runs in-band
# in the active Claude Code session.
#
# Usage:  doctor.sh [--brief]
#   --brief: one-line output for SessionStart hooks.

set -u

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

BRIEF=0
case "${1:-}" in
  --brief|-b) BRIEF=1 ;;
  --help|-h)
    cat <<'EOF'
usage: doctor.sh [--brief]

Reports memory pipeline health. Defaults to a multi-line summary.
--brief gives a single line suitable for SessionStart.
EOF
    exit 0 ;;
esac

NODE_COUNT=$(list_leaves | wc -l | tr -d ' ')

if command -v bash >/dev/null 2>&1 && [ -x "$SCRIPT_DIR/find-dirty.sh" -o -r "$SCRIPT_DIR/find-dirty.sh" ]; then
  DIRTY_COUNT=$(bash "$SCRIPT_DIR/find-dirty.sh" 2>/dev/null | grep -c . || true)
else
  DIRTY_COUNT=0
fi

STATE_FILE="${AIMS_MEMORY_STATE_FILE:-.claude/memory/.last-consolidated}"
if [ -r "$STATE_FILE" ]; then
  LAST_TS=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
  case "$LAST_TS" in
    ''|*[!0-9]*) LAST_TS=0 ;;
  esac
  if [ "$LAST_TS" -gt 0 ]; then
    NOW=$(date -u +%s)
    AGE=$((NOW - LAST_TS))
    if   [ "$AGE" -lt 120     ]; then LAST_HUMAN="just now"
    elif [ "$AGE" -lt 3600    ]; then LAST_HUMAN="$((AGE / 60))m ago"
    elif [ "$AGE" -lt 86400   ]; then LAST_HUMAN="$((AGE / 3600))h ago"
    else                              LAST_HUMAN="$((AGE / 86400))d ago"
    fi
  else
    LAST_HUMAN="never"
  fi
else
  LAST_HUMAN="never"
fi

# Run lint silently; capture issue count from stderr "clean (N nodes)" or
# count of issue lines on stdout.
LINT_OUT=$(bash "$SCRIPT_DIR/lint.sh" 2>&1 || true)
LINT_ISSUES=$(printf '%s' "$LINT_OUT" | grep -vE '^\[aims-memory\] lint: clean' | grep -c . || true)
if [ "$LINT_ISSUES" -eq 0 ]; then
  LINT_HUMAN="clean"
else
  LINT_HUMAN="$LINT_ISSUES issues"
fi

# Nodes > 4 KB (ADR-0008 soft limit).
LARGE_COUNT=0
if [ -d "${AIMS_MEMORY_DIR:-docs/memory}" ]; then
  LARGE_COUNT=$(find "${AIMS_MEMORY_DIR:-docs/memory}" -name '*.md' \
    -not -name 'README.md' -not -name '_inbox.md' \
    -size +4k 2>/dev/null | grep -c . || true)
fi

# Inert module nodes (empty code:) — post-edit-marker can never flag them
# dirty, so they never consolidate. The silent failure mode of the tree.
INERT_COUNT=0
while IFS= read -r leaf; do
  [ -z "$leaf" ] && continue
  [ "$(fm_get "$leaf" kind)" = "module" ] || continue
  [ -z "$(fm_list "$leaf" code)" ] && INERT_COUNT=$((INERT_COUNT + 1))
done < <(list_leaves)

if [ "$BRIEF" -eq 1 ]; then
  # One line for SessionStart. Highlight unhealthy states.
  if [ "$LAST_HUMAN" = "never" ] && [ "$DIRTY_COUNT" -gt 0 ]; then
    printf '[aims-memory] consolidation never ran (%d dirty)\n' "$DIRTY_COUNT"
  elif [ "$LAST_HUMAN" = "never" ]; then
    printf '[aims-memory] %d nodes, consolidation never ran, lint %s\n' \
      "$NODE_COUNT" "$LINT_HUMAN"
  else
    INERT_SUFFIX=""
    [ "$INERT_COUNT" -gt 0 ] && INERT_SUFFIX=", $INERT_COUNT inert"
    printf '[aims-memory] %d nodes, %d dirty, last consolidated %s, lint %s%s\n' \
      "$NODE_COUNT" "$DIRTY_COUNT" "$LAST_HUMAN" "$LINT_HUMAN" "$INERT_SUFFIX"
  fi
  exit 0
fi

cat <<EOF
aims memory pipeline health
  nodes total:        $NODE_COUNT
  dirty:              $DIRTY_COUNT
  last consolidated:  $LAST_HUMAN
  lint:               $LINT_HUMAN
  nodes > 4 KB:       $LARGE_COUNT
  inert (code: []):   $INERT_COUNT
EOF

if [ "$LINT_ISSUES" -gt 0 ]; then
  printf '\nlint detail:\n'
  printf '%s\n' "$LINT_OUT" | grep -vE '^\[aims-memory\] lint: clean' | sed 's/^/  /'
fi

exit 0
