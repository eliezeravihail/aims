---
node: hooks/session-start
kind: module
code:
  - templates/hooks/session-start.sh
  - .claude/hooks/session-start.sh
commits: []
sessions:
  - docs/plans/memory-tree-system.md
parents: []
children: []
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

## Design rationale

## Invariants & gotchas

## Known issues


## Pointers

## Open questions
