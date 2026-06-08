#!/usr/bin/env bash
# Smoke test for ADR-0021 per-node requirements:
#   - the renamed `## Requirements & invariants` section + seed line,
#   - the fm_section extractor,
#   - post-edit-marker surfacing a node's requirements at edit time,
#   - lint accepting a seeded node.
# The natural-language capture convention is behavioral (CLAUDE.md), not
# unit-testable here. Pure bash; exits non-zero on first failure.

set -eu

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }

cd "$ROOT"                       # so relative code: paths resolve for lint
export AIMS_MEMORY_DIR="$TMP/memory"

# shellcheck source=/dev/null
. "$ROOT/templates/memory/_lib.sh"

# Scaffold a node with a REAL existing code path so lint has nothing else to flag.
bash "$ROOT/templates/memory/new-node.sh" iface/foo module templates/memory/_lib.sh >/dev/null
LEAF="$AIMS_MEMORY_DIR/iface/foo.md"
[ -f "$LEAF" ] || fail "scaffold did not create $LEAF"

# Case 1: scaffold uses the renamed section with the seed requirement line.
grep -qxF '## Requirements & invariants' "$LEAF" || fail "case 1: renamed heading missing"
grep -q 'none recorded beyond CLAUDE.md'  "$LEAF" || fail "case 1: seed requirement line missing"
grep -qxF '## Invariants & gotchas' "$LEAF" && fail "case 1: old heading still present"
pass "new-node scaffolds ## Requirements & invariants with the seed line"

# Case 2: fm_section extracts ONLY that section's body.
sec=$(fm_section "$LEAF" "Requirements & invariants")
printf '%s' "$sec" | grep -q 'none recorded beyond CLAUDE.md' \
  || fail "case 2: fm_section did not return the seed line"
printf '%s' "$sec" | grep -q '## Known issues' \
  && fail "case 2: fm_section bled into the next section"
pass "fm_section extracts the named section body only"

# Case 3: post-edit-marker surfaces the requirements at edit time.
out=$(printf '%s' '{"tool_input":{"file_path":"templates/memory/_lib.sh"}}' \
      | bash "$ROOT/templates/hooks/post-edit-marker.sh")
printf '%s' "$out" | grep -q 'Recorded requirements for the edited file' \
  || fail "case 3: marker note missing the requirements preamble"
printf '%s' "$out" | grep -q 'none recorded beyond CLAUDE.md' \
  || fail "case 3: marker did not surface the node's requirement text"
pass "post-edit-marker surfaces node requirements on a matching edit"

# Case 4: lint stays clean on the seeded node (renamed heading accepted).
issues=$(bash "$ROOT/templates/memory/lint.sh" 2>/dev/null)
[ -z "$issues" ] || fail "case 4: lint reported issues on a seeded node: $issues"
pass "lint clean on a seeded node (renamed section accepted)"

printf '\nAll requirements tests passed.\n'
