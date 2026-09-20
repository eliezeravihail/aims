# BP1 stage-by-stage log (correctness gate + structure)

## Stage 1 — reserve / release / available
- **Correctness gate:** aims **9/9**, plain **9/9** — both CLEAR on the hidden stage-1 tests.
- **Structure (the divergence to watch):**
  - **aims:** availability is **derived, never stored** — `available(sku) = added(sku) − reserved(sku)`,
    computed on read; ground facts are `_added` (monotonic) and a reservation ledger `_reservations[id]`.
    One owner (`Inventory.available`). Its review explicitly rejected a stored per-sku reserved counter as a
    second copy of the availability fact (drift risk) with no stage-1 force.
  - **plain:** availability is **stored** — a `_available[sku]` dict kept in sync with a `_reservations`
    dict; reserve/release mutate both. Two quantities held consistent by matched decrement/increment.
- **Prediction for stage 2 (expiry, time-dependent):** the aims *derived* design should absorb expiry by
  filtering expired reservations at `now` inside the single `available` owner. The plain *stored* counter
  cannot be eagerly updated on expiry (expiry depends on the query-time `now`), so it must either be reopened
  toward a derived model or grow a lazy-sweep path — a likely reopened-owner event. This is the trajectory
  hypothesis; stage 2 tests it.
