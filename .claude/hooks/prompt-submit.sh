#!/usr/bin/env bash
# aims UserPromptSubmit hook — intent router.
#
# Reads the user's prompt from stdin (Claude Code passes a JSON payload).
# Classifies intent into one of: bug, feature, refactor, decision,
# mechanical, question, ambiguous, or none.
#
# When the intent is actionable, emits a JSON additionalContext block that
# instructs the Claude session to call AskUserQuestion before proceeding —
# turning Claude itself into the conversational router.
#
# Suppression rules (return early, no router):
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
# (and isn't pasted code), assume an ambiguous task and let the model
# disambiguate via AskUserQuestion. Keeps the router useful for
# Hebrew/etc. prompts without per-language pattern maintenance.
if [ -z "$intent" ]; then
  plen=${#prompt}
  # Skip code-paste-looking prompts.
  if [ "$plen" -ge 40 ] && [ "$plen" -le 2048 ] \
     && ! printf '%s' "$prompt" | grep -q '```'; then
    intent="ambiguous"
  fi
fi

[ -z "$intent" ] && exit 0

# ── Build router context (JSON-safe via printf + escaping) ─────────────────
# Single-quote the heredoc and substitute $intent at the end.
read -r -d '' router_text <<'TEXT' || true
[aims-router] The user's most recent prompt looks like a __INTENT__ task.

Before doing the actual work, you MUST first call the AskUserQuestion tool to
let the user pick the workflow. Use this menu, adapting only the wording:

  bug         → (a) /plan a real fix  (b) /grunt a quick patch
                (c) diagnose only — explain root cause, no edits
  feature     → (a) /plan it (recommended)  (b) sketch a quick prototype
                (c) just discuss the design first
  refactor    → (a) /plan it (almost always the right answer)
                (b) /grunt — only if it's a pure rename/format
  decision    → (a) /plan to explore options first, then /adr
                (b) /adr now — only if the choice is already clear
  mechanical  → (a) /grunt it now (fast, Haiku)
                (b) /plan first if the scope is unclear
  question    → (a) just answer  (b) answer then /plan if it leads to changes
  ambiguous   → no English keyword matched; ask the user "Which workflow:
                /plan, /grunt, /adr, or just answer?" and proceed by their pick.

After the user picks, follow that workflow's discipline AS IF they had typed
the slash command:
  - /plan choice  → create .claude/.planning-lock first, do read-only
                    exploration, end with ExitPlanMode, then write plan to
                    docs/plans/ and remove the lock.
  - /grunt choice → mechanical edits only, refuse on judgment calls.
  - /adr choice   → draft to docs/adr/NNNN-slug.md, status: proposed.
  - diagnose / answer / discuss → no file changes.

Skip this routing only if the user's prompt explicitly chose a path
(e.g. "just patch it", "I already decided X, write the ADR").
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
printf '[aims-router] intent=%s — Claude will ask you which workflow.\n' "$intent" >&2
exit 0
