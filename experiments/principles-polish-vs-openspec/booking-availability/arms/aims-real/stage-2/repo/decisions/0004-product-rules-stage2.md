---
title: "0004 — stage-2 product rules: buffer, minimum notice, granularity (owner delegated most choices)"
date: 2026-09-23
status: accepted
supersedes: "0002 §1 in part (gap-aligned stepping is now the no-granularity case only)"
---
## Context
Stage-2 brief adds three per-resource rules. QUESTIONS.md Q1–Q4 were answered by the product owner:
Q1(a) "the buffer may run to or past closing; only the booking must fit inside working hours";
Q3(c) "align from the working-hours start"; Q4 "all times are in the resource's local day; ignore
cross-zone". Q1(b), Q2, Q3(a), Q3(b) and the rest of Q4 were answered "not specified; choose a simple,
sensible approach and state it". The choices below are the Guide's, made under that delegation.

## Decisions
1. **Buffer is occupancy, not a booking.** Each existing booking `[s, e)` makes the resource unavailable over
   `[s, e + buffer)`. The buffer is never returned and has no booker. *(Brief.)*
2. **Opening edge (Q1b, chosen).** A buffer counts wherever it lies inside working hours, including the
   buffer of a booking that ended before opening: booking 08:00–09:00 + 15 min → not free until 09:15.
   Reason: the resource really is being cleaned then; one rule ("buffer is busy time") with no edge case.
3. **Closing edge (Q1a, owner).** A new booking must lie inside working hours; its own buffer may run to or
   past closing. With hours 09:00–17:00, 30 min, buffer 15 → 16:30 is offered.
4. **The new slot needs its own buffer.** `[start, start + duration + buffer)` must not overlap any existing
   booking's occupancy (booking + its buffer) inside working hours. Occupancy outside working hours is
   still ignored (stage-1 R3 unchanged), so a buffer running past close cannot collide with anything.
5. **Existing bookings that break the buffer rule (Q2, chosen): accepted.** The buffer rule constrains only
   the slots being offered. Bookings are historical fact (they may predate the buffer setting). Their
   combined occupancy may overlap; that is normal input. True booking-vs-booking overlaps are still
   rejected exactly as in stage 1 (on the raw bookings, before buffers and clipping — stage-1 A1 kept).
6. **Granularity (Q3a, chosen): every grid point that fits.** With granularity `g`, candidate starts are
   `hours.start + k·g` (k ≥ 0), and **every** candidate where rule 4 and working hours hold is offered —
   not only every `duration`-th one. Reason: this is what "align to a grid" means to a caller; stepping by
   duration on top would silently drop valid times.
7. **Granularity is optional (Q3b, chosen).** A resource with no granularity keeps stage-1 R1 unchanged:
   back-to-back from the start of each free gap, stepping by the duration (the buffer only changes where a
   gap ends and which starts fit, per rule 4). Reason: the brief says stage-1 behaviour is unchanged where
   the new rules do not apply; making granularity mandatory would change every stage-1 result.
8. **Grid origin (Q3c, owner).** The grid is counted from the start of working hours.
9. **Minimum notice (Q4, chosen).** Notice is any non-negative length (`timedelta`), not only whole hours.
   The caller supplies the queried calendar `day` and `now` as a naive local date-time (no zones). A start
   `t` is offered only if `datetime.combine(day, t) >= now + notice` — a start exactly at the cutoff is
   offered. Notice **removes** starts; it never moves the grid or the gap-aligned anchors. A cutoff on a
   later day removes all starts; a cutoff on an earlier day removes none.
10. **When `now` is required (chosen).** `now` (with `day`) is optional. Without it no notice filter is
    applied — the stage-1 behaviour, useful for what-if queries. **But** a resource whose notice is
    greater than zero with no `now` is a caller error, not a silent skip: a configured rule must not be
    dropped quietly. With `now` supplied and notice 0, starts before `now` are dropped (notice 0 means
    "not in the past", which is what the rule literally says).
11. **Validation (chosen).** Rejected with a clear error: negative buffer, negative notice, granularity
    `<= 0` when given, a tz-aware `now`, notice > 0 without `now`. Buffer 0 and notice 0 (without `now`)
    behave exactly as stage 1.
12. **Midnight (chosen).** A buffer that would run past midnight is simply cut at the end of the day; it
    can never overflow or wrap. Working hours still end before midnight (stage-1 A3).

## Rules out
Buffer as a synthetic booking; rejecting buffer-violating existing bookings; mandatory granularity; a grid
anchored at the clock hour; notice that shifts the grid; silently ignoring a configured notice.
