---
kind: code
title: "SessionStart hook — informational only, never blocks. Surfaces:"
created: 2026-07-15
updated: 2026-07-29
code_globs: ["templates/hooks/session-start.sh", ".claude/hooks/session-start.sh"]
tags: [hooks]
---

## Purpose

SessionStart hook — informational only, never blocks. Surfaces:
in_progress plans from `.capsa/plans/`; orphan draft plans without an
active lock (ADR-0015); recently-touched decisions from
`.capsa/decisions/` (title/status from frontmatter); the capsule's
`.capsa/charter.md` for orientation, capped at 2 KB and framed as
repository data (ADR-0025); a one-line capsule-health summary; and the
standing project-conventions block (planning-as-behavior per ADR-0022,
reply-format `===[aims: <msg>]===` per ADR-0021).

## Invariants & gotchas

- Must `exit 0` even on internal failure — SessionStart must not gate
  the session.
- Plan-state detection reads the Capsa plan frontmatter `status:` via
  `plans_with_status`; grep fallback when `_lib.sh` is absent.
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
  `plans_with_status` — plan 0017 (memory-subsystem-diet).
- 2026-07-29: surfaces `.capsa/plans` + `.capsa/decisions` + the
  charter (replacing the removed memory-tree README); reads Capsa
  frontmatter `status:` — f62ef11 (decision 0031).
