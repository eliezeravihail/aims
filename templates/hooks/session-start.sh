#!/usr/bin/env bash
# aims SessionStart hook — informational only. Exits 0 always; never blocks.
# Surfaces: in-progress plans, and the presence of a .capsa/ design capsule with the reading rule.
# Durable design knowledge lives in the capsule (placement = scope); this hook only points at it —
# the read-time staleness hook (staleness_read.py) does the drift-flagging when a record is read.
set -u

PLAN_DIR="${AIMS_PLAN_DIR:-docs/plans}"
CAPSULE="${AIMS_CAPSULE_DIR:-.capsa}"

emit() { printf '[aims] %s\n' "$1"; }

# In-progress plans (header-scoped: only the Status line near the top counts).
if [ -d "$PLAN_DIR" ]; then
  in_progress=$(grep -lE "^Status:[[:space:]]*in-progress" "$PLAN_DIR"/*.md 2>/dev/null)
  if [ -n "$in_progress" ]; then
    emit "in-progress plan(s):"
    printf '        %s\n' $in_progress
  fi
fi

# The design capsule.
if [ -d "$CAPSULE" ]; then
  emit "design capsule present at $CAPSULE/ — read the records in force where you are working:"
  printf '        walk from the node you touch to the capsule root; read the normative records\n'
  printf '        (requirements, decisions, component.md) plus in-scope insights — not the whole tree.\n'
  printf '        A record flagged stale on read is *possibly* out of date; re-verify before relying on it.\n'
fi

exit 0
