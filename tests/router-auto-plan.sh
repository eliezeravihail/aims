#!/usr/bin/env bash
# Smoke test for the UserPromptSubmit convention-note gate
# (templates/hooks/prompt-submit.sh).
#
# Post-ADR-0029 the hook has NO intent classifier: a task-shaped prompt
# (length >= 30 chars, no ``` fence, not a trailing-`?` question) gets the
# FACTUAL planning-convention note. It NEVER creates a .planning-lock
# (ADR-0020). Slash-commands / short prompts / questions / code-pastes get
# nothing.

set -eu
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { printf '[SKIP] jq missing\n'; exit 0; }
cd "$TMP"

HOOK="$ROOT/templates/hooks/prompt-submit.sh"
note_has() { printf '%s' "$1" | jq -r '.hookSpecificOutput.additionalContext // empty' | grep -q "$2"; }

# Case 1: task-shaped English prompt → factual note, NO lock.
rm -rf .claude
out=$(printf '{"prompt":"the parser crashes on empty input, please fix"}' | bash "$HOOK" 2>/dev/null)
[ ! -f .claude/.planning-lock ] || fail "case 1: gate must NOT create a lock"
note_has "$out" 'Project convention' || fail "case 1: expected a factual planning note"
note_has "$out" 'nothing is blocked'  || fail "case 1: note should state nothing is blocked"
pass "task-shaped prompt → factual note, no lock"

# Case 2: trailing-? question → no note, no lock (any length).
rm -rf .claude
out=$(printf '{"prompt":"how does the marker hook decide which node to flag?"}' | bash "$HOOK" 2>/dev/null)
[ ! -f .claude/.planning-lock ] || fail "case 2: no lock for question"
if note_has "$out" 'Project convention'; then fail "case 2: question should get no planning note"; fi
pass "trailing-? question → no note, no lock"

# Case 3: slash-prefixed prompt → suppressed (no output, no lock).
rm -rf .claude
out=$(printf '{"prompt":"/plan something"}' | bash "$HOOK" 2>/dev/null)
[ ! -f .claude/.planning-lock ] || fail "case 3: no lock for slash command"
[ -z "$out" ] || fail "case 3: slash-prefixed prompt should produce no output"
pass "gate suppresses on slash-command prompts"

# Case 4: short prompt (<30 chars) → no note.
rm -rf .claude
out=$(printf '{"prompt":"fix the login typo"}' | bash "$HOOK" 2>/dev/null)
[ ! -f .claude/.planning-lock ] || fail "case 4: short prompt must not lock"
if note_has "$out" 'Project convention'; then fail "case 4: short prompt should get no planning note"; fi
pass "short prompt → no note"

# Case 5: code-paste prompt → no note, no lock.
rm -rf .claude
out=$(printf '%s' '{"prompt":"```python\nprint(1)\n```"}' | bash "$HOOK" 2>/dev/null)
[ ! -f .claude/.planning-lock ] || fail "case 5: code-paste must not lock"
if note_has "$out" 'Project convention'; then fail "case 5: code-paste should get no planning note"; fi
pass "gate skips code-paste prompts"

# Case 6: short non-ASCII prompt → no note (byte-vs-char length must not
# clear the 30-char gate). "How much does this add?" in Hebrew is ~22 chars
# but 42 bytes; under a POSIX locale a byte count would falsely pass it.
rm -rf .claude
out=$(printf '%s' '{"prompt":"כמו עלות זה מוסיף לשיחה"}' | bash "$HOOK" 2>/dev/null)
[ ! -f .claude/.planning-lock ] || fail "case 6: short non-ASCII prompt must not lock"
if note_has "$out" 'Project convention'; then fail "case 6: short non-ASCII prompt should get no planning note"; fi
pass "short non-ASCII prompt → no note (char-counted, not byte-counted)"

# Case 7: task-shaped Hebrew prompt (>=30 chars, no ?) → note. The old
# English-keyword classifier could never fire on this; the shape gate is
# language-neutral by construction.
rm -rf .claude
out=$(printf '%s' '{"prompt":"תוסיף מנגנון קאש לשכבת האחסון וכתוב לזה טסטים"}' | bash "$HOOK" 2>/dev/null)
[ ! -f .claude/.planning-lock ] || fail "case 7: Hebrew task must not lock"
note_has "$out" 'Project convention' || fail "case 7: task-shaped Hebrew prompt should get the note"
pass "task-shaped Hebrew prompt → note (language-neutral gate)"

# Case 8: plan-state detection reads the Capsa frontmatter `status:` field,
# not the body. A plan whose frontmatter says completed but whose BODY quotes
# "status: in_progress" (e.g. in a code block) must NOT count as an active
# plan — so a task-shaped prompt still gets the note. Requires _lib.sh in the
# sandbox so plans_with_status parses frontmatter (the grep fallback is
# frontmatter-anchored too, but _lib is the real path).
rm -rf .claude .capsa
mkdir -p .capsa/plans .claude/memory
cp "$ROOT/templates/memory/_lib.sh" .claude/memory/_lib.sh
cat > .capsa/plans/0001-decoy.md <<'EOF'
---
id: 1
title: "decoy"
kind: initiative
status: completed
opened: 2026-01-01
completed: 2026-01-01
---

## Outcome
Done. The frontmatter status is completed; this body line —
```
status: in_progress
```
must no longer be confused for an active plan.
EOF
# With frontmatter-scoped parsing there is NO active plan, so nothing may
# swallow a task-shaped prompt because of the decoy.
out=$(printf '{"prompt":"add a cache layer to the storage adapter now"}' | bash "$HOOK" 2>/dev/null)
note_has "$out" 'Project convention' || fail "case 8: decoy body status must not suppress the note"
pass "frontmatter-scoped status — decoy 'in_progress' in body ignored"

printf '\nAll gate (inform-never-lock) tests passed.\n'
