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

- Exit 2 = block (stderr is surfaced to the model and the user). Exit 0 = allow.
- The planning-lock check always runs regardless of `aims-mode`. The lock always blocks.
- The source-path soft-block (only in `block` mode) applies to paths matching `src/*|lib/*|app/*|server/*|client/*|packages/*`.
- Test files (`*_test.*|*.test.*|*.spec.*|*/tests/*|*/__tests__/*`) and docs (`*.md|*.txt`) are exempt from the source-path check.

## Editing considerations

- When adding new source-path patterns, update BOTH the `is_source_path` case statement AND the exemption case in the same edit. They must stay in sync.
- The hook reads tool_input JSON from stdin via `jq` (preferred) or a sed/grep fallback. Both branches must remain equivalent — test both when changing path extraction logic.

## Deliberations & history

## Open questions
