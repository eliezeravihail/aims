#!/usr/bin/env bash
# Smoke test for the PostToolUse marker hook (templates/hooks/post-edit-marker.sh)
# and the underlying mark.sh logic.
#
# Pure bash; no Anthropic API needed. Exits 0 on success, non-zero on
# first failure with a clear message.

set -eu

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }

export AIMS_MEMORY_DIR="$TMP/memory"

# Seed a leaf with a couple of code paths.
bash "$ROOT/templates/memory/new-node.sh" interface/foo module >/dev/null
LEAF="$AIMS_MEMORY_DIR/interface/foo.md"
[ -f "$LEAF" ] || fail "scaffold did not create $LEAF"
python3 -c "
p='$LEAF'
s=open(p).read()
s=s.replace('code: []', 'code:\n  - src/foo.py\n  - src/bar.py:10-30')
open(p,'w').write(s)
"

# Case 1: marker on a matching path flips dirty:true.
printf '%s' '{"tool_input":{"file_path":"src/foo.py"}}' | \
  bash "$ROOT/templates/hooks/post-edit-marker.sh"
. "$ROOT/templates/memory/_lib.sh"
v=$(fm_get "$LEAF" dirty)
[ "$v" = "true" ] || fail "case 1: expected dirty=true, got '$v'"
pass "marker flips dirty:true on matching code: entry"

# Case 2: range-suffixed code: entries match the bare path.
# Reset to dirty:false first.
python3 -c "
import re
p='$LEAF'
s=open(p).read()
s=re.sub(r'dirty: true', 'dirty: false', s, count=1)
open(p,'w').write(s)
"
printf '%s' '{"tool_input":{"file_path":"src/bar.py"}}' | \
  bash "$ROOT/templates/hooks/post-edit-marker.sh"
v=$(fm_get "$LEAF" dirty)
[ "$v" = "true" ] || fail "case 2: expected dirty=true on range match, got '$v'"
pass "marker matches src/bar.py against src/bar.py:10-30"

# Case 3: non-matching path goes to _inbox.md.
rm -f "$AIMS_MEMORY_DIR/_inbox.md"
python3 -c "
import re
p='$LEAF'
s=open(p).read()
s=re.sub(r'dirty: true', 'dirty: false', s, count=1)
open(p,'w').write(s)
"
printf '%s' '{"tool_input":{"file_path":"src/unknown.py"}}' | \
  bash "$ROOT/templates/hooks/post-edit-marker.sh"
v=$(fm_get "$LEAF" dirty)
[ "$v" = "false" ] || fail "case 3: leaf should stay clean for unknown path, got '$v'"
grep -qxF -- "- src/unknown.py" "$AIMS_MEMORY_DIR/_inbox.md" || \
  fail "case 3: inbox missing src/unknown.py entry"
pass "marker routes unknown paths to _inbox.md (no leaf marked)"

# Case 4: marker correctly skips paths under docs/memory/ and .claude/.
python3 -c "
import re
p='$LEAF'
s=open(p).read()
s=re.sub(r'dirty: true', 'dirty: false', s, count=1)
open(p,'w').write(s)
"
printf '%s' '{"tool_input":{"file_path":"docs/memory/foo.md"}}' | \
  bash "$ROOT/templates/hooks/post-edit-marker.sh"
printf '%s' '{"tool_input":{"file_path":".claude/settings.json"}}' | \
  bash "$ROOT/templates/hooks/post-edit-marker.sh"
v=$(fm_get "$LEAF" dirty)
[ "$v" = "false" ] || fail "case 4: leaf should NOT be dirty after meta-path edits, got '$v'"
pass "marker skips docs/memory/* and .claude/* edits"

# Case 5: find-dirty.sh sees the right state.
python3 -c "
p='$LEAF'
s=open(p).read()
s=s.replace('dirty: false', 'dirty: true', 1)
open(p,'w').write(s)
"
out=$(bash "$ROOT/templates/memory/find-dirty.sh")
[ "$out" = "$LEAF" ] || fail "case 5: find-dirty got '$out', expected '$LEAF'"
pass "find-dirty.sh returns the dirty leaf path"

# Case 6: inbox dedup — same unknown path twice yields one entry.
printf '%s' '{"tool_input":{"file_path":"src/unknown.py"}}' | \
  bash "$ROOT/templates/hooks/post-edit-marker.sh"
n=$(grep -cxF -- "- src/unknown.py" "$AIMS_MEMORY_DIR/_inbox.md" || true)
[ "$n" = "1" ] || fail "case 6: expected 1 inbox entry for src/unknown.py, got $n"
pass "inbox de-duplicates identical paths"

# Case 7: absolute path inside repo gets normalized and marks dirty.
python3 -c "
import re
p='$LEAF'
s=open(p).read()
s=re.sub(r'dirty: true', 'dirty: false', s, count=1)
open(p,'w').write(s)
"
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "$ROOT")
printf '{"tool_input":{"file_path":"%s/src/foo.py"}}' "$REPO_ROOT" | \
  bash "$ROOT/templates/hooks/post-edit-marker.sh"
v=$(fm_get "$LEAF" dirty)
[ "$v" = "true" ] || fail "case 7: absolute repo path should normalize and mark dirty, got '$v'"
pass "marker normalizes absolute repo paths"

# Case 8: absolute path under .claude/ gets skipped (not added to inbox).
prev_inbox=$(wc -l < "$AIMS_MEMORY_DIR/_inbox.md" 2>/dev/null || echo 0)
printf '{"tool_input":{"file_path":"%s/.claude/settings.json"}}' "$REPO_ROOT" | \
  bash "$ROOT/templates/hooks/post-edit-marker.sh"
new_inbox=$(wc -l < "$AIMS_MEMORY_DIR/_inbox.md" 2>/dev/null || echo 0)
[ "$prev_inbox" = "$new_inbox" ] || \
  fail "case 8: absolute .claude/ path should be skipped, inbox grew $prev_inbox→$new_inbox"
pass "marker skips absolute paths under .claude/"

# Case 9: absolute path outside the repo is dropped silently.
prev_inbox=$(wc -l < "$AIMS_MEMORY_DIR/_inbox.md" 2>/dev/null || echo 0)
printf '%s' '{"tool_input":{"file_path":"/etc/hosts"}}' | \
  bash "$ROOT/templates/hooks/post-edit-marker.sh"
new_inbox=$(wc -l < "$AIMS_MEMORY_DIR/_inbox.md" 2>/dev/null || echo 0)
[ "$prev_inbox" = "$new_inbox" ] || \
  fail "case 9: out-of-repo absolute path should be dropped, inbox grew $prev_inbox→$new_inbox"
pass "marker drops absolute paths outside the repo"

printf '\nAll marker tests passed.\n'
