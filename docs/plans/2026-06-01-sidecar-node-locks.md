---
Status: completed
Date: 2026-06-01
Slug: sidecar-node-locks
Supersedes: docs/adr/0018-multi-session-consolidation-claims.md
---

# Sidecar `.lock` files for memory nodes (git-style mutex)

## Problem (refined from ADR-0018)

ADR-0018 introduced a `consolidating_by:` frontmatter field on every node
as a multi-session mutex. Two issues raised in design review:

1. **Granularity:** in a future where node-count ≈ file-count, per-node
   frontmatter claims clutter every leaf with mutex bookkeeping.
2. **Wrong place:** the claim lives *inside the data* (frontmatter) — a
   runtime concern leaks into the schema.

The user's preferred mental model: **like `git`** — drop a sidecar `.lock`
file in the containing directory the moment a session intends to touch a
node, remove it when done. The presence of the lock is itself the signal;
no in-data state needed. And: writes to a locked node must be **blocked
and surfaced to the user**, not silently swallowed.

## Decision

Replace the `consolidating_by:` frontmatter mechanism with **sidecar
lockfiles**:

```
docs/memory/<tag>/<leaf>.lock
```

(co-located with `<leaf>.md` — one lockfile per node).

### Acquire (atomic, O_EXCL)

```bash
LOCK="${leaf%.md}.lock"
if (set -C; printf '%s\n' "$SESSION_ID" > "$LOCK") 2>/dev/null; then
  # got it
else
  # someone else owns it; back off
fi
```

`set -C` is bash's `noclobber` — equivalent to `open(O_CREAT|O_EXCL)`.
No flock, no TOCTOU window. The file body holds the owning session_id
(useful for the pre-write check below).

### Release

On normal completion of `mark.sh <node> consolidated`:

```bash
rm -f "${node%.md}.lock"
```

On abnormal exit, the Stop hook installs `trap "rm -f $LOCK" EXIT` while
it holds the lock — bash auto-cleans on script exit.

### Stale-lock TTL

A lockfile older than `AIMS_LOCK_TTL_SEC` (default 600s) is abandoned —
any session may remove it and re-acquire. mtime is the signal; no body
parsing needed.

```bash
if [ -e "$LOCK" ] && find "$LOCK" -mmin +10 -print | grep -q .; then
  rm -f "$LOCK"
fi
```

## Touchpoints

### 1. `templates/hooks/stop-consolidate.sh`

Replace the entire "Multi-session claim filter" block:
- For each dirty leaf, attempt O_EXCL lock create with current session_id.
- Locked-out leaves are dropped from the consolidation prompt this turn.
- `trap "rm -f ..." EXIT` ensures release on any exit path.

### 2. `templates/memory/mark.sh consolidated`

Remove the `fm_set consolidating_by ""` line. Add:
```bash
rm -f "${node%.md}.lock"
```

### 3. `templates/memory/new-node.sh`

Drop the `consolidating_by:` field from the scaffold (no longer needed).

### 4. `templates/hooks/pre-write.sh` — **new responsibility**

Before allowing any `Edit/Write` to a `docs/memory/<tag>/<leaf>.md` path:
- Compute `${target%.md}.lock`.
- If lockfile exists, read its session_id.
- If the lock is held by a **different** session and fresh (mtime within
  TTL), exit 2 with stderr:
  ```
  [aims] Memory node "<leaf>" is currently locked by another session
         (sid=<owner>). Refusing this edit to prevent clobbering.
         If the other session has crashed:  rm <lockfile>
         Then retry the edit.
  ```
  This is the "alert and ask" — the model surfaces it; the user decides
  whether to override (manual `rm` of the lock) or wait.
- If the lock is held by *our* session (we're inside our own
  consolidation pass), allow.
- If no lock or lock is stale (older than TTL), allow.

This **broadens the safety net**: even an ad-hoc Edit on a memory node
(not driven by stop-consolidate) is guarded against concurrent writers.

Note (separate bug surfaced during this very planning session): the
existing planning-lock carve-out in `pre-write.sh` matches `docs/plans/*.md`
as a relative pattern but Claude Code passes absolute paths
(`/home/user/aims/docs/plans/...`). The carve-out silently misses on
absolute paths. **Fix in the same commit:** normalize the path against
`git rev-parse --show-toplevel` (the marker hook already does this; mirror
that logic) before the `case` statement.

