#!/usr/bin/env bash
# aims PostToolUse hook on Edit | Write | MultiEdit | NotebookEdit, over a
# Capsa capsule (.capsa/).
#
# PHILOSOPHY: inform, never block (ADR-0020). Always exits 0. Three jobs, all
# information-only:
#   1. Route the edited path: if no insight's `code_globs` covers it, mark.sh
#      appends it to the out-of-capsule inbox.
#   2. Refresh an ADVISORY marker (a freshness-cache sidecar) for each insight
#      whose globs match, so concurrent sessions can coordinate — NOT a block.
#      Markers live OUTSIDE the capsule under .claude/ (Capsa §1.5: no run-state
#      in the capsule).
#   3. Inject a FACTUAL additionalContext note naming the insight(s) that now
#      may be stale. Staleness itself is COMPUTED (Capsa §1.4), not stored;
#      this note is just the timely heads-up. Factual, never imperative.
#
# Concurrency (advisory only): same session refreshes its marker silently;
# another session's marker older than AIMS_NODE_LOCK_STALE_SEC (default 3600s)
# is taken over; a fresher one is reported as a possible concurrent edit (the
# documented convention then has the model ask the user before updating).

set -u

if   [ -d ".claude/memory" ];   then MEM_HELPERS=".claude/memory"
elif [ -d "templates/memory" ]; then MEM_HELPERS="templates/memory"
else exit 0; fi
# shellcheck source=/dev/null
. "$MEM_HELPERS/_lib.sh"

STALE="${AIMS_NODE_LOCK_STALE_SEC:-3600}"
MARKER_DIR="${AIMS_MARKER_DIR:-$STATE_DIR/markers}"
payload=$(cat || true)

j() { command -v jq >/dev/null 2>&1 && printf '%s' "$payload" | jq -r "$1 // empty" 2>/dev/null; }

target=$(j '.tool_input.file_path // .tool_input.path // .tool_input.notebook_path')
[ -z "$target" ] && target=$(printf '%s' "$payload" \
  | grep -oE '"(file_path|notebook_path|path)"[[:space:]]*:[[:space:]]*"[^"]+"' \
  | head -1 | sed -E 's/.*"[^"]+"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')
[ -z "$target" ] && exit 0

sid=$(j '.session_id')
[ -z "$sid" ] && sid=$(printf '%s' "$payload" \
  | grep -oE '"session_id"[[:space:]]*:[[:space:]]*"[^"]+"' \
  | head -1 | sed -E 's/.*"([^"]+)"[^"]*$/\1/')
sid="${sid:-unknown}"

# Normalize to a repo-relative, CASE-PRESERVED path so it matches the mixed-case
# `code_globs` lists. Cross-platform: Windows drive-letter/backslash + git-bash
# MSYS ($PWD = /c/...). canon_lc folds to one lower form for the prefix TEST;
# the returned suffix is sliced from the case-preserved forward-slashed form
# (both forms are length-aligned because `C:/` and `/c/` are both 3 chars).
canon_lc() { printf '%s' "$1" | sed -e 's#\\#/#g' -e 's#^\([A-Za-z]\):/#/\1/#' -e 's#//*#/#g' | tr '[:upper:]' '[:lower:]'; }
norm_fwd() { printf '%s' "$1" | sed -e 's#\\#/#g' -e 's#//*#/#g'; }

rel=""
nlc=$(canon_lc "$target"); nfwd=$(norm_fwd "$target")
case "$nlc" in
  /*)
    for base in "$PWD" "$(git rev-parse --show-toplevel 2>/dev/null || true)"; do
      [ -n "$base" ] || continue
      blc=$(canon_lc "$base")
      case "$nlc" in
        "$blc"/*) off=$(( ${#blc} + 1 )); rel="${nfwd:off}"; break ;;
      esac
    done
    [ -z "$rel" ] && exit 0   # absolute path outside the repo
    ;;
  *) rel="$nfwd" ;;           # already relative
esac

# Skip non-source surfaces: the capsule itself (records are data, not the code
# insights track), aims run-state, git internals, vendored/build dirs.
case "$rel" in
  .capsa/*|.claude/*|.git/*|*/node_modules/*|*/dist/*|*/build/*) exit 0 ;;
esac

# (1) Route the edited path; unmatched paths land in the out-of-capsule inbox.
bash "$MEM_HELPERS/mark.sh" "$rel" >/dev/null 2>&1 || true

# Flatten an insight path to a single marker filename under MARKER_DIR.
marker_path() { printf '%s/%s.marker' "$MARKER_DIR" "$(printf '%s' "$1" | tr '/' '_')"; }

# (2)+(3) Resolve matching insight(s); refresh advisory markers; build a note.
now=$(date -u +%s 2>/dev/null || echo 0)
notes=""
while IFS= read -r leaf; do
  [ -z "$leaf" ] && continue
  hit=0
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    if path_matches "$rel" "$p"; then hit=1; break; fi
  done < <(insight_globs "$leaf")
  [ "$hit" -eq 1 ] || continue

  title=$(fm_get "$leaf" title); title="${title:-$leaf}"
  marker=$(marker_path "$leaf")
  detail=""
  clobber=1
  if [ -f "$marker" ]; then
    lsid=$(head -n1 "$marker" 2>/dev/null || true)
    lmt=$(stat -c %Y "$marker" 2>/dev/null || stat -f %m "$marker" 2>/dev/null || echo 0)
    age=$(( now - lmt ))
    if [ "$lsid" = "$sid" ]; then
      :                                   # same session — refresh silently
    elif [ "$age" -lt "$STALE" ]; then
      detail=" An advisory marker from a different session (sid=${lsid:-?}) was set ${age}s ago (< ${STALE}s window) — a concurrent edit of this insight by another session is possible."
      clobber=0                           # do not overwrite a live peer's marker
    else
      detail=" A stale advisory marker from another session (sid=${lsid:-?}, ${age}s old) was taken over."
    fi
  fi
  # Refuse to follow a symlink (a malicious repo could plant one at the marker
  # path to clobber an arbitrary user-writable file). O_EXCL via `set -C`.
  if [ "$clobber" -eq 1 ] && [ ! -L "$marker" ]; then
    mkdir -p "$MARKER_DIR" 2>/dev/null || true
    rm -f "$marker" 2>/dev/null || true
    (set -C; printf '%s\n%s\n' "$sid" "$rel" > "$marker") 2>/dev/null || true
  fi
  notes="${notes}${notes:+ }Insight \"${title}\" (${leaf}) documents ${rel} (just edited); it may now be stale.${detail}"
done < <(list_insights)

[ -z "$notes" ] && exit 0

NOTE="aims memory: ${notes} Per project convention, the relevant insight body is updated to reflect such changes; when a concurrent edit by another session is reported, the user is asked before updating. (Factual context; nothing is blocked.)"

if command -v jq >/dev/null 2>&1; then
  jq -nc --arg c "$NOTE" '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$c}}'
else
  # shared json_escape — handles tabs / CR / all C0 control chars.
  esc=$(json_escape "$NOTE")
  printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s"}}\n' "$esc"
fi
exit 0
