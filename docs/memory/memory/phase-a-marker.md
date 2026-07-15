---
node: memory/phase-a-marker
kind: module
code:
  - templates/hooks/post-edit-marker.sh
  - .claude/hooks/post-edit-marker.sh
  - templates/memory/mark.sh
commits: []
sessions:
  - docs/plans/memory-tree-system.md
parents: []
children: []
related:
  - memory/helpers
  - memory/phase-b-consolidation
claude_md_refs:
  - "Hooks"
external_refs:
  - { path: docs/adr/0007-tree-based-memory-with-auto-maintenance.md, kind: adr, why: Phase A specification — the cheap, deterministic flag flipper }
  - { path: tests/marker.sh, kind: test, why: six smoke cases for marker behaviour }
owners:
  - ema
dirty: false
last_touched: 2026-07-15T09:17:03Z
last_consolidated: 2026-07-15T09:17:03Z
---

## Purpose

Phase A of the two-phase maintenance design: a PostToolUse hook on
Edit/Write/MultiEdit/NotebookEdit that flips `dirty: true` on every
node whose `code:` references the edited file (via `mark.sh`), stamps
an advisory `<leaf>.marker`, and injects a factual note naming the
stale node. Unknown paths go to `docs/memory/_inbox.md`. Dumb on
purpose — judgment is deferred to Phase B (ADR-0007/0009). Never
blocks, always exits 0.

## Invariants & gotchas

- Never blocks, never exits non-zero — a broken marker must not block
  the user's edit.
- Skip-list: `.claude/*`, `.git/*`, vendored dirs, `docs/memory/*`,
  and `docs/plans/*` (plan files are workflow artifacts referenced via
  `sessions:`, never `code:`). `docs/adr/` IS tracked — nodes may cite
  ADRs in `code:` so doctrine changes dirty-mark them (D2).
- The advisory `.marker` (session-id + mtime) is the ONLY sidecar
  since ADR-0030 retired the strict `.lock`. Same session refreshes
  silently; another session's marker younger than
  `AIMS_NODE_LOCK_STALE_SEC` (3600s) → "possible concurrent edit"
  note (ask the user before updating); older → taken over.
- Marker writes are symlink-guarded + O_EXCL (M4) — a planted symlink
  cannot redirect the write.
- `path_matches` (in `_lib.sh`) is the single matching implementation;
  don't reimplement. Output JSON goes through `json_escape`.

## Pointers

- ADR-0007 — Phase A specification.
- ADR-0024 — introduced the `.marker`/`.lock` split (the `.lock` half
  now retired by ADR-0030).
- ADR-0030 — advisory markers are the only cross-session signal.
- tests/marker.sh — smoke cases incl. glob matching (ADR-0014).

## Deltas

- 2026-06-11: mutex split — advisory `.marker` vs strict `.lock`;
  symlink-guarded marker write (M4) — 124e74a, ADR-0024.
- 2026-06-11: `docs/adr/` became a tracked surface (D2) — e409d6e.
- 2026-07-15: `docs/plans/*` added to the skip-list (drafts no longer
  leak into `_inbox.md`); `mark.sh consolidated` now triggers
  `readme-sync.sh` and no longer removes `.lock` sidecars — ADR-0030,
  docs/plans/2026-07-15-memory-subsystem-diet.md.
