#!/usr/bin/env bash
# aims SessionStart hook — informational only. Exits 0 always; never blocks.
# Design knowledge is co-located with the code: a source file's knowledge is in its same-named
# companion (`<file>.md`); cross-cutting records (goals.md, architecture.md, decisions/) live at the
# root. This hook only points at that; the read-time staleness hook flags drift when a companion is read.
set -u

emit() { printf '[aims] %s\n' "$1"; }

# In-progress plans, if the project keeps any.
if [ -d docs/plans ]; then
  ip=$(grep -lE "^Status:[[:space:]]*in-progress" docs/plans/*.md 2>/dev/null)
  [ -n "$ip" ] && { emit "in-progress plan(s):"; printf '        %s\n' $ip; }
fi

# The co-located design records.
if [ -f goals.md ] || ls **/*.py.md >/dev/null 2>&1; then
  emit "design records are co-located with the code:"
  printf '        to understand a file, open its companion (<file>.md beside it); for system context\n'
  printf '        read the root records (goals.md, architecture.md, decisions/). Navigate — do not read\n'
  printf '        the whole tree. A record flagged stale on read is *possibly* out of date; re-verify.\n'
fi

exit 0
