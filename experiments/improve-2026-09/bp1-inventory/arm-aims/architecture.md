---
title: "architecture"
date: 2026-09-20
---
## Boundaries & seams
- One module, `inventory.py`, with one public class `Inventory` and one public exception
  `InsufficientStock`. The public API (`__init__`, `add_stock`, `available`, `reserve`,
  `reserve_up_to`, `confirm`, `release`) is the only seam; everything else (`_added`,
  `_reservations`, `_reserved`, `_record`, `_new_id`, `_Reservation`) is internal representation,
  free to change. A single internal `_record(sku, qty, expiry)` is the one place a hold enters the
  ledger — both `reserve` (after its availability check) and `reserve_up_to` commit through it.
- Stock quantities and sku keys cross the seam as the language's own `int`/`str`; reservation ids
  cross as opaque `str`; time (`now`, `ttl_seconds`) crosses as the language's own `float`. No internal
  type is exposed.

## Invariants
- **Availability rule (the one owned invariant):** `available(sku, now) == added(sku) - reserved(sku,
  now)`, where `reserved(sku, now)` is the sum of qty over the *live* reservations for that sku (a hold
  with `expiry <= now`, or after release, contributes zero). It is *derived* on read, never stored — so
  no availability number can drift from the reservation ledger. Time is injected via `now`; no real
  clock is read. (Stage 1 was the `now`-independent special case; the rule generalized without moving
  its owner.)
- R1 availability is never negative and never exceeds added-minus-reserved (structural: reserve only
  records a hold that fits; release only removes a hold; added only grows).
- R2 a reservation holds exactly its qty until its id leaves the ledger *or* its expiry is reached.
- R3 reservation ids are unique and opaque.
- R4 reserve is all-or-nothing: it validates against availability before recording, so a rejected
  reserve (bad qty or insufficient stock) leaves state untouched.
- R5 at time `now`, a reservation with `expiry <= now` holds zero units (expiry frees units).
- R6 results are deterministic in the injected `now`; no wall clock is read.
- R7 releasing an already-expired reservation is a no-op — it already held zero units at `now`, so
  removing it cannot double-count them.
- R8 a confirmed reservation holds its units permanently; expiry no longer applies, even past a ttl
  it once had. "Permanent" reuses the `expiry is None` representation — `confirm` clears the ledger
  entry's expiry (no new state), so `_reserved` counts it at every `now`. Confirming an unknown or
  released id is a no-op.
- R9 `reserve_up_to` never over-reserves: it records `min(qty, available(sku, now))` units, so the
  hold always fits (R1) and the returned `reserved_qty` is that minimum. It never raises
  InsufficientStock; when nothing is available it records a real 0-unit hold and returns qty 0.

## Likely change axes
- Deliberately *not* designed for speculative change axes (YAGNI): only the built stages' behavior
  exists.
- The single ground-truth representation (added totals + reservation ledger, availability derived) is
  the seam a later requirement extends behind, without reopening `available`'s rule. Stage 2 (expiry)
  did exactly this: the ledger entry gained an `expiry` field and the derivations gained a `now`
  parameter, while `available == added - reserved` and its single owner stayed put — no parallel
  filter, no stored expired-state.
- Stage 3 (confirm + best-effort reserve) extended the same seam again without reopening the
  availability rule: `confirm` clears a hold's `expiry` (reusing the `expiry is None` = permanent
  representation, no new state); `reserve_up_to` reads the `available` owner, takes `min(qty, avail)`,
  and commits through the extracted `_record` ledger-write seam. `available == added - reserved` and
  its owner were untouched.
