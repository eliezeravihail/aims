#!/usr/bin/env bash
# Smoke test for the UserPromptSubmit intent router
# (templates/hooks/prompt-submit.sh).
#
# Post-overhaul (ADR-0020): the router INFORMS, it never locks. For an
# actionable intent it injects a FACTUAL planning-convention note; it NEVER
# creates a .planning-lock. Questions / slash-commands / code-pastes get nothing.

set -eu
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { printf '[SKIP] jq missing\n'; exit 0; }
cd "$TMP"

HOOK="$ROOT/templates/hooks/prompt-submit.sh"
note_has() { printf '%s' "$1" | jq -r '.hookSpecificOutput.additionalContext // empty' | grep -q "$2"; }

# Case 1: bug intent → NO lock; a factual planning note (never an imperative).
rm -rf .claude
out=$(printf '{"prompt":"the parser crashes on empty input"}' | bash "$HOOK" 2>/dev/null)
[ ! -f .claude/.planning-lock ] || fail "case 1: router must NOT create a lock"
note_has "$out" 'Project convention' || fail "case 1: expected a factual planning note"
note_has "$out" 'nothing is blocked'  || fail "case 1: note should state nothing is blocked"
pass "bug intent → factual note, no lock"

# Case 2: question intent → no lock, no planning note.
rm -rf .claude
out=$(printf '{"prompt":"how does the marker hook decide which node to flag?"}' | bash "$HOOK" 2>/dev/null)
[ ! -f .claude/.planning-lock ] || fail "case 2: no lock for question"
if note_has "$out" 'Project convention'; then fail "case 2: question should get no planning note"; fi
pass "question → no note, no lock"

# Case 3: slash-prefixed prompt → suppressed (no output, no lock).
rm -rf .claude
out=$(printf '{"prompt":"/plan something"}' | bash "$HOOK" 2>/dev/null)
[ ! -f .claude/.planning-lock ] || fail "case 3: no lock for slash command"
[ -z "$out" ] || fail "case 3: slash-prefixed prompt should produce no output"
pass "router suppresses on slash-command prompts"

# Case 4: ambiguous actionable prose → factual note, still NO lock.
rm -rf .claude
out=$(printf '{"prompt":"make the inbox surface the bytes-truncated indicator in a way that survives compaction"}' | bash "$HOOK" 2>/dev/null)
[ ! -f .claude/.planning-lock ] || fail "case 4: ambiguous prompt must NOT create a lock"
note_has "$out" 'Project convention' || fail "case 4: ambiguous actionable → factual note"
pass "ambiguous actionable → factual note, no lock"

# Case 5: code-paste prompt → no note, no lock.
rm -rf .claude
out=$(printf '%s' '{"prompt":"```python\nprint(1)\n```"}' | bash "$HOOK" 2>/dev/null)
[ ! -f .claude/.planning-lock ] || fail "case 5: code-paste must not lock"
if note_has "$out" 'Project convention'; then fail "case 5: code-paste should get no planning note"; fi
pass "router skips code-paste prompts"

printf '\nAll router (inform-never-lock) tests passed.\n'
