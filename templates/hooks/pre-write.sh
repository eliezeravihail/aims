#!/usr/bin/env bash
# aims PreToolUse hook for Edit / Write / MultiEdit.
#
# Two responsibilities:
#   1. Hard block while .claude/.planning-lock exists (planning is read-only).
#   2. In `block` mode, soft-block writes to source paths without an
#      in-progress plan AND when the target path looks like production code.
#
# Mode is read from .claude/aims-mode (one of: nudge | block).
# Default if file missing: nudge (warn-only).
#
# Exit codes:
#   0 — allow.
#   2 — block (Claude Code surfaces stderr to the model + user).

set -u

LOCK=".claude/.planning-lock"
MODE_FILE=".claude/aims-mode"
PLAN_DIR="${AIMS_PLAN_DIR:-docs/plans}"

mode="nudge"
[ -f "$MODE_FILE" ] && mode=$(tr -d ' \n' < "$MODE_FILE")

# Read JSON payload (Claude Code passes tool_input).
payload=$(cat || true)

extract_path() {
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$payload" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null
  else
    printf '%s' "$payload" | grep -oE '"file_path"\s*:\s*"[^"]+"' | head -1 | sed -E 's/.*"file_path"\s*:\s*"([^"]+)".*/\1/'
  fi
}

target=$(extract_path)

# Normalize absolute paths against the repo root so the carve-outs below
# (which are relative) match either form. Without this, Claude Code's
# absolute file_path silently misses the docs/plans/ exception during the
# planning lock — bug surfaced and fixed in ADR-0019.
target_rel="$target"
if [ -n "$target" ]; then
  case "$target" in
    /*)
      repo_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
      if [ -n "$repo_root" ]; then
        case "$target" in
          "$repo_root"/*) target_rel="${target#"$repo_root"/}" ;;
        esac
      fi
      ;;
  esac
fi

# (1) Planning lock — always blocks, regardless of mode.
# Exception: writes to the plan draft itself under PLAN_DIR are the whole
# point of the /plan auto-engage flow (ADR-0015) and must be allowed even
# during the lock — otherwise the auto-engage cascade deadlocks (the model
# is told to draft a plan but every Write hits this gate).
if [ -f "$LOCK" ]; then
  case "$target_rel" in
    "$PLAN_DIR"/*.md|docs/plans/*.md|"$PLAN_DIR"/*.md.tmp|docs/plans/*.md.tmp) exit 0 ;;
  esac
  cat >&2 <<EOF
[aims] Planning in progress (.claude/.planning-lock present).
       File edits are not allowed until you call ExitPlanMode and the user
       approves the plan. After approval, /plan will remove the lock.
       (Writes under docs/plans/ are allowed — that's where the draft goes.)
       To abort planning manually:  rm .claude/.planning-lock
EOF
  exit 2
fi

# (1b) Memory-node sidecar lock (ADR-0019).
# If the target is a docs/memory/<tag>/<leaf>.md path with a `<leaf>.lock`
# sidecar held by a *different* fresh session, refuse and tell the user
# how to recover. Stale locks (mtime > AIMS_LOCK_TTL_SEC) and own-session
# locks pass through.
LOCK_TTL="${AIMS_LOCK_TTL_SEC:-600}"
case "$target_rel" in
  docs/memory/*/*.md)
    sidecar="${target_rel%.md}.lock"
    if [ -e "$sidecar" ]; then
      lock_mtime=$(stat -c %Y "$sidecar" 2>/dev/null || stat -f %m "$sidecar" 2>/dev/null || echo 0)
      sidecar_age=$(( $(date -u +%s) - lock_mtime ))
      if [ "$sidecar_age" -lt "$LOCK_TTL" ]; then
        sid_payload=""
        if command -v jq >/dev/null 2>&1; then
          sid_payload=$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null || true)
        fi
        sid_lock=$(head -n1 "$sidecar" 2>/dev/null || true)
        if [ -n "$sid_lock" ] && [ "$sid_lock" != "$sid_payload" ]; then
          cat >&2 <<EOF
[aims] Memory node "$target_rel" is locked by another session
       (sid=$sid_lock). Refusing this edit to prevent clobbering.
       If that session crashed:  rm $sidecar
       Then retry the edit.
EOF
          exit 2
        fi
      fi
    fi
    ;;
esac

# (2) Significant-change check — only in block mode, only on real source paths.
[ "$mode" != "block" ] && exit 0
[ -z "$target_rel" ] && exit 0

is_source_path=0
case "$target_rel" in
  src/*|lib/*|app/*|server/*|client/*|packages/*) is_source_path=1 ;;
esac
[ "$is_source_path" -eq 0 ] && exit 0

# Allow if the path looks like a test or doc.
case "$target_rel" in
  *_test.*|*test_*.*|*.test.*|*.spec.*|*/tests/*|*/__tests__/*|*.md|*.txt) exit 0 ;;
esac

# Require an in-progress plan to write to source paths.
has_active_plan=0
if [ -d "$PLAN_DIR" ]; then
  if grep -lE '^Status:\s*in-progress' "$PLAN_DIR"/*.md 2>/dev/null | grep -q .; then
    has_active_plan=1
  fi
fi

if [ "$has_active_plan" -eq 0 ]; then
  cat >&2 <<EOF
[aims] About to edit "$target_rel" (production source) without an in-progress plan.
       Run \`/plan\` first, OR set hook mode to nudge:
         echo nudge > .claude/aims-mode
       OR delete this hook if you want it off entirely.
EOF
  exit 2
fi

exit 0
