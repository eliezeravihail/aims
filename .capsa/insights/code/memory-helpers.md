---
kind: code
title: "The bash helpers forming the deterministic substrate for the memory"
created: 2026-07-15
updated: null
code_globs: ["templates/memory/_lib.sh", "templates/memory/mark.sh", "templates/memory/new-node.sh", "templates/memory/find-dirty.sh", "templates/memory/lint.sh", "templates/memory/check-refs.sh", "templates/memory/consolidate.sh", "templates/memory/classify-inbox.sh", "templates/memory/doctor.sh", "templates/memory/readme-sync.sh", ".claude/memory/_lib.sh", ".claude/memory/doctor.sh"]
tags: [memory]
---

## Purpose

The bash helpers forming the deterministic substrate for the memory
tree. `_lib.sh` owns frontmatter primitives (`fm_get`, `fm_set`,
`fm_list`, `list_leaves`, `path_matches`, `now_iso`, `json_escape`)
plus the header-scoped plan-state readers (`plan_status`,
`plans_with_status`). Nine thin commands sit on top: `mark`,
`new-node`, `find-dirty`, `lint`, `check-refs`, `doctor`,
`consolidate`, `classify-inbox`, `readme-sync`. POSIX-friendly awk; no
network calls anywhere (ADR-0009).

## Invariants & gotchas

- Only `mark.sh consolidated` may write
  `dirty/last_touched/last_consolidated`; it also triggers
  `readme-sync.sh` so the top README index tracks Purpose lines.
- The marker must normalize absolute paths before calling `mark.sh`;
  `path_matches` accepts absolute needles as defense-in-depth and
  treats every `code:` entry as an fnmatch glob (ADR-0014; greedy `*`,
  over-marking accepted, silent staleness not).
- `plan_status`/`plans_with_status` read ONLY the first 5 lines — plan
  state lives in the header; body content quoting a Status line must
  never count. Hooks carry a header-blind grep fallback for lib-less
  installs.
- A `module` node with `code: []` is inert — the marker can never flag
  it (ADR-0012); `lint.sh` reports it. The `/install-on` freshness
  probe reads `last_consolidated` frontmatter, never mtime.
- `fm_set` preserves the source file's mode across the tempfile rename
  (`chmod --reference` / BSD fallback) — `mktemp` is 0600.
- bash ≥ 4 guards in `lint.sh` (and the two hooks using `mapfile` /
  `declare -A`): stock macOS bash 3.2 exits 0 with one breadcrumb.
- `lint.sh` enforces the ADR-0028 4-section schema, validates SHAs in
  `## Deltas` against `code:` paths, warns at ≥ `AIMS_MEMORY_DELTA_MAX`
  deltas (compaction due) and >150/200 body lines, and checks the
  README index for drift.
- `consolidate.sh` caps evidence at 2 KB/source (commit summaries +
  uncommitted stat/patch), selects delta vs compact mode, and never
  touches files itself.
- All helpers exit 0 on a missing `docs/memory/`.

## Pointers

- ADR-0007 / ADR-0008 / ADR-0009 — design, node-as-interface, in-band.
- ADR-0028 — delta consolidation + 4-section schema (mode selection in
  `consolidate.sh`, schema + delta checks in `lint.sh`).
- ADR-0030 — strict `.lock` retired; `mark.sh consolidated` no longer
  removes lock files.
- ADR-0012 / ADR-0014 — code-glob mandate + fnmatch semantics.
- tests/marker.sh, tests/consolidate.sh — the covering suites.

## Deltas

- 2026-05-27: `ANTHROPIC_API_KEY`/curl path removed from helpers;
  prompt builders consumed in-band — ADR-0009.
- 2026-06-11: `fm_set` mode preservation (L2); lint subshell/`issues`
  fix + missing-commit branch (L1); bash≥4 guards (L4); leaf size cap —
  91fe2bd.
- 2026-07-15: schema checks retargeted to the 4-section ADR-0028
  layout; SHA validation moved from Known-issues to Deltas;
  compaction-due warning added — ADR-0028.
- 2026-07-15: `readme-sync.sh` added (generated top-README index;
  called from `mark.sh consolidated`, drift-checked by lint);
  `plan_status`/`plans_with_status` added to `_lib.sh`; `mark.sh` no
  longer removes `.lock` sidecars — ADR-0030,
  docs/plans/2026-07-15-memory-subsystem-diet.md.
