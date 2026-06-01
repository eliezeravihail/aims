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

- Never edit a past ADR's body. Only the status pointer (`Superseded by: ADR-NNNN`) may change in an existing ADR.
- Status starts at `proposed`. Promotion to `accepted` happens externally (PR review, team decision); never auto-accept.
- The ADR index (`docs/adr/README.md`) must be updated every time a new ADR is written. The `/adr` command does this; do not skip it.
- Do not write an ADR for an undecided question — use `/plan` instead.

## Editing considerations

- Next number = max(existing NNNN) + 1, zero-padded to 4 digits. Scan `docs/adr/[0-9]*.md`; skip `_template.md` and `README.md`.
- When superseding, both the new ADR (`Supersedes: ADR-MMMM`) and the old ADR's status line (`Superseded by: ADR-NNNN`) must be updated. Two file edits.

## Deliberations & history

## Open questions
