---
title: "0003 — stage-1 architecture (opening panel round)"
date: 2026-09-23
status: accepted
---
## Decision
The architecture in `DESIGN.md`: a published `TimeRange` value type (the only time arithmetic), a private
`DaySchedule` (owns R3 clipping + R4 sort/overlap rejection, one constructor), a module-private R1 stepping
helper, one entry `available_starts`, and two error types. Library function, no CLI.

## Strengths harvest (panel, three axis Workers → merge → one revise round)
- Clean code: all time arithmetic in one file on the range type; R1 policy separate from tiling
  mechanics; zero dependencies including tests.
- Encapsulation: seeded-random invariant test over the input space; `__all__`/surface test; deterministic
  validation precedence; unbounded-output risk surfaced.
- Genericity: floor/ceiling calibration (`Iterable[TimeRange]` in, `list[time]` out, `time` not
  `datetime`); `DaySchedule` as the type-level evidence that R3/R4 hold (`busy`, not `bookings`);
  adjacent-pair overlap proof.

## Alternatives (axis splits)
- Decided: publish `TimeRange` over `(time, time)` tuples at the seam (encapsulation's pull) — a tuple is
  a data clump with an invisible rule owner; the encapsulation concern (leaking mechanics) is met by
  keeping only total, rule-fixed methods public and pinning the member set in a test.
- Harmonized: R1 owner — genericity wanted a stepping module, encapsulation a `_FreeGap` type, clean code
  a method on the range. Result: total `TimeRange.leading` (mechanics, in the time-model file) + one
  private stepping function (policy). `_FreeGap` cut.
- Decided: `timedelta` over a `SlotDuration` type — one rule, one owner; falsifier: a second public
  operation taking a duration.
- Decided: `DaySchedule` over a `Bookings` set — the concept is occupancy; breaks would not be bookings.
- Harmonized: errors — one (clean), two (genericity), five (encapsulation) → two, split only where the
  payload differs (C9's pair).
- Revise round correction: the merge's claim "a bypassed duration precondition fails loudly" was false
  for negative sizes with count-based tiling; replaced by total operations and a loop that cannot hang.

## Assumptions stated, not confirmed by the owner
A1 overlap outside hours → reject; A3 no 24:00 close; A5 no output cap / granularity (see DESIGN.md §1.2).
