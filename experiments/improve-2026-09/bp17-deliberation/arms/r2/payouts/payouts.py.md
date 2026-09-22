# payouts.py

## Insights
- `Ledger` looks like an ordinary store with a list in it. It is an **append-only event log**: its
  `entries()` is consumed by the audit exporter as an outward feed. That fact lives outside this module and
  is the reason for `decisions/0001`.
- `Ledger.reverse` negates the **stored** payouts rather than re-running `_allocate` on a negative total.
  That is not a style preference: `_allocate` floors, so re-deriving 100c over three equal shares as -100c
  gives -32/-34/-34 against the original 34/33/33 — a net of +2/-1/-1, not zero. Only mirroring the amounts
  that were actually booked makes the pair net to zero per payee.

## Decisions
- Undoing a settlement **appends a linked reversal**; the original entry is never mutated or removed —
  `decisions/0001`. The simpler mutate-in-place design was argued for at length and rejected.
- The link is a `reverses` field on `Settlement`, defaulting to `None`, so the reversal is an ordinary entry
  on the same feed and existing three-argument construction keeps working. A reversal id is the original's
  plus `:reversal`, which keeps `get(id)` usable for both halves of the pair.
- `reverse` refuses a second reversal of the same settlement (`ValueError`). Reversing twice would restate
  the net as the negative of the original and collide on the derived id, so it is a caller error, not an
  undo of the undo.

## Discussions
- We debated giving `Settlement` a `status` field to make `get(id)` self-contained. Dropped for the same
  reason as mutation: the exporter has already emitted the entry, so a later status change is a rewrite of
  an exported event. Callers needing a net position fold the reversal themselves; we accepted that cost.
