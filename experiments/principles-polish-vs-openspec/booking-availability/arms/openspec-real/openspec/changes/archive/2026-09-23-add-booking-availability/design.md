# Design

## Context

Greenfield. See `proposal.md` for motivation and `specs/slot-availability/spec.md` for the behavior
contract. Fixed ground (`substrate.md`): Python 3.11+, standard library only, single process, no
persistence, network, or UI. The caller supplies all data: the service does no lookup of resources or
bookings.

## Goals / Non-Goals

**Goals:**
- One place for each rule: validation, interval algebra, slot alignment, and I/O formatting each have a
  single owner.
- A pure core: same inputs give the same output, with no clock, I/O, or global state. Every spec scenario
  is then a direct unit test.
- Exact time arithmetic with no floating point and no rounding.

**Non-Goals:**
- A resource or booking repository, caching, or storage.
- Pluggable alignment strategies, buffers, or multi-day or multi-resource queries. The seams below make
  these easy to add later, but stage 1 does not build them.

## Assumptions (product questions answered by default)

| # | Question | Assumption |
|---|----------|------------|
| A1 | What does "aligned to the top of the interval" anchor to? | The start of each **free gap**. Slots run back-to-back from there, and alignment restarts after every booking. It is not a fixed grid from opening time. |
| A2 | Do touching intervals conflict? | No. All intervals are half-open `[start, end)`. |
| A3 | Bookings that overlap each other or spill outside working hours? | Accepted. They are merged or clipped, and only busy time inside working hours matters. It is a query, not the booking system's integrity checker. |
| A4 | Time zones / DST / overnight hours? | None. Inputs are wall-clock times of day on one day. Working hours cannot cross midnight, and the latest end is 23:59:59 (no `24:00`). |
| A5 | Time granularity? | Whatever the input carries (`datetime.time` / `timedelta` are exact). No rounding. The CLI takes duration in whole minutes. |
| A6 | Duration longer than any gap, or than the whole day? | An empty result, not an error. |
| A7 | What is "resource" in the input? | Only the carrier of working hours and bookings. Identity plays no part in the calculation, so the core takes no resource id. |
| A8 | Closed day (no working hours)? | Not representable in stage 1. Working hours must have start < end. A caller with a closed day does not call the service. |

## Architecture

```
  +-----------+   JSON    +-----------------+  AvailabilityQuery  +----------------------+
  |  caller   | --------> |  cli (adapter)  | ------------------> |  availability        |
  | (shell)   | <-------- |  parse / format | <------------------ |  find_slots(query)   |
  +-----------+  JSON/err +-----------------+   list[time]        +----------+-----------+
                                                                            | orchestrates
   library callers ---- AvailabilityQuery ----------------------------------+
                                                                            |
             +-----------------------+---------------------+----------------+
             v                       v                     v
     +---------------+      +-----------------+    +------------------+
     |  model        |      |  intervals      |    |  slotting        |
     |  value types, |      |  merge, clip,   |    |  back-to-back    |
     |  invariants   |      |  subtract       |    |  alignment rule  |
     +---------------+      +-----------------+    +------------------+
       (no deps)             (depends: model)       (depends: model)
```

Dependencies point only downward. `intervals` and `slotting` do not know about each other, about bookings
as a concept, or about the CLI.

### Components

**1. `model`: value types and their invariants**
- `Interval(start, end)`: a frozen dataclass over a *day offset* (see D2). It enforces `start < end` at
  construction and has half-open `overlaps` and `contains` semantics. This is the single owner of rule A2.
- `AvailabilityQuery(working_hours: Interval, bookings: Sequence[Interval], duration: timedelta)`:
  a frozen dataclass. It enforces `duration > 0` and wraps construction errors so the message names the
  failing field (for example `bookings[2]: start 11:00 is not before end 10:00`).
- `InvalidQuery(ValueError)`: the only error type the core raises.
- Owns: all input-validity rules. Nothing downstream re-validates.

**2. `intervals`: pure interval algebra (no domain words)**
- `merge(intervals) -> list[Interval]`: sort, then coalesce overlapping or touching intervals.
- `free_gaps(window: Interval, busy: Iterable[Interval]) -> list[Interval]`: clip busy intervals to
  the window, merge them, and return the complement inside the window, ascending.
