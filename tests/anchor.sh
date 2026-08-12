#!/usr/bin/env bash
# Behavior test for the co-located knowledge layer: knowledge/anchor.py + knowledge/staleness_hook.py.
# Records live IN the code tree; the anchor target is derived from the record's own location (no code:).
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
A="$ROOT/knowledge/anchor.py"; H="$ROOT/knowledge/staleness_hook.py"
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
fail(){ echo "FAIL: $1"; exit 1; }
cd "$W"
mkdir -p src/render/decisions
printf 'def svg(m): return "<svg/>"\n' > src/render/render.py
cat > charter.md <<'EOF'
---
title: "app"
date: 2026-08-12
---
root.
EOF
cat > src/render/component.md <<'EOF'
---
title: "render"
date: 2026-08-12
---
render.
EOF
cat > src/render/decisions/0001.md <<'EOF'
---
title: "svg not canvas"
date: 2026-08-12
---
static pages.
EOF
hook(){ echo "{\"tool_input\":{\"file_path\":\"$1\"},\"cwd\":\"$W\"}" | python3 "$H"; }

python3 "$A" src/render/component.md >/dev/null || fail "stamp component"
python3 "$A" src/render/decisions/0001.md >/dev/null || fail "stamp decision"
python3 "$A" charter.md | grep -q 'no anchor' || fail "root should get no anchor"

grep -q '^shape:' src/render/component.md || fail "component -> shape"
grep -q '^hash:'  src/render/decisions/0001.md || fail "decision -> content hash"
grep -qE '^(shape|hash):' charter.md && fail "root record must carry no anchor"
grep -q 'code:' src/render/component.md && fail "there must be no code: field"

# idempotent
cp src/render/component.md b.md; python3 "$A" src/render/component.md >/dev/null
diff -q b.md src/render/component.md >/dev/null || fail "not idempotent"

# silent in-sync
for f in src/render/component.md src/render/decisions/0001.md charter.md; do
  [ -z "$(hook $f)" ] || fail "advisory when in-sync: $f"; done

# content edit -> decision flags, component (shape) silent
printf 'def svg(m): return "<svg>x</svg>"\n' > src/render/render.py
hook src/render/decisions/0001.md | grep -q stale || fail "content drift not flagged"
[ -z "$(hook src/render/component.md)" ] || fail "shape fired on content edit"

# new file -> component (shape) flags
printf 'X=1\n' > src/render/theme.py
hook src/render/component.md | grep -q stale || fail "structural change not flagged"

# editing the record itself must not trip (design records excluded)
python3 "$A" src/render/component.md >/dev/null
printf '\nmore.\n' >> src/render/component.md
[ -z "$(hook src/render/component.md)" ] || fail "record self-trip"

# moving the component dir moves its records with it (no path stored) -> still in sync
mv src/render src/svg
[ -z "$(hook src/svg/component.md)" ] || fail "record broke after directory move"

echo "anchor: all checks passed"
