#!/usr/bin/env bash
# Behavior test for the capsa staleness layer: tools/aims_anchor.py + hooks/staleness_read.py.
# Asserts: idempotent stamping; silent when in-sync; content drift detected; shape is content-blind
# but catches structural change; claim-kind conflict guarded; fail-open on a missing source.
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
id: 1
title: "core owns arithmetic"
status: accepted
date: 2026-08-12
---

## Context
x
EOF
cat > .capsa/components/core/component.md <<'EOF'
---
title: "core"
status: active
created: 2026-08-12
---

## Purpose
x
EOF

hook() { echo "{\"tool_input\":{\"file_path\":\"$1\"},\"cwd\":\"$WORK\"}" | python3 "$HOOK"; }

python3 "$TOOL" .capsa/decisions/0001 src/core/a.py src/core/b.py >/dev/null || fail "stamp anchors"
python3 "$TOOL" --shape .capsa/components/core/component src/core >/dev/null || fail "stamp shape"

# 1. idempotent
cp .capsa/decisions/0001.md before.md
python3 "$TOOL" .capsa/decisions/0001 src/core/a.py src/core/b.py >/dev/null
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

# 6. claim-kind conflict guarded
python3 "$TOOL" --shape .capsa/decisions/0001 src/core 2>&1 | grep -q 'not both' || fail "conflict not guarded"

# 7. fail-open on missing source (advisory, no crash, exit 0)
rm src/core/b.py
hook .capsa/decisions/0001.md | grep -q 'possibly moved' || fail "missing source not handled"

echo "capsa-anchor: all checks passed"
