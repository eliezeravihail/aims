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
- (stage 2) Reserve 4 with `ttl_seconds=5` at `now=0`: 6 available while the hold is live, and 10
  available at `now>=5` — the units return automatically at the injected expiry, with no release call.
- (stage 3) Reserve 4 with `ttl_seconds=5` at `now=0`, then `confirm` the id: the hold is now
  permanent — 6 still available at `now=100`, past the ttl it once had. Confirming an unknown or
  released id is a harmless no-op.
- (stage 3) `reserve_up_to(sku, 10)` when only 2 are available: returns `(id, 2)` and holds those 2;
  when nothing is available, returns `(id, 0)` — a real (releasable/confirmable) id holding 0 units.

## Non-goals
- No persistence, no concurrency/threading guarantees, no networking — purely in-memory, single-threaded.
- Time is **injected** (`now`), not read from a real clock — no background timer sweeps expiries.
  *(The former "no confirmation or partial reservation semantics" non-goal is superseded by stage 3,
  which adds `confirm` and `reserve_up_to`.)*
- No removal or decrement of added stock; `add_stock` only increases the total for a sku.
