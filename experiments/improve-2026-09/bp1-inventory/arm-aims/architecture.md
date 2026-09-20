---
title: "architecture"
date: 2026-09-20
---
## Boundaries & seams
- One module, `inventory.py`, with one public class `Inventory` and one public exception
  `InsufficientStock`. The public API (`__init__`, `add_stock`, `available`, `reserve`, `release`)
  is the only seam; everything else (`_added`, `_reservations`, `_reserved`, `_new_id`,
  `_Reservation`) is internal representation, free to change.
- Stock quantities and sku keys cross the seam as the language's own `int`/`str`; reservation ids
  cross as opaque `str`. No internal type is exposed.

## Invariants
- **Availability rule (the one owned invariant):** `available(sku) == added(sku) - reserved(sku)`,
  where `reserved(sku)` is the sum of qty over outstanding reservations for that sku. It is *derived*
  on read, never stored — so no availability number can drift from the reservation ledger.
- R1 availability is never negative and never exceeds added-minus-reserved (structural: reserve only
  records a hold that fits; release only removes a hold; added only grows).
- R2 a reservation holds exactly its qty until its id leaves the ledger.
- R3 reservation ids are unique and opaque.
- R4 reserve is all-or-nothing: it validates against availability before recording, so a rejected
  reserve (bad qty or insufficient stock) leaves state untouched.

## Likely change axes
- Deliberately *not* designed for speculative change axes (YAGNI): only stage-1 behavior is built.
- The single ground-truth representation (added totals + reservation ledger, availability derived)
  is the seam a later requirement would extend behind, without reopening `available`'s rule — but no
  such extension is built or assumed now.
