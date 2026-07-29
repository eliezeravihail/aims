---
kind: code
title: "SessionStart hook — informational only, never blocks. Surfaces:"
created: 2026-07-15
updated: null
code_globs: ["templates/hooks/session-start.sh", ".claude/hooks/session-start.sh"]
tags: [hooks]
---

## Purpose

SessionStart hook — informational only, never blocks. Surfaces:
in-progress plans; orphan draft plans without an active lock
(ADR-0015); recently-touched ADRs; the memory tree's top-level
README.md capped at 2 KB (ADR-0007), framed as repository data
(ADR-0025); a one-line memory pipeline health summary; and the
standing project-conventions block (planning-as-behavior per ADR-0022,
reply-format `===[aims: <msg>]===` per ADR-0021).

## Invariants & gotchas

- Must `exit 0` even on internal failure — SessionStart must not gate
  the session.
- Plan-state detection is **header-scoped** via `plans_with_status`
  (first 5 lines); grep fallback when `_lib.sh` is absent.
- Lock/draft states are mutually exclusive in steady state: lock +
  in-progress = active; lock + draft = awaiting approval; lock +
  neither = orphaned lock (auto-cleared); no lock + draft = orphan
  draft (warned, with recovery hint).
- The planning-lock line is advisory-only wording — post-ADR-0020 the
  lock blocks nothing.
- Recent-ADR list filters out only `superseded`/`deprecated`;
  manually-set `rejected` ADRs would still surface.

## Pointers

- ADR-0021 — the reply-format marker the conventions block surfaces.
- ADR-0022 — planning-as-behavior wording in the conventions block.
- ADR-0025 — the README injection's data-framing fence.
- templates/hooks/exit-plan-mode.sh — creates the drafts whose orphans
  this hook warns about.

## Deltas

- 2026-06-11: stale "Edit/Write blocked" lock line replaced with the
  factually-correct advisory wording (L3) — 91fe2bd.
- 2026-07-15: all four plan-state greps switched to header-scoped
  `plans_with_status` — docs/plans/2026-07-15-memory-subsystem-diet.md.
