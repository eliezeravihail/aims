---
node: discipline/done
kind: module
code:
  - templates/commands/done.md
  - .claude/commands/done.md
commits: []
sessions:
  - docs/plans/memory-tree-system.md
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

## Logical rules & invariants

- Do NOT close a plan with failing verification. Surface the failures and stop; let the user fix them first.
- Do NOT edit any past ADR body. Closing a plan can create new ADRs; it never edits old ones.
- If `.claude/.planning-lock` still exists at close time, remove it as cleanup.
- Step 7 (memory consolidation) must use `--force` to bypass the Stop hook's throttle.

## Editing considerations

- The final report format must always include: plan path, verification result count (N pass / M fail), ADRs created, CLAUDE.md change status, and memory tree status.
- The verification commands come from the plan's `## Verification` section — run them literally, do not improvise alternatives.

## Deliberations & history

## Open questions
