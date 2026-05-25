#!/usr/bin/env bash
# Mark every leaf that references <changed_path> as dirty.
# If no leaf references it, append to docs/memory/_inbox.md.
#
# Usage:  mark.sh <changed_path>
# Output: count of leaves marked (single integer to stdout).
#
# Pure bash + awk + sed. No LLM. Designed to run in <50ms.

set -u

# Resolve script dir so we can source _lib.sh whether called from anywhere.
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

if [ $# -lt 1 ] || [ -z "${1:-}" ] || [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
usage: mark.sh <changed_path>

Marks every leaf whose `code:` frontmatter list contains <changed_path>
as dirty (sets `dirty: true` and updates `last_touched`).
If no leaf matches, appends the path to docs/memory/_inbox.md.
EOF
  exit 0
fi

changed="$1"
[ -d "$MEMORY_DIR" ] || exit 0

count=0
matched=0
NOW=$(now_iso)

while IFS= read -r leaf; do
  [ -z "$leaf" ] && continue
  while IFS= read -r path; do
    [ -z "$path" ] && continue
    if path_matches "$changed" "$path"; then
      fm_set "$leaf" dirty true
      fm_set "$leaf" last_touched "$NOW"
      count=$((count + 1))
      matched=1
      break
    fi
  done < <(fm_list "$leaf" code)
done < <(list_leaves)

if [ "$matched" -eq 0 ]; then
  mkdir -p "$(dirname "$INBOX")"
  # De-dup: only append if not already present. The `--` separator
  # is required because our needle starts with `-`.
  if ! [ -f "$INBOX" ] || ! grep -qxF -- "- $changed" "$INBOX"; then
    printf '%s\n' "- $changed" >> "$INBOX"
  fi
fi

printf '%d\n' "$count"
