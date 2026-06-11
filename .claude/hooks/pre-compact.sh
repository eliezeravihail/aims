#!/usr/bin/env bash
# aims PreCompact hook — advisory only (ADR-0020).
#
# Fires just before Claude Code summarizes context. Reports dirty memory
# state on stderr so the developer (and any later session inspecting the
# transcript) sees what was pending the moment context was compacted.
# Never blocks compaction; never touches the throttle state file (so the
# next post-compaction Stop can still trigger normally).
#
# Per ADR-0024 this hook MUST NOT race the consolidation mutex —
# it does no consolidation work, only reads `find-dirty.sh`.
#
# Inspiration / credit:
#   - project-bedrock (https://github.com/robotaitai/project-bedrock) —
#     wires lifecycle hooks across SessionStart / Stop / PreCompact to
#     keep the memory layer current.
#   - claude-code-context-handoff
#     (https://github.com/who96/claude-code-context-handoff) — uses
#     PreCompact + SessionEnd to persist a handoff note across context
#     boundaries.

set -u

if   [ -d ".claude/memory" ];   then MEM_HELPERS=".claude/memory"
elif [ -d "templates/memory" ]; then MEM_HELPERS="templates/memory"
else exit 0; fi

n=$(bash "$MEM_HELPERS/find-dirty.sh" 2>/dev/null | grep -c . || echo 0)
if [ "$n" -gt 0 ]; then
  printf '[aims] PreCompact: %d dirty memory node(s) — will resume after compaction.\n' "$n" >&2
fi
exit 0
