#!/usr/bin/env bash
# aims Stop hook — throttled in-band insight consolidation over a Capsa
# capsule (.capsa/). (ADR-0009 / ADR-0028.)
#
# Stop fires after every Claude turn. Unconditional work here would
# spike turn cost, so throttle in bash:
#
#   Run consolidation only when
#       N_STALE >= AIMS_MEMORY_DIRTY_MAX   (default 5)
#     OR
#       (now - last consolidation run) >= AIMS_MEMORY_INTERVAL_SEC  (def 1800s)
#
# "Stale" is COMPUTED (find-dirty.sh compares each insight's `updated:` date
# against git; Capsa §1.4), never a stored flag. When the threshold trips this
# hook does NOT call any LLM (there is no ANTHROPIC_API_KEY here). It builds a
# consolidation prompt in bash and injects it via the Stop-hook
# `decision: block` + `reason` contract; blocking keeps the turn going so the
# active Claude Code session performs the Edits in-band, ending each insight
# with `bash <helpers>/mark.sh <insight> consolidated` (which bumps `updated:`).
#
# All aims run-state (throttle timer, report snapshot, inbox) lives OUTSIDE the
# capsule under .claude/ (Capsa §1.5). Override per project via throttle.conf.
# Blocks the stop ONLY when the throttle trips; otherwise exits 0 silently.

set -u

# L4: this hook uses mapfile (bash 4). macOS ships bash 3.2; rather than
# polyfill, emit a factual breadcrumb and exit 0 (informational, ADR-0020).
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

