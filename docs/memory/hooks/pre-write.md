---
node: hooks/pre-write
kind: module
code:
  - templates/hooks/pre-write.sh
  - .claude/hooks/pre-write.sh
commits: []
sessions: []
parents: []
children: []
related:
  - discipline/plan
claude_md_refs:
  - "Hooks"
external_refs:
  - { path: docs/adr/0003-hooks-default-nudge-lock-always-blocks.md, kind: adr, why: default mode = nudge; planning-lock always hard-blocks regardless of mode }
  - { path: docs/adr/0017-pre-write-carves-out-plan-drafts.md,        kind: adr, why: lock carves out docs/plans/*.md so /plan auto-engage can write the draft }
owners:
  - ema
dirty: false
last_touched: 2026-05-31T21:37:22Z
last_consolidated: 2026-05-31T21:37:22Z
---

## Purpose

PreToolUse hook on `Edit | Write | MultiEdit | NotebookEdit`. Two
responsibilities: (1) hard-block while `.claude/.planning-lock` exists
(planning is read-only) — **except** for writes to `docs/plans/*.md`, which
are explicitly carved out so the `/plan` auto-engage flow (ADR-0015) can
write its draft; (2) in `block` mode, soft-block writes to recognised
source paths without an in-progress plan. Exit 2 surfaces stderr to the
model and the user.

## Design rationale

- The carve-out exists because ADR-0015's auto-engage *tells the model to
  write a draft* the moment the lock is set. Without the exception, every
  Write/Edit fails and the cascade deadlocks (the fragile Bash-heredoc
  fallback breaks on apostrophes in plan content — see ADR-0017).
- The carve-out is path-scoped to the configurable `PLAN_DIR`
  (default `docs/plans/`) and only matches `*.md`/`*.md.tmp` — so it
  doesn't accidentally license writes to any plan-adjacent file.
- `block` mode is opt-in per project via `.claude/aims-mode` and only
  triggers on canonical source roots (`src/`, `lib/`, `app/`,
  `server/`, `client/`, `packages/`); tests/docs/markdown stay free.

## Invariants & gotchas

- The hook MUST exit 2 (not 1) to surface the stderr block message to
  Claude Code — anything else and the gate becomes invisible.
- The carve-out covers ONLY plan drafts. Any other Write under the lock
  (including ADRs and memory nodes) still hard-blocks; the model is
  expected to draft → approve → unlock → edit.
- `target` extraction handles both `tool_input.file_path` and
  `tool_input.path` — the latter is how `NotebookEdit` reports.

## Known issues


## Pointers

## Open questions
