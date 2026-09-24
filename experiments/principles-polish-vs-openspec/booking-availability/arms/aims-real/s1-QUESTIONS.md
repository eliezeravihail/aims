# Questions for the product owner — booking availability, stage 1

The design has not started yet. The language and platform are already settled by `substrate.md`
(Python 3.11+, standard library only, single process, no persistence), so none of the questions below
are about technology. Each one changes what a caller of the service would **see**. Each has a proposed
default, so "yes to all defaults" is a complete answer.

Worked example used below: working hours 09:00–17:00, existing bookings 09:00–09:45 and 11:00–12:00,
duration 30 min.

## Q1. Slot alignment: what does "aligned to the top of the interval" mean?

The request says slots are "aligned to the top of the interval (back-to-back)". There are two readings,
and they give different answers for the example:

- **(A) Aligned to each free gap.** Slots start at the beginning of each free gap and step by the
  duration. Free gap 09:45–11:00 gives **09:45, 10:15**. Free gap 12:00–17:00 gives 12:00, 12:30, …, 16:30.
- **(B) Aligned to a fixed grid.** The grid starts at the start of working hours and steps by the
  duration. A grid slot is offered only if it fits. Free gap 09:45–11:00 gives **10:00, 10:30**.

**Proposed default: (A).** Which one is correct?

## Q2. Do touching intervals count as overlapping?

Suppose a booking ends at 10:00. Can a new booking start at exactly 10:00? Likewise, can a slot end
exactly at the end of working hours (16:30–17:00 in the example)?

**Proposed default:** Yes to both. Intervals are half-open, `[start, end)`.

## Q3. What happens with bad or odd input?

What should the service do in each of these cases?

- (a) A booking lies partly or fully outside working hours.
- (b) Two existing bookings overlap each other.
- (c) A booking or the working hours has `end <= start`.
- (d) The duration is zero or negative.
- (e) The duration is longer than any free gap.

**Proposed default:**
- For (a) and (b): accept the input. Only the time a booking takes up *inside* working hours matters,
  and overlapping bookings are merged.
- For (c) and (d): reject with a clear error.
- For (e): return an empty list. This is a normal result, not an error.

## Q4. How are times and time zones represented?

**Proposed default:** Times are wall-clock times on a single calendar date. There are no time zones and
no DST handling. Working hours are one continuous window per day, with no breaks. There are no buffers
between bookings.

If time zones or DST-transition days must be handled correctly in stage 1, please say so. That changes
the time model.

---
Once these are answered, the aims loop restarts from `.aims/state.md`. The cursor there is
`awaiting-human`.
