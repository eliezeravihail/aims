---
kind: code
title: "The ADR convention and its shipped templates (`templates/adr-*.tmpl`,"
created: 2026-07-15
updated: 2026-07-29
code_globs: ["templates/decision.md.tmpl"]
tags: [discipline]
---

## Purpose

The ADR convention and its shipped template (`templates/decision.md.tmpl`,
seeded into targets by `/install-on`). ADRs are Capsa decision records in
`.capsa/decisions/NNNN-slug.md`; they are append-only — a superseded
decision gets a new record with `superseded_by:` / `supersedes:` pointers,
never an in-place edit.

## Invariants & gotchas

- Past decision bodies are never edited; only the `status:`/`superseded_by:`
  frontmatter may be updated when superseded.
- ADRs are proposed automatically during plan close-out per a
  confidence rule (create on clear architectural commitment; skip on
  bug/refactor/doc/test/mechanical; ask when borderline). Manual
  creation stays supported: write `.capsa/decisions/NNNN-slug.md` with
  `status: proposed` (no index to maintain — the validator lists them).

## Pointers

- ADR-0001 — the foundational append-only decision.
- ADR-0010 — removed the `/adr` command; auto-proposal at close-out.
- decision 0031 — aims adopts the Capsa capsule format.
- templates/decision.md.tmpl — the shipped Capsa decision scaffold.

## Deltas

- 2026-05-27: `/adr` command removed; ADR creation folded into plan
  close-out — ADR-0010.
- 2026-07-29: ADRs became Capsa decision records in `.capsa/decisions/`;
  the shipped scaffold is `templates/decision.md.tmpl` (the `adr-*.tmpl`
  set was removed) and there is no README index — f62ef11.
