---
node: discipline/plan
kind: module
code:
  - templates/commands/plan.md
  - .claude/commands/plan.md
commits: []
sessions: []
parents: []
children: []
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

## Design rationale

## Invariants & gotchas

## Known issues


## Pointers

## Open questions
