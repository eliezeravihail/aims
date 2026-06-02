#!/usr/bin/env bash
# aims UserPromptSubmit hook — intent router + memory-node auto-injector.
#
# Reads the user's prompt from stdin (Claude Code passes a JSON payload).
#
# Two jobs in one emission:
#
#   1. ROUTER (factual awareness — never a lock). Classifies intent into one
#      of: bug, feature, refactor, decision, mechanical, question, ambiguous,
#      or none. For any actionable intent, injects a FACTUAL planning-convention
#      note. NEVER creates a lock and NEVER blocks (overhaul plan
#      docs/plans/2026-06-01-aims-overhaul.md).
#
#   2. MEMORY INJECTOR (ADR-0016). For every memory node whose `code:`
#      glob (fnmatch per ADR-0014) is plausibly referenced by the prompt,
#      injects that node's body — purpose, invariants, pointers, known
#      issues — so the model has node context without being asked.
#      Per-session de-dup via `.claude/memory/.injected-<session_id>`.
#      Total injection capped at SIZE_CAP bytes.
#
# Both jobs land in a single `additionalContext` emission.
#
# Suppression rules (return early, neither job runs):
#   - Prompt starts with `/`             — user already chose a command
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

# ── Memory-node auto-injection (ADR-0016) ────────────────────────────────
MEMORY_DIR="${AIMS_MEMORY_DIR:-docs/memory}"
SESSION_ID=$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null || true)
INJECTED_STATE=".claude/memory/.injected-${SESSION_ID:-default}"
SIZE_CAP=8192
NAME_MIN_LEN=5
LIT_MIN_LEN=4
declare -a matched=()
memory_text=""

