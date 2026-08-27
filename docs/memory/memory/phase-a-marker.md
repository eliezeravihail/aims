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
last_touched: 2026-08-27T21:10:23Z
last_consolidated: 2026-08-27T21:10:23Z
---

## Purpose

Phase A of the two-phase maintenance design: a PostToolUse hook that
runs after every Edit/Write/MultiEdit/NotebookEdit and flips
`dirty: true` on every node whose `code:` list references the edited
file. Pure bash + sed; ~27 ms per call on a tiny tree. Unknown paths
go to `docs/memory/_inbox.md` for later classification. The hook
never blocks and always exits 0.

## Design rationale

- The marker is dumb on purpose: it doesn't try to summarize the
  change, only flag it. All judgment is deferred to Phase B
  (ADR-0007) and now runs in-band (ADR-0009).
- `mark.sh` carries the inverse `consolidated` subcommand used by
  the in-band model to flip the same flag clean after a successful
  body rewrite — keeps both transitions in one helper.
- Per ADR-0024 the mutex protocol is **split** into two files. The
  marker hook writes an **advisory `<leaf>.marker`** stamping
  `session_id + mtime`; it never blocks and same-session refreshes are
  silent. A separately-owned **strict `<leaf>.lock`** (acquired via
  `set -C` by `stop-consolidate.sh`) is the consolidation mutex.
  `mark.sh consolidated` removes the marker; only the Stop hook
  creates/removes the strict lock. Names no longer collide.
- The marker file write is **symlink-guarded** (M4 / ADR-0024) — if
  the path exists and is a symlink, the marker refuses to follow it,
  closing a write-through-symlink hazard.
- Hook output uses the centralized `json_escape` helper from `_lib.sh`
  (M2) so control chars and quotes in paths can't corrupt the
  `additionalContext` JSON.

## Invariants & gotchas

- Never blocks. Never exits non-zero. A broken marker must not
  block the user's edit.
- `path_matches` (in `_lib.sh`) handles trailing slashes and the
  optional `:line` suffix in `code:` entries; don't reimplement
  matching elsewhere.

## Known issues

- fixed: the advisory marker and the strict consolidation mutex shared
  one `<leaf>.lock` path, starving same-session consolidation — split
  into `.marker`/`.lock` (commit 124e74a, ADR-0024).
- fixed: marker write followed symlinks, letting a malicious repo
  redirect it to any user-writable file — symlink-guarded + O_EXCL
  (commit 124e74a, M4).

## Pointers

- ADR-0007 — Phase A specification.
- ADR-0009 — adds the `consolidated` mode to `mark.sh`.
- ADR-0024 — the `.marker`/`.lock` protocol split (supersedes ADR-0019).
- Commit e409d6e (D2) — `docs/adr/` is now a tracked surface: nodes may
  cite ADRs in `code:` and dirty-mark on doctrine changes.
- `templates/memory/mark.sh:34-46` — `consolidated` subcommand.

## Open questions
