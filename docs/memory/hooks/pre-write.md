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
  - { path: docs/adr/0019-sidecar-lockfiles-for-memory-nodes.md,      kind: adr, why: pre-write refuses memory-node edits while another session holds the sidecar .lock; same patch normalizes absolute paths against the repo root so the docs/plans carve-out actually fires }
owners:
  - ema
dirty: false
last_touched: 2026-06-02T15:53:38Z
last_consolidated: 2026-06-02T15:53:38Z
---

## Purpose

PreToolUse hook on `Edit | Write | MultiEdit | NotebookEdit`. Three
responsibilities now: (1) hard-block while `.claude/.planning-lock` exists
(planning is read-only) — **except** for writes to `docs/plans/*.md`, which
are explicitly carved out so the `/plan` auto-engage flow (ADR-0015) can
write its draft; (2) **refuse Edit/Write to a `docs/memory/<tag>/<leaf>.md`
node when a `<leaf>.lock` sidecar is held by another fresh session**
(ADR-0019 — multi-session mutex on memory nodes); (3) in `block` mode,
soft-block writes to recognised source paths without an in-progress plan.
Exit 2 surfaces stderr to the model and the user.

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
- **Path normalization (ADR-0019).** Claude Code passes absolute
  `tool_input.file_path`; the planning-lock carve-out, the memory-node
  lock check, and the source-path detector all compare against a
  relative form. The hook normalizes `target` against
  `git rev-parse --show-toplevel` exactly once, then uses `target_rel`
  everywhere downstream. Without this, the docs/plans/ carve-out
  silently missed and even the `/plan` flow's own draft writes were
  blocked.
- **Memory-node lock owner check** reads
  `head -n1 docs/memory/<tag>/<leaf>.lock` and compares against the
  caller's `session_id` from the payload. Lock body is just the sid;
  staleness uses mtime + `AIMS_LOCK_TTL_SEC` (default 600s). Stale or
  same-session locks pass through silently.

## Invariants & gotchas

- The hook MUST exit 2 (not 1) to surface the stderr block message to
  Claude Code — anything else and the gate becomes invisible.
- The carve-out covers ONLY plan drafts. Any other Write under the lock
  (including ADRs and memory nodes) still hard-blocks; the model is
  expected to draft → approve → unlock → edit.
- `target` extraction handles both `tool_input.file_path` and
  `tool_input.path` — the latter is how `NotebookEdit` reports.

(Body above is stale — describes ADR-0017/0019-era blocking behavior
that ADR-0020 removed. Current hook is inform-only; the NOTE is
state-aware per ADR-0023. Re-consolidate on next non-trivial edit.)

## Known issues

- fixed (ADR-0019): the carve-out matched `target` against
  `docs/plans/*.md` as a relative pattern, but Claude Code passes
  absolute paths — so even legitimate `/plan` draft writes were
  blocked. Normalized via `git rev-parse --show-toplevel`.

## Pointers

- ADR-0019 — sidecar lock check + path normalization (historical).
- ADR-0020 — hooks inform, never block; removed all gating from this
  hook. The Three-responsibility model in ## Purpose above is obsolete.
- ADR-0023 — state-aware NOTE: names the file being edited and the
  missing plan; anchors the planning convention to the moment of
  first source edit, fixing the conversational-drift skip mode.
- `templates/hooks/pre-write.sh:84` — the NOTE string.
- `tests/inform-never-block.sh` — never-block + once-per-session
  inject invariant tests.

## Open questions
