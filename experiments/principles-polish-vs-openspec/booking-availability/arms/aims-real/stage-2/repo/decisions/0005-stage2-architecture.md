---
title: "0005 — stage-2 architecture: buffer, notice, granularity absorbed (panel round)"
date: 2026-09-23
status: accepted
supersedes: "0003 in part — TimeRange.leading, DaySchedule.free_gaps, DaySchedule I2/I3, A6 precedence"
---
## Decision
The architecture in `DESIGN.md` (stage 2), adapting the unbuilt stage-1 design:
- **Buffer → `DaySchedule` only.** Order in `__init__`: sort → R4 on raw bookings → widen by buffer (M1 cap)
  → clip to hours. `bookable_spans()` (was `free_gaps`) trims gaps closed by occupancy by the buffer and
  leaves the tail to closing untrimmed — the whole of B2's closing-edge asymmetry.
- **No occupancy merge.** Runs may overlap; the unchanged walk relies on I2′ (starts and ends
  non-decreasing), which follows from R4 + one buffer for every booking + a monotone midnight cap.
- **Slot policy = a lattice `(origin, step)`** chosen in `slots._aligned_starts`: R1 `(span.start, d)`,
  grid `(hours.start, g)`; one total `TimeRange.fitting_starts` enumerates and fit-tests. `leading` removed.
- **Notice → published `AsOf(day, now)`**, whose `eligible_starts(notice)` is the one date/instant →
  time-of-day conversion (window or `None`); applied by one filter line; N2 in `slots._eligible_starts`.
- **Seam:** `available_starts(hours, bookings, duration, *, rules=ResourceRules(), as_of=None)`;
  `ResourceRules(buffer, minimum_notice, granularity)` published, validates V1. No new error types.

## Strengths harvest (three axis Workers → merge → one revise round)
- Clean code: I2′ instead of a merge (no `joined`, no fold); the lattice unification of R1 and grid;
  `extended`/`trimmed` as two direction-visible operations; build order with a behaviour-preserving step 0.
- Encapsulation: the proof that a new booking fits iff it lies inside a span; `whole_day` as the one home
  of the end-of-day sentinel; `__contains__` keeping bound comparisons in `time_range.py`; the `AsOf.day`
  datetime guard; full precedence table; notice-as-filter argued against the forbidden trailing filter.
- Genericity: `fitting_starts` by floor-divided k-range (overflow-free, work ∝ output); `AsOf` in its own
  module (calendar changes for a different reason than time of day); N2 off the published settings type;
  floor/ceiling table (`_day` receives a `timedelta`, not `ResourceRules`); exact brute-force oracle.
- Revise round: I2′ made load-bearing in the `DaySchedule` docstring with the tests that fail per premise
  (B23 ordering, B24 monotone midnight cap); the A5 cost claim corrected; oracle computes its own union;
  four crossings added (notice × buffer, notice × opening edge, grid × short span, A2 × buffer).

## Alternatives (axis splits)
- **Decided: I2′ over coalescing** (encapsulation and genericity wanted a union to restore I3). The merge
  costs a public `TimeRange.joined` and a fold the walk does not need. Genericity's concern — correctness
  resting on an unstated fact — is met by stating I2′ in the one constructor that establishes it and pinning
  each premise with an exact-output test. Falsifier: non-uniform widening (per-booking buffers) → merge first,
  in `__init__`.
- **Harmonized: slot policy.** Encapsulation pulled toward a private `_SlotPolicy` Protocol whose methods
  cannot test fit; clean code and genericity toward data. The lattice keeps encapsulation's guarantee more
  strongly — no policy code exists that could test fit. Falsifier for a seam: a non-lattice policy.
- **Harmonized: notice shape.** Clean code returned a cutoff `time` (`time.min` = no effect) compared in
  `slots`; the others a window. The window keeps the comparison on `TimeRange` and names "nothing eligible"
  as `None`, with the whole day as the honest "no filter".
- **Decided: N2 owner** — `slots._eligible_starts` over `ResourceRules.earliest_start(as_of)` (clean): the
  latter puts query logic on the published settings type and makes `rules` depend on `as_of`.
- **Decided: `extended`/`trimmed` over one signed `shift_end`** (genericity): direction at the call site;
  different totality.
- **Decided: `AsOf` in `as_of.py`** over inside `time_range.py` (clean): different reason to change.
- **Harmonized: naming** — `as_of=AsOf(...)` (clean/encapsulation) over `when=QueryTime(...)`;
  `minimum_notice` (encapsulation) as the brief's term.

## Assumptions stated, not confirmed by the owner
A10–A14 in DESIGN.md §1.2 — notably A12 (a past day with `as_of` returns `[]`) and A14 (offered starts may
overlap each other's buffers; they are alternatives for one booking).
