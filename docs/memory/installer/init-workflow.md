---
node: installer/init-workflow
kind: module
code:
  - templates/commands/install-on.md
  - .claude/commands/install-on.md
# renamed from init-workflow.md per ADR-0010 (idempotent install + memory bootstrap)
commits: []
sessions: []
parents: []
children: []
related:
  - installer/templates
  - discipline/plan
  - discipline/done
claude_md_refs:
  - "Build & test commands"
  - "Workflow"
external_refs:
  - { path: docs/adr/0005-clone-and-bootstrap-install.md, kind: adr, why: the install model this command implements }
owners:
  - ema
dirty: false
last_touched: 2026-05-25T11:46:53Z
last_consolidated: 2026-05-25T11:46:53Z
---

## Purpose

Documents /init-workflow — the clone-and-bootstrap installer. Five phases: sniff (read-only on TARGET), interview (fill gaps via AskUserQuestion), show plan + ask approval, apply (copy from AIMS_ROOT to TARGET), doctor (final report). Question 7 (memory tree) and the corresponding file-table rows enable the ADR-0007 layer on install.

## Design rationale

## Invariants & gotchas

## Known issues


## Pointers

## Open questions
