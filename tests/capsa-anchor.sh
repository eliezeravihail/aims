#!/usr/bin/env bash
# Behavior test for the lean capsa staleness layer: tools/aims_anchor.py + hooks/staleness_read.py.
# A record declares `code:` once; the tool stamps a single `hash:` (content) or `shape:` (structure).
# Asserts: idempotent stamping; silent when in-sync; content drift detected; shape is content-blind
# but catches structural change; a component auto-picks shape; fail-open on a missing source;
# a record with no `code:` is a no-op.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOL="$ROOT/tools/aims_anchor.py"
HOOK="$ROOT/hooks/staleness_read.py"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
fail() { echo "FAIL: $1"; exit 1; }

cd "$WORK"
mkdir -p src/core .capsa/decisions .capsa/components/core
printf 'def a():\n    return 1\n' > src/core/a.py
printf 'def b():\n    return 2\n' > src/core/b.py

cat > .capsa/decisions/0001.md <<'EOF'
---
title: "core owns arithmetic"
date: 2026-08-12
code: src/core/**
---
core owns arithmetic.
EOF
cat > .capsa/components/core/component.md <<'EOF'
---
title: "core"
date: 2026-08-12
code: src/core
---
Pure arithmetic.
EOF
cat > .capsa/decisions/0002-pure-thesis.md <<'EOF'
---
title: "design is the goal"
date: 2026-08-12
---
No code anchor.
EOF

hook() { echo "{\"tool_input\":{\"file_path\":\"$1\"},\"cwd\":\"$WORK\"}" | python3 "$HOOK"; }

python3 "$TOOL" .capsa/decisions/0001 >/dev/null || fail "stamp content"
python3 "$TOOL" .capsa/components/core/component >/dev/null || fail "stamp shape (component auto)"

# component auto-picked shape; decision picked content
grep -q '^shape:' .capsa/components/core/component.md || fail "component did not get shape:"
grep -q '^hash:' .capsa/decisions/0001.md || fail "decision did not get hash:"

# 1. idempotent
cp .capsa/decisions/0001.md before.md
python3 "$TOOL" .capsa/decisions/0001 >/dev/null
diff -q before.md .capsa/decisions/0001.md >/dev/null || fail "not idempotent"

# 2. silent in-sync
[ -z "$(hook .capsa/decisions/0001.md)" ] || fail "advisory when in-sync"

# 3. content drift detected
printf 'def a():\n    return 999\n' > src/core/a.py
hook .capsa/decisions/0001.md | grep -q 'may be stale' || fail "content drift not detected"

# 4. shape content-blind (editing a file under the component is NOT a structural change)
[ -z "$(hook .capsa/components/core/component.md)" ] || fail "shape fired on content edit"

# 5. structural change detected
printf 'def c():\n    return 3\n' > src/core/c.py
hook .capsa/components/core/component.md | grep -q 'structure under' || fail "structural change not detected"

# 6. pure-thesis record (no code:) is a no-op for the tool and silent for the hook
python3 "$TOOL" .capsa/decisions/0002-pure-thesis | grep -q 'nothing to anchor' || fail "no-code not a no-op"
[ -z "$(hook .capsa/decisions/0002-pure-thesis.md)" ] || fail "pure-thesis flagged"

# 7. fail-open on missing source
rm -rf src/core
[ -n "$(hook .capsa/decisions/0001.md)" ] || fail "missing source not reported"
hook .capsa/decisions/0001.md | grep -q 'stale' || fail "missing source should advise re-verify"

echo "capsa-anchor: all checks passed"
