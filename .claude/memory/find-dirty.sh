#!/usr/bin/env bash
# Print the relative path of every leaf with `dirty: true` in its frontmatter.
# Empty output if nothing is dirty.
#
# Usage:  find-dirty.sh

set -u

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
usage: find-dirty.sh

Prints (one per line) the path of every memory leaf whose frontmatter
has `dirty: true`. Output is empty if no leaves are dirty.
EOF
  exit 0
fi

while IFS= read -r leaf; do
  [ -z "$leaf" ] && continue
  val=$(fm_get "$leaf" dirty)
  if [ "$val" = "true" ]; then
    printf '%s\n' "$leaf"
  fi
done < <(list_leaves)
