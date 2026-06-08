#!/usr/bin/env bash
# Smoke test for the IN-BAND Stop-hook consolidation contract (ADR-0009).
#
# The pre-ADR-0009 design POSTed to an Anthropic endpoint and let the hook
# rewrite the node itself; that mechanism (and its mock HTTP server) is gone.
# Today stop-consolidate.sh makes NO network call and does NOT edit nodes:
# it emits {"decision":"block","reason":<prompt>} naming each dirty node and
# the `mark.sh consolidated` command, bumps the throttle state file, and
# respects the throttle. The body rewrite + clean-flip is the in-band model's
# job — simulated here by calling mark.sh directly.
#
# Exits 0 on success, non-zero on first failure.

set -eu

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }

command -v jq >/dev/null 2>&1 || { printf '[SKIP] jq not available; skipping\n'; exit 0; }

export AIMS_MEMORY_DIR="$TMP/memory"
export AIMS_MEMORY_STATE_FILE="$TMP/.last-consolidated"
export AIMS_PLAN_DIR="$TMP/plans"          # empty → no in-progress-plan nudge
mkdir -p "$AIMS_PLAN_DIR"

cd "$ROOT"                                 # so the hook resolves its memory helpers
# shellcheck source=/dev/null
. "$ROOT/templates/memory/_lib.sh"

HOOK="$ROOT/templates/hooks/stop-consolidate.sh"

# Seed a dirty leaf with a real, existing code path.
bash "$ROOT/templates/memory/new-node.sh" interface/foo module templates/memory/_lib.sh >/dev/null
LEAF="$AIMS_MEMORY_DIR/interface/foo.md"
fm_set "$LEAF" dirty true

# Case 1: --force on a dirty leaf emits an in-band block prompt; the hook does
# NOT flip the leaf clean (that is the model's half).
out=$(bash "$HOOK" --force </dev/null 2>"$TMP/err")
[ "$(printf '%s' "$out" | jq -r '.decision' 2>/dev/null)" = "block" ] \
  || { cat "$TMP/err" >&2; fail "case 1: expected decision=block"; }
reason=$(printf '%s' "$out" | jq -r '.reason')
printf '%s' "$reason" | grep -qF "=== NODE: $LEAF" \
  || fail "case 1: reason missing the node section for $LEAF"
printf '%s' "$reason" | grep -q 'mark.sh' \
  || fail "case 1: reason missing the mark.sh consolidated instruction"
[ "$(fm_get "$LEAF" dirty)" = "true" ] \
  || fail "case 1: hook must NOT flip dirty itself (the in-band model does)"
pass "stop-consolidate --force queues an in-band block prompt; leaf stays dirty"

# Case 2: the throttle state file was bumped.
[ -r "$AIMS_MEMORY_STATE_FILE" ] || fail "case 2: state file not written"
pass "throttle state file (.last-consolidated) updated"

# Case 3: simulate the model finishing — mark.sh consolidated flips clean and
# removes the sidecar lock (ADR-0019).
printf 'peer\n%s\n' "interface/foo.md" > "${LEAF%.md}.lock"   # a held lock to clear
bash "$ROOT/templates/memory/mark.sh" "$LEAF" consolidated >/dev/null
[ "$(fm_get "$LEAF" dirty)" = "false" ] || fail "case 3: mark.sh consolidated should set dirty=false"
[ ! -e "${LEAF%.md}.lock" ] || fail "case 3: mark.sh consolidated should remove the .lock sidecar"
pass "mark.sh consolidated flips clean and clears the lock (model's half)"

# Case 4: nothing dirty, empty inbox, no in-progress plan → --force is silent.
out=$(bash "$HOOK" --force </dev/null 2>/dev/null)
[ -z "$out" ] || fail "case 4: no-op run should emit nothing, got: $out"
pass "no-op (0 dirty, no inbox, no plan): silent even with --force"

# Case 5: throttle — 1 dirty < DIRTY_MAX and interval not elapsed → no emission,
# leaf stays dirty.
fm_set "$LEAF" dirty true
out=$(AIMS_MEMORY_DIRTY_MAX=5 AIMS_MEMORY_INTERVAL_SEC=99999 \
      bash "$HOOK" </dev/null 2>/dev/null)
[ -z "$out" ] || fail "case 5: throttle should suppress emission, got: $out"
[ "$(fm_get "$LEAF" dirty)" = "true" ] || fail "case 5: leaf should stay dirty under throttle"
pass "throttle suppresses when N_DIRTY < threshold and interval recent"

printf '\nAll consolidate (in-band) tests passed.\n'