# Source shared helpers (json_escape, plans_with_status, list_insights, etc.).
# shellcheck disable=SC1091
[ -r "$MEM_HELPERS/_lib.sh" ] && . "$MEM_HELPERS/_lib.sh"
command -v plans_with_status >/dev/null 2>&1 || plans_with_status() {
  local d="$1" want="$2" f
  [ -d "$d" ] || return
  for f in "$d"/*.md; do
    [ -e "$f" ] || continue
    grep -qE "^status:[[:space:]]*$want" "$f" 2>/dev/null && printf '%s\n' "$f"
  done
  return 0
}

if [ -r "$MEM_HELPERS/throttle.conf" ]; then
  # shellcheck disable=SC1091
  . "$MEM_HELPERS/throttle.conf"
fi

DIRTY_MAX="${AIMS_MEMORY_DIRTY_MAX:-5}"
INTERVAL_SEC="${AIMS_MEMORY_INTERVAL_SEC:-1800}"
STATE_FILE="${AIMS_MEMORY_STATE_FILE:-$STATE_DIR/.last-consolidated}"
FORCE=0

case "${1:-}" in
  --force|-f) FORCE=1 ;;
esac

# ── Read payload once (used by the URL harvest below) ───────────────────
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
INBOX_PATH="$INBOX"
[ -s "$INBOX_PATH" ] && INBOX_NONEMPTY=1

# In-progress plan detection (for close-out nudge). Capsa plans carry a
# frontmatter `status:` field; `in_progress` is the active value.
IN_PROGRESS_PLAN=""
if [ -d "$PLANS_DIR" ]; then
  IN_PROGRESS_PLAN=$(plans_with_status "$PLANS_DIR" in_progress | head -1)
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

# ── No consolidation mutex (ADR-0030) ──
# The strict sidecar `.lock` protocol is retired: the tool runs single-session
# in practice, and the worst uncoordinated case — two sessions consolidating
# one insight — is a last-write-wins delta append. Cross-session awareness
# remains the post-edit-marker's advisory marker (kept outside the capsule).

# ── Repeat-offender detection (ADR-0027) ──────────────────────
# The previous Stop fire wrote a snapshot of the work it asked the model to do.
# If we now see the SAME state (same inbox bytes, same stale insight set), the
# prior `===[aims: <msg>]===` report drained nothing. We don't block; we name
# the discrepancy factually so the next attempt cannot proceed without it.
SNAPSHOT_FILE="${AIMS_SNAPSHOT_FILE:-$STATE_DIR/.last-report-snapshot}"
N_INBOX_LINES=0
[ -f "$INBOX_PATH" ] && N_INBOX_LINES=$(grep -c '^- ' "$INBOX_PATH" 2>/dev/null || echo 0)
# State fingerprint: inbox content + sorted stale insight paths.
state_now=$( {
  [ -f "$INBOX_PATH" ] && cat "$INBOX_PATH"
  printf -- '--dirty--\n'
  printf '%s\n' "${DIRTY[@]}" | sort
} | { command -v sha1sum >/dev/null 2>&1 && sha1sum | cut -d' ' -f1; } )

PREV_LIED=0
PREV_N_DIRTY=0
PREV_N_INBOX=0
if [ -r "$SNAPSHOT_FILE" ]; then
  PREV_N_DIRTY=$(sed -n '1p' "$SNAPSHOT_FILE" 2>/dev/null || echo 0)
  PREV_N_INBOX=$(sed -n '2p' "$SNAPSHOT_FILE" 2>/dev/null || echo 0)
  PREV_HASH=$(sed -n '3p' "$SNAPSHOT_FILE" 2>/dev/null || true)
  case "$PREV_N_DIRTY" in ''|*[!0-9]*) PREV_N_DIRTY=0 ;; esac
  case "$PREV_N_INBOX" in ''|*[!0-9]*) PREV_N_INBOX=0 ;; esac
  if [ -n "$PREV_HASH" ] && [ "$PREV_HASH" = "$state_now" ] \
     && [ $((PREV_N_DIRTY + PREV_N_INBOX)) -gt 0 ]; then
    PREV_LIED=1
  fi
fi

# ── Build the per-insight prompt sections in bash ────────────────
EXTRA_CTX="${AIMS_EXTRA_CONTEXT:-}"

prompt_parts=()
if [ "$PREV_LIED" -eq 1 ]; then
  prompt_parts+=("[aims-memory] DISCREPANCY DETECTED (ADR-0027). The previous Stop hook fired with $PREV_N_DIRTY stale insight(s) and $PREV_N_INBOX inbox bullet(s); a \`===[aims: <msg>]===\` report was emitted. State has NOT changed since: the same stale set and the same inbox bytes are still present. The previous report did not match measured state. Do the work this turn before any reply: apply the Edits below, run the mark.sh commands, drain the inbox bullets per the classification rules. Do not emit \`queue drained\` (or any drain-claim) unless the inbox file is actually empty and zero insights are stale.")
fi
prompt_parts+=("[aims-memory] Consolidation queue is ready (ADR-0009 / ADR-0028).
There are $N_DIRTY stale insight(s) below — insights in .capsa/insights/
whose code_globs changed after their \`updated:\` date. Before responding to
the user, process each one in order: append a dated delta line to the insight
body per the rules, then run the mark.sh command at the end of its section
(which bumps \`updated:\` to today — clearing the computed staleness). If there
are more than 10 stale insights, handle the first 10 and report that the rest
will be caught on the next turn. Do NOT hand-edit the \`updated:\` field —
\`mark.sh <insight> consolidated\` owns it.
Reply-format: report this consolidation pass to the user as a single
short line in the form \`===[aims: <message>]===\` — examples:
\`===[aims: insights updated]===\`, \`===[aims: queue drained]===\`,
\`===[aims: 4 stale]===\`. One line only, no per-insight prose unless the
user asks, no opening/closing wrapper. Regular conversational mentions
of aims topics elsewhere in the reply are NOT prefixed.
The drain-claim words (\`queue drained\`, \`insights updated\`, \`inbox cleared\`)
are reserved — emit them ONLY when the corresponding measured state has
actually changed (inbox empty, stale count zero). Otherwise pick a
state-accurate message (e.g. \`N stale, M inbox\`).")

if [ -n "$IN_PROGRESS_PLAN" ]; then
  prompt_parts+=("[aims-plan] In-progress plan detected: $IN_PROGRESS_PLAN
If the implementation steps in that plan are complete (or you just
finished implementing them), run the inline close-out per the /plan
command's Phase 4: verify steps, run \`## Verification\`, auto-decide
ADRs (create a .capsa/decisions/ record when there is a clear
architectural commitment; skip when bug/refactor/doc/test/mechanical;
ask only when borderline), set the plan's frontmatter \`status: completed\`
and \`completed:\` date, append \`## Outcome\` + \`## Closing checks\`.
If implementation isn't done yet, ignore this nudge.")
fi

if [ -n "$EXTRA_CTX" ]; then
  prompt_parts+=("=== ADDITIONAL CONTEXT (from caller) ===
Mine for invariants, design rationale, fixed bugs (ONLY if a real commit
SHA is cited), and open design questions. Append as a dated delta line to
the relevant insight body. Do NOT add content where the connection to
this insight's code is weak.

$EXTRA_CTX")
fi

if [ -n "$TRANSCRIPT_URLS" ]; then
  prompt_parts+=("=== URLs CITED IN SESSION TRANSCRIPT ===
Consider citing under an insight's body as an external pointer. Only add a
URL if it is clearly about a given insight's code; otherwise drop it.

$TRANSCRIPT_URLS")
fi

# Per-insight sections (capped at 10 to keep prompt size bounded).
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

# Bump the throttle state file so we don't re-nudge on the very next turn.
mkdir -p "$(dirname "$STATE_FILE")"
printf '%s\n' "$NOW" > "$STATE_FILE"

# ADR-0027: write the report snapshot AFTER we've decided to emit.
mkdir -p "$(dirname "$SNAPSHOT_FILE")"
{
  printf '%s\n' "$N_DIRTY"
  printf '%s\n' "$N_INBOX_LINES"
  printf '%s\n' "$state_now"
  printf '%s\n' "$NOW"
} > "$SNAPSHOT_FILE"

# Emit JSON for Claude Code's Stop hook contract. `decision: block` keeps the
# turn going and feeds `reason` back to the model as the work to do.
if command -v jq >/dev/null 2>&1; then
  jq -nc --arg r "$full_prompt" \
    '{decision: "block", reason: $r}'
else
  if command -v json_escape >/dev/null 2>&1; then
    esc=$(json_escape "$full_prompt")
  else
    esc=$(printf '%s' "$full_prompt" \
      | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' \
      | awk 'BEGIN{ORS="\\n"} {print}')
  fi
  printf '{"decision":"block","reason":"%s"}\n' "$esc"
fi

printf '[aims-memory] queued %d insight(s) for in-band consolidation\n' "$PROCESSED" >&2
exit 0
