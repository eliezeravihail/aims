#!/usr/bin/env bash
# aims capsule health summary (over a Capsa capsule, .capsa/).
# Prints a one-screen status of the insight layer:
#   - total insights
#   - stale count (computed: `updated:` vs git; Capsa §1.4)
#   - last-consolidated timestamp (or "never")
#   - lint summary (schema conformance + aims body conventions)
#   - count of insights over the 4 KB soft limit (ADR-0008)
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

Reports capsule/insight health. Defaults to a multi-line summary.
--brief gives a single line suitable for SessionStart.
EOF
    exit 0 ;;
esac

NODE_COUNT=$(list_insights | wc -l | tr -d ' ')

if [ -r "$SCRIPT_DIR/find-dirty.sh" ]; then
  DIRTY_COUNT=$(bash "$SCRIPT_DIR/find-dirty.sh" 2>/dev/null | grep -c . || true)
else
  DIRTY_COUNT=0
fi

STATE_FILE="${AIMS_MEMORY_STATE_FILE:-$STATE_DIR/.last-consolidated}"
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

# Run lint silently; capture issue count from stderr "clean (N insights)" or
# count of issue lines on stdout.
LINT_OUT=$(bash "$SCRIPT_DIR/lint.sh" 2>&1 || true)
LINT_ISSUES=$(printf '%s' "$LINT_OUT" | grep -vE '^\[aims-memory\] lint: clean' | grep -c . || true)
if [ "$LINT_ISSUES" -eq 0 ]; then
  LINT_HUMAN="clean"
else
  LINT_HUMAN="$LINT_ISSUES issues"
fi

# Insights > 4 KB (ADR-0008 soft limit).
LARGE_COUNT=0
if [ -d "$INSIGHTS_DIR" ]; then
  LARGE_COUNT=$(find "$INSIGHTS_DIR" -name '*.md' -size +4k 2>/dev/null | grep -c . || true)
fi

if [ "$BRIEF" -eq 1 ]; then
  # One line for SessionStart. Highlight unhealthy states.
  if [ "$LAST_HUMAN" = "never" ] && [ "$DIRTY_COUNT" -gt 0 ]; then
    printf '[aims-memory] consolidation never ran (%d stale)\n' "$DIRTY_COUNT"
  elif [ "$LAST_HUMAN" = "never" ]; then
    printf '[aims-memory] %d insights, consolidation never ran, lint %s\n' \
      "$NODE_COUNT" "$LINT_HUMAN"
  else
    printf '[aims-memory] %d insights, %d stale, last consolidated %s, lint %s\n' \
      "$NODE_COUNT" "$DIRTY_COUNT" "$LAST_HUMAN" "$LINT_HUMAN"
  fi
  exit 0
fi

cat <<EOF
aims capsule health
  insights total:     $NODE_COUNT
  stale:              $DIRTY_COUNT
  last consolidated:  $LAST_HUMAN
  lint:               $LINT_HUMAN
  insights > 4 KB:    $LARGE_COUNT
EOF

if [ "$LINT_ISSUES" -gt 0 ]; then
  printf '\nlint detail:\n'
  printf '%s\n' "$LINT_OUT" | grep -vE '^\[aims-memory\] lint: clean' | sed 's/^/  /'
fi

exit 0
