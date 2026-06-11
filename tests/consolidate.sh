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

echo
echo "RESULT: all consolidate tests passed."
