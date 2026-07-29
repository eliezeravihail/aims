#!/usr/bin/env bash
# Test stop-consolidate.sh under the ADR-0009 in-band protocol, over a Capsa
# capsule with COMPUTED freshness.
#
# Covers:
#   1. --force on a stale insight emits Stop block-JSON with the insight section.
#   2. ADR-0030: no strict mutex is created; the advisory marker never gates.
#   3. ADR-0028: a small insight → delta-mode; one past the delta threshold →
#      compact-mode.
#   4. Throttle quietly silences the hook below threshold within the interval.
#   5. ADR-0027: report-discrepancy detection across Stop fires.
#
# Self-contained isolated git repo (own .claude/memory + .capsa). jq optional.

set -u
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
pass(){ printf '  PASS: %s\n' "$1"; }
fail(){ printf '  FAIL: %s\n' "$1" >&2; exit 1; }

cd "$TMP"
git init -q; git config user.email t@t; git config user.name t
mkdir -p .claude/memory .capsa/insights/code .capsa/plans src
cp "$ROOT"/templates/memory/*.sh .claude/memory/
export AIMS_MEMORY_STATE_FILE="$TMP/.claude/aims-state/.last-consolidated"
export AIMS_SNAPSHOT_FILE="$TMP/.claude/aims-state/.last-report-snapshot"
mkdir -p "$TMP/.claude/aims-state"

# A stale code insight: its code_globs file has an uncommitted change.
LEAF=".capsa/insights/code/foo.md"
cat > "$LEAF" <<'EOF'
---
kind: code
title: "Foo module"
created: 2026-01-01
updated: 2026-01-01
code_globs: ["src/foo.py"]
tags: []
---

## Purpose
p
## Invariants & gotchas
i
## Pointers
ptr
## Deltas
EOF
: > src/foo.py
git add -A && git commit -qm seed
echo "// change" > src/foo.py   # uncommitted → foo insight is stale

run_stop(){
  local sid="${1:-S1}"; shift || true
  printf '{"session_id":"%s"}' "$sid" \
    | bash "$ROOT/templates/hooks/stop-consolidate.sh" "$@"
}

echo "### consolidate: --force emits Stop block-JSON with insight section ###"
out=$(run_stop S1 --force)
echo "$out" | grep -q '"decision":"block"' || fail "expected decision:block on --force"
echo "$out" | grep -q '"reason"'            || fail "expected reason field"
echo "$out" | grep -q 'foo.md'              || fail "reason should mention the stale insight"
pass "force run emits Stop block-JSON with insight section"

echo "### ADR-0030: no strict mutex inside the capsule ###"
[ -z "$(find .capsa -name '*.lock' 2>/dev/null)" ] || fail "no .lock may be created in the capsule"
pass "no lock created by the Stop hook"

echo "### ADR-0028: small insight → delta-mode prompt ###"
echo "$out" | grep -q 'mode: delta' || fail "expected delta-mode ACTION for a small insight"
pass "delta mode selected for a small insight"

echo "### ADR-0028: insight past the delta threshold → compact-mode prompt ###"
LEAF2=".capsa/insights/code/bar.md"
{
  cat <<'EOF'
---
kind: code
title: "Bar module"
created: 2026-01-01
updated: 2026-01-01
code_globs: ["src/bar.py"]
tags: []
---

## Purpose
p
## Invariants & gotchas
i
## Pointers
ptr
## Deltas
EOF
  for i in $(seq 1 13); do printf -- '- 2026-01-%02d: delta %d — cafe%03d\n' "$i" "$i" "$i"; done
} > "$LEAF2"
: > src/bar.py; git add -A && git commit -qm bar
echo "// change" > src/bar.py   # make bar stale too
out=$(run_stop S2b --force)
echo "$out" | grep -q 'bar.md'       || fail "second stale insight should be queued"
echo "$out" | grep -q 'mode: compact' || fail "expected compact-mode ACTION past the delta threshold"
pass "compact mode selected past the delta threshold"
rm -f "$LEAF2"; git add -A && git commit -qm rmbar

echo "### throttle: silent when N_STALE<max and interval not elapsed ###"
date -u +%s > "$AIMS_MEMORY_STATE_FILE"
out=$(AIMS_MEMORY_DIRTY_MAX=5 AIMS_MEMORY_INTERVAL_SEC=99999 run_stop S3 || true)
[ -z "$out" ] || fail "throttle should silence the hook (got '$out')"
pass "throttle blocks when below threshold"

echo "### ADR-0027: discrepancy detection across Stop fires ###"
rm -f "$AIMS_SNAPSHOT_FILE"
echo 0 > "$AIMS_MEMORY_STATE_FILE"
out1=$(run_stop S4 --force)
echo "$out1" | grep -q 'DISCREPANCY DETECTED' && fail "first emit should not see a discrepancy"
[ -f "$AIMS_SNAPSHOT_FILE" ] || fail "first emit should have written the snapshot"
pass "first emit writes snapshot; no discrepancy breadcrumb"

out2=$(run_stop S4 --force)
echo "$out2" | grep -q 'DISCREPANCY DETECTED' \
  || fail "second emit on unchanged state must prepend discrepancy"
echo "$out2" | grep -q 'previous report did not match measured state' \
  || fail "discrepancy must name the inconsistency factually"
pass "second emit on unchanged state surfaces the discrepancy"

# State change (foo committed → no longer stale) + an inbox bullet: no discrepancy.
git add -A && git commit -qm cleanfoo
printf -- '- src/other.py\n' > "$TMP/.claude/aims-state/inbox.md"
out3=$(run_stop S5 --force)
echo "$out3" | grep -q 'DISCREPANCY DETECTED' \
  && fail "state change must NOT trigger a discrepancy on the next emit"
pass "state change clears discrepancy on next emit"

echo
echo "RESULT: all consolidate tests passed."
