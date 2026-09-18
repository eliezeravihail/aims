#!/usr/bin/env bash
# Deterministic coherence checks over the SHIPPED method surfaces (no model involved).
# aims' commands and references are PROSE, not code — you cannot unit-test "did the plan come out good".
# But a large, checkable slice of "does a command work" is structural: does every reference resolve, is
# every command discoverable, does every declared Kind have a review lens, is every ADR number unique.
# This catches exactly the class the 2026-09 self-review found by hand (a dangling results-v4 pointer, an
# undiscoverable /aims-panel-plan, a Kind with no lens, a duplicate 0008). Static; runs in the test suite.
#
# Scope: the shipped method + root records. NOT experiments/ (their product trees carry their own ADR
# namespaces and deliberately illustrative references) and NOT .aims/ (run-state + target-project paths).
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
fail=0
bad(){ printf '  FAIL: %s\n' "$1" >&2; fail=$((fail + 1)); }

SURFACES=(skills commands knowledge goals.md architecture.md base-dependencies.md README.md CLAUDE.md decisions)

# 1. ADR numbers are unique. (Would have caught the 0008 collision between two parallel branches.)
dupes="$(ls decisions/ 2>/dev/null | grep -oE '^[0-9]{4}' | sort | uniq -d)"
[ -z "$dupes" ] || bad "duplicate decisions/ ADR number(s): $(echo $dupes)"

# 2. Every decisions/NNNN referenced in a shipped surface resolves to an ADR file.
for ref in $(grep -rhoE 'decisions/[0-9]{4}' "${SURFACES[@]}" 2>/dev/null | sort -u); do
  n="${ref#decisions/}"
  ls decisions/${n}-*.md >/dev/null 2>&1 || bad "reference to nonexistent decisions/${n}"
done

# 3. Every references/X.md named in the skill/commands resolves (the references live under skills/aims-guide/).
for r in $(grep -rhoE 'references/[a-z0-9-]+\.md' skills commands 2>/dev/null | sort -u); do
  [ -f "skills/aims-guide/$r" ] || bad "reference to nonexistent skills/aims-guide/$r"
done

# 4. Every commands/X.md named in a surface resolves.
for c in $(grep -rhoE 'commands/[a-z0-9-]+\.md' "${SURFACES[@]}" 2>/dev/null | sort -u); do
  [ -f "$c" ] || bad "reference to nonexistent $c"
done

# 5. Every shipped aims-* command is discoverable: listed in both plugin manifests and the README.
for cmd in commands/aims-*.md; do
  name="$(basename "$cmd" .md)"
  grep -q "$name" .claude-plugin/plugin.json      || bad "$name missing from .claude-plugin/plugin.json"
  grep -q "$name" .claude-plugin/marketplace.json || bad "$name missing from .claude-plugin/marketplace.json"
  grep -q -- "/$name" README.md                   || bad "/$name missing from the README command list"
done

# 6. Every Kind the state template declares has a review lens (a "### <kind>" section) in review-panel.md.
#    The template's Kind comment is the single source of the Kind list.
tmpl="skills/aims-guide/assets/state-template.md"
lens="skills/aims-guide/references/review-panel.md"
kind_line="$(grep -m1 -oE '(design \| implementation \| add-feature[^>]*)' "$tmpl" 2>/dev/null | head -1)"
if [ -z "$kind_line" ]; then
  bad "could not find the Kind list in $tmpl"
else
  # split on '|' and the em-dash; take the bare kind words
  echo "$kind_line" | sed 's/—.*//' | tr '|' '\n' | while read -r k; do
    k="$(echo "$k" | tr -d '[:space:]')"
    [ -z "$k" ] && continue
    grep -qiE "^### ${k}\b" "$lens" || echo "MISSINGLENS $k"
  done > /tmp/aims_coh_lens
  while read -r m; do [ -n "$m" ] && bad "Kind '${m#MISSINGLENS }' has no lens in review-panel.md"; done < /tmp/aims_coh_lens
  rm -f /tmp/aims_coh_lens
fi

if [ "$fail" -eq 0 ]; then echo "[PASS] shipped surfaces are coherent"; else echo "[FAIL] $fail coherence problem(s)"; exit 1; fi
