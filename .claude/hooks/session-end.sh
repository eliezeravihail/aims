#!/usr/bin/env bash
# aims SessionEnd hook — advisory breadcrumb only.
#
# Audit finding M3 (docs/plans/2026-06-11-aims-audit-fixes-master.md):
# the prior implementation execed `stop-consolidate.sh --force`. But
# Stop-hook block-JSON (`{"decision":"block","reason":...}`) has no
# meaning at SessionEnd — no following model turn consumes it. Meanwhile
# stop-consolidate unconditionally bumps `.last-consolidated`, which then
# silently delays the NEXT session's interval throttle by 30 min while
# no consolidation work actually happened.
#
# This hook now only reports state on stderr. It never touches the
# throttle file. Per ADR-0020 it informs and does not block; per
# ADR-0024 it must not race the consolidation mutex.

set -u

if   [ -d ".claude/memory" ];   then MEM_HELPERS=".claude/memory"
elif [ -d "templates/memory" ]; then MEM_HELPERS="templates/memory"
else exit 0; fi

n=$(bash "$MEM_HELPERS/find-dirty.sh" 2>/dev/null | grep -c . || echo 0)
if [ "$n" -gt 0 ]; then
  printf '[aims] SessionEnd: %d dirty memory node(s) left for next session.\n' "$n" >&2
fi
exit 0
