---
node: discipline/done
kind: topic
code: []
# (was: templates/commands/done.md, .claude/commands/done.md — both removed per ADR-0010)
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
last_touched: 2026-07-15T09:17:00Z
last_consolidated: 2026-07-15T09:17:00Z
---

## Purpose

Historical breadcrumb for the removed `/done` slash command (plan
close-out: verify steps, run verification, decide ADRs, consolidate
memory, mark completed). Its behavior lives on as `/plan` Phase 5,
run inline at the end of the implementation session.

## Invariants & gotchas

- The close-out invariants `/done` enforced still hold in Phase 5:
  never close a plan with failing verification or unimplemented steps;
  never edit past ADRs; the plan gains `## Outcome` + `## Closing
  checks` and `Status:` flips to `completed`.
- Consolidation at close-out is in-band (ADR-0009): the closing model
  reads `consolidate.sh <node>` output, Edits, then
  `mark.sh <node> consolidated`. No API key involved.

## Pointers

- ADR-0010 — removed `/done`; close-out embedded in `/plan`.
- ADR-0009 — the in-band mechanism close-out uses.
- ADR-0007 — the memory tree close-out propagates into.

## Deltas

- 2026-05-27: `/done` removed; close-out embedded in `/plan` Phase 5 —
  ADR-0010.
- 2026-05-27: step 7's `ANTHROPIC_API_KEY` curl path replaced with
  in-band consolidation — ADR-0009.
