# ADR-0017: `pre-write` carves out plan drafts during the planning lock
Status: proposed
Date: 2026-05-31
Supersedes: —
Superseded by: —

## Context

ADR-0003 introduced `.claude/.planning-lock` as a hard, mode-independent
gate: while the lock exists, `pre-write` blocks every Edit/Write/MultiEdit.
ADR-0015 then made the `prompt-submit` router auto-create that lock on any
actionable intent and instruct the model to **draft a plan file to disk**
before asking the user to approve. Those two designs collide: the auto-engage
flow tells the model to write `docs/plans/<UTC-date>-<slug>.md`, but the
lock makes every Write fail with `exit 2`.

The previous workaround was "write the draft via a Bash heredoc, since the
hook only matches Edit/Write/MultiEdit/NotebookEdit." Real sessions showed
this is fragile in two ways:

1. The Bash tool's JSON encoding wraps the command in single quotes; any
   apostrophe in the plan content breaks the wrapper with
   `Exit code 2: unexpected EOF while looking for matching '`.
2. When heredoc fails, the model falls back to `Write` → blocked by
   `pre-write` → cascade deadlock with no escape path inside the lock.

The auto-engage flow's whole purpose is to write a draft. Blocking the
draft write is a contradiction.

## Decision

`pre-write` carves out `docs/plans/*.md` (and `docs/plans/*.md.tmp`,
matching the configurable `PLAN_DIR` env override) from the planning-lock
gate. Writes anywhere else under the lock continue to fail with the same
`exit 2` and message; only the draft file the model was just instructed to
write is allowed. The auto-engage instructions in `prompt-submit.sh` are
updated to recommend the `Write` tool directly, dropping the fragile
heredoc workaround.

This preserves the lock's real purpose (block production edits during
read-only planning) while removing the contradiction with ADR-0015.

## Consequences

- ✅ `/plan` auto-engage actually works end-to-end. The model writes the
  draft with `Write`, prints the approval prompt, and the user approves —
  no Bash-quoting failure mode.
- ✅ The lock continues to block every production source edit. The carve-out
  is path-scoped to `docs/plans/`, which is documentation-only.
- ✅ Manual `/plan` flows (lock set, draft written directly) get the same
  affordance — consistent behavior across auto-engage and manual entry.
- ⚠️ A misbehaving session could write multiple draft files under
  `docs/plans/` during the lock. Acceptable: the user reviews drafts before
  approval, and stale drafts are visible in source control.
- 🔒 Rules out blanket "all writes blocked under the lock" semantics — the
  lock is now scoped to "production edits blocked; plan artifact allowed."

## Alternatives considered

- **Keep the heredoc workaround.** Rejected: documented to fail on common
  content (apostrophes in English/Hebrew prose) and offers no fallback.
- **Have `prompt-submit` not create the lock at all; let `/plan` Phase 1
  create it after the model finishes exploration.** Rejected: defeats the
  purpose of auto-engage (the Edit/Write block must be in place from the
  *next* turn, before the model can sneak in a non-plan edit).
- **Detect heredoc in Bash payloads and route them through.** Rejected:
  bash-content parsing inside a hook is brittle and doesn't address the
  underlying contradiction.

## Verification

- `printf '{"tool_input":{"file_path":"docs/plans/<date>-<slug>.md"}}' | bash .claude/hooks/pre-write.sh`
  with the lock present → `exit 0`.
- Same payload but `file_path: templates/hooks/foo.sh` → `exit 2`.
- Without the lock, both → `exit 0` (unchanged).
- `templates/hooks/prompt-submit.sh` Phase 2 text reads "using the Write
  tool" (no `heredoc` mention).
- All hook copies remain byte-identical
  (`md5sum templates/hooks/{pre-write,prompt-submit}.sh .claude/hooks/{pre-write,prompt-submit}.sh`).
