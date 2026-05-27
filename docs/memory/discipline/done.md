---
node: discipline/done
kind: module
code:
  - templates/commands/done.md
  - .claude/commands/done.md
commits: []
sessions:
  - docs/plans/memory-tree-system.md
parents: []
children: []
related:
  - discipline/plan
  - memory/phase-b-consolidation
claude_md_refs:
  - "Workflow"
  - "Models policy"
external_refs:
  - { path: docs/adr/0007-tree-based-memory-with-auto-maintenance.md, kind: adr, why: /done step 7 forces memory consolidation via --force }
owners:
  - ema
dirty: false
last_touched: 2026-05-25T11:46:53Z
last_consolidated: 2026-05-25T11:46:53Z
---

## Purpose

Documents the /done slash command — closes an active plan, verifies each step, runs verification commands, prompts for ADRs, forces a memory consolidation pass (step 7, bypassing the throttle), and offers to link new CLAUDE.md sections from the memory tree. Final report includes the memory-tree status.

## Design rationale

## Invariants & gotchas

## Known issues


## Pointers

## Open questions
