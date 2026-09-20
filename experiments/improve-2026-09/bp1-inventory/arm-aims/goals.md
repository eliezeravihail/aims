---
title: "goals"
date: 2026-09-20
---
## Primary goal
An in-memory inventory reservation service (`inventory.py`, one module, Python 3 stdlib only):
callers add stock for a sku, reserve units (receiving an opaque id), check what is available, and
release a reservation to return its units. The service guarantees that availability always reflects
stock added minus units currently held by outstanding reservations.

## Use scenarios
- Add 10 units of a sku, reserve 4, observe 6 available; release the reservation, observe 10 again.
- Reserve exactly the available quantity (down to 0); a further reserve of even 1 unit is rejected
  with `InsufficientStock`, and nothing changes.
- Release an unknown or already-released id — a harmless no-op (idempotent), so a caller can retry.

## Non-goals
- No persistence, no concurrency/threading guarantees, no networking — purely in-memory, single-threaded.
- No expiry, confirmation, or partial reservation semantics in this stage (only add/available/reserve/release).
- No removal or decrement of added stock; `add_stock` only increases the total for a sku.
