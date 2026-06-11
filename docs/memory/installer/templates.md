---
node: installer/templates
kind: topic
code:
  - templates/CLAUDE.md.tmpl
  - templates/settings.json.tmpl
  - templates/adr-template.md.tmpl
  - templates/adr-readme.md.tmpl
  - templates/adr-0001.md.tmpl
  - templates/plan-template.md.tmpl
commits: []
sessions: []
parents: []
children: []
related:
  - installer/install-on
claude_md_refs:
  - "Plugin-specific notes (not from template)"
external_refs:
  - { path: docs/adr/0005-clone-and-bootstrap-install.md, kind: adr, why: defines the substitution-on-write template model }
owners:
  - ema
dirty: true
last_touched: 2026-06-11T07:33:27Z
last_consolidated: 2026-05-31T14:26:12Z
---

## Purpose

The .tmpl files under templates/ that /install-on substitutes into a target project. Substitution variables: {{PROJECT_NAME}}, {{TEST_CMD}}, {{LINT_CMD}}, {{TYPECHECK_CMD}}, {{ADR_DIR}}, {{HOOK_MODE}}, {{DATE}}. CLAUDE.md.tmpl gained a `## Memory tree` section in the ADR-0007 implementation.

## Design rationale

## Invariants & gotchas

## Known issues


## Pointers

## Open questions
