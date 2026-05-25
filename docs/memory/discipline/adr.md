---
node: discipline/adr
kind: module
code:
  - templates/commands/adr.md
  - .claude/commands/adr.md
  - templates/adr-template.md.tmpl
  - templates/adr-readme.md.tmpl
  - templates/adr-0001.md.tmpl
commits: []
sessions: []
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

Documents the /adr slash command and the ADR convention. ADRs are append-only — a superseded decision gets a new ADR with a `Superseded by:` pointer, not an in-place edit. The templates under `templates/adr-*.tmpl` are seeded into a target project by /init-workflow.

## Logical rules & invariants

## Editing considerations

## Deliberations & history

## Open questions
