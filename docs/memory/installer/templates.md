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
dirty: false
last_touched: 2026-08-27T21:10:23Z
last_consolidated: 2026-08-27T21:10:23Z
---

## Purpose

The .tmpl files under templates/ that /install-on substitutes into a target
project. Substitution variables: {{PROJECT_NAME}}, {{TEST_CMD}},
{{LINT_CMD}}, {{TYPECHECK_CMD}}, {{ADR_DIR}}, {{HOOK_MODE}}, {{DATE}},
{{SUMMARY_LANG}}. CLAUDE.md.tmpl gained a `## Memory tree` section in the
ADR-0007 implementation.

## Design rationale

- `settings.json.tmpl` wires every aims lifecycle hook, including the
  `PreCompact` entry added in commit 9973146 (Track 3; inspired by
  project-bedrock and claude-code-context-handoff) — advisory dirty-state
  breadcrumb before context compaction.

## Invariants & gotchas

- The hook list in `settings.json.tmpl` must stay in lockstep with the
  shipped set in install-on Phase 4 and with `templates/hooks/*` —
  `tests/copies-identical.sh` guards the hooks pair; the settings entry
  list is manual.

## Known issues

- fixed: `settings.json.tmpl` lacked the PreCompact hook entry until
  commit 9973146 (Track 3).

## Pointers

- ADR-0005 — the substitution-on-write template model.
- `templates/hooks/pre-compact.sh` — the hook the new entry runs.

## Open questions
