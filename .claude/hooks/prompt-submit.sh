#!/usr/bin/env bash
# aims UserPromptSubmit hook — intent router.
#
# Reads the user's prompt from stdin (Claude Code passes a JSON payload).
# Classifies intent into one of: bug, feature, refactor, decision,
# mechanical, question, ambiguous, or none.
#
# When the intent is actionable (anything except `question`), the router
# **auto-engages** the /plan flow by:
#   1. Creating .claude/.planning-lock (Edit/Write blocked until approved).
#   2. Injecting a JSON additionalContext that instructs the session to
#      draft a plan, write it to docs/plans/<UTC-date>-<slug>.md with
#      Status: draft, then ask the user to approve / edit / abort.
#
# Suppression rules (return early, no auto-engage):
#   - Prompt starts with `/`             — user already chose a command
#   - A planning lock is active          — already mid-flow
#   - An in-progress plan exists AND the prompt is short  — likely a follow-up
#   - Prompt empty                       — nothing to route
#
# Exit codes:
#   0 — always (UserPromptSubmit hooks should not block).

set -u

# ── Read payload ────────────────────────────────────────────
payload=$(cat || true)
if command -v jq >/dev/null 2>&1; then
  prompt=$(printf '%s' "$payload" | jq -r '.prompt // empty' 2>/dev/null || true)
else
  prompt=$(printf '%s' "$payload")
fi
[ -z "$prompt" ] && exit 0

# ── Suppression ───────────────────────────────────────────────
case "$prompt" in
  /*) exit 0 ;;
esac

[ -f .claude/.planning-lock ] && exit 0

PLAN_DIR="${AIMS_PLAN_DIR:-docs/plans}"
has_active_plan=0
if [ -d "$PLAN_DIR" ]; then
  if grep -lE '^Status:\s*in-progress' "$PLAN_DIR"/*.md 2>/dev/null | grep -q .; then
    has_active_plan=1
  fi
fi

prompt_len=${#prompt}
if [ "$has_active_plan" -eq 1 ] && [ "$prompt_len" -lt 120 ]; then
  exit 0   # short follow-up during active plan — let Claude carry on
fi

# ── Classify intent (first match wins) ────────────────────────────────────
lower=$(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]')

intent=""
match() { printf '%s' "$lower" | grep -qE "$1"; }

# Bug — strongest signals first.
if match 'traceback|stack trace|exception:|error:|errno|segfault|core dumped|panic:'; then
  intent="bug"
elif match '\bbug\b|crash(es|ed|ing)?|broken|does ?n.?t work|not working|fails to|throws'; then
  intent="bug"

# Mechanical (cheap path; check before refactor / feature).
elif match '\brename\b.*\bto\b|\bbump\b.*version|format (this|the|all)|update.*timestamps|^reformat\b'; then
  intent="mechanical"

# Refactor / restructure.
elif match 'refactor|restructure|redesign|rewrite|clean ?up|extract (a |the )?(method|function|class)|migrate (to|from)'; then
  intent="refactor"

# Decision.
elif match ' vs |should we|should i|choose between|trade-?off|which (one |is )?better|pick between'; then
  intent="decision"

# Feature.
elif match '\b(add|implement|build|create|introduce|support)\b.*(feature|endpoint|command|module|page|screen|hook|rule)|new feature\b|add a way to|let users? '; then
  intent="feature"

# Question — asked, not commanded.
elif printf '%s' "$prompt" | grep -qE '\?\s*$'; then
  intent="question"
elif match '^(how |what |why |when |where |can |could |should |does |is |are |do you |what.?s )'; then
  intent="question"
fi

# Multilingual fallback: regex matchers above are English-only. If no
# intent was inferred but the prompt is long enough to be actionable
# (and isn't pasted code), assume an ambiguous task and let auto-engage
# carry it into /plan mode (the model can still rm the lock if the user
# actually meant a question).
if [ -z "$intent" ]; then
  plen=${#prompt}
  # Skip code-paste-looking prompts.
  if [ "$plen" -ge 40 ] && [ "$plen" -le 2048 ] \
     && ! printf '%s' "$prompt" | grep -q '```'; then
    intent="ambiguous"
  fi
fi

[ -z "$intent" ] && exit 0
# `question` is the only intent that does NOT require a plan.
[ "$intent" = "question" ] && exit 0

# ── Auto-engage /plan ─────────────────────────────────────────
# Create the planning lock NOW so Edit/Write/MultiEdit are blocked for
# the next turn. The model must Phase 1 (read-only) → Phase 2 (draft to
# disk via Bash heredoc, since Write is blocked) → Phase 3 (approval gate
# flips Status: draft → in-progress and removes the lock) → Phase 4
# (implement) → Phase 5 (close-out).
mkdir -p .claude
touch .claude/.planning-lock

# ── Build router context (JSON-safe via printf + escaping) ─────────────────
read -r -d '' router_text <<'TEXT' || true
[aims-router] Intent looks like a __INTENT__ task — auto-engaging /plan.

The planning lock (.claude/.planning-lock) is now in place; Edit/Write
are blocked until the user approves a draft. Run the /plan flow:

  Phase 1: read-only exploration (Read, Grep, Glob, Bash read-only).
  Phase 2: write the draft to docs/plans/<UTC-date>-<slug>.md with
           Status: draft using a Bash heredoc (Write is blocked by the
           lock). Print: "Draft saved to docs/plans/<file>.
           Approve / edit / abort?".
  Phase 3: on approval → flip Status: draft → in-progress, then
           `rm -f .claude/.planning-lock`, then implement (Phase 4).
           On reject/iterate → rewrite the draft in place; re-ask.
           On abort → delete the draft + remove the lock.
  Phase 5: inline close-out (Status: in-progress → completed,
           auto-ADR, node consolidation) — same as before.

Skip auto-engagement only if the user's prompt explicitly opts out
("just patch it", "don't plan, just do it", "אל תתכנן"). In that case
run `rm -f .claude/.planning-lock` and proceed inline.
TEXT

router_text=${router_text//__INTENT__/$intent}

# ── Emit JSON for Claude Code ────────────────────────────────────────────
if command -v jq >/dev/null 2>&1; then
  jq -nc --arg ctx "$router_text" \
    '{hookSpecificOutput: {hookEventName: "UserPromptSubmit", additionalContext: $ctx}}'
else
  # Minimal hand-escape: escape backslashes, double quotes, newlines.
  esc=$(printf '%s' "$router_text" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | awk 'BEGIN{ORS="\\n"} {print}')
  printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$esc"
fi

# Also surface a one-line breadcrumb on stderr so the user sees what happened.
printf '[aims-router] intent=%s — auto-engaging /plan.\n' "$intent" >&2
exit 0
