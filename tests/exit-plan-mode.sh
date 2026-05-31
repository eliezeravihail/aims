#!/usr/bin/env bash
# Smoke test for the exit-plan-mode bridge hook
# (templates/hooks/exit-plan-mode.sh, ADR-0015).
#
# Verifies that a harness-mode ExitPlanMode payload is persisted to
# docs/plans/<UTC-date>-<slug>.md with Status: in-progress; that a
# collision is a no-op; and that an empty body writes nothing.

set -eu
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { printf '[SKIP] jq missing\n'; exit 0; }
cd "$TMP"
mkdir -p docs/plans

# Case 1: writes a plan file from a tool_input.plan payload.
plan_body='# Refactor the loader

## TL;DR
Move json loading out of the parser.

## Changes
### src/loader.py
…
'
payload=$(jq -nc --arg p "$plan_body" '{tool_input: {plan: $p}}')
out=$(printf '%s' "$payload" | bash "$ROOT/templates/hooks/exit-plan-mode.sh" 2>&1 || true)
written=$(ls docs/plans/*.md 2>/dev/null | head -1 || true)
[ -n "$written" ] || fail "case 1: no file created (stderr: $out)"
grep -q '^Status: in-progress$' "$written" || fail "case 1: missing Status: in-progress in $written"
grep -q 'Refactor the loader' "$written"  || fail "case 1: body not preserved in $written"
pass "exit-plan-mode writes docs/plans/<file> with in-progress status"

# Case 2: collision → no overwrite, no second file.
printf '%s' "$payload" | bash "$ROOT/templates/hooks/exit-plan-mode.sh" >/dev/null 2>&1
n=$(ls docs/plans/*.md | wc -l)
[ "$n" = "1" ] || fail "case 2: overwrite happened — found $n files"
pass "exit-plan-mode skips on slug collision"

# Case 3: empty body → no file.
rm -f docs/plans/*.md
printf '%s' '{"tool_input":{"plan":""}}' | \
  bash "$ROOT/templates/hooks/exit-plan-mode.sh" >/dev/null 2>&1
[ -z "$(ls docs/plans/*.md 2>/dev/null)" ] || \
  fail "case 3: empty plan still wrote a file"
pass "exit-plan-mode no-ops on empty body"

# Case 4: missing tool_input key → no file, no crash.
rm -f docs/plans/*.md
printf '%s' '{}' | bash "$ROOT/templates/hooks/exit-plan-mode.sh" >/dev/null 2>&1
[ -z "$(ls docs/plans/*.md 2>/dev/null)" ] || \
  fail "case 4: empty payload still wrote a file"
pass "exit-plan-mode no-ops on empty payload"

printf '\nAll exit-plan-mode tests passed.\n'
