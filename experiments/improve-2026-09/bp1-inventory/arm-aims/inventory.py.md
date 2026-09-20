---
title: "inventory.py"
date: 2026-09-20
hash: "sha256:c6a8556a729d6226d3b62732ba841996237cbc6f6887662589c19c7f169cd4e9"
---
## Insights
- The load-bearing invariant is the availability rule, and its single owner is `Inventory.available`.
  Availability is **derived** — `added(sku) - reserved(sku)` — and never stored as a mutable counter.
  This is what makes R1/R2/R4 structural rather than defended: there is no second copy of "available"
  that could disagree with the reservation ledger.
- Idempotent release (R2 tail / unknown-id no-op) is the reason a reservation must be a first-class
  ledger entry keyed by id, not a bare decrement of a counter: a counter cannot tell whether an id was
  already released, so double-release would inflate availability above added stock (violating R1). The
  ledger + `dict.pop(id, None)` gives idempotency for free.

## Decisions
- Ground truth is two facts only: `_added[sku]` (total added, monotonic) and `_reservations[id] ->
  _Reservation(sku, qty)` (the outstanding-holds ledger). `available` and `_reserved` are pure
  derivations; nothing else stores an availability number. Owner of the availability rule:
  `Inventory.available` (with `_reserved` naming the "outstanding for sku" term of the rule).
- `reserve` validates (qty > 0, then qty <= available) **before** any mutation, then records — giving
  R4 all-or-nothing on both the ValueError and the InsufficientStock path.
- `add_stock` and `reserve` reject qty <= 0 at the boundary with `ValueError` (fail fast); the card
  states add qty as > 0, treated here as a precondition.
- Reservation ids are `uuid4().hex` (opaque, R3) with a regeneration loop guarding against collision
  so uniqueness is structural, not merely probabilistic.

## Discussions
- Availability could be kept as an O(1) per-sku counter incremented/decremented on reserve/release
  instead of summed over the ledger. Rejected: that reintroduces a second stored copy of the
  availability fact that must be kept in sync with the ledger — two owners, drift risk — to buy a
  performance win no stage-1 requirement asks for. The derived form keeps one owner; `_reserved`'s
  O(n-reservations) scan is acceptable absent any performance requirement.
- `_Reservation` is a 2-field NamedTuple rather than a plain tuple: it costs nothing and names the
  `(sku, qty)` pair as the concept it is. It deliberately owns no behavior/rule — the availability
  rule lives in `Inventory`, not in the reservation — so it is not an anemic-model smell, just a typed
  record. A bare tuple would have been equally correct; the named form was kept for readability only.
