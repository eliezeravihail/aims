# payouts.py

## Insights
- `Ledger` looks like an ordinary store with a list in it. It is an **append-only event log**: its
  `entries()` is consumed by the audit exporter as an outward feed. That fact lives outside this module and
  is the reason for `decisions/0001`.

## Decisions
- Undoing a settlement **appends a linked reversal**; the original entry is never mutated or removed —
  `decisions/0001`. The simpler mutate-in-place design was argued for at length and rejected.

## Discussions
- We debated giving `Settlement` a `status` field to make `get(id)` self-contained. Dropped for the same
  reason as mutation: the exporter has already emitted the entry, so a later status change is a rewrite of
  an exported event. Callers needing a net position fold the reversal themselves; we accepted that cost.
