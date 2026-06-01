# Plan: Auto-inject memory node body on relevant prompts
Status: completed
Started: 2026-05-31
Completed: 2026-05-31

## TL;DR
Extend `prompt-submit.sh` so any user prompt that mentions a path or filename
tracked by a memory node's `code:` glob auto-injects that node's body
(purpose / invariants / pointers / known issues) into the turn — alongside
the existing router + auto-engage `/plan` output, in one combined
`additionalContext`. Glob matching reuses ADR-0014 semantics: derive each
glob's literal prefix (cut at first `*`/`?`/`[`) and substring-test the
prompt, plus bare-basename word match for literal entries. Per-session
de-dup via `.claude/memory/.injected-<session_id>`; SIZE_CAP=8192; pure
bash, no LLM. No-op when `docs/memory/` is missing or the tree is inert.
A pure-question prompt with a file reference gets memory only (no lock,
no auto-engage). New ADR-0016 extending ADR-0007 + ADR-0015.

## Changes

### templates/hooks/prompt-submit.sh  (and identical .claude/hooks/prompt-submit.sh)
Add a memory-scan block after suppression and before intent classification;
make auto-engage text conditional on a non-question intent (locks only when
actionable); combine memory_text + router_text into one `additionalContext`.

The full file is the spec; key blocks:

```bash
# ── Memory-node auto-injection (ADR-0016) ───────────────────────────────
MEMORY_DIR="${AIMS_MEMORY_DIR:-docs/memory}"
SESSION_ID=$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null || true)
INJECTED_STATE=".claude/memory/.injected-${SESSION_ID:-default}"
SIZE_CAP=8192
NAME_MIN_LEN=5
LIT_MIN_LEN=4

# For each glob:
base="${glob%%:*}"                   # strip :line-range
lit="${base%%[\*\?\[]*}"             # literal prefix (ADR-0014-friendly)
if [ "${#lit}" -ge "$LIT_MIN_LEN" ]; then
  case "$prompt" in *"$lit"*) hit=1; break ;; esac
fi
if [ "$lit" = "$base" ]; then        # no glob chars → also basename word match
  name="${base##*/}"
  if [ "${#name}" -ge "$NAME_MIN_LEN" ]; then
    printf '%s' "$prompt" | grep -qwF "$name" && hit=1
  fi
fi
```

```bash
# Auto-engage only when intent is non-question (lock + router_text); memory
# emits independently.
if [ -n "$intent" ] && [ "$intent" != "question" ]; then
  mkdir -p .claude && touch .claude/.planning-lock
  router_text="..."   # unchanged auto-engage template
fi
combined="$memory_text${combined:+$'\n\n'}$router_text"
[ -z "$combined" ] && exit 0
```

### docs/adr/0016-prompt-memory-injection.md  (new, status proposed)
Records the new job, fnmatch-aligned matching rule, independence of lock and
memory, SIZE_CAP and de-dup state file. Extends ADR-0007 / ADR-0015 / ADR-0014.

### docs/memory/hooks/prompt-submit.md  (existing node — consolidate)
Body updated to describe the three-job hook (router + memory + suppression)
and pin the lock-independence invariant.

## Verification
- `bash -n templates/hooks/prompt-submit.sh && bash -n .claude/hooks/prompt-submit.sh` → clean.
- `md5sum` pair identical.
- Smoke 1 (question + file): emission has `[aims-memory]`, NO `[aims-router]`, NO lock.
- Smoke 2 (feature + file): emission has both banners; `.claude/.planning-lock` created.
- Smoke 3 (`/plan ...`): silent.

## Close-out checklist
- ADR: WROTE — 0016-prompt-memory-injection
- Nodes: UPDATE — docs/memory/hooks/prompt-submit.md
- CLAUDE.md: NONE — mechanics-level change
- Tests: N/A — manual smoke per Verification + bash -n
- TODO: NONE

## Risks / unknowns
- Literal-prefix heuristic: a node with `code: docs/*` would inject on any
  prompt mentioning `docs/`. `LIT_MIN_LEN=4` + `SIZE_CAP` bound the blast
  radius; per-session de-dup limits the cost to once per node per session.
- `session_id` field shape: if Claude Code's payload lacks `session_id`, the
  state file falls back to `.injected-default` (degrades to "once per cwd
  until pruned"). 7-day prune keeps it bounded.

## Outcome
Hook rewritten on top of master's auto-engage base (post-PR #31) to add a
deterministic memory-node injector. Three smoke tests green: question +
file → memory only; feature + file → memory + auto-engage + lock; slash →
silent. Recorded as ADR-0016. Consolidated `hooks/prompt-submit` node.

## Closing checks
- `bash -n` template + .claude hooks → clean.
- `md5sum` template ↔ .claude `prompt-submit.sh` identical.
- Smoke 1 (question + file): `additionalContext` contains `[aims-memory]`
  + `node: memory/helpers` body; NO `[aims-router]`; NO lock.
- Smoke 2 (feature + file): `additionalContext` contains BOTH banners;
  `.claude/.planning-lock` created.
- Smoke 3 (slash): silent.
- Resolved checklist:
  - ADR: WROTE — 0016-prompt-memory-injection
  - Nodes: UPDATE — docs/memory/hooks/prompt-submit.md
  - CLAUDE.md: NONE — mechanics-level change
  - Tests: N/A — manual smoke per Verification + bash -n
  - TODO: NONE
