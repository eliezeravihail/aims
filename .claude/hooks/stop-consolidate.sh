#!/usr/bin/env bash
# aims Stop hook — throttled in-band memory consolidation (ADR-0009).
#
# Stop fires after every Claude turn. Unconditional work here would
# spike turn cost, so throttle in bash:
#
#   Run consolidation only when
#       N_DIRTY >= AIMS_MEMORY_DIRTY_MAX   (default 5)
#     OR
#       (now - last_consolidated) >= AIMS_MEMORY_INTERVAL_SEC  (default 1800s)
#
# When the threshold trips, this hook does NOT call any LLM directly
# (per ADR-0009: there is no ANTHROPIC_API_KEY in this environment).
# Instead it builds a consolidation prompt in bash and injects it via
# the Stop-hook `decision: block` + `reason` contract; blocking keeps
# the turn going so the active Claude Code session performs the Edits
# in-band, ending with `bash .claude/memory/mark.sh <node> consolidated`.
#
# Override per project via .claude/memory/throttle.conf.
# Blocks the stop ONLY when the throttle trips (to inject the prompt);
# otherwise exits 0 with no output.

set -u

if [ -d ".claude/memory" ]; then
  MEM_HELPERS=".claude/memory"
elif [ -d "templates/memory" ]; then
  MEM_HELPERS="templates/memory"
else
  exit 0
fi

if [ -r ".claude/memory/throttle.conf" ]; then
  # shellcheck disable=SC1091
  . ".claude/memory/throttle.conf"
fi

DIRTY_MAX="${AIMS_MEMORY_DIRTY_MAX:-5}"
INTERVAL_SEC="${AIMS_MEMORY_INTERVAL_SEC:-1800}"
STATE_FILE="${AIMS_MEMORY_STATE_FILE:-.claude/memory/.last-consolidated}"
FORCE=0

case "${1:-}" in
  --force|-f) FORCE=1 ;;
esac

# ── Read payload once (used by URL harvest below + claim filter) ────────
payload=""
if [ ! -t 0 ]; then
  payload=$(cat 2>/dev/null || true)
fi
SESSION_ID=""
if [ -n "$payload" ] && command -v jq >/dev/null 2>&1; then
  SESSION_ID=$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null || true)
fi
SESSION_ID="${SESSION_ID:-default}"

# Harvest URLs from the session transcript (pure bash; no LLM).
TRANSCRIPT_URLS=""
if [ "$FORCE" -ne 1 ] && [ -n "$payload" ] && command -v jq >/dev/null 2>&1; then
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

