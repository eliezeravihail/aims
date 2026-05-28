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
last_touched: 2026-05-28T15:10:11Z
last_consolidated: 2026-05-28T15:10:11Z
---

## Purpose

Documents the /plan slash command — the entry point to non-trivial work in aims. /plan creates `.claude/.planning-lock`, runs read-only discovery, and writes a durable plan under `docs/plans/` before any Edit/Write is allowed. The planning-lock convention is enforced by the `pre-write.sh` hook (see hooks/pre-write).

## Design rationale

Plan format is **signal-only**: a plan is read for its executive summary
(`## TL;DR`), its concrete code/diffs (`## Changes` — one subsection per
file, the real snippet IS the spec), and its `## ADRs / TODO`. Prose
narration, multi-option essays, and phase-by-phase storytelling are
explicitly cut. No hard line cap — length follows the code detail, not
padding.

## Invariants & gotchas

- `## Changes` carries actual code, not descriptions of code; its ordered
  subsections double as the implementation steps and as the close-out
  verification checklist (Phase 4 walks them).
- No `## Options considered` section — fold a one-line "chose X over Y" into
  the TL;DR instead.

## Known issues


## Pointers

## Open questions
