# ADR-0027: Stop hook detects consolidation-report discrepancy across fires
Status: accepted
Date: 2026-06-11
Supersedes: —
Superseded by: —

## Context

aims relies on **awareness, not enforcement** (ADR-0020): the Stop hook
injects a consolidation prompt and asks the model to emit a single
reply-format line `===[aims: <msg>]===` (ADR-0021) summarising what it
did. The architecture review of 2026-06-11 flagged a structural gap:

> Missing: any feedback loop measuring whether injected context changes
> behavior. The system's whole bet is "awareness suffices," and it has
> one data point against (ADR-0023) and zero instrumentation for.

A live data point landed in the same session: across three consecutive
Stop fires the model replied `===[aims: queue drained]===` while the
inbox file still held 13 bullets. The reply was untrue; nothing in the
system noticed. The Stop hook simply re-fired with the same prompt — the
model had no signal that its previous claim had been wrong.

## Decision

`stop-consolidate.sh` now writes a **report snapshot** when it emits the
consolidation prompt. The snapshot lives at
`docs/memory/.last-report-snapshot` (gitignored) and records:

```
<N_DIRTY>
<N_INBOX_LINES>
<sha1 of inbox bytes + sorted dirty leaf paths>
<emit timestamp>
```

On the next Stop fire, the hook compares the current state hash against
the snapshot. If:

- a snapshot exists,
- it asked for non-trivial work (`PREV_N_DIRTY + PREV_N_INBOX > 0`), and
- the current state hash is **identical** to the snapshot,

then the prior turn emitted a drain-claim reply without changing
anything. The hook prepends a factual breadcrumb to the new prompt:

> [aims-memory] DISCREPANCY DETECTED (ADR-0027). The previous Stop hook
> fired with N dirty node(s) and M inbox bullet(s); a `===[aims: <msg>]===`
> report was emitted. State has NOT changed since: the same dirty set and
> the same inbox bytes are still present. The previous report did not
> match measured state. Do the work this turn before any reply: …

The prompt is also tightened: the drain-claim words (`queue drained`,
`nodes updated`, `inbox cleared`) are now **reserved** — emit them only
when measured state has actually changed.

This is still inform-never-block (ADR-0020): the hook does not refuse,
it names the discrepancy. The bet remains "awareness suffices", but
awareness is now grounded in a measurement rather than a hope.

## Consequences

- ✅ A false report is surfaced on the very next turn as a factual
  discrepancy, not silently re-tried. The model sees its own prior
  inconsistency explicitly.
- ✅ Cheap: one sha1 + a four-line file write per Stop emit. No new
  helper dependencies (sha1sum is POSIX-ish; absent on rare platforms,
  hash collapses to empty and detection silently degrades — acceptable).
- ⚠️ Detection is **per-Stop**, not per-reply. A model that lies once
  and the next fire happens to legitimately have the same state hash
  (e.g. an external session edited the same files) would be falsely
  flagged. In practice the snapshot also stores N_DIRTY and N_INBOX so
  a divergence is visible; the breadcrumb names exact numbers.
- ⚠️ The detection assumes the prior emit reached the model. If the
  Stop hook emitted but the harness dropped the block-JSON (e.g. a
  malformed `reason`), the next-fire breadcrumb will be misleading.
  Tracks 1+3 of `2026-06-11-aims-audit-fixes-master.md` close the
  known cases where this could happen (mutex protocol + JSON escaping).

## Pointers

- ADR-0009 — in-band consolidation protocol the snapshot guards.
- ADR-0020 — inform-never-block invariant the discrepancy breadcrumb
  obeys (factual, not imperative).
- ADR-0021 — the `===[aims: <msg>]===` reply-format whose accuracy this
  ADR makes verifiable.
- ADR-0026 — Stop-hook `decision: block` carve-out the snapshot rides
  on; the discrepancy breadcrumb is prepended to the same `reason`
  field.
- `templates/hooks/stop-consolidate.sh` — the snapshot read/write
  lives there.
- `tests/consolidate.sh` — smoke test for the discrepancy path.
