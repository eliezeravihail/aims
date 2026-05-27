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
last_touched: 2026-05-27T18:40:53Z
last_consolidated: 2026-05-27T18:40:53Z
---

## Purpose

Documents the `/done` slash command — closes an active plan, verifies
each step, runs verification commands, prompts for ADRs, runs memory
consolidation in-band on nodes overlapping the plan's touched files,
and offers to link new CLAUDE.md sections from the memory tree. Final
report includes memory-tree status from `doctor.sh`.

## Design rationale

- Step 7 runs the consolidation in-band per ADR-0009: instead of
  exporting `AIMS_EXTRA_CONTEXT` and shelling out to a `--force`
  Stop hook that called Sonnet via curl, the closing model itself
  reads the prompt from `bash .claude/memory/consolidate.sh <node>`,
  layers in the plan/ADR text as bridge context, performs the Edit,
  and finishes with `mark.sh <node> consolidated`. One fewer hop,
  no API key.
- Inbox classification is symmetric: `classify-inbox.sh` emits the
  prompt; the closing model applies confident matches via Edit and
  asks via `AskUserQuestion` for the ambiguous ones.

## Invariants & gotchas

- `/done` MUST NOT close a plan with failing verification or
  unimplemented steps — it reports what's missing and stops.
- `/done` MUST NOT edit past ADRs; it can only create new ones.
- The plan file gains an `## Outcome` and `## Closing checks`
  section on close; `Status` flips to `completed`.

## Known issues

- fixed: step 7 used to skip silently when `ANTHROPIC_API_KEY` was
  absent, leaving the memory tree un-propagated; replaced with the
  in-band path (commit 0c0852f).

## Pointers

- ADR-0007 — memory tree the step propagates into.
- ADR-0009 — in-band mechanism step 7 now uses.
- `templates/commands/done.md` — the command itself.

## Open questions
