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

- All `{{VARS}}` must be substituted when writing a template file. An unsubstituted variable in the output is a bug.
- CLAUDE.md merge is section-aware: never overwrite an existing `## Heading`; append missing sections wrapped in `<!-- added by aims -->`.
- `settings.json.tmpl` merge touches only the `hooks` key. All other keys in an existing file are left untouched.

## Editing considerations

- When adding a new substitution variable, update BOTH the "Variables to substitute" table in `init-workflow.md` AND every template file that uses it.
- If `{{TYPECHECK_CMD}}` is unknown (project has no type checker), omit the typecheck line from CLAUDE.md rather than writing `{{TYPECHECK_CMD}}` literally.

## Deliberations & history

## Open questions
