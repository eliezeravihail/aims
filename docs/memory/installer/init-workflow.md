---
node: installer/init-workflow
kind: module
code:
  - commands/init-workflow.md
  - .claude/commands/init-workflow.md
commits: []
sessions: []
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

Documents /init-workflow — the clone-and-bootstrap installer. Five phases: sniff (read-only on TARGET), interview (fill gaps via AskUserQuestion), show plan + ask approval, apply (copy from AIMS_ROOT to TARGET + optional memory-tree seeding), doctor (final report). Question 7 has three options: `full` (copy + seed docs/memory/ inline, default), `install-only` (copy only; user runs /memory-init later), or `skip`.

## Logical rules & invariants

- If TARGET == AIMS_ROOT, refuse immediately. Never install aims into its own source repo.
- Never write outside TARGET (except `chmod +x` on files just created inside TARGET).
- Idempotent: detect prior install via `TARGET/.claude/aims-mode`. Re-running must merge, not overwrite.
- Read-only on `TARGET/src/`, `TARGET/tests/`, `TARGET/lib/`, package manifests, `TARGET/README.md`, `TARGET/LICENSE`.

## Editing considerations

- `commands/init-workflow.md` is NOT copied to TARGET. It is the installer; copying it would make a target appear self-bootstrappable.
- The four discipline commands live under `AIMS_ROOT/templates/commands/`, not `AIMS_ROOT/commands/`. This is what keeps them out of the global plugin surface.
- `commands/init-workflow.md` and `.claude/commands/init-workflow.md` must stay identical — when editing one, edit the other.

## Deliberations & history

## Open questions
