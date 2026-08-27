---
node: testing/smoke-tests
kind: module
code:
  - tests/marker.sh
  - tests/consolidate.sh
  - tests/exit-plan-mode.sh
  - tests/router-auto-plan.sh
  - tests/inform-never-block.sh
  - tests/copies-identical.sh
commits: []
sessions: []
parents: []
children: []
related:
  - memory/phase-a-marker
  - memory/phase-b-consolidation
claude_md_refs:
  - "Build & test commands"
external_refs: []
owners: []
dirty: false
last_touched: 2026-08-27T21:10:23Z
last_consolidated: 2026-08-27T21:10:23Z
---

## Purpose

Bash smoke tests for aims internals — no Anthropic API, no network.
- `marker.sh` (10 cases) — `path_matches` / marker hook / inbox dedup,
  including glob matching (ADR-0014 case 10).
- `consolidate.sh` (7 cases) — the Stop-hook block-JSON contract:
  --force emit shape, H1 (`.lock` survives normal exit, ADR-0024),
  H2 (`.marker` independent of `.lock`), throttle silence, and the
  three ADR-0027 discrepancy cases (first-emit clean; unchanged state
  surfaces DISCREPANCY DETECTED; state change clears it). Rewritten in
  commits 124e74a + ba9d38d from a pre-ADR-0009 HTTP-mock test that no
  longer matched reality.
- `exit-plan-mode.sh` (4 cases) — the harness-bridge hook (ADR-0015).
- `router-auto-plan.sh` (6 cases) — auto-engage intent router
  (ADR-0015). Case 6 guards char-vs-byte length: a short Hebrew prompt
  (~22 chars / 42 bytes) must NOT trip the actionable fallback.
- `inform-never-block.sh` (27 cases) — the ADR-0020 contract across all
  four inject hooks; section B wraps prompts as JSON payloads (M1),
  section C asserts the `.marker` suffix (ADR-0024).
- `copies-identical.sh` — diffs every distribution pair
  (templates↔.claude, templates/commands↔commands) and fails on any
  divergence (D4; caught a real drift during its own implementation).

## Design rationale

- Each script is self-contained: `mktemp -d` sandbox, ROOT-anchored,
  `trap rm -rf` cleanup. No global state survives a run.
- Helpers print `[PASS]` / `[FAIL]` and the failing case exits non-zero,
  so a CI runner can shell them sequentially without a framework.
- `jq` is the only non-POSIX dep; tests `[SKIP]` cleanly when it's
  missing.

## Invariants & gotchas

- Run from any directory: `bash tests/<file>.sh` resolves `$ROOT` via
  `BASH_SOURCE` so the helper paths stay correct under `cd`.
- The router tests touch `.claude/.planning-lock` inside their sandbox;
  never let the working `.claude/` directory leak into the test cwd
  (the `cd $TMP` line is load-bearing).

## Known issues

- fixed: `tests/consolidate.sh` mocked a pre-ADR-0009 Anthropic HTTP
  endpoint and failed against the in-band design — rewritten to assert
  the actual Stop-block-JSON contract (commit 124e74a, H3).
- fixed: `tests/inform-never-block.sh` section B fed raw prose; with jq
  installed `jq -r '.prompt'` errored silently and one assertion failed —
  inputs wrapped as JSON payloads (commit 124e74a, M1).

## Pointers

- ADR-0014 — glob matching, covered by `marker.sh` case 10.
- ADR-0015 — auto-plan flow, covered by both new tests.
- ADR-0024 — H1/H2 mutex-split cases in `consolidate.sh`.
- ADR-0027 — discrepancy-detection cases in `consolidate.sh` (ba9d38d).
- `CLAUDE.md` "Build & test commands" — invocation contract.

## Open questions

None.
