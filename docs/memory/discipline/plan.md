---
node: discipline/plan
kind: module
code:
  - templates/commands/plan.md
  - .claude/commands/plan.md
commits: []
sessions: []
related:
  - hooks/pre-write
  - discipline/done
claude_md_refs:
  - "Workflow"
  - "Models policy"
external_refs:
  - { path: docs/adr/0003-hooks-default-nudge-lock-always-blocks.md, kind: adr, why: planning-lock is what makes /plan actually read-only }
  - { path: docs/adr/0002-single-dispatch-over-multi-agent.md, kind: adr, why: /plan runs on Opus per the single-dispatch model policy }
owners:
  - ema
dirty: false
last_touched: 2026-05-25T11:46:53Z
last_consolidated: 2026-05-25T11:46:53Z
---

## Purpose

Documents the /plan slash command — the entry point to non-trivial work in aims. /plan creates `.claude/.planning-lock`, runs read-only discovery, and writes a durable plan under `docs/plans/` before any Edit/Write is allowed. The planning-lock convention is enforced by the `pre-write.sh` hook (see hooks/pre-write).

## Logical rules & invariants

- The planning lock (`.claude/.planning-lock`) MUST be created as the very first step — before any Read, Glob, or Bash call.
- While the lock exists, `pre-write.sh` hard-blocks Edit/Write/MultiEdit/NotebookEdit regardless of `aims-mode`.
- The lock MUST be removed after ExitPlanMode approval or on user abort. A dangling lock is always a bug.
- The plan file is written to `docs/plans/YYYY-MM-DD-<slug>.md` only after ExitPlanMode approval, never before.

## Editing considerations

- Do not modify `/plan` to skip or delay lock creation — the lock is the contract with `pre-write.sh`.
- If the user rejects ExitPlanMode, do NOT remove the lock. Iterate on the plan inside the locked state.
- The slug is the first ≤6 words of `$ARGUMENTS`, lowercased and hyphenated. Keep it stable once the file is written.

## Deliberations & history

## Open questions
