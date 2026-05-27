#!/usr/bin/env bash
# Mark leaves dirty (when source paths change) or consolidated
# (when the in-band model finishes updating a node body).
#
# Usage:
#   mark.sh <changed_path>                  # mark dirty (default)
#   mark.sh <node_file> consolidated        # flip clean + bump timestamps
#
# Output (dirty mode): count of leaves marked (single integer to stdout).
# Output (consolidated mode): silent on success.
#
# Pure bash + awk + sed. No LLM. Designed to run in <50ms.

set -u

# Resolve script dir so we can source _lib.sh whether called from anywhere.
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

if [ $# -lt 1 ] || [ -z "${1:-}" ] || [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
usage:
  mark.sh <changed_path>                  # mark every leaf that references
                                          # <changed_path> as dirty; if no
                                          # leaf matches, append to inbox.
  mark.sh <node_file> consolidated        # flip <node_file> clean: set
                                          # dirty:false and bump last_touched
                                          # + last_consolidated.
EOF
  exit 0
fi

# Consolidated mode: <node_file> consolidated
if [ "${2:-}" = "consolidated" ]; then
  node="$1"
  if [ ! -f "$node" ]; then
    printf 'mark.sh: not a file: %s\n' "$node" >&2
    exit 1
  fi
  NOW=$(now_iso)
  fm_set "$node" dirty false
  fm_set "$node" last_touched "$NOW"
  fm_set "$node" last_consolidated "$NOW"
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
