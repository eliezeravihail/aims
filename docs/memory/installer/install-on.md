---
node: installer/install-on
kind: module
code:
  - commands/install-on.md
  - templates/commands/install-on.md
  - .claude/commands/install-on.md
# renamed from init-workflow per ADR-0010 (idempotent install + memory bootstrap)
commits: []
sessions: []
parents: []
children: []
related:
  - installer/templates
  - discipline/plan
claude_md_refs:
  - "Build & test commands"
  - "Workflow"
external_refs:
  - { path: docs/adr/0005-clone-and-bootstrap-install.md, kind: adr, why: the install model this command implements }
owners:
  - ema
dirty: false
last_touched: 2026-05-28T15:06:22Z
last_consolidated: 2026-05-28T15:06:22Z
---

## Purpose

Documents `/install-on` (renamed from `/init-workflow` per ADR-0010) — the
clone-and-bootstrap installer. Six phases: (1) detect install state +
`PRIOR_AIMS` flag, (2) interview gaps via AskUserQuestion, (3) show planned
changes per class + approval gate, (4) apply (copy from AIMS_ROOT, clean
stale files, merge settings/CLAUDE.md), (5) memory bootstrap or augment
(always; ADR-0007/0009), (6) doctor report. Memory tree is always installed.

## Design rationale

ADR-0011 made re-install **self-refreshing**: the system layer is fully
replaced and stale aims files are deleted, while user-authored documentation
stays sacred. This split exists because aims ships some docs (the ADR
bootstrap `0001`, `_template.md`, the ADR README prose) that must track the
plugin, not freeze at first install.

## Invariants & gotchas

- **The idempotency seam (ADR-0011).** Refresh: hooks, memory scripts, the two
  commands, aims-owned `settings.json` hook entries, and aims-shipped ADR
  scaffolding. Delete: `*.sh` in `.claude/{hooks,memory}/` not in the shipped
  set; commands other than `install-on`/`plan`. Never touch: authored ADRs
  (`NNNN != 0001`), the ADR README `## Index` rows, CLAUDE.md sections, plans,
  memory node bodies, non-`hooks` settings keys.
- **`docs/adr/README.md` is index-aware** — refresh the prose above
  `## Index`, splice the existing index rows back verbatim. Never overwrite it
  wholesale (that destroys the user's ADR log).
- All three command copies (`commands/`, `templates/commands/`,
  `.claude/commands/`) must stay byte-identical — verify with `md5sum`.

## Known issues


## Pointers

## Open questions
