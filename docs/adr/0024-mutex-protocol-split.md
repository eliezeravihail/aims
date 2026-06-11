# ADR-0024: Mutex protocol split — `.lock` strict, `.marker` advisory
Status: accepted
Date: 2026-06-11
Supersedes: docs/adr/0019-sidecar-lockfiles-for-memory-nodes.md
Superseded by: —

## Context

ADR-0019 introduced a single sidecar `<leaf>.lock` to coordinate concurrent
consolidation. Subsequent work then repurposed that same path as an advisory
edit marker written by `post-edit-marker.sh` on every PostToolUse event. The
two protocols collided:

- `post-edit-marker.sh` stamped `${leaf%.md}.lock` on every edit with a 3600 s
  stale window and a plain `>` write (advisory bookkeeping).
- `stop-consolidate.sh::try_claim` used `O_EXCL` (via `set -C`) on the SAME
  path with a 600 s TTL and no ownership check (strict mutex).

Empirically verified failure: a node touched in the last 10 minutes — even by
the **same** session — failed `try_claim`, was dropped from the CLAIMED set,
and `--force` produced empty output. The two protocols starved each other.

A second bug compounded it: `trap release_held_locks EXIT` in
`stop-consolidate.sh` released the mutex on every normal exit, before the
model had performed any of the consolidation edits the lock was meant to
guard. The lock had no chance to do its job.

## Decision

Split the protocols by suffix:

| Sidecar              | Owner                          | Protocol                           | TTL     |
|----------------------|--------------------------------|------------------------------------|---------|
| `<leaf>.marker`      | `post-edit-marker.sh`          | Advisory: plain truncate, symlink-guarded | 3600 s |
| `<leaf>.lock`        | `stop-consolidate.sh` / `mark.sh` | Strict mutex: `O_EXCL` create     | 600 s   |

- `<leaf>.marker` carries SESSION_ID + edited path; refreshed on every edit by
  the same session; reported (not clobbered) when a fresh peer marker exists;
  reclaimed when stale. Symlink-guarded (`[ ! -L "$marker" ]`) so a malicious
  repo cannot redirect the write.
- `<leaf>.lock` is the consolidation mutex. Created via `set -C` (`O_CREAT|O_EXCL`)
  with the holding session's SESSION_ID inside. Removed by
  `mark.sh <node> consolidated` once the model commits its edits, or by the
  abnormal-exit trap (`INT|TERM|HUP`) in `stop-consolidate.sh`.

`stop-consolidate.sh` no longer releases held mutexes on **normal** exit —
the trap is scoped to `INT TERM HUP` so the lock survives the hook return and
is handed to the model.

## Consequences

- ✅ Same-session consolidation under recent edits now works (the most common
  case in practice).
- ✅ Edits and consolidation runs no longer race on the same path.
- ✅ Symlink attack on the marker path is closed.
- ⚠️ A node may now have up to two sidecars present on disk simultaneously
  (`.marker` + `.lock`). `.gitignore` already covers `*.lock` and is extended
  to cover `*.marker`.
- ⚠️ `mark.sh consolidated` removes only `.lock`. The `.marker` lives by its
  own TTL — it is a bookkeeping artifact, not a coordination primitive.

Implementation lives in `templates/hooks/post-edit-marker.sh` (`.marker` write,
symlink guard, O_EXCL) and `templates/hooks/stop-consolidate.sh` (`trap`
scoped to abnormal exit only). The `.claude/` mirror is kept byte-identical.
Verified by `tests/inform-never-block.sh` (section C) and the rewritten
`tests/consolidate.sh` (H1 + H2 cases).
