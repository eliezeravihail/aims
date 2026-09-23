---
title: "0001 — Half-open interval semantics and a single overlap owner"
date: 2026-09-20
---
## Context
The calendar reserves time intervals and must decide, unambiguously, when two reservations conflict.
The one hard call the task hides is the boundary case: may a reservation that *ends* exactly where
another *begins* coexist? Getting this wrong is silently value-correct on most inputs and breaks only
on the touching case.

## Decision
Intervals are **half-open, `[start, end)`** — `start` included, `end` excluded. Two intervals conflict
iff they share an interior point: `a.start < b.end and b.start < a.end`. Consequently intervals that
only touch at a boundary (`[10,20)` and `[20,30)`) do **not** conflict and may both be booked.

The overlap relation has exactly **one owner**, `Interval.overlaps`; the occupancy query
(`Calendar._is_free`) is expressed in terms of it, and `book` reserves only what `_is_free` admits.
Request validity (`end > start`) has one owner too — `Interval`'s constructor — translated to the
API's "invalid -> not bookable" answer at a single boundary point (`Calendar._as_interval`).

## Rejected alternatives
- **Closed intervals `[start, end]`.** Would make touching reservations conflict, contradicting the
  spec's `book(10,20)` then `book(20,30)` both succeeding, and forcing off-by-one arithmetic at every
  adjacency. Rejected.
- **Duplicating the overlap test inside both `book` and `is_free`.** Two owners of one rule; they would
  drift. Rejected in favor of `book` funneling through the shared query.
- **Validating `end <= start` at the `Calendar` boundary as well as in `Interval`.** A second owner of
  the validity rule. Rejected: validity is enforced once in `Interval` and translated once at the seam.
