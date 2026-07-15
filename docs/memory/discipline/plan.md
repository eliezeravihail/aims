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
  - { path: docs/adr/0003-hooks-default-nudge-lock-always-blocks.md, kind: adr, why: planning-lock is what made /plan read-only (historical; superseded by 0020) }
  - { path: docs/adr/0002-single-dispatch-over-multi-agent.md, kind: adr, why: /plan runs on Opus per the single-dispatch model policy }
  - { path: docs/adr/0013-plan-summary-language-and-open-design-questions.md, kind: adr, why: language toggle + Open design questions section }
  - { path: docs/adr/0015-auto-plan-and-draft-on-disk.md, kind: adr, why: draft-on-disk before approval + auto-engage from prompt-submit }
owners:
  - ema
dirty: false
last_touched: 2026-07-15T09:17:01Z
last_consolidated: 2026-07-15T09:17:01Z
---

## Purpose

The `/plan` slash command. Per ADR-0022, planning is a project
**behavior** — the `prompt-submit` injection describes the flow
factually so the assistant runs it inline for any task-shaped prompt.
`/plan` is an **optional Opus shortcut**: it dispatches Phase 1-2
(read-only discovery + draft write) to a `general-purpose` Agent
subagent with `model: "opus"`; the main session resumes for Phase 3
(approval), Phase 4 (implementation), Phase 5 (close-out). The main
session model is never switched.

## Invariants & gotchas

- `## Changes` carries actual code, not descriptions of code; its
  ordered subsections double as the implementation steps and the
  close-out verification checklist (Phase 5 walks them).
- `## Close-out checklist` is mandatory and every line always present
  (ADR / Nodes / CLAUDE.md / Tests / TODO), each with an explicit
  verdict — `NONE — reason` is written, never omitted.
- Phase 2 writes the draft with the **Write tool**; no hook blocks it
  (hooks inform, never block — ADR-0020). The draft-on-disk survives
  interruption; SessionStart surfaces orphans.
- The TL;DR heading/body language comes from `.claude/aims-summary-lang`
  (`he` → `## תקציר מנהלים`; unknown → `en`) — ADR-0013.

## Pointers

- ADR-0022 — planning-as-behavior; `/plan` dispatches an Opus subagent.
- ADR-0015 — draft-on-disk + auto-engage (preceding design).
- ADR-0013 — summary language + Open design questions section.
- templates/commands/plan.md — single source of truth.

## Deltas

- 2026-06-02: planning became a behavior; `/plan` reduced to an
  optional Opus-subagent dispatch — ADR-0022.
