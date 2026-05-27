#!/usr/bin/env bash
# aims Stop hook — throttled memory consolidation.
#
# Stop fires after every Claude turn. An unconditional LLM call here
# would mean ~30 LLM calls per active session. Throttle in bash:
#
#   Run consolidation only when
#       N_DIRTY >= AIMS_MEMORY_DIRTY_MAX   (default 5)
#     OR
#       (now - last_consolidated) >= AIMS_MEMORY_INTERVAL_SEC  (default 1800s)
#
# Override per project via .claude/memory/throttle.conf
# (a shell snippet that sets the two AIMS_MEMORY_* variables).
#
# Never blocks. Always exits 0.

set -u

if [ -d ".claude/memory" ]; then
  MEM_HELPERS=".claude/memory"
elif [ -d "templates/memory" ]; then
  MEM_HELPERS="templates/memory"
else
  exit 0
fi

# Pick up project overrides, if any.
if [ -r ".claude/memory/throttle.conf" ]; then
  # shellcheck disable=SC1091
  . ".claude/memory/throttle.conf"
fi

DIRTY_MAX="${AIMS_MEMORY_DIRTY_MAX:-5}"
INTERVAL_SEC="${AIMS_MEMORY_INTERVAL_SEC:-1800}"
STATE_FILE="${AIMS_MEMORY_STATE_FILE:-.claude/memory/.last-consolidated}"
FORCE=0

# --force / -f: ignore the throttle (used by /done).
case "${1:-}" in
  --force|-f) FORCE=1 ;;
esac

# Read the hook payload from stdin (Claude Code Stop hook contract:
# JSON with `transcript_path`). Used to harvest URLs cited in the
# session — those that survive the consolidate.sh LLM filter become
# "## Pointers > External" entries on nodes touched this session.
# Empty/unreadable transcript → empty URL list (no abort).
TRANSCRIPT_URLS=""
if [ "$FORCE" -ne 1 ] && [ ! -t 0 ]; then
  payload=$(cat 2>/dev/null || true)
  if [ -n "$payload" ] && command -v jq >/dev/null 2>&1; then
    transcript_path=$(printf '%s' "$payload" \
      | jq -r '.transcript_path // empty' 2>/dev/null || true)
    if [ -n "$transcript_path" ] && [ -r "$transcript_path" ]; then
      TRANSCRIPT_URLS=$(grep -oE 'https?://[^[:space:]"<>)\\]+' \
        "$transcript_path" 2>/dev/null \
        | sort -u \
        | head -50 \
        || true)
    fi
  fi
fi
export AIMS_TRANSCRIPT_URLS="$TRANSCRIPT_URLS"

# Discover dirty leaves cheaply.
mapfile -t DIRTY < <(bash "$MEM_HELPERS/find-dirty.sh" 2>/dev/null || true)
N_DIRTY=${#DIRTY[@]}
[ "$N_DIRTY" -eq 0 ] && exit 0

NOW=$(date -u +%s)
LAST=0
if [ -r "$STATE_FILE" ]; then
  LAST=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
  case "$LAST" in
    ''|*[!0-9]*) LAST=0 ;;
  esac
fi
ELAPSED=$((NOW - LAST))

should_run=0
if [ "$FORCE" -eq 1 ]; then
  should_run=1
elif [ "$N_DIRTY" -ge "$DIRTY_MAX" ]; then
  should_run=1
elif [ "$ELAPSED" -ge "$INTERVAL_SEC" ]; then
  should_run=1
fi

[ "$should_run" -eq 0 ] && exit 0

# Run consolidation per dirty leaf. consolidate.sh handles its own
# graceful-skip when no API key is present (leaf stays dirty).
for leaf in "${DIRTY[@]}"; do
  [ -z "$leaf" ] && continue
  bash "$MEM_HELPERS/consolidate.sh" "$leaf" || true
done

# Classify any inbox entries — apply confident proposals; surface
# uncertain ones to the user at next /done.
if [ -s "${AIMS_MEMORY_DIR:-docs/memory}/_inbox.md" ]; then
  bash "$MEM_HELPERS/classify-inbox.sh" 2>/dev/null | \
    awk -F'\t' '
      $2 == "existing-leaf" { print "[aims-memory] inbox →", $1, "→", $3 > "/dev/stderr" }
      $2 == "new-leaf"      { print "[aims-memory] inbox suggests new leaf:", $3, "(" $4 ")", "from", $1 > "/dev/stderr" }
      $2 == "uncertain"     { print "[aims-memory] inbox uncertain:", $1, "(" $3 ")" > "/dev/stderr" }
    ' || true
fi

mkdir -p "$(dirname "$STATE_FILE")"
printf '%s\n' "$NOW" > "$STATE_FILE"

printf '[aims-memory] consolidated %d leaf(s)\n' "$N_DIRTY" >&2
exit 0
