#!/usr/bin/env bash
# Smoke test for the PostToolUse marker hook (templates/hooks/post-edit-marker.sh)
# over a Capsa capsule with COMPUTED freshness (no stored dirty flag).
#
# The hook's jobs now: name any insight whose `code_globs` cover the edited
# path (factual note), route unmatched paths to the out-of-capsule inbox, and
# refresh an advisory marker under .claude/ (never inside the capsule).
#
# Self-contained: builds a throwaway git repo with its own .claude/memory
# (copied from templates) and .capsa/insights, so git-based staleness is real
# and nothing touches the host repo. Pure bash. Exits 0 on success.

set -eu

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }

# ── Build an isolated repo ──────────────────────────────────────────────
cd "$TMP"
git init -q
git config user.email t@t; git config user.name t
mkdir -p .claude/memory .capsa/insights/code src
cp "$ROOT"/templates/memory/*.sh .claude/memory/
HOOK="$ROOT/templates/hooks/post-edit-marker.sh"
INBOX=".claude/aims-state/inbox.md"

# Seed a code insight covering two paths (one range-suffixed).
LEAF=".capsa/insights/code/foo.md"
cat > "$LEAF" <<'EOF'
---
kind: code
title: "Foo module"
created: 2026-01-01
updated: 2026-01-01
code_globs: ["src/foo.py", "src/bar.py:10-30"]
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
: > src/foo.py; : > src/bar.py

# Case 1: matching path → note names the insight; inbox NOT created.
out=$(printf '%s' '{"tool_input":{"file_path":"src/foo.py"}}' | bash "$HOOK")
case "$out" in *"Foo module"*) ;; *) fail "case 1: note should name the insight (got: $out)";; esac
[ ! -f "$INBOX" ] || fail "case 1: matching path must NOT go to the inbox"
pass "marker names the insight on a matching code_globs entry"

# Case 2: range-suffixed entry matches the bare path.
out=$(printf '%s' '{"tool_input":{"file_path":"src/bar.py"}}' | bash "$HOOK")
case "$out" in *"Foo module"*) ;; *) fail "case 2: range match should name insight";; esac
pass "marker matches src/bar.py against src/bar.py:10-30"

# Case 3: non-matching path goes to the inbox.
rm -f "$INBOX"
printf '%s' '{"tool_input":{"file_path":"src/unknown.py"}}' | bash "$HOOK" >/dev/null
grep -qxF -- "- src/unknown.py" "$INBOX" || fail "case 3: inbox missing src/unknown.py"
pass "marker routes unmatched paths to the inbox"

# Case 4: capsule + tooling surfaces are skipped (no inbox, no note).
rm -f "$INBOX"
o1=$(printf '%s' '{"tool_input":{"file_path":".capsa/insights/code/foo.md"}}' | bash "$HOOK")
o2=$(printf '%s' '{"tool_input":{"file_path":".claude/settings.json"}}' | bash "$HOOK")
[ -z "$o1$o2" ] || fail "case 4: .capsa/ and .claude/ edits must inject nothing"
[ ! -f "$INBOX" ] || fail "case 4: skip-listed paths must not touch the inbox"
pass "marker skips .capsa/* and .claude/* edits"

# Case 5: inbox de-dup — same unmatched path twice yields one entry.
rm -f "$INBOX"
printf '%s' '{"tool_input":{"file_path":"src/dup.py"}}' | bash "$HOOK" >/dev/null
printf '%s' '{"tool_input":{"file_path":"src/dup.py"}}' | bash "$HOOK" >/dev/null
n=$(grep -cxF -- "- src/dup.py" "$INBOX" || true)
[ "$n" = "1" ] || fail "case 5: expected 1 inbox entry, got $n"
pass "inbox de-duplicates identical paths"

# Case 6: absolute path inside the repo is normalized and matched.
rm -f "$INBOX"
out=$(printf '%s' "{\"tool_input\":{\"file_path\":\"$TMP/src/foo.py\"}}" | bash "$HOOK")
case "$out" in *"Foo module"*) ;; *) fail "case 6: absolute repo path should match";; esac
[ ! -f "$INBOX" ] || fail "case 6: absolute matching path must NOT leak into inbox"
pass "marker normalizes an absolute repo path before matching"

# Case 7: absolute path outside the repo bails out silently.
rm -f "$INBOX"
printf '%s' '{"tool_input":{"file_path":"/etc/passwd"}}' | bash "$HOOK" >/dev/null
[ ! -f "$INBOX" ] || fail "case 7: outside-repo path must NOT be added to the inbox"
pass "marker bails on absolute paths outside the repo"

# Case 8 (ADR-0014): a glob code_globs entry matches.
LEAF2=".capsa/insights/code/loaders.md"
cat > "$LEAF2" <<'EOF'
---
kind: code
title: "Loaders"
created: 2026-01-01
updated: 2026-01-01
code_globs: ["src/loaders/*.py"]
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
mkdir -p src/loaders; : > src/loaders/json_loader.py
rm -f "$INBOX"
out=$(printf '%s' '{"tool_input":{"file_path":"src/loaders/json_loader.py"}}' | bash "$HOOK")
case "$out" in *"Loaders"*) ;; *) fail "case 8: glob should match json_loader.py";; esac
[ ! -f "$INBOX" ] || fail "case 8: glob-matched path must NOT leak into inbox"
pass "marker matches code_globs globs (ADR-0014)"

# Case 9: computed staleness — find-dirty reports an insight whose code_globs
# has an uncommitted change; a fresh (committed & up-to-date) insight is not.
git add -A && git commit -qm seed
# Now edit a tracked file without committing → src/foo.py is dirty.
echo "// change" > src/foo.py
out=$(bash .claude/memory/find-dirty.sh)
case "$out" in *"$LEAF"*) ;; *) fail "case 9: find-dirty should list the stale insight (got: $out)";; esac
pass "find-dirty reports the insight with an uncommitted code_globs change"

# Case 10: `mark.sh <insight> consolidated` bumps updated: (clears staleness
# for committed state — here still stale due to the uncommitted edit, so we
# just assert the date bumped).
bash .claude/memory/mark.sh "$LEAF" consolidated
. .claude/memory/_lib.sh
today_val=$(today)
got=$(fm_get "$LEAF" updated)
[ "$got" = "$today_val" ] || fail "case 10: expected updated=$today_val, got '$got'"
pass "mark.sh consolidated bumps updated: to today"

printf '\nAll marker tests passed.\n'
