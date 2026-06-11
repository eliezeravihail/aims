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

# L4: this hook uses mapfile (bash 4) and `declare -A`-style features
# downstream. macOS ships bash 3.2 by default; rather than polyfill, emit a
# factual breadcrumb and exit 0 (informational, per ADR-0020). To upgrade:
#     brew install bash
if (( BASH_VERSINFO[0] < 4 )); then
  printf '[aims] stop-consolidate.sh: bash >= 4 required; current is %s. Skipping.\n' \
    "$BASH_VERSION" >&2
  exit 0
fi

if [ -d ".claude/memory" ]; then
  MEM_HELPERS=".claude/memory"
elif [ -d "templates/memory" ]; then
  MEM_HELPERS="templates/memory"
else
  exit 0
fi

# Source shared helpers (json_escape, etc.). Best-effort — the hook still
# works without _lib.sh, just with the older inline escaper.
# shellcheck disable=SC1091
[ -r "$MEM_HELPERS/_lib.sh" ] && . "$MEM_HELPERS/_lib.sh"

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

# ── Sidecar lockfile filter (ADR-0019, supersedes ADR-0018) ─────────────
# Drop dirty leaves another session is already consolidating. The mutex is a
# sidecar `<leaf-without-md>.lock` next to the node, created with O_EXCL
# (bash `set -C`). Body = our SESSION_ID; mtime drives stale-detection.
# `mark.sh <node> consolidated` removes the file; a trap below releases on
# any abnormal exit between claim and `mark.sh`.
LOCK_TTL="${AIMS_LOCK_TTL_SEC:-600}"
CLAIMED=()
HELD_LOCKS=()

reap_stale_lock() {
  local lock="$1"
  [ -e "$lock" ] || return 0
  if find "$lock" -mmin "+$((LOCK_TTL / 60))" -print 2>/dev/null | grep -q .; then
    rm -f "$lock"
  fi
}

try_claim() {
  local leaf="$1" lock="${leaf%.md}.lock"
  reap_stale_lock "$lock"
  # noclobber → O_CREAT|O_EXCL atomic create.
  if (set -C; printf '%s\n' "$SESSION_ID" > "$lock") 2>/dev/null; then
    HELD_LOCKS+=("$lock")
    return 0
  fi
  return 1
}

for leaf in "${DIRTY[@]}"; do
  [ -z "$leaf" ] && continue
  try_claim "$leaf" && CLAIMED+=("$leaf")
done

# Release any lock we still hold if we die before the model marks the node
# consolidated. mark.sh removes its own lock on success.
release_held_locks() {
  for l in "${HELD_LOCKS[@]}"; do
    [ -e "$l" ] || continue
    # Only remove if WE own it (defensive — a reclaim by another session
    # after TTL expiry would have a different SESSION_ID inside).
    owner=$(head -n1 "$l" 2>/dev/null || true)
    [ "$owner" = "$SESSION_ID" ] && rm -f "$l"
  done
}
# Release held mutexes ONLY on abnormal exit. On the normal success path we
# hand the locks to the model — `mark.sh <node> consolidated` removes them
# once each node is rewritten. A prior `trap … EXIT` deleted the mutex on
# every normal exit, defeating the protocol entirely (ADR-0024).
trap release_held_locks INT TERM HUP

DIRTY=("${CLAIMED[@]}")
N_DIRTY=${#DIRTY[@]}

# If the throttle tripped only because of dirty nodes and another session
# already took all of them, exit silently — no work for us this turn.
if [ "$N_DIRTY" -eq 0 ] && [ "$INBOX_NONEMPTY" -eq 0 ] && [ -z "$IN_PROGRESS_PLAN" ]; then
  exit 0
fi

# ── Repeat-offender detection (ADR-0027) ──────────────────────
# The previous Stop fire wrote a snapshot of the work it asked the model
# to do. If we now see the SAME state (same inbox bytes, same dirty leaf
# set), the prior `===[aims: <msg>]===` report drained nothing — it was
# a false report. We don't block; we name the discrepancy factually so
# the next attempt cannot proceed without seeing it.
SNAPSHOT_FILE="${AIMS_MEMORY_DIR:-docs/memory}/.last-report-snapshot"
N_INBOX_LINES=0
[ -f "$INBOX_PATH" ] && N_INBOX_LINES=$(grep -c '^- ' "$INBOX_PATH" 2>/dev/null || echo 0)
# State fingerprint: inbox content + sorted dirty leaf paths.
state_now=$( {
  [ -f "$INBOX_PATH" ] && cat "$INBOX_PATH"
  printf -- '--dirty--\n'
  printf '%s\n' "${DIRTY[@]}" | sort
} | { command -v sha1sum >/dev/null 2>&1 && sha1sum | cut -d' ' -f1; } )

PREV_LIED=0
PREV_N_DIRTY=0
PREV_N_INBOX=0
if [ -r "$SNAPSHOT_FILE" ]; then
  # Snapshot format: one line each — N_DIRTY, N_INBOX, state_hash, emit_ts.
  PREV_N_DIRTY=$(sed -n '1p' "$SNAPSHOT_FILE" 2>/dev/null || echo 0)
  PREV_N_INBOX=$(sed -n '2p' "$SNAPSHOT_FILE" 2>/dev/null || echo 0)
  PREV_HASH=$(sed -n '3p' "$SNAPSHOT_FILE" 2>/dev/null || true)
  case "$PREV_N_DIRTY" in ''|*[!0-9]*) PREV_N_DIRTY=0 ;; esac
  case "$PREV_N_INBOX" in ''|*[!0-9]*) PREV_N_INBOX=0 ;; esac
  # The prior emit asked the model to drain SOMETHING (dirty or inbox);
  # if state hash is byte-identical to what was sent, the model didn't.
  if [ -n "$PREV_HASH" ] && [ "$PREV_HASH" = "$state_now" ] \
     && [ $((PREV_N_DIRTY + PREV_N_INBOX)) -gt 0 ]; then
    PREV_LIED=1
  fi
