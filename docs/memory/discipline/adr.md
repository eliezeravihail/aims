---
node: discipline/adr
kind: module
code:
  - templates/adr-template.md.tmpl
  - templates/adr-readme.md.tmpl
  - templates/adr-0001.md.tmpl
# (was: templates/commands/adr.md, .claude/commands/adr.md — both removed per ADR-0010)
commits: []
sessions: []
parents: []
children: []
related:
  - discipline/done
claude_md_refs:
  - "Decision records"
external_refs:
  - { path: docs/adr/0001-record-architecture-decisions.md, kind: adr, why: the foundational decision: record decisions in append-only ADRs }
owners:
  - ema
dirty: false
last_touched: 2026-07-15T09:17:00Z
last_consolidated: 2026-07-15T09:17:00Z
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
