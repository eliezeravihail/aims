#!/usr/bin/env bash
# Test stop-consolidate.sh under the ADR-0009 in-band protocol.
#
# Covers:
#   1. --force on a dirty leaf emits Stop block-JSON with the node section.
#   2. H1 (ADR-0024): after a normal --force exit the mutex SURVIVES so the
#      model can later mark the node consolidated. The prior `trap EXIT`
#      released it on the success path, defeating the protocol.
#   3. H2 (ADR-0024): the advisory `.marker` (written by post-edit-marker)
#      does NOT gate the strict `.lock` mutex — separate suffix, separate
#      protocol.
#   4. Throttle quietly silences the hook when N_DIRTY<max and the interval
#      has not elapsed.
#
# jq is OPTIONAL — the JSON shape is asserted with plain grep so the test
# runs on stock machines too.

set -u
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
pass(){ printf '  PASS: %s\n' "$1"; }
fail(){ printf '  FAIL: %s\n' "$1" >&2; exit 1; }

export AIMS_MEMORY_DIR="$TMP/memory"
export AIMS_MEMORY_STATE_FILE="$TMP/.last-consolidated"
mkdir -p "$AIMS_MEMORY_DIR/x"
LEAF="$AIMS_MEMORY_DIR/x/foo.md"
cat > "$LEAF" <<EOF
---
node: x/foo
kind: module
code:
  - $TMP/src/foo.py
dirty: true
last_touched: 2026-01-01T00:00:00Z
last_consolidated: 2026-01-01T00:00:00Z
---
body
EOF
mkdir -p "$TMP/src"; : > "$TMP/src/foo.py"

# Helper: run stop-consolidate.sh from the templates/ copy (single source of
# truth). The `.claude/` mirror is byte-identical (enforced by
# tests/copies-identical.sh from Track 4).
run_stop(){
  local sid="${1:-S1}"; shift || true
  printf '{"session_id":"%s"}' "$sid" \
    | bash "$ROOT/templates/hooks/stop-consolidate.sh" "$@"
}

echo "### consolidate: --force emits Stop block-JSON with node section ###"
out=$(run_stop S1 --force)
echo "$out" | grep -q '"decision":"block"' || fail "expected decision:block on --force"
echo "$out" | grep -q '"reason"'           || fail "expected reason field"
echo "$out" | grep -q 'x/foo'              || fail "reason should mention dirty node x/foo"
pass "force run emits Stop block-JSON with node section"

echo "### H1 (ADR-0024): .lock SURVIVES normal exit (kept for the model) ###"
[ -f "$AIMS_MEMORY_DIR/x/foo.lock" ] || fail "H1: lock removed prematurely by EXIT trap"
pass "H1: strict mutex survives normal exit"

echo "### H2 (ADR-0024): .marker is independent of .lock ###"
# A peer post-edit-marker would stamp .marker; that must not gate try_claim.
printf 'OTHER\n' > "$AIMS_MEMORY_DIR/x/foo.marker"
rm -f "$AIMS_MEMORY_DIR/x/foo.lock"
out=$(run_stop S2 --force)
echo "$out" | grep -q 'x/foo' || fail "H2: .marker must not gate the mutex"
pass "H2: advisory .marker and strict .lock are independent"

echo "### throttle: silent when N_DIRTY<max and interval not elapsed ###"
date -u +%s > "$AIMS_MEMORY_STATE_FILE"
rm -f "$AIMS_MEMORY_DIR/x/foo.lock"
out=$(AIMS_MEMORY_DIRTY_MAX=5 AIMS_MEMORY_INTERVAL_SEC=99999 run_stop S3 || true)
[ -z "$out" ] || fail "throttle should silence the hook (got '$out')"
pass "throttle blocks when below threshold"

echo "### ADR-0027: discrepancy detection across Stop fires ###"
# Reset state: clear prior snapshots from earlier test cases, drop lock,
# move throttle state file backwards.
rm -f "$AIMS_MEMORY_DIR/x/foo.lock" "$AIMS_MEMORY_DIR/.last-report-snapshot"
echo 0 > "$AIMS_MEMORY_STATE_FILE"
# First emit: writes the snapshot AND should NOT prepend a discrepancy
# breadcrumb (no prior snapshot).
out1=$(run_stop S4 --force)
echo "$out1" | grep -q 'DISCREPANCY DETECTED' \
  && fail "first emit should not see a discrepancy"
[ -f "$AIMS_MEMORY_DIR/.last-report-snapshot" ] \
  || fail "first emit should have written the snapshot"
pass "first emit writes snapshot; no discrepancy breadcrumb"

# Simulate the model claiming `===[aims: queue drained]===` but doing
# nothing: state stays identical. Clear the lock so try_claim succeeds
# again on the next fire (the lock would normally survive — but a fresh
# claim by the same session uses the held-locks path; we keep this
# simple by removing it).
rm -f "$AIMS_MEMORY_DIR/x/foo.lock"
out2=$(run_stop S4 --force)
echo "$out2" | grep -q 'DISCREPANCY DETECTED' \
  || fail "second emit on unchanged state must prepend discrepancy"
echo "$out2" | grep -q 'previous report did not match measured state' \
  || fail "discrepancy must name the inconsistency factually"
pass "second emit on unchanged state surfaces the discrepancy"

# Sanity: when state DOES change (leaf cleaned), no discrepancy on the
# next emit even if the snapshot lingers. Simulate by clearing dirty=true.
sed -i.bak 's/^dirty: true/dirty: false/' "$LEAF"; rm -f "$LEAF.bak"
# Add an inbox bullet to keep the hook firing on something.
printf -- '- $TMP/src/foo.py\n' > "$AIMS_MEMORY_DIR/_inbox.md"
rm -f "$AIMS_MEMORY_DIR/x/foo.lock"
out3=$(run_stop S5 --force)
echo "$out3" | grep -q 'DISCREPANCY DETECTED' \
  && fail "state change must NOT trigger a discrepancy on the next emit"
pass "state change clears discrepancy on next emit"

echo
echo "RESULT: all consolidate tests passed."
