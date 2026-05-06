#!/usr/bin/env bash
# ais UserPromptSubmit hook — trigger-based reminders, never blocks.
#
# Reads the user's prompt from stdin (Claude Code passes it as JSON).
# Detects intent triggers and prints a one-line nudge.
# Exits 0 always.

set -u

# Read JSON payload from stdin; extract `.prompt` if jq is available, else
# fall back to crude grep on the raw stream.
payload=$(cat || true)
if command -v jq >/dev/null 2>&1; then
  prompt=$(printf '%s' "$payload" | jq -r '.prompt // empty' 2>/dev/null || true)
else
  prompt=$(printf '%s' "$payload" | tr -d '\n')
fi

[ -z "$prompt" ] && exit 0
lower=$(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]')

PLAN_DIR="${AIS_PLAN_DIR:-docs/plans}"

has_active_plan=0
if [ -d "$PLAN_DIR" ]; then
  if grep -lE '^Status:\s*in-progress' "$PLAN_DIR"/*.md 2>/dev/null | grep -q .; then
    has_active_plan=1
  fi
fi

# Triggers — case-insensitive substring match on the user's prompt.
case "$lower" in
  *refactor*|*redesign*|*rewrite*|*migrate*|*restructure*)
    if [ "$has_active_plan" -eq 0 ]; then
      printf '[ais] Sounds like non-trivial work. Consider `/plan` first.\n' >&2
    fi
    ;;
esac

case "$lower" in
  *' vs '*|*'should we'*|*'choose between'*|*'option a'*|*'tradeoff'*|*'trade-off'*)
    printf '[ais] Decision-shaped request. Consider `/adr` once chosen.\n' >&2
    ;;
esac

case "$lower" in
  *'add feature'*|*'new feature'*|*'implement'*|*'build a '*)
    if [ "$has_active_plan" -eq 0 ]; then
      printf '[ais] Feature work — `/plan` produces a durable contract.\n' >&2
    fi
    ;;
esac

exit 0