fi

# ── Build the per-node prompt sections in bash ────────────────
EXTRA_CTX="${AIMS_EXTRA_CONTEXT:-}"

prompt_parts=()
if [ "$PREV_LIED" -eq 1 ]; then
  prompt_parts+=("[aims-memory] DISCREPANCY DETECTED (ADR-0027). The previous Stop hook fired with $PREV_N_DIRTY dirty node(s) and $PREV_N_INBOX inbox bullet(s); a \`===[aims: <msg>]===\` report was emitted. State has NOT changed since: the same dirty set and the same inbox bytes are still present. The previous report did not match measured state. Do the work this turn before any reply: apply the Edits below, run the mark.sh commands, drain the inbox bullets per the classification rules. Do not emit \`queue drained\` (or any drain-claim) unless the inbox file is actually empty and zero leaves are dirty.")
fi
prompt_parts+=("[aims-memory] Consolidation queue is ready (per ADR-0009).
There are $N_DIRTY dirty node(s) below. Before responding to the user,
process each one in order: apply the Edit per the rules, then run the
mark.sh command at the end of its section. If there are more than 10
dirty nodes, handle the first 10 and report that the rest will be
caught on the next turn. Do NOT touch frontmatter dirty/last_touched/
last_consolidated — mark.sh owns those.
Reply-format: report this consolidation pass to the user as a single
short line in the form \`===[aims: <message>]===\` — examples:
\`===[aims: nodes updated]===\`, \`===[aims: queue drained]===\`,
\`===[aims: 4 dirty]===\`. One line only, no per-node prose unless the
user asks, no opening/closing wrapper. Regular conversational mentions
of aims topics elsewhere in the reply are NOT prefixed.
The drain-claim words (\`queue drained\`, \`nodes updated\`, \`inbox cleared\`)
are reserved — emit them ONLY when the corresponding measured state has
actually changed (inbox empty, dirty count zero). Otherwise pick a
state-accurate message (e.g. \`N dirty, M inbox\`).")

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

# ADR-0027: write the report snapshot AFTER we've decided to emit. Next
# Stop fire will compare against it; if state is unchanged but the model
# emitted a drain-claim reply between the two fires, the discrepancy
# breadcrumb prepends to the next prompt.
mkdir -p "$(dirname "$SNAPSHOT_FILE")"
{
  printf '%s\n' "$N_DIRTY"
  printf '%s\n' "$N_INBOX_LINES"
  printf '%s\n' "$state_now"
  printf '%s\n' "$NOW"
} > "$SNAPSHOT_FILE"

# Emit JSON for Claude Code's Stop hook contract. A Stop hook injects an
# instruction by blocking the stop: `decision: block` keeps the turn going
# and feeds `reason` back to the model as the work to do. (`additionalContext`
# via hookSpecificOutput is not valid for the Stop event.) The throttle state
# is already bumped above, so this won't re-fire on the very next turn.
if command -v jq >/dev/null 2>&1; then
  jq -nc --arg r "$full_prompt" \
    '{decision: "block", reason: $r}'
else
  # M2: shared json_escape — handles tabs / CR / all C0 control chars. The
  # reason field embeds `git log -p` diffs which are full of tabs; the prior
  # sed-only escaper produced JSON that jq-less consumers couldn't parse.
  if command -v json_escape >/dev/null 2>&1; then
    esc=$(json_escape "$full_prompt")
  else
    esc=$(printf '%s' "$full_prompt" \
      | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' \
      | awk 'BEGIN{ORS="\\n"} {print}')
  fi
  printf '{"decision":"block","reason":"%s"}\n' "$esc"
fi

printf '[aims-memory] queued %d node(s) for in-band consolidation\n' "$PROCESSED" >&2
exit 0
