---
title: "goals"
date: 2026-09-23
---
## Primary goal
Given one resource's working hours for one day, that day's existing bookings, and a requested slot
duration, return the start times at which a new booking of that duration fits — earliest first.

## Use scenarios
- Worked example (the acceptance anchor): working hours 09:00–17:00, bookings 09:00–09:45 and
  11:00–12:00, duration 30 min → `09:45, 10:15, 12:00, 12:30, …, 16:30`.
- A caller (a scheduling UI or another service in the same process) asks "when can I book 30 min on this
  resource on this day?" and presents the answer as a pick-list.

## Product rules (decided — see decisions/0002)
- Slots are stepped back-to-back from the start of each free gap (gap-aligned, not a fixed day grid).
- Intervals are half-open `[start, end)`: touching is not overlapping.
- Bookings arrive unsorted is fine; they are sorted internally. Parts of bookings outside working hours
  are ignored. Overlapping bookings, `end <= start` intervals and non-positive durations are rejected
  with a clear error. A duration longer than every free gap yields an empty list (a normal result).
- Times are wall-clock times in the resource's local day. No time zones, no DST, no midnight crossing.

## Non-goals (stage 1)
- Creating, cancelling or storing bookings; persistence of any kind.
- Multiple resources, recurrence, breaks inside working hours, buffers between bookings.
- Time zones / DST; multi-day queries.
