# ADR-0030: Retire the strict consolidation lock; advisory markers only
Status: proposed
Date: 2026-07-15
Supersedes: ADR-0024 (strict-`.lock` half; the advisory `.marker` half stands)
Superseded by: —

## Context

Cross-session coordination on memory nodes went through three protocol
iterations: in-frontmatter claims (ADR-0018), sidecar `.lock` files
(ADR-0019), and a split into strict `.lock` + advisory `.marker`
(ADR-0024). The strict half required O_EXCL claims, TTL-based stale
reaping, ownership checks, and an abnormal-exit release trap in
`stop-consolidate.sh` (~50 lines), plus lock cleanup in `mark.sh` —
for a tool that in practice runs single-session. Meanwhile ADR-0028
changed the consolidation action to delta-append, shrinking the worst
uncoordinated outcome from "two full rewrites race" to "two sessions
append lines".

## Decision

We will remove the strict `.lock` protocol entirely. `stop-consolidate.sh`
hands every dirty node to the model without claiming; `mark.sh
consolidated` no longer removes lock files (none exist). The
post-edit-marker's **advisory `.marker`** — stamp + factual
"possible concurrent edit" note, ask-the-user convention — remains the
only cross-session signal, unchanged.

## Consequences

- ✅ ~55 lines of mutex machinery gone; no TTL tuning, no stale-lock
  recovery states, no trap semantics to preserve.
- ✅ One protocol lineage (0018→0019→0024 strict) closed instead of
  maintained as dead weight.
- ⚠️ Two truly concurrent sessions may both consolidate the same node;
  last write wins. Accepted: both writes are valid delta appends, the
  advisory marker surfaces the situation, and the ADR-0027 snapshot
  flags an unexpanded queue on the next fire.
- 🔒 Rules out any hook refusing an edit for coordination reasons
  (re-affirming ADR-0020).

## Alternatives considered

- **Keep the lock behind an env flag (dormant)**: rejected — dead
  protocol code is its own staleness liability; nothing would exercise
  it.
- **Git-level coordination (branch per session)**: rejected — out of
  scope for a hooks-only plugin.

## Verification

- `grep -rn '\.lock' templates/hooks/ templates/memory/` → no
  consolidation-mutex hits (only the unrelated `.planning-lock`
  breadcrumbs in session-start).
- `bash tests/consolidate.sh` — passes with no lock scaffolding.
