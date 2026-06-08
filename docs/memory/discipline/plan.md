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
  - { path: docs/adr/0013-plan-summary-language-and-open-design-questions.md, kind: adr, why: language toggle + Open design questions section }
  - { path: docs/adr/0015-auto-plan-and-draft-on-disk.md, kind: adr, why: draft-on-disk before approval + auto-engage from prompt-submit }
owners:
  - ema
dirty: false
last_touched: 2026-05-31T14:25:01Z
last_consolidated: 2026-05-31T14:25:01Z
---

## Purpose

Documents the /plan slash command — the entry point to non-trivial work
in aims. /plan runs read-only discovery (by discipline, not a lock — see
ADR-0020), **materializes a `Status: draft` plan to disk** (Phase 2, via
the Write tool), then asks for approval. Approval flips the status to
`in-progress`; abort deletes the draft. No `.planning-lock` is created.

## Design rationale

- **Draft-on-disk before approval** (ADR-0015): the file IS the artifact
  to review, and survives session interruption mid-flow. SessionStart
  surfaces a draft-without-lock as an orphan that needs `touch` (resume)
  or `rm` (abandon).
- Plan format is **signal-only**: TL;DR + Changes (one subsection per
  file, real code IS the spec) + Open design questions + Close-out
  checklist. No phase-by-phase narration, no multi-option essays.
- Phase 1 is read-only by discipline (no lock); Phase 2 writes the draft
  with the Write tool; Phase 3 is the approval gate; Phase 4 = implement;
  Phase 5 = close-out.

## Requirements & invariants

- Requirements: none recorded beyond CLAUDE.md. Before editing, re-verify
  against CLAUDE.md and ask the user.

- `## Changes` carries actual code, not descriptions of code; its ordered
  subsections double as the implementation steps and as the close-out
  verification checklist (Phase 5 walks them).
- `## Close-out checklist` is **mandatory and every line always present**
  (ADR / Nodes / CLAUDE.md / Tests / TODO), each with an explicit verdict —
  `NONE — reason` is written, never omitted. Phase 5 resolves each line
  and the final report echoes them.
- Phase 2 writes the draft with the **Write tool** (docs/plans is always
  allowed; no hook blocks it). The router (prompt-submit) injects a factual
  planning-convention note for actionable prompts but never locks — the
  contract is uniform: hooks inform, never block (ADR-0020).

## Known issues


## Pointers

## Open questions
