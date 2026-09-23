---
title: "goals"
date: 2026-09-20
---
## Insights
- The product is a single in-memory module: a reservation calendar over half-open integer
  intervals `[start, end)`, with no external dependencies and no persistence.

## Decisions
- **Primary goal.** Reserve non-overlapping half-open intervals and answer, without side effects,
  whether an interval is currently bookable.
- **Core scenarios.**
  - `book(start, end)` reserves `[start, end)` and returns True, or returns False when the request
    overlaps an existing reservation or is invalid — leaving the calendar unchanged on refusal.
  - `is_free(start, end)` reports whether `[start, end)` could be booked right now, as a pure query.
  - Adjacent reservations that only touch at a boundary (`[10,20)` then `[20,30)`) both succeed.
  - A request with `end <= start` is invalid: `book` and `is_free` both return False.
  - An empty calendar admits any valid request.
- **Time units** are opaque integers; ordering is the only meaning attached to them (negatives are fine).

## Discussions
- Out of scope (no present force): cancellation, listing reservations, next-free-slot search,
  persistence, concurrency, associating an owner/identity with a reservation. Added only if a real
  requirement arrives — not speculatively.
