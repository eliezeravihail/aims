#!/usr/bin/env bash
# aims SessionStart hook — informational only. Exits 0 always; never blocks.
# Design knowledge is co-located with the code: a source file's knowledge is in its same-named
# companion (`<file>.md`); cross-cutting records (goals.md, architecture.md, decisions/) live at the
# root. This hook only points at that; the read-time staleness hook flags drift when a companion is read.
set -u

# Does this project carry aims records? A companion is `<file>.<ext>.md` beside any source file, in any
# language and at any depth — so the probe must be language-agnostic and recursive. (`**` is NOT
# recursive in bash unless globstar is set, and a `*.py.md` probe would miss `.kt.md`, `.ts.md`, `.go.md`
# and every other companion.)
has_records() {
  [ -f goals.md ] || [ -f architecture.md ] || [ -d decisions ] && return 0
  find . \( -name .git -o -name node_modules -o -name .venv -o -name __pycache__ \) -prune -o \
       -type f -name '*.*.md' -print -quit 2>/dev/null | read -r _ && return 0
  return 1
}

if has_records; then
  printf '[aims] design records are co-located with the code:\n'
  printf '       to understand a file, open its companion (<file>.md beside it); for system context\n'
  printf '       read the root records (goals.md, architecture.md, decisions/). Navigate — do not read\n'
  printf '       the whole tree. A companion flagged stale on read is *possibly* out of date; re-verify.\n'
fi

exit 0
