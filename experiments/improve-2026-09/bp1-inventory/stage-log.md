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

## Stage 3 — confirm (permanent) + reserve_up_to (partial)
- **Correctness gate:** aims **21/21**, plain **21/21** — both CLEAR (all three stages' hidden tests).
- **Trajectory measure:**
  - **aims: EXTENDED, 0 reopens.** `confirm` reuses the existing permanence representation (`expiry is
    None`) — explicitly rejecting a `confirmed` flag as a second owner of permanence; `reserve_up_to` reads
    `available` and takes a min; a behavior-preserving `_record` extraction shares the single ledger-write
    between `reserve` and `reserve_up_to`. Availability and expiry owners untouched. +45/−4 diff.
  - **plain: EXTENDED, 0 reopens.** Added `confirm` (set expiry None) + `reserve_up_to` (reuse
    `available`/`_held`) as two new methods; +36/−0, no existing method changed. After its stage-2 model
    rewrite, stage 3 rides the derived model cleanly.
  - Both arms independently modelled confirm as "permanent = expiry None" (no flag-cram) — concept-fit
    parity at stage 3.

## Totals (the outcome-first reading)
| | correctness (all stages) | reopened-owner events | module lines s1/s2/s3 | tokens (Σ) | wall-clock (Σ) |
|---|---|---|---|---|---|
| **aims** | 21/21 ✓ | **0** | 100 / 137 / 178 | ~258k | ~11.2 min |
| **plain** | 21/21 ✓ | **1** (stage-2 model rewrite) | 60 / 89 / 125 | ~140k | ~3.1 min |

- **Correctness: a tie** — both arms correct at every stage; neither shipped a wrong number.
- **Trajectory: a real but modest, NON-compounding edge for aims** — it never reopened an owner (its
  stage-1 derived design + the record naming the seam absorbed both changes), while the plain arm paid **one**
  model reopen at stage 2 to reach the same derived design, then extended cleanly. The edge did not compound
  into rot: the plain arm's strong model refactored to parity (the paper's "strong models refactor deeply").
- **Cost:** aims ≈**1.85× tokens**, ≈**3.7× wall-clock**, and a ~1.4× larger module (more docstrings /
  records). The premium bought one avoided reopen and durable records, not a correctness win.
- **Q2 continuity signal:** the fresh aims stage-2 session read the co-located record, which explicitly
  named the extension seam, and extended exactly there — the record steered the fresh session (n=1).
