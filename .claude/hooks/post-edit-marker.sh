#!/usr/bin/env bash
# aims PostToolUse hook on Edit | Write | MultiEdit | NotebookEdit.
#
# PHILOSOPHY: inform, never block / never hard-lock the node (overhaul plan
# docs/plans/2026-06-01-aims-overhaul.md). Always exits 0. Three jobs, all
# information-only:
#   1. Mark every memory leaf whose `code:` references the edited file dirty
#      (delegates to mark.sh, which also routes unmatched paths to _inbox.md).
#   2. Stamp an ADVISORY marker (sidecar <leaf>.lock = session-id + mtime) on
#      each matched node so concurrent sessions can coordinate — NOT a block.
#   3. Inject a FACTUAL additionalContext note naming the node(s) and describing
#      any concurrent-edit situation. Factual, never imperative (an imperative
#      would trip Claude's prompt-injection defense and be shown to the user).
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
# `code:` lists. Cross-platform: Windows drive-letter/backslash + git-bash MSYS
# ($PWD = /c/...). canon_lc folds to one lower form for the prefix TEST; the
# returned suffix is sliced from the case-preserved forward-slashed form (both
# forms are length-aligned because `C:/` and `/c/` are both 3 chars).
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

# Skip non-source surfaces (the memory tree itself, tooling, vendored dirs).
case "$rel" in
  .claude/*|.git/*|*/node_modules/*|*/dist/*|*/build/*|docs/memory/*) exit 0 ;;
esac

# (1) Canonical dirty-mark + inbox routing.
bash "$MEM_HELPERS/mark.sh" "$rel" >/dev/null 2>&1 || true

# (2)+(3) Resolve matching node(s); stamp advisory markers; build a factual note.
now=$(date -u +%s 2>/dev/null || echo 0)
notes=""
while IFS= read -r leaf; do
  [ -z "$leaf" ] && continue
  hit=0
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    if path_matches "$rel" "$p"; then hit=1; break; fi
  done < <(fm_list "$leaf" code)
  [ "$hit" -eq 1 ] || continue

  node=$(fm_get "$leaf" node); node="${node:-$leaf}"
  # ADR-0024: the advisory marker uses `.marker`; the strict consolidation
  # mutex (managed by stop-consolidate.sh / mark.sh) uses `.lock`. The two
  # protocols share a leaf but never a path.
  marker="${leaf%.md}.marker"
  detail=""
  clobber=1
  if [ -f "$marker" ]; then
    lsid=$(head -n1 "$marker" 2>/dev/null || true)
    lmt=$(stat -c %Y "$marker" 2>/dev/null || stat -f %m "$marker" 2>/dev/null || echo 0)
    age=$(( now - lmt ))
    if [ "$lsid" = "$sid" ]; then
      :                                   # same session — refresh silently
    elif [ "$age" -lt "$STALE" ]; then
      detail=" An advisory marker from a different session (sid=${lsid:-?}) was set ${age}s ago (< ${STALE}s window) — a concurrent edit of this node by another session is possible."
      clobber=0                           # do not overwrite a live peer's marker
    else
      detail=" A stale advisory marker from another session (sid=${lsid:-?}, ${age}s old) was taken over."
    fi
  fi
  # M4 (ADR-0024): refuse to follow a symlink (malicious repo could plant one
  # at the marker path to clobber an arbitrary user-writable file). Use O_EXCL
  # via `set -C` after rm so the write is atomic on the truncate path too.
  if [ "$clobber" -eq 1 ] && [ ! -L "$marker" ]; then
    rm -f "$marker" 2>/dev/null || true
    (set -C; printf '%s\n%s\n' "$sid" "$rel" > "$marker") 2>/dev/null || true
  fi
  notes="${notes}${notes:+ }Memory node ${node} (${leaf}) documents ${rel} (just edited); its body may now be stale.${detail}"
done < <(list_leaves)

[ -z "$notes" ] && exit 0

NOTE="aims memory: ${notes} Per project convention, the relevant node body is updated to reflect such changes; when a concurrent edit by another session is reported, the user is asked before updating. (Factual context; nothing is blocked.)"

if command -v jq >/dev/null 2>&1; then
  jq -nc --arg c "$NOTE" '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$c}}'
else
  esc=$(printf '%s' "$NOTE" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')
  printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s"}}\n' "$esc"
fi
exit 0