mapfile -t DIRTY < <(bash "$MEM_HELPERS/find-dirty.sh" 2>/dev/null || true)
N_DIRTY=${#DIRTY[@]}

INBOX_NONEMPTY=0
INBOX_PATH="${AIMS_MEMORY_DIR:-docs/memory}/_inbox.md"
[ -s "$INBOX_PATH" ] && INBOX_NONEMPTY=1

# In-progress plan detection (for close-out nudge).
IN_PROGRESS_PLAN=""
if [ -d "docs/plans" ]; then
  IN_PROGRESS_PLAN=$(grep -lE '^Status:[[:space:]]*in-progress' \
    docs/plans/*.md 2>/dev/null | head -1 || true)
fi

if [ "$N_DIRTY" -eq 0 ] && [ "$INBOX_NONEMPTY" -eq 0 ] && [ -z "$IN_PROGRESS_PLAN" ]; then
  exit 0
fi

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
elif [ "$ELAPSED" -ge "$INTERVAL_SEC" ] && [ "$N_DIRTY" -gt 0 ]; then
  should_run=1
elif [ "$ELAPSED" -ge "$INTERVAL_SEC" ] && [ "$INBOX_NONEMPTY" -eq 1 ]; then
  should_run=1
elif [ "$ELAPSED" -ge "$INTERVAL_SEC" ] && [ -n "$IN_PROGRESS_PLAN" ]; then
  should_run=1
fi

[ "$should_run" -eq 0 ] && exit 0

# ── Multi-session claim filter (ADR-0018) ────────────────────────────────
# Skip dirty nodes that another session is already consolidating. A claim is
# `consolidating_by: <session_id>@<unix-ts>` in the node frontmatter; an
# entry older than CLAIM_TTL is treated as abandoned and may be reclaimed.
# All writes inside the flock so two stop hooks can't double-claim. flock
# absence (rare) degrades gracefully to a best-effort TOCTOU window.
CLAIM_TTL="${AIMS_CLAIM_TTL_SEC:-600}"
CLAIM_LOCK=".claude/memory/.claim-lock"
mkdir -p "$(dirname "$CLAIM_LOCK")"
CLAIMED=()

claim_one() {
  local leaf="$1" existing ex_sid ex_ts age
  existing=$(fm_get "$leaf" consolidating_by 2>/dev/null)
  if [ -n "$existing" ]; then
    ex_sid="${existing%@*}"
    ex_ts="${existing##*@}"
    case "$ex_ts" in ''|*[!0-9]*) ex_ts=0 ;; esac
    age=$((NOW - ex_ts))
    # Fresh claim by a different session → defer to them.
    if [ "$ex_sid" != "$SESSION_ID" ] && [ "$age" -lt "$CLAIM_TTL" ]; then
      return 1
    fi
  fi
  fm_set "$leaf" consolidating_by "${SESSION_ID}@${NOW}"
  return 0
}

# shellcheck source=_lib.sh
. "$MEM_HELPERS/_lib.sh"

if command -v flock >/dev/null 2>&1; then
  exec 9>>"$CLAIM_LOCK"
  if flock -n 9; then
    for leaf in "${DIRTY[@]}"; do
      [ -z "$leaf" ] && continue
      claim_one "$leaf" && CLAIMED+=("$leaf")
    done
    flock -u 9
  fi
  exec 9>&-
else
  for leaf in "${DIRTY[@]}"; do
    [ -z "$leaf" ] && continue
    claim_one "$leaf" && CLAIMED+=("$leaf")
  done
fi

DIRTY=("${CLAIMED[@]}")
N_DIRTY=${#DIRTY[@]}

# If the throttle tripped only because of dirty nodes and another session
# already took all of them, exit silently — no work for us this turn.
if [ "$N_DIRTY" -eq 0 ] && [ "$INBOX_NONEMPTY" -eq 0 ] && [ -z "$IN_PROGRESS_PLAN" ]; then
  exit 0
fi

# ── Build the per-node prompt sections in bash ────────────────
EXTRA_CTX="${AIMS_EXTRA_CONTEXT:-}"

prompt_parts=()
prompt_parts+=("[aims-memory] Consolidation queue is ready (per ADR-0009).
There are $N_DIRTY dirty node(s) below. Before responding to the user,
process each one in order: apply the Edit per the rules, then run the
mark.sh command at the end of its section. If there are more than 10
dirty nodes, handle the first 10 and report that the rest will be
caught on the next turn. Do NOT touch frontmatter dirty/last_touched/
last_consolidated — mark.sh owns those.")

if [ -n "$IN_PROGRESS_PLAN" ]; then
  prompt_parts+=("[aims-plan] In-progress plan detected: $IN_PROGRESS_PLAN
If the implementation steps in that plan are complete (or you just
finished implementing them), run the inline close-out per the /plan
command's Phase 4: verify steps, run \`## Verification\`, auto-decide
ADRs (create when clear architectural commitment; skip when bug/
refactor/doc/test/mechanical; ask only when borderline), set
\`Status: completed\`, append \`## Outcome\` + \`## Closing checks\`.
If implementation isn't done yet, ignore this nudge.")
fi

if [ -n "$EXTRA_CTX" ]; then
  prompt_parts+=("=== ADDITIONAL CONTEXT (from caller) ===
Mine for invariants (→ ## Invariants & gotchas), design rationale
(→ ## Design rationale), fixed bugs (→ ## Known issues > fixed, ONLY
if a real commit SHA is cited), and open design questions
(→ ## Open questions). Do NOT add content where the connection to
this node's code is weak.

$EXTRA_CTX")
fi

if [ -n "$TRANSCRIPT_URLS" ]; then
  prompt_parts+=("=== URLs CITED IN SESSION TRANSCRIPT ===
Consider for '## Pointers > External'. Only add a URL if it is clearly
about a given node's code; otherwise drop it. Format:
  - External: <URL> — <one-line context>

$TRANSCRIPT_URLS")
fi

# Per-node sections (capped at 10 to keep prompt size bounded).
PROCESSED=0
for leaf in "${DIRTY[@]}"; do
  [ -z "$leaf" ] && continue
  [ "$PROCESSED" -ge 10 ] && break
  section=$(bash "$MEM_HELPERS/consolidate.sh" "$leaf" 2>/dev/null || true)
  [ -n "$section" ] && prompt_parts+=("$section")
  PROCESSED=$((PROCESSED + 1))
done

# Inbox section, if any.
if [ "$INBOX_NONEMPTY" -eq 1 ]; then
  inbox_section=$(bash "$MEM_HELPERS/classify-inbox.sh" 2>/dev/null || true)
  [ -n "$inbox_section" ] && prompt_parts+=("$inbox_section")
fi

# Assemble.
full_prompt=$(printf '%s\n\n' "${prompt_parts[@]}")

# Bump the throttle state file so we don't re-nudge on the very next
# turn while the model is still working on this batch.
mkdir -p "$(dirname "$STATE_FILE")"
printf '%s\n' "$NOW" > "$STATE_FILE"

# Emit JSON for Claude Code's Stop hook contract. A Stop hook injects an
# instruction by blocking the stop: `decision: block` keeps the turn going
# and feeds `reason` back to the model as the work to do. (`additionalContext`
# via hookSpecificOutput is not valid for the Stop event.) The throttle state
# is already bumped above, so this won't re-fire on the very next turn.
if command -v jq >/dev/null 2>&1; then
  jq -nc --arg r "$full_prompt" \
    '{decision: "block", reason: $r}'
else
  esc=$(printf '%s' "$full_prompt" \
    | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' \
    | awk 'BEGIN{ORS="\\n"} {print}')
  printf '{"decision":"block","reason":"%s"}\n' "$esc"
fi

printf '[aims-memory] queued %d node(s) for in-band consolidation\n' "$PROCESSED" >&2
exit 0
