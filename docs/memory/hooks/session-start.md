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
  - hooks/exit-plan-mode
  - discipline/plan
claude_md_refs:
  - "Hooks"
  - "Plugin-specific notes (not from template)"
external_refs:
  - { path: docs/adr/0004-router-via-hook-injected-context.md, kind: adr, why: this hook is the canonical 'context-injection at session start' channel }
  - { path: docs/adr/0007-tree-based-memory-with-auto-maintenance.md, kind: adr, why: surfaces docs/memory/README.md (the tree's tag list) up to 2KB }
owners:
  - ema
dirty: true
last_touched: 2026-06-02T14:24:04Z
last_consolidated: 2026-05-31T14:24:04Z
---

## Purpose

SessionStart hook — informational only, never blocks. Surfaces:
in-progress plans; **orphan draft plans** without an active lock
(ADR-0015); recently-touched ADRs; stale-planning-lock warnings; the
memory tree's top-level README.md (ADR-0007); and a one-line memory
pipeline health summary (ADR-0008).

## Design rationale

- The orphan-draft warning closes the recovery hole opened by writing
  the plan draft to disk **before** the approval gate (ADR-0015 Phase 2).
  A power-cut or context compaction between Phase 2 and Phase 3 leaves
  a `Status: draft` file on disk without `.claude/.planning-lock`; the
  warning surfaces that on the next session so the user can `touch` the
  lock to resume or `rm` the draft to abandon.
- Memory tree README is capped at 2 KB to keep prompt injection light;
  the trail-off message tells the model how to read more.

## Invariants & gotchas

- Must `exit 0` even on internal failure — SessionStart hooks should
  not gate the session.
- Stale-lock vs orphan-draft are mutually exclusive in steady state:
  lock + in-progress plan = active; lock + no in-progress = stale; no
  lock + draft = orphan; no lock + no draft = healthy.

## Known issues

- Recent-ADR list filters out `superseded` and `deprecated` only;
  manually-set `rejected` ADRs would still surface.

## Pointers

- `templates/hooks/session-start.sh` — single source of truth.
- `templates/hooks/exit-plan-mode.sh` — the bridge that creates the
  drafts whose orphans this hook warns about.

## Open questions

None.
