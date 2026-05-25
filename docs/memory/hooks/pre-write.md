---
node: hooks/pre-write
kind: module
code:
  - templates/hooks/pre-write.sh
  - .claude/hooks/pre-write.sh
commits: []
sessions: []
related:
  - discipline/plan
claude_md_refs:
  - "Hooks"
external_refs:
  - { path: docs/adr/0003-hooks-default-nudge-lock-always-blocks.md, kind: adr, why: default mode = nudge; planning-lock always hard-blocks regardless of mode }
owners:
  - ema
dirty: false
last_touched: 2026-05-25T11:46:53Z
last_consolidated: 2026-05-25T11:46:53Z
---

## Purpose

PreToolUse hook on Edit | Write | MultiEdit | NotebookEdit. Two responsibilities: (1) hard-block while `.claude/.planning-lock` exists (planning is read-only); (2) in `block` mode, soft-block writes to recognised source paths without an in-progress plan. Exit 2 surfaces stderr to the model and the user.

## Logical rules & invariants

## Editing considerations

## Deliberations & history

## Open questions
