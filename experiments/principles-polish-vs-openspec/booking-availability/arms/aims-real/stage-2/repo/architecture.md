---
title: "architecture"
date: 2026-09-23
---
The full architecture is `DESIGN.md` (stage 2; to be superseded by the code's own docstrings once built).
This record keeps only what the code will not say.

## Boundaries & seams
- Published seam: `TimeRange`, `ResourceRules`, `AsOf`, `available_starts`, `InvalidAvailabilityRequest`,
  `OverlappingBookingsError`. `DaySchedule`, bookable spans, the lattice choice and the eligibility helper are
  private — occupancy, alignment and eligibility are the decisions most likely to change.
- `TimeRange` is published deliberately (decisions/0003): a caller cannot construct an invalid range.
- The core sees no `date`/`datetime`: `AsOf.eligible_starts` is the only crossing (decisions/0005).

## Invariants
- Validation happens once — value-type construction (`TimeRange`, `ResourceRules`, `AsOf`), the first two
  statements of `available_starts` (duration, N2), and the single `DaySchedule` constructor (R4).
- R4 runs on raw bookings *before* buffers and clipping (A1, and what makes buffer-violating input
  acceptable — decisions/0004 §5).
- The gap walk is correct only while occupancy starts and ends are non-decreasing (I2′). This holds because
  every booking gets the same buffer and the midnight cut is a monotone cap. **Per-booking buffers break it:
  merge occupancy into its union in `DaySchedule.__init__` first.**

## Likely change axes
- Slot alignment (a new policy) → `slots._aligned_starts`; a non-lattice policy is what would earn a seam.
- Occupancy (breaks, per-booking buffers) → `DaySchedule` only (see the I2′ falsifier above).
- Notice/calendar (zones for `now`, multi-day) → `as_of.py` and the entry signature.
- Time of day (24:00 close) → `time_range.py`.
- Latency on late cutoffs → a lower bound inside `fitting_starts` replacing the filter line (DESIGN §3.6).
