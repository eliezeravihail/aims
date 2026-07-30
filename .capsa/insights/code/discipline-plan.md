---
kind: code
title: "The `/plan` slash command. Per ADR-0022, planning is a project"
created: 2026-07-15
updated: 2026-07-29
code_globs: ["templates/commands/plan.md", ".claude/commands/plan.md"]
tags: [discipline]
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
  (ADR / Insights / Charter / Tests / TODO), each with an explicit
  verdict — `NONE — reason` is written, never omitted.
- Phase 2 writes a conforming Capsa plan to `.capsa/plans/NNNN-slug.md`
  (frontmatter `id`/`title`/`kind`/`status: draft`/`opened`); approval
  flips `status:` to `in_progress`; close-out sets `completed`.
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
- 2026-07-29: `/plan` writes Capsa plan records to `.capsa/plans/`
  (YAML `status:` frontmatter, id auto-incremented) and close-out
  writes decisions to `.capsa/decisions/` + consolidates insights;
  checklist Nodes→Insights, CLAUDE.md→Charter — f62ef11 (decision 0031).
