#!/usr/bin/env bash
# Lint the memory tree.
# For every leaf, verify that:
#   - each path in `code:` exists on disk
#   - each path in `external_refs:` exists on disk
#   - each `claude_md_refs:` heading exists in CLAUDE.md
# Reports orphans to stdout, one per line.  Exit code 0 (informational).
#
# Usage:  lint.sh

set -u

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
usage: lint.sh

Walks every leaf under docs/memory/ and reports references that do
not resolve on disk. Always exits 0.
EOF
  exit 0
fi

CLAUDE_MD="${AIMS_CLAUDE_MD:-CLAUDE.md}"

# Collect CLAUDE.md headings (without leading #s).
declare -A CLAUDE_HEADINGS=()
if [ -r "$CLAUDE_MD" ]; then
  while IFS= read -r h; do
    [ -z "$h" ] && continue
    CLAUDE_HEADINGS["$h"]=1
  done < <(awk '/^#+ /{ sub(/^#+ +/, ""); print }' "$CLAUDE_MD")
fi

issues=0

while IFS= read -r leaf; do
  [ -z "$leaf" ] && continue

  # code: paths
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    base="${p%%:*}"   # strip :start-end if present
    if ! [ -e "$base" ]; then
      printf '%s: code path missing: %s\n' "$leaf" "$p"
      issues=$((issues + 1))
    fi
  done < <(fm_list "$leaf" code)

  # external_refs: paths (already reduced to just the path by fm_list)
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    # Expand ~ for files under the user's home.
    case "$p" in
      "~/"*) p="${HOME}/${p#~/}" ;;
      "~") p="${HOME}" ;;
    esac
    if ! [ -e "$p" ]; then
      printf '%s: external_ref missing: %s\n' "$leaf" "$p"
      issues=$((issues + 1))
    fi
  done < <(fm_list "$leaf" external_refs)

  # claude_md_refs: headings
  while IFS= read -r h; do
    [ -z "$h" ] && continue
    if [ -z "${CLAUDE_HEADINGS[$h]+x}" ]; then
      printf '%s: claude_md_ref missing in %s: %s\n' "$leaf" "$CLAUDE_MD" "$h"
      issues=$((issues + 1))
    fi
  done < <(fm_list "$leaf" claude_md_refs)
done < <(list_leaves)

if [ "$issues" -eq 0 ]; then
  printf '[aims-memory] lint: clean (%d leaves)\n' "$(list_leaves | wc -l)" >&2
fi

exit 0
