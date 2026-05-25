#!/usr/bin/env bash
# For every leaf, report which of its external references have changed
# since the leaf's last_consolidated timestamp.
#
# Output (TSV, one row per changed reference):
#   <leaf>\t<ref>\t<reason>
#
# <reason> is one of:
#   external-file-mtime   (the file's mtime is newer)
#   claude-md-section-mtime  (CLAUDE.md mtime is newer; we don't track per-section)
#
# Used by consolidate.sh. Never modifies anything; never calls an LLM.
#
# Usage:  check-refs.sh [<leaf>]
#   With no args, checks all leaves. With a leaf path, only that one.

set -u

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
usage: check-refs.sh [<leaf>]

Compares each leaf's external_refs and claude_md_refs against the leaf's
last_consolidated timestamp. Emits TSV: <leaf> TAB <ref> TAB <reason>
for each reference that has changed since.
EOF
  exit 0
fi

CLAUDE_MD="${AIMS_CLAUDE_MD:-CLAUDE.md}"

# epoch_of <file>  — mtime as epoch seconds, or 0 if missing.
epoch_of() {
  local f="$1"
  [ -e "$f" ] || { printf '0\n'; return; }
  # GNU and BSD stat differ; try both.
  if stat -c %Y "$f" 2>/dev/null; then return; fi
  if stat -f %m "$f" 2>/dev/null; then return; fi
  printf '0\n'
}

# Parse an ISO-8601 UTC timestamp to epoch. 0 if unparseable.
iso_to_epoch() {
  local ts="$1"
  [ -z "$ts" ] && { printf '0\n'; return; }
  # GNU date
  if date -u -d "$ts" +%s 2>/dev/null; then return; fi
  # BSD date
  if date -u -j -f '%Y-%m-%dT%H:%M:%SZ' "$ts" +%s 2>/dev/null; then return; fi
  printf '0\n'
}

check_leaf() {
  local leaf="$1"
  local lc_iso lc_epoch
  lc_iso=$(fm_get "$leaf" last_consolidated)
  lc_epoch=$(iso_to_epoch "$lc_iso")

  # external_refs
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    case "$p" in
      "~/"*) p="${HOME}/${p#~/}" ;;
      "~")   p="${HOME}" ;;
    esac
    local pe; pe=$(epoch_of "$p")
    if [ "$pe" -gt "$lc_epoch" ]; then
      printf '%s\t%s\texternal-file-mtime\n' "$leaf" "$p"
    fi
  done < <(fm_list "$leaf" external_refs)

  # claude_md_refs — we don't track per-section mtimes, so we report the
  # leaf as having stale CLAUDE.md refs if CLAUDE.md itself changed and
  # the leaf has any claude_md_refs at all.
  if [ -r "$CLAUDE_MD" ]; then
    local cmd_epoch; cmd_epoch=$(epoch_of "$CLAUDE_MD")
    if [ "$cmd_epoch" -gt "$lc_epoch" ]; then
      while IFS= read -r h; do
        [ -z "$h" ] && continue
        printf '%s\t%s\tclaude-md-section-mtime\n' "$leaf" "$h"
      done < <(fm_list "$leaf" claude_md_refs)
    fi
  fi
}

if [ $# -ge 1 ] && [ -n "$1" ]; then
  check_leaf "$1"
else
  while IFS= read -r leaf; do
    [ -z "$leaf" ] && continue
    check_leaf "$leaf"
  done < <(list_leaves)
fi
