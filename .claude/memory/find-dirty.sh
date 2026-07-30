#!/usr/bin/env bash
# Print the path of every insight that is STALE relative to its code_globs.
# Staleness is COMPUTED (not a stored flag): an insight is stale iff a file in
# its code_globs changed after the insight's `updated:` date — committed or
# uncommitted (see insight_stale in _lib.sh). Empty output if nothing is stale.
#
# Usage:  find-dirty.sh
# (Name kept for call-site stability; semantics are computed staleness.)

set -u

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_lib.sh
. "$SCRIPT_DIR/_lib.sh"

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
usage: find-dirty.sh

Prints (one per line) every insight in .capsa/insights/ that is stale
relative to its code_globs, computed from `updated:` vs git. Empty if
none are stale. No flag is read or written.
EOF
  exit 0
fi

while IFS= read -r leaf; do
  [ -z "$leaf" ] && continue
  if insight_stale "$leaf"; then
    printf '%s\n' "$leaf"
  fi
done < <(list_insights)
