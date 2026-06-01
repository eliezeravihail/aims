# ADR-0018: Multi-session-safe consolidation via in-frontmatter claims
Status: superseded by 0019
Date: 2026-06-01
Supersedes: —
Superseded by: docs/adr/0019-sidecar-lockfiles-for-memory-nodes.md

## Context

ADR-0009 made the Stop hook inject a consolidation prompt that the active
Claude Code session executes in-band. The design implicitly assumed **one
session per project**: any dirty node found at Stop time belongs to "the"
session that produced the edit. In practice users open multiple sessions
against the same repo (one editing, one reading a log, etc). The shared
`docs/memory/*/*.md` frontmatter is the only coordination point. The
failure mode (reported by users):

1. Session A edits source → `post-edit-marker` flips matching nodes
   `dirty: true`.
2. Session B (passive — e.g. "read this log") hits its Stop hook. It sees
   the dirty nodes, follows the injected instruction, and starts editing
   the node bodies.
3. Session A also hits its Stop hook, sees the same dirty nodes, and
   starts its own edits in parallel.
4. The two sessions produce conflicting bodies and clobber each other's
   work; `mark.sh consolidated` runs twice on the same node from two
   sessions, with no detection that the work was duplicated.

A passive session **picking up consolidation** is desirable (work isn't
wasted). The bug is concurrent writers on the same node — pure data race.

## Decision

We add a single new optional frontmatter field, `consolidating_by`, which
records a one-process claim while a session is mid-consolidation:

```
consolidating_by: <session_id>@<unix-timestamp>
```

- `<session_id>` is `payload.session_id` from the Stop hook input;
  fallback `default` when missing.
- `<unix-timestamp>` is `date -u +%s` at claim time.
- Empty / missing field = unclaimed.

The Stop hook (`stop-consolidate.sh`) filters its `DIRTY` list through a
**claim check** before building the consolidation prompt:

- If `consolidating_by` is empty or stale (age ≥ `AIMS_CLAIM_TTL_SEC`,
  default 600s), the current session claims it via
  `fm_set <leaf> consolidating_by <sid>@<now>` and includes the node.
- If `consolidating_by` names **another** session and is fresh, the node
  is skipped this turn — the other session is on it. The throttle state
  is **not** bumped for nodes we don't claim, so the next Stop hook will
  re-evaluate.
- If `consolidating_by` is our own session_id (renewal / retry), we
  refresh the timestamp and keep the node.

The whole claim phase runs under `flock -n` on `.claude/memory/.claim-lock`
so two Stop hooks racing in sub-second windows can't double-claim the same
node. When `flock` is unavailable the loop degrades to a best-effort
TOCTOU race window — better than nothing on systems without it.

`mark.sh <node> consolidated` clears the claim alongside the existing
`dirty: false` + timestamp bumps — so the node is immediately available
for the next legitimate consolidation cycle.

`new-node.sh` scaffolds the field as empty, making the convention
discoverable in every newly-created node.

## Consequences

- ✅ Two concurrent sessions can co-exist on the same project. A passive
  session can usefully consolidate dirty nodes left by an editor; the
  editor session sees them already claimed and skips them.
- ✅ Stale claims (crashed sessions, killed Claude Code processes) expire
  after `CLAIM_TTL` (default 10 minutes). A node never gets permanently
  stuck.
- ✅ Backwards compatible: nodes that don't carry the field are treated as
  unclaimed; first session to touch them adds the field.
- ✅ No new external state files beyond `.claude/memory/.claim-lock`
  (lockfile only, byte-empty).
- ⚠️ `CLAIM_TTL` is a guess: too short → live sessions get their work
  stolen mid-flight; too long → a real crash blocks for too long. The
  default (10 min) is more generous than a typical consolidation pass.
  Configurable via `AIMS_CLAIM_TTL_SEC`.
- ⚠️ Race on the **boundary**: a session finishing its edit and calling
  `mark.sh consolidated` could race with another session claiming the now-
  released node. Acceptable: the second consolidation would be a no-op
  because `dirty` is already `false`; the marker would no-op too.
- 🔒 Rules out "all sessions try to consolidate every dirty node"
  (silent data races) and "only the originating session consolidates"
  (wasted opportunity for passive sessions).

## Alternatives considered

- **Tag dirty marks with the originating session_id**; only the matching
  session consolidates. Rejected by user feedback: a passive read-only
  session usefully picking up consolidation work is a *feature*, not a
  bug. The fix is mutual exclusion, not partitioning.
- **Single global consolidation lock (no per-node).** Rejected: two
  sessions editing disjoint dirty nodes shouldn't serialize on each other.
- **External lockfile per node.** Rejected: spreads state across both the
  frontmatter and the filesystem; the field IS the natural place for the
  claim (visible in the node, lives with the data).

## Verification

- `bash -n templates/hooks/stop-consolidate.sh && bash -n .claude/hooks/stop-consolidate.sh`
  → clean. `md5sum` pair identical.
- `new-node.sh tmp/x module foo.py` scaffolds a leaf containing
  `consolidating_by:` (empty value).
- `mark.sh <node> consolidated` clears `consolidating_by` along with
  `dirty`/timestamps.
- Race smoke: prime one node dirty, run stop-consolidate as session A,
  observe `consolidating_by: A@<ts>`. Run again as B → field unchanged.
  Run `mark.sh consolidated` (releasing) and re-dirty → B can now claim.
