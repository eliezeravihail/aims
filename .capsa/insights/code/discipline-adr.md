---
kind: code
title: "The ADR convention and its shipped templates (`templates/adr-*.tmpl`,"
created: 2026-07-15
updated: null
code_globs: ["templates/decision.md.tmpl"]
tags: [discipline]
---

## Purpose

The ADR convention and its shipped templates (`templates/adr-*.tmpl`,
seeded into targets by `/install-on`). ADRs are append-only — a
superseded decision gets a new ADR with a `Superseded by:` pointer,
never an in-place edit.

## Invariants & gotchas

- Past ADR bodies are never edited; only a status/pointer line may be
  updated when superseded.
- ADRs are proposed automatically during plan close-out per a
  confidence rule (create on clear architectural commitment; skip on
  bug/refactor/doc/test/mechanical; ask when borderline). Manual
  creation stays supported: copy `_template.md` to `NNNN-slug.md`,
  status `proposed`, add an index row.

## Pointers

- ADR-0001 — the foundational append-only decision.
- ADR-0010 — removed the `/adr` command; auto-proposal at close-out.
- docs/adr/README.md — the index the templates scaffold.

## Deltas

- 2026-05-27: `/adr` command removed; ADR creation folded into plan
  close-out — ADR-0010.
