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

## Stage 2 — reservation expiry (TTL, injected clock)
- **Correctness gate:** aims **14/14**, plain **14/14** — both CLEAR (stage-1 + stage-2 hidden tests).
- **Trajectory measure (the decisive one — reopen vs extend):**
  - **aims: EXTENDED, 0 reopens.** `available = added − reserved` (the owner) **unchanged**; only the
    `reserved` term became time-aware (`_reserved(sku, now)` counts a hold while `expiry is None or expiry
    > now`); the ledger entry gained an `expiry` field. ~18–20 functional lines. The **fresh session read
    the co-located record**, which explicitly named this seam ("extend behind, without reopening
    `available`'s rule"), and extended exactly there — a Q2 continuity signal.
  - **plain: REOPENED (1).** Confronted with time-dependent expiry, it **rewrote its model** — the stage-1
    stored `_available` counter → a derived `_stock` + held-at-`now` computation, rewriting `__init__`,
    `add_stock`, `available`, `reserve`, `release` (~45 functional lines). It reached the *same* derived
    design the aims arm started with, but paid a model reopen to get there.
  - Raw diff sizes are similar (aims +56/−19, plain +51/−22) because adding expiry touches reserve/
    available/release either way — but the **reopened-owner count** separates them cleanly: **aims 0, plain 1**.
- **Reading:** the paper's "strong models refactor deeply" holds — the plain arm recovered a good design.
  aims' edge here is that its stage-1 derived design (and the record naming the seam) **avoided the reopen**.
  Stage 3 tests whether this compounds or the arms re-converge.
