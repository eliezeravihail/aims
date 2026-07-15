#!/usr/bin/env bash
# Regenerate the node index of docs/memory/README.md from node frontmatter
# + each node's first Purpose line. Deterministic; no LLM (Track B of
# docs/plans/2026-07-15-memory-subsystem-diet.md).
#
# The index lives between marker comments:
#   <!-- BEGIN NODE INDEX -->
#   ...generated...
#   <!-- END NODE INDEX -->
#
# Usage:
#   readme-sync.sh           # rewrite the block in place
#   readme-sync.sh --check   # exit 1 on drift, change nothing
#
# Called automatically at the end of `mark.sh <node> consolidated`, and
# by lint.sh in --check mode. Exit 0 if the README or markers are absent
# (nothing to sync — e.g. a target project with a hand-rolled README).

set -u

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

README="$MEMORY_DIR/README.md"
[ -r "$README" ] || exit 0
grep -q '<!-- BEGIN NODE INDEX -->' "$README" || exit 0

gen_index() {
  while IFS= read -r leaf; do
    [ -z "$leaf" ] && continue
    node=$(fm_get "$leaf" node)
    purpose=$(awk '/^## Purpose/{p=1;next} /^## /{p=0} p && NF {print; exit}' "$leaf")
    printf -- '- `%s` — %s\n' "${node:-$leaf}" "${purpose:-(no purpose line)}"
  done < <(list_leaves)
}

idx=$(gen_index)
new=$(awk -v idx="$idx" '
  /<!-- BEGIN NODE INDEX -->/ { print; print idx; skip=1; next }
  /<!-- END NODE INDEX -->/   { skip=0 }
  !skip { print }
' "$README")

if [ "${1:-}" = "--check" ]; then
  if [ "$new" != "$(cat "$README")" ]; then
    printf '[aims-memory] README node index out of sync — run readme-sync.sh\n' >&2
    exit 1
  fi
  exit 0
fi

printf '%s\n' "$new" > "$README"
