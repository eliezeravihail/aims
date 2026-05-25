#!/usr/bin/env bash
# aims SessionStart hook — informational only.
# Surfaces:
#   - in-progress plans
#   - recently-touched ADRs
#   - leftover planning-lock (warns if present without active plan)
# Exits 0 always; never blocks.

set -u

ADR_DIR="${AIMS_ADR_DIR:-docs/adr}"
PLAN_DIR="${AIMS_PLAN_DIR:-docs/plans}"
LOCK=".claude/.planning-lock"

print_section() {
  local title="$1"
  printf '  %s\n' "$title"
}

# Stale lock detection.
if [ -f "$LOCK" ]; then
  has_active_plan=0
  if [ -d "$PLAN_DIR" ]; then
    if grep -lE '^Status:\s*in-progress' "$PLAN_DIR"/*.md 2>/dev/null | grep -q .; then
      has_active_plan=1
    fi
  fi
  if [ "$has_active_plan" -eq 0 ]; then
    printf '[aims] WARNING: .claude/.planning-lock exists but no in-progress plan.\n'
    printf '       If you abandoned a /plan, run: rm .claude/.planning-lock\n'
  else
    printf '[aims] Planning lock active — Edit/Write blocked until ExitPlanMode.\n'
  fi
fi

# In-progress plans.
if [ -d "$PLAN_DIR" ]; then
  active=$(grep -lE '^Status:\s*in-progress' "$PLAN_DIR"/*.md 2>/dev/null || true)
  if [ -n "$active" ]; then
    printf '[aims] In-progress plans:\n'
    while IFS= read -r f; do
      title=$(awk -F': ' '/^# /{print substr($0, 3); exit}' "$f")
      printf '       %s — %s\n' "${f#$PLAN_DIR/}" "${title:-untitled}"
    done <<< "$active"
  fi
fi

# Recently-touched ADRs (last 30 days).
if [ -d "$ADR_DIR" ]; then
  recent=$(find "$ADR_DIR" -maxdepth 1 -name '[0-9]*.md' -mtime -30 2>/dev/null | sort | tail -5)
  if [ -n "$recent" ]; then
    printf '[aims] Recent ADRs:\n'
    while IFS= read -r f; do
      title=$(awk -F': ' '/^# /{print substr($0, 3); exit}' "$f")
      printf '       %s\n' "${title:-${f##*/}}"
    done <<< "$recent"
  fi
fi

# Memory tree top-level (ADR-0007). Surface the README so the model
# knows the tag list to navigate. Capped at 2KB to keep the prompt
# injection light.
MEMORY_DIR="${AIMS_MEMORY_DIR:-docs/memory}"
MEMORY_README="$MEMORY_DIR/README.md"
if [ -r "$MEMORY_README" ]; then
  printf '[aims] Memory tree (%s):\n' "$MEMORY_DIR"
  head -c 2048 "$MEMORY_README" | sed 's/^/       /'
  size=$(wc -c < "$MEMORY_README")
  if [ "$size" -gt 2048 ]; then
    printf '       … (%d bytes truncated; view with: cat %s)\n' "$((size - 2048))" "$MEMORY_README"
  fi
fi

exit 0
