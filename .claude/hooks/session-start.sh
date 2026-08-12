#!/usr/bin/env bash
# aims SessionStart hook — informational only. Exits 0 always; never blocks.
# Design knowledge is co-located with the code: a component's record is `component.md` inside its
# directory, with its `decisions/` and `insights/` beside it; cross-cutting records (charter.md, root
# decisions/) live at the repo root. This hook only points at that; the read-time staleness hook
# (knowledge/staleness_hook.py) flags drift when a record is read.
set -u

emit() { printf '[aims] %s\n' "$1"; }

# In-progress plans, if the project keeps any.
if [ -d docs/plans ]; then
  ip=$(grep -lE "^Status:[[:space:]]*in-progress" docs/plans/*.md 2>/dev/null)
  [ -n "$ip" ] && { emit "in-progress plan(s):"; printf '        %s\n' $ip; }
fi

# The co-located design records.
if [ -f charter.md ] || ls */**/component.md >/dev/null 2>&1 || ls **/component.md >/dev/null 2>&1; then
  emit "design records are co-located with the code:"
  printf '        read the records in force where you work — the component.md in the directory you\n'
  printf '        are touching and its decisions/insights, then walk up to the repo root (charter.md,\n'
  printf '        root decisions/). Not the whole tree. A record flagged stale on read is *possibly*\n'
  printf '        out of date; re-verify against the current code before relying on it.\n'
fi

exit 0
