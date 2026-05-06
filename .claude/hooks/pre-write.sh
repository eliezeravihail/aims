#!/usr/bin/env bash
# ais PreToolUse hook for Edit / Write / MultiEdit.
#
# Two responsibilities:
#   1. Hard block while .claude/.planning-lock exists (planning is read-only).
#   2. In `block` mode, soft-block writes to source paths without an
#      in-progress plan AND when the target path looks like production code.
#
# Mode is read from .claude/ais-mode (one of: nudge | block).
# Default if file missing: nudge (warn-only).
#
# Exit codes:
#   0 — allow.
#   2 — block (Claude Code surfaces stderr to the model + user).

set -u

LOCK=".claude/.planning-lock"
MODE_FILE=".claude/ais-mode"
PLAN_DIR="${AIS_PLAN_DIR:-docs/plans}"

mode="nudge"
[ -f "$MODE_FILE" ] && mode=$(tr -d ' \n' < "$MODE_FILE")

# Read JSON payload (Claude Code passes tool_input).
payload=$(cat || true)

extract_path() {
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$payload" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null
  else
    printf '%s' "$payload" | grep -oE '"file_path"\s*:\s*"[^"]+"' | head -1 | sed -E 's/.*"file_path"\s*:\s*"([^"]+)".*/\1/'
  fi
}

target=$(extract_path)

# (1) Planning lock — always blocks, regardless of mode.
if [ -f "$LOCK" ]; then
  cat >&2 <<EOF
[ais] Planning in progress (.claude/.planning-lock present).
       File edits are not allowed until you call ExitPlanMode and the user
       approves the plan. After approval, /plan will remove the lock.
       To abort planning manually:  rm .claude/.planning-lock
EOF
  exit 2
fi

# (2) Significant-change check — only in block mode, only on real source paths.
[ "$mode" != "block" ] && exit 0
[ -z "$target" ] && exit 0

is_source_path=0
case "$target" in
  src/*|lib/*|app/*|server/*|client/*|packages/*) is_source_path=1 ;;
esac
[ "$is_source_path" -eq 0 ] && exit 0

# Allow if the path looks like a test or doc.
case "$target" in
  *_test.*|*test_*.*|*.test.*|*.spec.*|*/tests/*|*/__tests__/*|*.md|*.txt) exit 0 ;;
esac

# Require an in-progress plan to write to source paths.
has_active_plan=0
if [ -d "$PLAN_DIR" ]; then
  if grep -lE '^Status:\s*in-progress' "$PLAN_DIR"/*.md 2>/dev/null | grep -q .; then
    has_active_plan=1
  fi
fi

if [ "$has_active_plan" -eq 0 ]; then
  cat >&2 <<EOF
[ais] About to edit "$target" (production source) without an in-progress plan.
       Run \`/plan\` first, OR set hook mode to nudge:
         echo nudge > .claude/ais-mode
       OR delete this hook if you want it off entirely.
EOF
  exit 2
fi

exit 0
