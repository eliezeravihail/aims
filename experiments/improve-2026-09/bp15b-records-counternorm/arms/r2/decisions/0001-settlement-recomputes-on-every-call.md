# 0001 — a repeat settlement RECOMPUTES and overwrites; it is deliberately not idempotent

- Status: accepted

## What this looks like

`settle` writes `self._done[settlement_id]` but never reads it before computing. It looks like the
idempotency guard was forgotten — the store appears to be write-only and pointless. **It was not forgotten.**

## The doubt, and the decision

The industry-standard idempotency-key pattern (a repeat request replays the stored response) is what everyone
here expected, including us. We deliberately do **not** do it. A repeat `settle` recomputes from the arguments
it is given now, and overwrites the stored rows.

## Why (this rationale exists nowhere in the code)

Upstream issues **corrections**: a payee's share is fixed, a total is restated, a payee is removed after a
dispute. Settlement ids are stable across a correction — the corrected settlement carries the *same* id on
purpose, because the downstream ledger is **append-only and reconciles latest-wins**. Replaying the stored
split would keep paying the *pre-correction* numbers forever, and the ledger would reconcile against a figure
we never recomputed. Money already moved is reconciled downstream, not here; our job is to always state the
current truth for this id.

## Rejected alternative

- **Idempotency-key replay** (`if settlement_id in self._done: return self._done[...]`) — the obvious "fix".
  It was added once, in good faith, and froze three corrected settlements at their stale pre-correction split;
  the mismatch surfaced a week later in reconciliation. **Do not add this guard.**

## Consequence

`settle` must keep recomputing on every call. A new entry point that computes **without** paying must not be
built by adding a read-through cache to `settle`.
