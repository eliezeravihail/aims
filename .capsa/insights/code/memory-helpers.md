---
kind: code
title: "The bash helpers forming the deterministic substrate for the memory"
created: 2026-07-15
updated: 2026-07-29
code_globs: ["templates/memory/_lib.sh", "templates/memory/mark.sh", "templates/memory/new-insight.sh", "templates/memory/find-dirty.sh", "templates/memory/lint.sh", "templates/memory/consolidate.sh", "templates/memory/classify-inbox.sh", "templates/memory/doctor.sh", ".claude/memory/_lib.sh", ".claude/memory/doctor.sh"]
tags: [memory]
---

## Purpose

The bash helpers forming the deterministic substrate for the aims layer
over a Capsa capsule. `_lib.sh` owns frontmatter primitives (`fm_get`,
`fm_set`, `fm_list`, `path_matches`, `now_iso`, `today`, `json_escape`),
the Capsa insight helpers (`list_insights`/`list_leaves`,
`insight_globs`, `insight_updated_epoch`, `insight_stale`), and the
plan-state readers (`plan_status`, `plans_with_status`) that read the
Capsa frontmatter `status:` field. Six thin commands sit on top:
`mark`, `new-insight`, `find-dirty`, `lint`, `doctor`, `consolidate`,
`classify-inbox`. POSIX-friendly awk; no network calls (ADR-0009).

## Invariants & gotchas

- **Staleness is COMPUTED, never stored** (Capsa §1.4): `insight_stale`
  returns true when a `code_globs` file has an uncommitted change, a
  commit newer than the insight's `updated:` date, or (no git) a newer
  mtime. There is no `dirty` flag. `mark.sh consolidated` only bumps
  `updated:` (via `fm_set`); it writes no other state and has no
  README-sync side effect.
- The marker must normalize absolute paths before calling `mark.sh`;
  `path_matches` accepts absolute needles as defense-in-depth and
  treats every `code_globs` entry as an fnmatch glob (ADR-0014; greedy
  `*`, over-marking accepted, silent staleness not).
- `plan_status`/`plans_with_status` read the Capsa plan frontmatter
  `status:` field; body content quoting a status line must never count.
  Hooks carry a frontmatter-anchored grep fallback for lib-less installs.
- A code insight with no `code_globs` is rejected by the Capsa validator
  (and can never be flagged stale); `dev`/`design` insights carry none.
  The `/install-on` freshness probe reads insight `updated:`, never mtime.
- `fm_set` preserves the source file's mode across the tempfile rename
  (`chmod --reference` / BSD fallback) — `mktemp` is 0600.
- bash ≥ 4 guards in `lint.sh` (and the hooks using `mapfile` /
  `declare -A`): stock macOS bash 3.2 exits 0 with one breadcrumb.
- `lint.sh` delegates schema conformance to `validator/validate.py` and
  keeps the ADR-0028 body checks over code insights: 4-section schema,
  SHA validation in `## Deltas` against `code_globs`, compaction-due
  warning at ≥ `AIMS_MEMORY_DELTA_MAX`, >150/200 body-line caps.
- `consolidate.sh` caps evidence at 2 KB/source (commit summaries since
  `updated:` + uncommitted stat/patch), selects delta vs compact mode,
  and never touches files itself.
- All helpers exit 0 on a missing `.capsa/insights/`.

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
  longer removes `.lock` sidecars — ADR-0030, plan 0017.
- 2026-07-29: retargeted to the Capsa capsule with COMPUTED freshness —
  `_lib.sh` gained the insight/staleness helpers; `find-dirty` computes
  staleness from `updated:`+git; `mark consolidated` bumps `updated:`
  only; `lint` delegates schema to `validator/validate.py`;
  `new-node.sh`→`new-insight.sh`; `check-refs.sh`+`readme-sync.sh`
  removed; the `dirty`/`last_touched`/`last_consolidated` triple is
  gone — f62ef11 (decision 0031).
