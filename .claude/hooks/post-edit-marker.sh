#!/usr/bin/env bash
# aims PostToolUse hook on Edit | Write | MultiEdit | NotebookEdit.
# Flips `dirty: true` on any memory leaf whose `code:` list references
# the file that was just edited; appends unknown paths to _inbox.md.
#
# Cost target: <50ms. No LLM. No network. Never blocks; always exits 0.

set -u

# Resolve helper directory: first try the installed copy under
# .claude/memory/, fall back to the templates copy (for dogfooding).
if [ -d ".claude/memory" ]; then
  MEM_HELPERS=".claude/memory"
elif [ -d "templates/memory" ]; then
  MEM_HELPERS="templates/memory"
else
  exit 0   # Helpers not installed; nothing to do.
fi

# Read tool_input from stdin per Claude Code's hook contract.
payload=$(cat || true)

extract_path() {
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$payload" | jq -r '.tool_input.file_path // .tool_input.path // .tool_input.notebook_path // empty' 2>/dev/null
  else
    printf '%s' "$payload" | grep -oE '"(file_path|notebook_path|path)"\s*:\s*"[^"]+"' \
      | head -1 | sed -E 's/.*"[^"]+"\s*:\s*"([^"]+)".*/\1/'
  fi
}

target=$(extract_path)
[ -z "$target" ] && exit 0

# Normalize to a repo-relative path. Claude Code emits absolute
# file_path in tool_input; node code: lists are all repo-relative
# (ADR-0008), so without this normalization every edit falls through
# to mark.sh's "unknown path" branch and leaks an absolute path into
# _inbox.md.
if [ "${target#/}" != "$target" ]; then
  repo_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  case "$target" in
    "$repo_root"/*) target="${target#$repo_root/}" ;;
    "$repo_root")   exit 0 ;;
    *)              exit 0 ;;  # absolute but outside repo
  esac
fi

# Skip paths that aren't project source (no point marking them):
#   - inside .claude/, .git/, node_modules/, dist/, build/
#   - the memory tree itself
case "$target" in
  .claude/*|.git/*|*/node_modules/*|*/dist/*|*/build/*) exit 0 ;;
  docs/memory/*) exit 0 ;;
esac

bash "$MEM_HELPERS/mark.sh" "$target" >/dev/null 2>&1 || true
exit 0
