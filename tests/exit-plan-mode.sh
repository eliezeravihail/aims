#!/usr/bin/env bash
# Smoke test for the exit-plan-mode bridge hook
# (templates/hooks/exit-plan-mode.sh) over a Capsa capsule.
#
# Verifies that a harness-mode ExitPlanMode payload is persisted to
# .capsa/plans/NNNN-slug.md as a conforming Capsa plan with
# status: in_progress; that a slug collision is a no-op; that an empty
# body writes nothing; and that the plan id auto-increments.

set -eu
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { printf '[SKIP] jq missing\n'; exit 0; }
cd "$TMP"
mkdir -p .capsa/plans
HOOK="$ROOT/templates/hooks/exit-plan-mode.sh"

# Case 1: writes a Capsa plan record from a tool_input.plan payload.
plan_body='# Refactor the loader

## TL;DR
Move json loading out of the parser.

## Changes
### src/loader.py
…
'
payload=$(jq -nc --arg p "$plan_body" '{tool_input: {plan: $p}}')
out=$(printf '%s' "$payload" | bash "$HOOK" 2>&1 || true)
written=$(ls .capsa/plans/*.md 2>/dev/null | head -1 || true)
[ -n "$written" ] || fail "case 1: no file created (stderr: $out)"
grep -q '^status: in_progress$' "$written" || fail "case 1: missing status: in_progress in $written"
grep -q '^id: 0$' "$written"                || fail "case 1: expected first id 0 in $written"
grep -q 'Refactor the loader' "$written"    || fail "case 1: body not preserved in $written"
case "$written" in .capsa/plans/0000-*.md) ;; *) fail "case 1: filename should be 0000-<slug>.md (got $written)";; esac
pass "exit-plan-mode writes a Capsa plan with status: in_progress and id 0"

# Case 2: collision (same slug) → no overwrite, no second file.
printf '%s' "$payload" | bash "$HOOK" >/dev/null 2>&1
n=$(ls .capsa/plans/*.md | wc -l)
[ "$n" = "1" ] || fail "case 2: duplicate slug wrote a second file — found $n"
pass "exit-plan-mode skips on slug collision"

# Case 3: a DIFFERENT plan gets the next id (auto-increment).
payload2=$(jq -nc '{tool_input: {plan: "# Add a cache layer\n\n## TL;DR\nCache it.\n"}}')
printf '%s' "$payload2" | bash "$HOOK" >/dev/null 2>&1
second=$(ls .capsa/plans/*.md | grep -v '0000-' | head -1)
[ -n "$second" ] || fail "case 3: second distinct plan not written"
grep -q '^id: 1$' "$second" || fail "case 3: expected id 1 in $second"
pass "exit-plan-mode auto-increments the plan id"

# Case 4: empty body → no new file.
before=$(ls .capsa/plans/*.md | wc -l)
printf '%s' '{"tool_input":{"plan":""}}' | bash "$HOOK" >/dev/null 2>&1
after=$(ls .capsa/plans/*.md | wc -l)
[ "$before" = "$after" ] || fail "case 4: empty plan still wrote a file"
pass "exit-plan-mode no-ops on empty body"

# Case 5: missing tool_input key → no new file, no crash.
printf '%s' '{}' | bash "$HOOK" >/dev/null 2>&1
after2=$(ls .capsa/plans/*.md | wc -l)
[ "$before" = "$after2" ] || fail "case 5: empty payload still wrote a file"
pass "exit-plan-mode no-ops on empty payload"

# Case 6: the written plans conform to the Capsa schema (if the validator is
# reachable and python3 is present).
if command -v python3 >/dev/null 2>&1; then
  # Provide the minimal capsule the validator expects.
  cat > .capsa/capsule.yaml <<'EOF'
capsa_version: "0.2.0"
project:
  name: "t"
  slug: t
  repo: ""
  created: 2026-01-01
status: active
EOF
  cat > .capsa/charter.md <<'EOF'
---
updated: 2026-01-01
---
# Charter — t
EOF
  vout=$(python3 "$ROOT/validator/validate.py" .capsa 2>&1 || true)
  case "$vout" in
    *"conforming capsule"*) pass "written plans keep the capsule conforming" ;;
    *) fail "case 6: capsule not conforming after writes: $vout" ;;
  esac
fi

printf '\nAll exit-plan-mode tests passed.\n'
