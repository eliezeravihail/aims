---
title: "architecture"
date: 2026-09-23
---
The full stage-1 architecture is `DESIGN.md` (to be superseded by the code's own docstrings once built).
This record keeps only what the code will not say.

## Boundaries & seams
- Published seam: `TimeRange`, `available_starts`, `InvalidAvailabilityRequest`, `OverlappingBookingsError`.
  `DaySchedule` and the R1 stepping helper are private — occupancy normalization and slot policy are the
  decisions most likely to change, so they stay behind the seam.
- `TimeRange` is published deliberately (decisions/0003): a caller cannot construct an invalid range.

## Invariants
- Validation happens once — `TimeRange` construction, the first statement of `available_starts`, and the
  single `DaySchedule` constructor; everything after trusts it.
- Overlap is checked on raw bookings *before* clipping to working hours (assumption A1).

## Likely change axes
- Slot policy (grid alignment) → the R1 stepping helper only.
- Occupancy (breaks, buffers) → `DaySchedule.__init__` only.
- Time model (multi-day, zones, 24:00 close) → `time_range.py` and the entry signature; reaches callers.
