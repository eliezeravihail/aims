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
related:
  - installer/init-workflow
claude_md_refs:
  - "Plugin-specific notes (not from template)"
external_refs:
  - { path: docs/adr/0005-clone-and-bootstrap-install.md, kind: adr, why: defines the substitution-on-write template model }
owners:
  - ema
dirty: false
last_touched: 2026-05-25T11:46:53Z
last_consolidated: 2026-05-25T11:46:53Z
---

## Purpose

The .tmpl files under templates/ that /init-workflow substitutes into a target project. Substitution variables: {{PROJECT_NAME}}, {{TEST_CMD}}, {{LINT_CMD}}, {{TYPECHECK_CMD}}, {{ADR_DIR}}, {{HOOK_MODE}}, {{DATE}}. CLAUDE.md.tmpl gained a `## Memory tree` section in the ADR-0007 implementation.

## Logical rules & invariants

## Editing considerations

## Deliberations & history

## Open questions
