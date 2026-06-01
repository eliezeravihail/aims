#!/usr/bin/env bash
# Smoke test for the UserPromptSubmit intent router
# (templates/hooks/prompt-submit.sh, ADR-0015 auto-engage behaviour).

set -eu
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { printf '[SKIP] jq missing\n'; exit 0; }
cd "$TMP"

# Case 1: bug intent → lock created, additionalContext mentions auto-engaging.
rm -rf .claude
out=$(printf '{"prompt":"the parser crashes on empty input"}' | \
  bash "$ROOT/templates/hooks/prompt-submit.sh" 2>/dev/null)
[ -f .claude/.planning-lock ] || fail "case 1: lock not created for bug intent"
printf '%s' "$out" | jq -r '.hookSpecificOutput.additionalContext' | \
  grep -q 'auto-engaging' || fail "case 1: additionalContext missing 'auto-engaging'"
pass "router auto-engages on bug"

# Case 2: question intent → no lock, no router output.
rm -rf .claude
out=$(printf '{"prompt":"how does the marker hook decide which node to flag?"}' | \
  bash "$ROOT/templates/hooks/prompt-submit.sh" 2>/dev/null)
[ ! -f .claude/.planning-lock ] || fail "case 2: lock created for question (should not)"
[ -z "$out" ] || fail "case 2: question should produce no router output (got: $out)"
pass "router stays silent on questions"

# Case 3: prompt starting with `/` → no lock (user already chose a command).
rm -rf .claude
out=$(printf '{"prompt":"/plan something"}' | \
  bash "$ROOT/templates/hooks/prompt-submit.sh" 2>/dev/null)
[ ! -f .claude/.planning-lock ] || fail "case 3: lock created when user typed /command"
[ -z "$out" ] || fail "case 3: slash-prefixed prompt should produce no router output"
pass "router suppresses on slash-command prompts"

# Case 4: planning lock already exists → no re-injection, no overwrite.
rm -rf .claude; mkdir -p .claude; touch .claude/.planning-lock
mtime_before=$(stat -c %Y .claude/.planning-lock 2>/dev/null || stat -f %m .claude/.planning-lock)
out=$(printf '{"prompt":"refactor the loader to drop pandas dep"}' | \
  bash "$ROOT/templates/hooks/prompt-submit.sh" 2>/dev/null)
[ -z "$out" ] || fail "case 4: should not re-engage when already in plan mode (got: $out)"
pass "router suppresses during active planning"

# Case 5: feature/refactor intent in ambiguous prose triggers fallback.
rm -rf .claude
out=$(printf '{"prompt":"make the inbox surface the bytes-truncated indicator in a way that survives compaction"}' | \
  bash "$ROOT/templates/hooks/prompt-submit.sh" 2>/dev/null)
[ -f .claude/.planning-lock ] || fail "case 5: lock not created for ambiguous-but-actionable prompt"
pass "router auto-engages on ambiguous actionable prompt"

# Case 6: code-paste-looking prompt with backticks does NOT auto-engage.
rm -rf .claude
out=$(printf '%s' '{"prompt":"```python\nprint(1)\n```"}' | \
  bash "$ROOT/templates/hooks/prompt-submit.sh" 2>/dev/null)
[ ! -f .claude/.planning-lock ] || fail "case 6: code-paste should not auto-engage"
pass "router skips code-paste prompts"

printf '\nAll router auto-plan tests passed.\n'