if [ -d "$MEMORY_DIR" ] && [ "${#prompt}" -ge 8 ]; then
  MEM_HELPERS=""
  if   [ -r ".claude/memory/_lib.sh" ];   then MEM_HELPERS=".claude/memory"
  elif [ -r "templates/memory/_lib.sh" ]; then MEM_HELPERS="templates/memory"
  fi

  if [ -n "$MEM_HELPERS" ]; then
    # shellcheck source=/dev/null
    . "$MEM_HELPERS/_lib.sh"

    declare -A INJECTED=()
    if [ -r "$INJECTED_STATE" ]; then
      while IFS= read -r p; do
        [ -n "$p" ] && INJECTED["$p"]=1
      done < "$INJECTED_STATE"
    fi

    accum=0
    while IFS= read -r leaf; do
      [ -z "$leaf" ] && continue
      [ -n "${INJECTED[$leaf]+x}" ] && continue
      hit=0
      while IFS= read -r glob; do
        [ -z "$glob" ] && continue
        # Strip :line-range suffix.
        base="${glob%%:*}"
        # Literal prefix = everything before the first glob metachar.
        lit="${base%%[\*\?\[]*}"
        # Substring match on the literal prefix (if long enough).
        if [ -n "$lit" ] && [ "${#lit}" -ge "$LIT_MIN_LEN" ]; then
          case "$prompt" in *"$lit"*) hit=1; break ;; esac
        fi
        # Basename word match — only for literal entries (no glob chars).
        if [ "$lit" = "$base" ]; then
          name="${base##*/}"
          if [ -n "$name" ] && [ "${#name}" -ge "$NAME_MIN_LEN" ]; then
            if printf '%s' "$prompt" | grep -qwF "$name"; then
              hit=1
              break
            fi
          fi
        fi
      done < <(fm_list "$leaf" code)
      [ "$hit" -eq 1 ] || continue

      body=$(awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$leaf")
      bsize=${#body}
      if [ "$((accum + bsize))" -le "$SIZE_CAP" ]; then
        matched+=("$leaf")
        accum=$((accum + bsize))
        INJECTED["$leaf"]=1
      fi
      [ "$accum" -ge "$SIZE_CAP" ] && break
    done < <(list_leaves)

    if [ "${#matched[@]}" -gt 0 ]; then
      mkdir -p "$(dirname "$INJECTED_STATE")"
      : > "$INJECTED_STATE"
      for p in "${!INJECTED[@]}"; do
        printf '%s\n' "$p" >> "$INJECTED_STATE"
      done
      # Prune stale per-session state files (>7 days).
      find "$(dirname "$INJECTED_STATE")" -maxdepth 1 -name '.injected-*' \
        -type f -mtime +7 -delete 2>/dev/null || true

      memory_text="[aims-memory] Your prompt references code tracked by memory node(s). The relevant node body is below — use it as a navigator (purpose, invariants, pointers, known issues) BEFORE re-searching the codebase. Cite it where helpful; don't restate it verbatim.

"
      for leaf in "${matched[@]}"; do
        node_name=$(fm_get "$leaf" node)
        body=$(awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$leaf")
        memory_text+="=== node: ${node_name} (${leaf}) ===
${body}

"
      done
    fi
  fi
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

# Hebrew interrogatives — the Latin-script matchers above never fire on
# Hebrew text, so without this branch every Hebrew question falls through to
# the ambiguous fallback. Questions ending in "?" are already caught above
# regardless of language; this handles the ones that don't.
if [ -z "$intent" ]; then
  case "$prompt" in
    *"מה "*|*איך*|*כיצד*|*למה*|*מדוע*|*האם*|*מתי*|*איפה*|*היכן*|*כמה*|*"מי "*|*איזה*|*איזו*|*אילו*|*מהו*|*מהי*)
      intent="question" ;;
  esac
fi

# Multilingual fallback: regex matchers above are English-only. If no
# intent was inferred but the prompt is long enough to be actionable
# (and isn't pasted code), mark it ambiguous. Ambiguous no longer creates a
# planning lock (see the router section below) — it only suggests /plan — so
# a misread non-English prompt can never deadlock edits.
if [ -z "$intent" ]; then
  plen=${#prompt}
  if [ "$plen" -ge 40 ] && [ "$plen" -le 2048 ] \
     && ! printf '%s' "$prompt" | grep -q '```'; then
    intent="ambiguous"
  fi
fi

# ── Build router text — factual awareness, never a lock ───────────────────
# AIMS informs, never blocks/locks (docs/plans/2026-06-01-aims-overhaul.md). For an
# actionable-looking prompt, inject the planning convention as a FACTUAL note (an
# imperative "you must plan" would trip Claude's prompt-injection defense and be shown
# to the user instead of treated as context). NO .planning-lock is ever created.
# Questions and trivial prompts get nothing.
router_text=""
case "$intent" in
  bug|feature|refactor|decision|mechanical|ambiguous)
    router_text="[aims] Project convention: for a non-trivial change, plan before implementing — read-only discovery, then a \`Status: draft\` plan written to \`docs/plans/\`, then user approval, then implementation, then inline close-out (verify, ADR-if-warranted, mark completed, refresh memory). The full flow is documented in \`.claude/commands/plan.md\`. Planning is the *behavior*; the \`/plan\` slash command is an OPTIONAL shortcut that dispatches the planning pass to an Opus subagent — use it when the current model is not Opus and the task warrants careful planning. If you (the assistant) are not running on Opus and this prompt looks like a non-trivial change, ask the user ONCE via AskUserQuestion whether to use \`/plan\` for an Opus planner; otherwise just plan inline. (Informational; nothing is blocked.)"
    ;;
esac

# ── Combine + emit one additionalContext ─────────────────────────────────
combined=""
if [ -n "$memory_text" ]; then
  combined+="$memory_text"
fi
if [ -n "$router_text" ]; then
  [ -n "$combined" ] && combined+=$'\n\n'
  combined+="$router_text"
fi

[ -z "$combined" ] && exit 0

if command -v jq >/dev/null 2>&1; then
  jq -nc --arg ctx "$combined" \
    '{hookSpecificOutput: {hookEventName: "UserPromptSubmit", additionalContext: $ctx}}'
else
  esc=$(printf '%s' "$combined" \
    | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' \
    | awk 'BEGIN{ORS="\\n"} {print}')
  printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$esc"
fi

# Breadcrumbs on stderr.
[ -n "$router_text" ] && printf '[aims-router] intent=%s — factual planning note injected (no lock).\n' "$intent" >&2
[ "${#matched[@]}" -gt 0 ] && printf '[aims-memory] injected %d node(s)\n' "${#matched[@]}" >&2
exit 0
