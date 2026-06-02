# ADR-0019: Sidecar `.lock` files for memory nodes (supersedes 0018)
Status: proposed
Date: 2026-06-01
Supersedes: docs/adr/0018-multi-session-consolidation-claims.md
Superseded by: docs/adr/0020-hooks-inform-never-block.md (repurposed: sidecar `.lock` is now advisory, not a hard mutex)

## Context

ADR-0018 added a `consolidating_by: <sid>@<unix-ts>` frontmatter field as
the multi-session mutex on memory nodes. Two design problems surfaced
once it landed:

1. **Granularity drift.** The roadmap pushes node-count toward
   file-count; a per-node mutex baked into every frontmatter would
   clutter every leaf with mutex bookkeeping that is purely a runtime
   concern.
2. **State in the wrong place.** The claim leaks runtime
   coordination into the data schema. `mark.sh` already owns three
   privileged frontmatter fields (`dirty`, `last_touched`,
   `last_consolidated`); we resisted growing that set further only to
   then immediately add a fourth runtime field.

User's preferred mental model: **like `git` lock files.** Drop a sidecar
the moment you intend to touch a node, remove it when done. The
existence of the file IS the signal. And: any other write to a locked
node should be **refused with a clear error**, not silently overwritten.

## Decision

Replace `consolidating_by:` with a **sidecar lockfile per node**:

```
docs/memory/<tag>/<leaf>.lock      # co-located with <leaf>.md
```

Properties:

- **Acquire** atomically via `set -C` (bash `noclobber` →
  `open(O_CREAT|O_EXCL)`). Body = `<session_id>\n`. No flock, no TOCTOU.
- **Release** via `mark.sh <node> consolidated` (the normal success
  path) or via the `trap ... EXIT` in `stop-consolidate.sh` (abnormal
  exit between claim and `mark.sh`).
- **Stale-lock TTL.** A lockfile whose mtime is older than
  `AIMS_LOCK_TTL_SEC` (default 600s) is abandoned — any session may
  remove it and re-acquire. mtime alone drives detection; no body
  parsing.
- **`pre-write` enforcement.** When Edit/Write targets a
  `docs/memory/<tag>/<leaf>.md` and `<leaf>.lock` exists with a
  different session_id and a fresh mtime, the hook exits 2 with a
  message naming the owning sid and the exact `rm` command needed to
  recover. Own-session locks pass through (so the consolidation pass
  itself isn't blocked).
- `.gitignore` carries a glob: `docs/memory/**/*.lock`.

### Bonus fix in the same patch

`pre-write.sh` previously compared `target` against a relative pattern
(`docs/plans/*.md`). Claude Code passes absolute paths
(`/home/.../docs/plans/...`), so the planning-lock carve-out for
`docs/plans/` silently missed and even legitimate plan-draft writes
under `/plan` were blocked. The patch normalizes `target` against
`git rev-parse --show-toplevel` once (mirroring what the marker hook
already does) and uses the relative form for both the planning carve-out
and the new memory-node lock check.

## Consequences

- ✅ No more mutex state in node frontmatter; schema stays focused on
  content + provenance.
- ✅ Lock visibility matches `git`: `ls docs/memory/<tag>/` shows you who
  is editing what right now.
- ✅ Pre-write enforcement gives ad-hoc Edit/Write on a memory node the
  same protection as Stop-driven consolidation — even the user typing
  `edit docs/memory/foo/bar.md` is gated.
- ✅ No need for `flock`; portability up.
- ✅ Trap-based release tolerates crashes; TTL covers the rest.
- ⚠️ A node body that mid-edit gets force-removed by another session
  (after TTL) could in theory be clobbered. Acceptable: 10 min is far
  longer than any healthy consolidation.
- ⚠️ The pre-write check assumes Claude Code always passes
  `session_id` in the JSON payload. If a future harness drops the
  field, all locks look like "different session" and ad-hoc edits get
  blocked. The error message tells the user exactly how to override
  (`rm <lockfile>`), so the failure mode is loud but recoverable.

## Migration from ADR-0018

- Strip the empty `consolidating_by:` field from frontmatters that ended
  up with it during the 0018 round (3 nodes: `memory/helpers`,
  `memory/phase-a-marker`, `memory/phase-b-consolidation`).
- `mark.sh consolidated` no longer touches that field; it now
  `rm -f`s the sidecar.
- The `claim_one`/`flock` block in `stop-consolidate.sh` is replaced
  by `try_claim` + trap.
- `new-node.sh` scaffold drops the field.

## Verification

- `bash -n` on all hooks + helpers, both `templates/` and `.claude/`.
- Smoke: foreign-session lock on `helpers.md` → pre-write exits 2.
- Smoke: own-session lock on `helpers.md` → pre-write exits 0.
- Smoke: two Stop hook invocations with different SIDs against the same
  dirty leaf — second skips it; after `mark.sh consolidated` runs, a
  third reclaims.
- Smoke: lock with mtime 20 min old → next claim treats it as abandoned.
- `doctor.sh` / `lint.sh` clean post-migration.

## Alternatives considered

- **Per-tag lock** (`docs/memory/<tag>/.tag.lock`): less per-file state,
  but two disjoint nodes in the same tag would serialize for no gain.
- **Single global lock**: simplest, but two sessions editing disjoint
  nodes serialize unnecessarily.
- **Keep `consolidating_by:` but move it to a separate `_state.yml`**:
  centralizes state but adds a parser nobody asked for.

## Pointers

- `templates/hooks/stop-consolidate.sh` — `try_claim` + trap.
- `templates/hooks/pre-write.sh` — sidecar enforcement.
- `templates/memory/mark.sh` — `rm -f "${node%.md}.lock"`.
- `docs/adr/0018-multi-session-consolidation-claims.md` — superseded.
