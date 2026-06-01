---
node: hooks/session-start
kind: module
code:
  - templates/hooks/session-start.sh
  - .claude/hooks/session-start.sh
commits: []
sessions:
  - docs/plans/memory-tree-system.md
related:
  - memory/phase-b-consolidation
claude_md_refs:
  - "Hooks"
  - "Plugin-specific notes (not from template)"
external_refs:
  - { path: docs/adr/0004-router-via-hook-injected-context.md, kind: adr, why: this hook is the canonical 'context-injection at session start' channel }
  - { path: docs/adr/0007-tree-based-memory-with-auto-maintenance.md, kind: adr, why: surfaces docs/memory/README.md (the tree's tag list) up to 2KB }
owners:
  - ema
dirty: false
last_touched: 2026-05-25T11:46:53Z
last_consolidated: 2026-05-25T11:46:53Z
---

## Purpose

SessionStart hook — informational only, never blocks. Surfaces in-progress plans, recently-touched ADRs, stale-planning-lock warnings, and (per ADR-0007) the memory tree's top-level README.md so the model knows the tag list to navigate from.

## Logical rules & invariants

- Informational only — always exits 0. Never modifies any file.
- Memory README injection is capped at 2048 bytes to keep context injection light.
- Stale-lock warning fires only when the lock exists but no in-progress plan exists. If a plan is active, the lock is expected.

## Editing considerations

- Keep each surface area (plans, ADRs, lock, memory README) as independent `if` blocks. A missing directory should not prevent the other sections from printing.
- The `head -c 2048` cap on the memory README is intentional — do not raise it without profiling context-window impact.

## Deliberations & history

## Open questions
