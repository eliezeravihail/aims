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
last_touched: 2026-06-18T09:31:44Z
last_consolidated: 2026-06-18T09:31:44Z
---

## Purpose

The `.tmpl` files under `templates/` that `/install-on` substitutes
into a target project (substitution-on-write, ADR-0005). Substitution
variables: `{{PROJECT_NAME}}`, `{{TEST_CMD}}`, `{{LINT_CMD}}`,
`{{TYPECHECK_CMD}}`, `{{ADR_DIR}}`, `{{HOOK_MODE}}`, `{{DATE}}`, and
`{{SUMMARY_LANG}}` (the `/plan` TL;DR language). `CLAUDE.md.tmpl`
gained a `## Memory tree` section in the ADR-0007 implementation.

## Design rationale

- Templates are the single source of the installed system layer, so a
  feature must land in the `.tmpl` (and the marketplace `commands/`
  copy) or installed projects silently miss it.
- `settings.json.tmpl` wires the full hook set, including a `PreCompact`
  entry running `pre-compact.sh` (commit 9973146).

## Invariants & gotchas

- `settings.json.tmpl` must declare every lifecycle hook the plugin
  ships; a missing entry means the hook never fires on installed
  projects. The `PreCompact` hook reports dirty memory state before
  context summarization and never touches the consolidation throttle.

## Known issues


## Pointers

- ADR-0005 — substitution-on-write template model.
- ADR-0007 — added the `## Memory tree` section to `CLAUDE.md.tmpl`.
- `templates/settings.json.tmpl` — hook wiring (PreCompact added in
  commit 9973146).
- External: docs/adr/0005-clone-and-bootstrap-install.md updated since last consolidation — review for impact
- External: CLAUDE.md "Plugin-specific notes (not from template)" updated since last consolidation — review for impact

## Open questions
