#!/usr/bin/env bash
# aims marker over a Capsa capsule.
#
# Usage:
#   mark.sh <changed_path>              # route: if no insight's code_globs
#                                       # match <changed_path>, append it to
#                                       # the (out-of-capsule) inbox. Prints
#                                       # the count of matching insights.
#   mark.sh <insight_file> consolidated # bump the insight's `updated:` to
#                                       # today (Capsa §1.4: freshness is a
#                                       # date, not a flag). Silent on success.
#
# Staleness itself is COMPUTED (find-dirty.sh), never stored — so the
# "dirty" write path is gone. Pure bash + awk. No LLM.

set -u

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

if [ $# -lt 1 ] || [ -z "${1:-}" ] || [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
usage:
  mark.sh <changed_path>              route an edited path; unmatched → inbox
  mark.sh <insight_file> consolidated bump the insight's `updated:` date
EOF
  exit 0
fi

# Consolidated mode: <insight_file> consolidated
if [ "${2:-}" = "consolidated" ]; then
  node="$1"
  if [ ! -f "$node" ]; then
    printf 'mark.sh: not a file: %s\n' "$node" >&2
    exit 1
  fi
  fm_set "$node" updated "$(today)"
  exit 0
fi

changed="$1"
[ -d "$INSIGHTS_DIR" ] || { printf '0\n'; exit 0; }

count=0
matched=0
while IFS= read -r leaf; do
  [ -z "$leaf" ] && continue
  while IFS= read -r glob; do
    [ -z "$glob" ] && continue
    if path_matches "$changed" "$glob"; then
      count=$((count + 1))
      matched=1
      break
    fi
  done < <(insight_globs "$leaf")
done < <(list_insights)

if [ "$matched" -eq 0 ]; then
  mkdir -p "$(dirname "$INBOX")"
  if ! [ -f "$INBOX" ] || ! grep -qxF -- "- $changed" "$INBOX"; then
    printf '%s\n' "- $changed" >> "$INBOX"
  fi
fi

printf '%d\n' "$count"