### 5. `.gitignore`

Replace the per-design entry with a glob:
```
docs/memory/**/*.lock
```

### 6. ADR ledger

- `docs/adr/0018-multi-session-consolidation-claims.md` → flip
  `Status: proposed` → `Status: superseded by 0019`.
- New `docs/adr/0019-sidecar-lockfiles-for-memory-nodes.md`.
- Update `docs/adr/README.md` row 0018 (superseded) + new row 0019.

### 7. Memory nodes

Already-touched nodes from the ADR-0018 commit (`memory/helpers`,
`memory/phase-a-marker`, `memory/phase-b-consolidation`) need their body
sections updated:
- Strike the `consolidating_by` references.
- Reference ADR-0019 instead.
- Note the pre-write hook's new "refuse edit on locked node" duty in
  `hooks/pre-write.md`.

Also drop the now-empty `consolidating_by:` field that ended up in the
frontmatter of those three nodes during the ADR-0018 round.

## Open design questions

1. **Lock granularity** — chosen: **per-leaf**. The user explicitly said
   "the branch being worked on" earlier; per-leaf is finer than that.
   Per-tag would mean `docs/memory/<tag>/.tag.lock` and would
   over-serialize when two sessions touch disjoint nodes in the same tag
   (e.g. `memory/helpers` vs `memory/phase-a-marker`). Per-leaf is the
   git mental model the user landed on ("נעילה בעת שינויים").
2. **Lock content** — `<session_id>\n` is enough for the pre-write hook
   to compare against its own session_id. No timestamp inside the file —
   we use mtime for staleness. Simpler, harder to drift.
3. **TTL value** — keep 600s (10 min). Same value as ADR-0018; long
   enough that a real consolidation finishes, short enough that a crashed
   session unblocks in a meaningful window.
4. **`/plan` integration** — out of scope for this plan. `/plan` could
   later acquire locks for the leaves it intends to modify during Phase 4
   (implementation). For now, the lock mechanism is hook-driven only.
5. **Pre-write SESSION_ID source** — pre-write reads `tool_input.file_path`
   today; the JSON payload Claude Code sends also includes `session_id` at
   the top level. We extract it the same way `stop-consolidate.sh` does.

## Verification

- `bash -n templates/hooks/*.sh && bash -n templates/memory/*.sh` clean.
- `md5sum` pair-identity between `templates/` and `.claude/` copies.
- Smoke 1 (`pre-write` refuses locked node): create
  `docs/memory/memory/helpers.lock` with content `other-sid`, run the
  pre-write hook with a JSON payload editing `docs/memory/memory/helpers.md`.
  Expect exit 2 + stderr mentioning "locked by another session".
- Smoke 2 (`pre-write` allows own lock): same as above but lock body
  contains the same `SESSION_ID` that the payload announces. Expect exit 0.
- Smoke 3 (race): two `stop-consolidate.sh` runs in sequence with two
  different SESSION_IDs against the same dirty leaf — the second sees the
  lock and drops the leaf from its prompt. After `mark.sh consolidated`,
  a third run can re-acquire.
- Smoke 4 (stale): create lock with `touch -d "20 minutes ago"`; the next
  consolidation run treats it as abandoned and reclaims.
- Doctor / lint clean afterward.

## Rollout

Single commit ("memory: replace consolidating_by with sidecar .lock files")
+ ADR-0019 + ADR-0018 supersedure + node body refreshes + .gitignore
update + the absolute-path normalization patch in `pre-write.sh`. No data
migration: the three nodes that still carry `consolidating_by: ` from the
ADR-0018 round are hand-edited in the same commit to drop the field.

## Out of scope

- Cross-machine locks (NFS etc.) — `O_EXCL` semantics there are infamous;
  aims is single-host today.
- `/plan` acquiring locks during Phase 4 — separate decision once this
  lands.
- Lock contention UX in the prompt hook (any prompt-time visibility
  of "node is locked"). Today's surface is: pre-write rejects with a
  message; that's enough.
