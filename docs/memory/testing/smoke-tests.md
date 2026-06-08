---
node: testing/smoke-tests
kind: module
code:
  - tests/marker.sh
  - tests/consolidate.sh
  - tests/exit-plan-mode.sh
  - tests/router-auto-plan.sh
  - tests/requirements.sh
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
last_touched: 2026-06-08T10:41:36Z
last_consolidated: 2026-06-08T10:41:36Z
---

## Purpose

Bash smoke tests for aims internals — no Anthropic API, no network.
- `marker.sh` (10 cases) — `path_matches` / marker hook / inbox dedup,
  including glob matching (ADR-0014 case 10).
- `consolidate.sh` (5 cases) — the in-band Stop-hook contract (ADR-0009):
  `--force` emits `{"decision":"block","reason":…}` naming each dirty
  node + `mark.sh`, bumps the throttle state, never edits nodes itself;
  `mark.sh consolidated` does the clean-flip. No network/mock (jq only).
- `exit-plan-mode.sh` (4 cases) — the harness-bridge hook (ADR-0015).
- `router-auto-plan.sh` (6 cases) — auto-engage intent router
  (ADR-0015). Case 6 guards char-vs-byte length: a short Hebrew prompt
  (~22 chars / 42 bytes) must NOT trip the actionable fallback.
- `requirements.sh` (4 cases) — ADR-0021 per-node requirements: renamed
  section + seed line, `fm_section` extraction, and `post-edit-marker`
  surfacing requirements at edit time.

## Design rationale

- Each script is self-contained: `mktemp -d` sandbox, ROOT-anchored,
  `trap rm -rf` cleanup. No global state survives a run.
- Helpers print `[PASS]` / `[FAIL]` and the failing case exits non-zero,
  so a CI runner can shell them sequentially without a framework.
- `jq` is the only non-POSIX dep; tests `[SKIP]` cleanly when it's
  missing.

## Requirements & invariants

- Requirements: none recorded beyond CLAUDE.md. Before editing, re-verify
  against CLAUDE.md and ask the user.

- Run from any directory: `bash tests/<file>.sh` resolves `$ROOT` via
  `BASH_SOURCE` so the helper paths stay correct under `cd`.
- The router tests touch `.claude/.planning-lock` inside their sandbox;
  never let the working `.claude/` directory leak into the test cwd
  (the `cd $TMP` line is load-bearing).

## Known issues

None open.

## Pointers

- ADR-0014 — glob matching, covered by `marker.sh` case 10.
- ADR-0015 — auto-plan flow, covered by both new tests.
- `CLAUDE.md` "Build & test commands" — invocation contract.

## Open questions

None.
