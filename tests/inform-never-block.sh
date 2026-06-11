#!/usr/bin/env bash
# Behavior guard for the aims hooks (CLAUDE.md §4.2), rewritten for the
# 2026-06-01 overhaul: HOOKS INFORM, THEY NEVER BLOCK.
#
# Invariants asserted:
#   A. pre-write.sh NEVER exits non-zero (no path, with/without a plan) and
#      injects a FACTUAL planning note (additionalContext) once per session on a
#      source edit with no in-progress plan; nothing for docs/tests/.claude.
#   B. prompt-submit.sh NEVER creates a .planning-lock; injects a factual note
#      for actionable intents; nothing for questions.
#   C. post-edit-marker.sh NEVER blocks; injects a factual node note + stamps an
#      advisory marker; same-session refreshes silently; a fresh other-session
#      marker is reported as concurrent (not clobbered); a stale one is taken over.
#   D. session-start.sh never blocks; prints the factual conventions; still
#      auto-clears an orphaned planning-lock left by an older session.
#
# jq-free: runs in any environment (the other tests/ need jq/python3).
# Run from anywhere:  bash tests/inform-never-block.sh
# Exercises the dogfood .claude/hooks (kept identical to templates/hooks).

set -u
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
H="$ROOT/.claude/hooks"
trap 'rm -f "$ROOT/.claude/.planning-lock" "$ROOT"/.claude/.aims-plan-note-* 2>/dev/null || true' EXIT
pass=0; fail=0
ok(){ if [ "$1" = "$2" ]; then echo "  PASS: $3"; pass=$((pass+1)); else echo "  FAIL: $3 (got '$1' want '$2')"; fail=$((fail+1)); fi; }
has(){ case "$1" in *"$2"*) echo "  PASS: $3"; pass=$((pass+1));; *) echo "  FAIL: $3 (missing '$2')"; fail=$((fail+1));; esac; }
no(){ case "$1" in *"$2"*) echo "  FAIL: $3 (unexpected '$2')"; fail=$((fail+1));; *) echo "  PASS: $3"; pass=$((pass+1));; esac; }
LOCK=.claude/.planning-lock

echo "### A. pre-write.sh — never blocks; factual note once per session ###"
PD=$(mktemp -d)   # empty plan dir = no in-progress plan
rm -f "$LOCK" .claude/.aims-plan-note-* 2>/dev/null
pw(){ printf '%s' "$1" | AIMS_PLAN_DIR="$PD" bash "$H/pre-write.sh" 2>/dev/null; }
out=$(pw '{"session_id":"s1","tool_input":{"file_path":"C:/x/y/src/app/core.py"}}'); rc=$?
ok "$rc" "0" "source edit returns 0 (never blocks)"
has "$out" "Project convention" "source edit injects factual planning note"
has "$out" '"permissionDecision":"allow"' "decision is allow"
out2=$(pw '{"session_id":"s1","tool_input":{"file_path":"C:/x/y/src/app/other.py"}}'); ok "$?" "0" "2nd source edit returns 0"
ok "$out2" "" "2nd edit same session is silent (once-per-session)"
od=$(pw '{"session_id":"s2","tool_input":{"file_path":"C:/x/y/docs/plans/p.md"}}'); ok "$?" "0" "docs path returns 0"
ok "$od" "" "docs path injects nothing"
ot=$(pw '{"session_id":"s2","tool_input":{"file_path":"C:/x/y/tests/test_a.py"}}'); ok "$ot" "" "tests path injects nothing"
ok "$(ls "$LOCK" 2>/dev/null && echo y || echo n)" "n" "pre-write created NO lock"
rm -f .claude/.aims-plan-note-* 2>/dev/null; rm -rf "$PD"

