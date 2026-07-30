---
kind: code
title: "The `.tmpl` files under `templates/` that `/install-on` substitutes"
created: 2026-07-15
updated: 2026-07-29
code_globs: ["templates/CLAUDE.md.tmpl", "templates/settings.json.tmpl", "templates/decision.md.tmpl", "templates/plan-template.md.tmpl", "templates/capsule.yaml.tmpl", "templates/charter.md.tmpl"]
tags: [installer]
---

## Purpose

The `.tmpl` files under `templates/` that `/install-on` substitutes
into a target project (substitution-on-write, ADR-0005). The set is
`CLAUDE.md.tmpl`, `settings.json.tmpl`, `plan-template.md.tmpl`,
`decision.md.tmpl`, `capsule.yaml.tmpl`, `charter.md.tmpl` (the three
`adr-*.tmpl` were removed with the Capsa migration). Variables:
`{{PROJECT_NAME}}`, `{{PROJECT_SLUG}}`, `{{REPO_URL}}`, `{{TEST_CMD}}`,
`{{LINT_CMD}}`, `{{TYPECHECK_CMD}}`, `{{HOOK_MODE}}`, `{{DATE}}`,
`{{SUMMARY_LANG}}`. `CLAUDE.md.tmpl` carries `## Capsule` +
`## Insights (memory)` sections.

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
- decision 0031 — aims on the Capsa capsule format.
- templates/settings.json.tmpl — hook wiring.

## Deltas

- 2026-06-11: `PreCompact` hook wired into `settings.json.tmpl` —
  9973146.
- 2026-07-29: added `capsule.yaml.tmpl`/`charter.md.tmpl`/
  `decision.md.tmpl`, Capsa-ised `plan-template` + `CLAUDE.md.tmpl`,
  removed the three `adr-*.tmpl` — f62ef11 (decision 0031).
