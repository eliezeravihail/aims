#!/usr/bin/env bash
# aims PreToolUse hook (Edit | Write | MultiEdit | NotebookEdit).
#
# PHILOSOPHY: inform, never block (docs/plans/2026-06-01-aims-overhaul.md).
# This hook NEVER returns a blocking exit code and NEVER creates a lock. Its only
# effect is to inject a FACTUAL project note (additionalContext) at the moment a
# target-project SOURCE file is about to be edited without an in-progress plan —
# making the session aware of the planning convention. Allowlisted surfaces
# (docs/, tests/, *.md, .claude/) get nothing.
#
# "Source" is defined by EXCLUSION — anything not in the generic, tool-owned
# allow-set. No project path is ever hardcoded (the consuming project's source
# layout is confidential and must not appear here).
#
# Output contract (Claude Code hooks): exit 0 + JSON
#   {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow",
#     "additionalContext":"<FACTUAL note>"}}
# additionalContext MUST be factual, never imperative ("CRITICAL: do X"), or Claude's
# prompt-injection defense surfaces it to the user instead of treating it as context.

set -u

PLAN_DIR="${AIMS_PLAN_DIR:-docs/plans}"

allow_plain() { exit 0; }   # allow, inject nothing

payload=$(cat || true)

extract() {  # $1 = jq filter ; fallback grep key list
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$payload" | jq -r "$1 // empty" 2>/dev/null
  fi
}

target=$(extract '.tool_input.file_path // .tool_input.path // .tool_input.notebook_path')
if [ -z "$target" ]; then
  target=$(printf '%s' "$payload" | grep -oE '"(file_path|notebook_path|path)"[[:space:]]*:[[:space:]]*"[^"]+"' \
    | head -1 | sed -E 's/.*"[^"]+"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')
fi
[ -z "$target" ] && allow_plain

# Canonicalize to a repo-relative, lower-case form. Cross-platform: handles Windows
# drive-letter / backslash paths and git-bash MSYS ($PWD = /c/...). canon() folds
# both to one form; the prefix strip is then case/slash independent.
canon() {
  printf '%s' "$1" \
    | sed -e 's#\\#/#g' -e 's#^\([A-Za-z]\):/#/\1/#' -e 's#//*#/#g' \
    | tr '[:upper:]' '[:lower:]'
}
target_rel="$target"
ctarget=$(canon "$target")
case "$ctarget" in
  /*)
    for base in "$PWD" "$(git rev-parse --show-toplevel 2>/dev/null || true)"; do
      [ -n "$base" ] || continue
      cbase=$(canon "$base")
      case "$ctarget" in
        "$cbase"/*) target_rel="${ctarget#"$cbase"/}"; break ;;
      esac
    done
    ;;
esac

# Generic, project-independent allow-set — never "source", never reminded.
case "$target_rel" in
  docs/*|*.md|*.txt|tests/*|*/tests/*|*_test.*|*test_*.*|*.spec.*|.claude/*) allow_plain ;;
esac

# A target-project source edit. If a plan is already in progress, the session is
# planning-aware — stay silent. Otherwise inject the planning convention ONCE per
# session (avoid repeating the same note on every edit).
if [ -d "$PLAN_DIR" ] && grep -lqE '^Status:[[:space:]]*in-progress' "$PLAN_DIR"/*.md 2>/dev/null; then
  allow_plain
fi

sid=$(extract '.session_id')
[ -z "$sid" ] && sid=$(printf '%s' "$payload" | grep -oE '"session_id"[[:space:]]*:[[:space:]]*"[^"]+"' \
  | head -1 | sed -E 's/.*"([^"]+)"[^"]*$/\1/')
MARK=".claude/.aims-plan-note-${sid:-default}"
[ -f "$MARK" ] && allow_plain
mkdir -p .claude 2>/dev/null && : > "$MARK" 2>/dev/null || true
find .claude -maxdepth 1 -name '.aims-plan-note-*' -mtime +1 -delete 2>/dev/null || true

NOTE="About to edit '${target_rel}'. No \`Status: draft\` or \`Status: in-progress\` plan in \`${PLAN_DIR}\` covers this prompt. Project convention: a non-trivial change is materialized as a draft plan in \`${PLAN_DIR}/<YYYY-MM-DD>-<slug>.md\` BEFORE the first source edit — the plan file is the contract; the edit comes after the draft lands on disk and the user confirms. A brief user approval (\"yes\"/\"do it\") of a conversational proposal is approval to enter Phase 2 (write the draft), not to skip to Phase 4 (implement). (Informational only; nothing is blocked. This note fires once per session — subsequent edits are silent.)"

if command -v jq >/dev/null 2>&1; then
  jq -nc --arg c "$NOTE" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"allow",additionalContext:$c}}'
else
  # M2: use the shared json_escape helper (handles tabs / CR / all C0 control
  # chars). The prior ad-hoc sed only handled `\` and `"`, producing invalid
  # JSON whenever NOTE contained a tab or CR.
  if [ -r ".claude/memory/_lib.sh" ];   then . ".claude/memory/_lib.sh"
  elif [ -r "templates/memory/_lib.sh" ]; then . "templates/memory/_lib.sh"
  fi
  if command -v json_escape >/dev/null 2>&1; then
    esc=$(json_escape "$NOTE")
  else
    esc=$(printf '%s' "$NOTE" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')
  fi
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","additionalContext":"%s"}}\n' "$esc"
fi
exit 0