echo "### B. prompt-submit.sh — never locks; factual note for actionable ###"
PD=$(mktemp -d)
# M1 fix: wrap raw prose as a UserPromptSubmit JSON payload so jq parses it.
# A prior version piped bare text, which silently broke section B when jq was
# installed (jq -r '.prompt' would error → empty prompt → hook short-circuited).
ps(){
  rm -f "$LOCK"
  local payload
  if command -v python3 >/dev/null 2>&1; then
    payload=$(printf '%s' "$1" \
      | python3 -c 'import json,sys; print(json.dumps({"prompt": sys.stdin.read(), "session_id":"t"}))')
  else
    local esc; esc=$(printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g')
    payload=$(printf '{"prompt":"%s","session_id":"t"}' "$esc")
  fi
  printf '%s' "$payload" | AIMS_PLAN_DIR="$PD" bash "$H/prompt-submit.sh" 2>/dev/null
}
lockstate(){ [ -f "$LOCK" ] && echo y || echo n; }
o=$(ps 'please fix the crash that throws an exception'); ok "$(lockstate)" "n" "English bug: NO lock"
has "$o" "Project convention" "English bug: factual note injected"
o=$(ps 'תבצע אופטימיזציה כללית על כל המערכת שלנו בבקשה רבה'); ok "$(lockstate)" "n" "Hebrew prose: NO lock"
o=$(ps 'מה אתה מציע לגבי הבאג הזה ואיך לתקן אותו בבקשה'); ok "$(lockstate)" "n" "Hebrew question: NO lock"
no "$o" "Project convention" "Hebrew question: no planning note"
rm -f "$LOCK"; rm -rf "$PD"

echo "### C. post-edit-marker.sh — node note + advisory marker; never blocks ###"
MD=$(mktemp -d)
cat > "$MD/tnode.md" <<EOF
---
node: test/tnode
kind: module
code:
  - foo/bar.py
dirty: false
last_touched: 2026-01-01T00:00:00Z
last_consolidated: 2026-01-01T00:00:00Z
---
body
EOF
pem(){ printf '%s' "$1" | AIMS_MEMORY_DIR="$MD" bash "$H/post-edit-marker.sh" 2>/dev/null; }
P="$PWD/foo/bar.py"
o=$(pem "{\"session_id\":\"A\",\"tool_input\":{\"file_path\":\"$P\"}}"); ok "$?" "0" "edit returns 0 (never blocks)"
has "$o" "test/tnode" "injects the matching node name"
ok "$(head -n1 "$MD/tnode.marker" 2>/dev/null)" "A" "advisory marker stamped with session id"
o=$(pem "{\"session_id\":\"A\",\"tool_input\":{\"file_path\":\"$P\"}}")
no "$o" "is possible" "same session: no concurrent warning (silent refresh)"
# fresh OTHER-session marker -> concurrent, not clobbered ("is possible" is unique
# to the concurrent detail; the word "concurrent" also appears in the convention
# boilerplate of every note, so it is not a distinctive marker).
printf 'B\nfoo/bar.py\n' > "$MD/tnode.marker"
o=$(pem "{\"session_id\":\"A\",\"tool_input\":{\"file_path\":\"$P\"}}")
has "$o" "is possible" "fresh other-session marker -> concurrent warning"
ok "$(head -n1 "$MD/tnode.marker")" "B" "fresh peer marker NOT clobbered"
# stale OTHER-session marker -> taken over
printf 'B\nfoo/bar.py\n' > "$MD/tnode.marker"
o=$(AIMS_NODE_LOCK_STALE_SEC=0 pem "{\"session_id\":\"A\",\"tool_input\":{\"file_path\":\"$P\"}}")
has "$o" "taken over" "stale other-session marker -> taken over"
ok "$(head -n1 "$MD/tnode.marker")" "A" "stale marker overwritten by us"
# unrelated path -> no node note
o=$(pem "{\"session_id\":\"A\",\"tool_input\":{\"file_path\":\"$PWD/zzz/nope.py\"}}"); ok "$?" "0" "unrelated path returns 0"
no "$o" "test/tnode" "unrelated path: no node note"
rm -rf "$MD"

echo "### D. session-start.sh — never blocks; conventions; clears orphan lock ###"
EMPTY=$(mktemp -d)
rm -f "$LOCK"; touch "$LOCK"
o=$(AIMS_PLAN_DIR="$EMPTY" bash "$H/session-start.sh" 2>/dev/null); ok "$?" "0" "session-start returns 0"
has "$o" "Project conventions" "prints factual conventions"
ok "$([ -f "$LOCK" ] && echo y || echo n)" "n" "orphan lock auto-cleared"
rm -f "$LOCK"; rm -rf "$EMPTY"

echo
echo "RESULT: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
