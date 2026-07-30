---
kind: code
title: "`/install-on` — the clone-and-bootstrap installer (renamed from"
created: 2026-07-15
updated: 2026-07-29
code_globs: ["commands/install-on.md", "templates/commands/install-on.md", ".claude/commands/install-on.md"]
tags: [installer]
---

## Purpose

`/install-on` — the clone-and-bootstrap installer (renamed from
`/init-workflow` per ADR-0010). Six phases: (1) detect install state,
(2) interview gaps via AskUserQuestion (incl. plan summary language →
`.claude/aims-summary-lang` / `{{SUMMARY_LANG}}`), (3) planned-changes
preview + approval, (4) apply, (5) insights — cold-start or
freshness-gated augment, (6) doctor report. The Capsa capsule
(`.capsa/`) + vendored validator are always installed.

## Invariants & gotchas

- **Idempotency seam (ADR-0011).** Refresh: hooks, memory scripts, the
  two commands, the vendored `validator/` + `schema/`, aims-owned
  settings hooks. Delete: unshipped `*.sh` in `.claude/{hooks,memory}/`;
  commands other than `install-on`/`plan`. Never touch: capsule records
  (`.capsa/{decisions,plans,insights}/`), `.capsa/charter.md`,
  `.capsa/capsule.yaml`, CLAUDE.md sections, non-`hooks` settings keys.
- Capsule bootstrap creates `.capsa/{capsule.yaml,charter.md}` + the
  record dirs only if missing; existing records are never overwritten.
  A pre-Capsa target (`docs/adr|memory`) is a re-install; migration of
  old records is a separate step, surfaced in the doctor report.
- All three command copies must stay byte-identical
  (`tests/copies-identical.sh`).
- **Hooks/scripts lists must stay complete** — an entry omitted from
  the copy table is silently absent on installed projects. Current
  memory-scripts set includes `new-insight.sh` (was `new-node.sh`);
  hooks include `pre-compact.sh` + `exit-plan-mode.sh`.
- **Phase 5 freshness gate (ADR-0012)** reads the newest insight
  `updated:` from frontmatter via a `find`-based whole-tree walk (never
  file mtime — clones reset mtimes); insight work only if older than 7
  days.
- Cold-start must fill `code_globs` for every code insight (the Capsa
  validator rejects a code insight with none).

## Pointers

- ADR-0005 — clone-and-bootstrap model.
- ADR-0010 / ADR-0011 — two-command surface + self-refreshing seam.
- ADR-0012 — freshness gate + mandatory code globs.
- tests/copies-identical.sh — three-way byte-identity guard.

## Deltas

- 2026-06-11: marketplace copy re-synced (summary-language feature was
  missing); freshness probe became a find-based walk (L7);
  `pre-compact.sh` added to the hooks list; copies-identical CI guard
  added — docs/plans/2026-06-11-aims-audit-fixes-master.md (Track 4).
- 2026-07-15: `readme-sync.sh` added to the memory-scripts copy row
  (all three copies) — plan 0017 (memory-subsystem-diet).
- 2026-07-29: bootstraps a `.capsa/` capsule + vendors the validator
  instead of seeding `docs/{adr,plans,memory}`; Phase 5 gates on insight
  `updated:`; `new-node.sh`→`new-insight.sh`, `check-refs`/`readme-sync`
  dropped from the copy set — f62ef11 (decision 0031).
