#!/usr/bin/env bash
# aims SessionStart hook — informational only.
# Surfaces:
#   - in-progress plans
#   - recently-touched ADRs
#   - leftover planning-lock (warns if present without active plan)
# Exits 0 always; never blocks.

set -u

ADR_DIR="${AIMS_ADR_DIR:-docs/adr}"
PLAN_DIR="${AIMS_PLAN_DIR:-docs/plans}"
LOCK=".claude/.planning-lock"

print_section() {
  local title="$1"
  printf '  %s\n' "$title"
}

# Stale lock detection + auto-recovery.
# A lock is only legitimate when it guards an actual /plan flow: either an
# in-progress plan, or a draft awaiting approval (Phase 2 -> Phase 3). With
# neither, the lock is orphaned (interrupted run, or the prompt-submit
# auto-engage fired on something that turned out not to be a task) and would
# otherwise silently block every Edit/Write in this fresh session. Clear it.
if [ -f "$LOCK" ]; then
  has_active_plan=0
  has_draft=0
  if [ -d "$PLAN_DIR" ]; then
    grep -lE '^Status:[[:space:]]*in-progress' "$PLAN_DIR"/*.md 2>/dev/null | grep -q . && has_active_plan=1
    grep -lE '^Status:[[:space:]]*draft' "$PLAN_DIR"/*.md 2>/dev/null | grep -q . && has_draft=1
  fi
  if [ "$has_active_plan" -eq 1 ]; then
    printf '[aims] Planning lock active — Edit/Write blocked until ExitPlanMode.\n'
  elif [ "$has_draft" -eq 1 ]; then
    printf '[aims] Planning lock held for a draft awaiting approval (no in-progress plan yet).\n'
    printf '       Approve/iterate the draft, or run: rm .claude/.planning-lock\n'
  else
    rm -f "$LOCK"
    printf '[aims] Cleared an orphaned .claude/.planning-lock (no in-progress or draft plan).\n'
  fi
fi

# Orphan-draft detection: lock missing but a Status: draft plan exists.
# (Draft plans live in docs/plans/ between /plan Phase 2 and Phase 3
# approval; without a lock they were left behind by an interrupted run.)
if [ ! -f "$LOCK" ] && [ -d "$PLAN_DIR" ]; then
  drafts=$(grep -lE '^Status:[[:space:]]*draft' "$PLAN_DIR"/*.md 2>/dev/null || true)
  if [ -n "$drafts" ]; then
    printf '[aims] WARNING: draft plan(s) with no active planning lock:\n'
    while IFS= read -r d; do
      printf '       %s\n' "$d"
    done <<< "$drafts"
    printf '       Recover: touch .claude/.planning-lock to resume, or rm the file.\n'
  fi
fi

# In-progress plans.
if [ -d "$PLAN_DIR" ]; then
  active=$(grep -lE '^Status:\s*in-progress' "$PLAN_DIR"/*.md 2>/dev/null || true)
  if [ -n "$active" ]; then
    printf '[aims] In-progress plans:\n'
    while IFS= read -r f; do
      title=$(awk -F': ' '/^# /{print substr($0, 3); exit}' "$f")
      printf '       %s — %s\n' "${f#$PLAN_DIR/}" "${title:-untitled}"
    done <<< "$active"
  fi
fi

# Recently-touched ADRs (last 30 days). Skip superseded/deprecated;
# suffix non-accepted statuses so the model knows what is in force.
if [ -d "$ADR_DIR" ]; then
  recent=$(find "$ADR_DIR" -maxdepth 1 -name '[0-9]*.md' -mtime -30 2>/dev/null | sort | tail -8)
  if [ -n "$recent" ]; then
    out=""
    while IFS= read -r f; do
      status=$(awk -F': *' '/^Status:/{print tolower($2); exit}' "$f" 2>/dev/null | tr -d '\r ')
      case "$status" in
        superseded|deprecated) continue ;;
      esac
      title=$(awk -F': ' '/^# /{print substr($0, 3); exit}' "$f")
      case "$status" in
        ''|accepted) suffix='' ;;
        *)           suffix=" ($status)" ;;
      esac
      out+="       ${title:-${f##*/}}${suffix}"$'\n'
    done <<< "$recent"
    if [ -n "$out" ]; then
      printf '[aims] Recent ADRs:\n%s' "$out"
    fi
  fi
fi

# Memory tree top-level (ADR-0007). Surface the README so the model
# knows the tag list to navigate. Capped at 2KB to keep the prompt
# injection light.
MEMORY_DIR="${AIMS_MEMORY_DIR:-docs/memory}"
MEMORY_README="$MEMORY_DIR/README.md"
if [ -r "$MEMORY_README" ]; then
  printf '[aims] Memory tree (%s):\n' "$MEMORY_DIR"
  head -c 2048 "$MEMORY_README" | sed 's/^/       /'
  size=$(wc -c < "$MEMORY_README")
  if [ "$size" -gt 2048 ]; then
    printf '       … (%d bytes truncated; view with: cat %s)\n' "$((size - 2048))" "$MEMORY_README"
  fi
fi

# Memory pipeline health one-liner (ADR-0008 visibility).
MEMORY_HELPERS=""
if [ -r ".claude/memory/doctor.sh" ]; then
  MEMORY_HELPERS=".claude/memory"
elif [ -r "templates/memory/doctor.sh" ]; then
  MEMORY_HELPERS="templates/memory"
fi
if [ -n "$MEMORY_HELPERS" ]; then
  brief=$(bash "$MEMORY_HELPERS/doctor.sh" --brief 2>/dev/null || true)
  [ -n "$brief" ] && printf '%s\n' "$brief"
fi

# Standing project conventions (factual). The session applies these to the
# moment-of-change facts the PostToolUse hook injects. Inform, never coerce —
# no hook blocks edits.
cat <<'EOF'
[aims] Project conventions (factual):
       - For a non-trivial change, the assistant plans before implementing —
         read-only discovery, then a Status: draft plan in docs/plans/, then
         user approval, then implementation, then inline close-out. The full
         flow is in .claude/commands/plan.md. The /plan slash command is an
         OPTIONAL shortcut that dispatches Phase 1-2 to an Opus subagent —
         use it when the current model is not Opus and planning quality
         matters; otherwise plan inline.
       - After a non-trivial source change, the relevant docs/memory node is
         updated to reflect it (the post-edit hook names the node). When that
         hook reports a possible concurrent edit by another session, the user
         is asked before updating the node.
       - Reply-format: the `==== AIMS (internal) ====` prefix is used
         ONLY to report the result of a consolidation/update-hook run
         (the Stop hook draining the dirty queue or inbox). One line or
         a short phrase ("nodes updated", "queue drained", "4 dirty").
         Regular conversational mentions of aims topics (questions, plans,
         status) are NOT prefixed — only the hook-result report is.
       - These are conventions, not gates: no aims hook blocks an edit.
EOF

exit 0
