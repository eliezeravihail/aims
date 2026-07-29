---
kind: code
title: "`/install-on` — the clone-and-bootstrap installer (renamed from"
created: 2026-07-15
updated: null
code_globs: ["commands/install-on.md", "templates/commands/install-on.md", ".claude/commands/install-on.md"]
tags: [installer]
---

## Purpose

`/install-on` — the clone-and-bootstrap installer (renamed from
`/init-workflow` per ADR-0010). Six phases: (1) detect install state,
(2) interview gaps via AskUserQuestion (incl. question 6: plan
summary language → `.claude/aims-summary-lang` / `{{SUMMARY_LANG}}`),
(3) planned-changes preview + approval, (4) apply, (5) memory tree —
cold-start or freshness-gated augment, (6) doctor report. Memory tree
is always installed.

## Invariants & gotchas

- **Idempotency seam (ADR-0011).** Refresh: hooks, memory scripts, the
  two commands, aims-owned settings hooks, aims-shipped ADR
  scaffolding. Delete: unshipped `*.sh` in `.claude/{hooks,memory}/`;
  commands other than `install-on`/`plan`. Never touch: authored ADRs,
  ADR README `## Index` rows, CLAUDE.md sections, plans, memory node
  bodies, non-`hooks` settings keys.
- `docs/adr/README.md` is index-aware: refresh prose above `## Index`,
  splice existing rows back verbatim.
- All three command copies must stay byte-identical
  (`tests/copies-identical.sh`).
- **Hooks/scripts lists must stay complete** — an entry omitted from
  the copy table is silently absent on installed projects. Current
  memory-scripts set includes `readme-sync.sh`; hooks include
  `pre-compact.sh`.
- **Phase 5 freshness gate (ADR-0012)** reads newest
  `last_consolidated` from frontmatter via a `find`-based whole-tree
  walk (never file mtime — clones reset mtimes); tree work only if
  older than 7 days.
- Cold-start must fill `code:` globs for every module node; augment
  backfills inert ones (ADR-0012).

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
  (all three copies) — docs/plans/2026-07-15-memory-subsystem-diet.md.
