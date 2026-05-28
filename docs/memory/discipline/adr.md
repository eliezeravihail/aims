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
last_touched: 2026-05-25T11:46:53Z
last_consolidated: 2026-05-25T11:46:53Z
---

## Purpose

Documents the /adr slash command and the ADR convention. ADRs are append-only — a superseded decision gets a new ADR with a `Superseded by:` pointer, not an in-place edit. The templates under `templates/adr-*.tmpl` are seeded into a target project by /install-on.

## Design rationale

## Invariants & gotchas

## Known issues

- superseded by ADR-0010: `/adr` is removed. ADRs are now proposed
  automatically during plan close-out per a confidence rule
  (create on clear architectural commitment; skip on
  bug/refactor/doc/test/mechanical; ask when borderline). Manual
  ADR creation is still supported: copy `_template.md` to
  `NNNN-slug.md`, status `proposed`.


## Pointers

## Open questions
