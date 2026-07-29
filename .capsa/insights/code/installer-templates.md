---
kind: code
title: "The `.tmpl` files under `templates/` that `/install-on` substitutes"
created: 2026-07-15
updated: null
code_globs: ["templates/CLAUDE.md.tmpl", "templates/settings.json.tmpl", "templates/adr-template.md.tmpl", "templates/adr-readme.md.tmpl", "templates/adr-0001.md.tmpl", "templates/plan-template.md.tmpl"]
tags: [installer]
---

## Purpose

The `.tmpl` files under `templates/` that `/install-on` substitutes
into a target project (substitution-on-write, ADR-0005). Variables:
`{{PROJECT_NAME}}`, `{{TEST_CMD}}`, `{{LINT_CMD}}`, `{{TYPECHECK_CMD}}`,
`{{ADR_DIR}}`, `{{HOOK_MODE}}`, `{{DATE}}`, `{{SUMMARY_LANG}}`.
`CLAUDE.md.tmpl` carries a `## Memory tree` section (ADR-0007).

## Invariants & gotchas

- Templates are the single source of the installed system layer — a
  feature not present in the `.tmpl` (and the marketplace `commands/`
  copy) is silently missing on installed projects.
- `settings.json.tmpl` must declare every lifecycle hook the plugin
  ships (incl. `PreCompact` → `pre-compact.sh`, which reports dirty
  memory state before context compaction and never touches the
  consolidation throttle).

## Pointers

- ADR-0005 — substitution-on-write model.
- ADR-0007 — the `## Memory tree` CLAUDE.md section.
- templates/settings.json.tmpl — hook wiring.

## Deltas

- 2026-06-11: `PreCompact` hook wired into `settings.json.tmpl` —
  9973146.
