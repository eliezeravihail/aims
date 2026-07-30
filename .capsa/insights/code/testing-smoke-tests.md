---
kind: code
title: "Bash smoke tests for aims internals — no Anthropic API, no network."
created: 2026-07-15
updated: 2026-07-30
code_globs: ["tests/marker.sh", "tests/consolidate.sh", "tests/exit-plan-mode.sh", "tests/router-auto-plan.sh", "tests/inform-never-block.sh", "tests/copies-identical.sh"]
tags: [testing]
---

## Purpose

Bash smoke tests for aims internals — no Anthropic API, no network.
`marker.sh` (11 cases): `path_matches` / marker hook / inbox dedup /
glob matching / computed-staleness convergence. `consolidate.sh`: Stop block-JSON, no-`.lock` +
marker-independence (ADR-0030), delta vs compact mode selection
(ADR-0028), throttle, and the three ADR-0027 discrepancy cases.
`exit-plan-mode.sh` (6 cases): the harness-bridge hook writing Capsa
plan records + validator conformance.
`router-auto-plan.sh` (8 cases): the ADR-0029 shape gate incl.
language-neutral positive/negative and the Track D header-scoped
Status decoy. `inform-never-block.sh`: never-block + once-per-session
invariants. `copies-identical.sh`: distribution-pair byte identity.

## Invariants & gotchas

- Each script is self-contained: `mktemp -d` sandbox, `$ROOT` resolved
  via `BASH_SOURCE` (run from any directory), `trap rm -rf` cleanup.
- `[PASS]`/`[FAIL]` + non-zero exit on failure; `jq` is the only
  non-POSIX dep and tests `[SKIP]` cleanly without it.
- The router tests run hooks inside the sandbox cwd; never let the
  working `.claude/` leak in. Case 8 deliberately copies `_lib.sh`
  into the sandbox — without it the hook's header-blind grep fallback
  would defeat the header-scoping assertion.
- `consolidate.sh` cases assert on prompt text (`mode: delta`,
  `mode: compact`, `DISCREPANCY DETECTED`) — keep those strings stable
  in the generators or update both sides together.

## Pointers

- ADR-0028 / ADR-0029 / ADR-0030 — the behaviors the updated suites
  pin down.
- ADR-0027 — discrepancy cases in `tests/consolidate.sh`.
- `CLAUDE.md` "Build & test commands" — invocation contract.

## Deltas

- 2026-06-11: ADR-0027 discrepancy cases added to
  `tests/consolidate.sh` — ba9d38d.
- 2026-07-15: `router-auto-plan.sh` rewritten for the shape gate
  (8 cases; keeps the char-vs-byte Hebrew guard, adds a Hebrew
  positive + the Status-decoy case); `consolidate.sh` updated for
  delta/compact modes and lock retirement; `inform-never-block.sh`
  Hebrew-question case now uses a trailing `?` (non-`?` questions
  over-fire the note by design) — ADR-0028/0029/0030, plan 0017.
- 2026-07-29: all six suites rewritten for the `.capsa/` layout +
  computed freshness — marker/consolidate build isolated git repos
  with `.capsa/insights`; exit-plan-mode asserts Capsa plan records
  (`status: in_progress`, auto id) + validator conformance; router
  case 8 uses a `.capsa/plans` frontmatter-status decoy — f62ef11
  (decision 0031).