- Owns: rule A3 (overlap and out-of-hours tolerance) and the ordering guarantee of gaps.
  It is O(n log n) for n bookings.

**3. `slotting`: the slot-offering policy**
- `back_to_back(gap: Interval, duration) -> Iterator[offset]`: yields `gap.start + k*duration`
  while `start + duration <= gap.end`.
- Owns: rule A1 and the "leftover time is dropped" rule. It is the only code that knows how slots are
  aligned, so a later change of policy (a fixed grid, a step different from duration, buffers) touches
  only this module.

**4. `availability`: the service (public API)**
- `find_slots(query: AvailabilityQuery) -> list[datetime.time]`:
  `gaps = free_gaps(query.working_hours, query.bookings)` then
  `[to_time(s) for g in gaps for s in back_to_back(g, query.duration)]`.
- Owns: composition, and the ordering and uniqueness guarantee of the output. That guarantee follows from
  the gaps being ascending and disjoint and each gap's slots being ascending. No final sort is needed, and
  a test enforces this.
- Also the public construction helper `AvailabilityQuery.of(working=(time, time), bookings=[(time, time)],
  duration=timedelta)`. It converts `datetime.time` values to day offsets at the boundary.

**5. `cli`: thin adapter**
- `python -m booking_availability < query.json`. It parses JSON and `HH:MM[:SS]` strings into a query,
  calls `find_slots`, and prints a JSON array. It maps `InvalidQuery` and parse errors to stderr and exit
  code 2.
- Owns: the wire format only. It contains no availability logic.

## Decisions

**D1. A pure function core with a data-in query, not a service holding repositories.**
The substrate forbids persistence, and the input already carries the bookings. A repository interface
would be a speculative seam. *Alternative:* a `BookingRepository` protocol. It was rejected for stage 1
and is easy to add later in front of `find_slots` without changing the core.

**D2. Internal time is a `timedelta` offset from midnight, not `datetime.time`.**
`datetime.time` has no arithmetic, and `datetime.datetime` would add a date that the problem does not
have. Offsets are exact (integer microseconds), totally ordered, and support `+ duration`. Conversion to
`time` happens only at the API edge. *Alternatives:* integer minutes were rejected because they impose a
granularity (A5). A synthetic anchor `datetime` was rejected because it leaks a fake date into the model.

**D3. The subtract-then-slice algorithm, not candidate probing.**
Compute free gaps once, then slice each one. This is linear in the output after the sort, and it makes
"alignment restarts per gap" (A1) structural rather than a special case.
*Alternative:* step a cursor through working hours and test each candidate against every booking. That is
O(slots x bookings), and the realignment after an off-grid booking needs an explicit jump. Rejected.

**D4. Validation at construction (parse, don't validate).**
An `AvailabilityQuery` that exists is valid, so `intervals` and `slotting` take their preconditions
(`start < end`, `duration > 0`) for granted. *Alternative:* validate inside `find_slots`. Rejected because
it spreads checks across modules.

**D5. Tolerate bookings rather than reject them (A3).**
The service answers "where is it free?", and garbage-in bookings still have a well-defined busy set.
Rejecting overlaps would make availability fail whenever upstream data is imperfect. Inverted
(`start >= end`) bookings are still rejected, because they have no meaning.

**D6. The output type is `list[datetime.time]`, and only start times are returned.**
This matches the problem statement. The end time is derivable (`start + duration`). Returning a list rather
than a generator makes the result reusable and easy to compare in tests.

## Risks / Trade-offs

- [A1 may be the wrong reading. The product may want a fixed grid, for example on the hour.] → The policy
  is isolated in `slotting`. Switching it is a one-module change plus spec scenario updates.
- [No time zone or DST support. A real day can have 23 or 25 hours.] → Stated as A4. A later stage can
  put a zone-aware layer at the API edge that converts to day offsets, leaving the core unchanged.
- [End of day `24:00` cannot be expressed.] → Accepted for stage 1 (A4). A 23:59:59 end loses at most a
  second.
- [Large booking lists.] → O(n log n) is fine for one resource-day. No mitigation needed.

## Open Questions

None blocking. A1 and A8 are the assumptions most worth confirming with the product owner. Both are
localized as described above.
