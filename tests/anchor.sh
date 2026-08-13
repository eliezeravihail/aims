#!/usr/bin/env bash
# Behavior test for the companion knowledge layer: knowledge/anchor.py + knowledge/staleness_hook.py.
# A source file foo.py has a companion foo.py.md beside it, anchored to foo.py by content hash.
# System records (goals.md, architecture.md — no same-named source file) carry no anchor.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
A="$ROOT/knowledge/anchor.py"; H="$ROOT/knowledge/staleness_hook.py"
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
fail(){ echo "FAIL: $1"; exit 1; }
cd "$W"; mkdir -p src
printf 'def svg(m): return "<svg/>"\n' > src/render.py
cat > src/render.py.md <<'EOF'
---
title: "render.py"
date: 2026-08-12
---
## Insights
- SVG chosen over canvas: pages are static.
## Decisions
- render must not know how the maze was generated.
## Discussions
- considered PNG; dropped (not crisp when zoomed).
EOF
cat > goals.md <<'EOF'
---
title: "goals"
date: 2026-08-12
---
Build static maze sites.
EOF
hook(){ echo "{\"tool_input\":{\"file_path\":\"$1\"},\"cwd\":\"$W\"}" | python3 "$H"; }

python3 "$A" src/render.py.md >/dev/null || fail "stamp companion"
python3 "$A" goals.md | grep -q 'no anchor' || fail "system record should get no anchor"
grep -q '^hash:' src/render.py.md || fail "companion -> hash"
grep -qE '^(hash|shape):' goals.md && fail "system record must carry no anchor"
grep -q 'code:' src/render.py.md && fail "there must be no code: field"

# idempotent
cp src/render.py.md b.md; python3 "$A" src/render.py.md >/dev/null
diff -q b.md src/render.py.md >/dev/null || fail "not idempotent"

# silent in-sync
[ -z "$(hook src/render.py.md)" ] || fail "advisory when in-sync"
[ -z "$(hook goals.md)" ]        || fail "system record flagged"

# source change -> companion flags
printf 'def svg(m): return "<svg>x</svg>"\n' > src/render.py
hook src/render.py.md | grep -q stale || fail "drift not flagged"

# editing the companion prose does NOT trip (anchor is the source file, not the record)
python3 "$A" src/render.py.md >/dev/null
printf '\n- more prose.\n' >> src/render.py.md
[ -z "$(hook src/render.py.md)" ] || fail "companion self-trip"

# renaming BOTH together keeps it in sync (same-name pairing, no stored path)
git init -q 2>/dev/null
mv src/render.py src/svg.py && mv src/render.py.md src/svg.py.md
[ -z "$(hook src/svg.py.md)" ] || fail "rename-both broke sync"

# renaming only the source (companion left stale-named) -> flagged as possibly moved
printf 'def svg(m): return "<svg/>"\n' > src/svg.py
python3 "$A" src/svg.py.md >/dev/null
mv src/svg.py src/canvas.py
hook src/svg.py.md | grep -q 'missing\|stale' || fail "orphaned companion not flagged"

echo "anchor: all checks passed"
