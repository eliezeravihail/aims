# Design Y — stage 1



<!-- file: proposal.md -->

# Proposal

## Why

Callers need to know when a resource can take a new booking of a given length on a given day. Today nothing
answers that question. Stage 1 sets up the core availability calculation: working hours minus existing
bookings, cut into slots of the requested duration.

## What Changes

- Add a pure, in-process **availability query**. Inputs: one resource's working hours for one day, that
  day's existing bookings, and a slot duration. Output: the ordered list of start times where a booking of
  that duration fits.
- Define the **domain value types** (time interval, working hours, booking, slot request) and their input
  validation rules.
- Define the **slot-offering policy**. Slots are laid back-to-back from the start of each free gap, earliest
  first. A slot is offered only if it fits completely inside that gap.
- Expose it as a local function API with a thin CLI adapter (JSON in, JSON out) for manual use.
- Out of scope: persistence, creating or holding bookings, multi-day or multi-resource queries, time zones
  and DST handling beyond what the input carries, buffers between bookings, and a fixed global alignment
  grid.

## Capabilities

### New Capabilities
- `slot-availability`: computing bookable slot start times for one resource on one day, from working hours,
  existing bookings, and a requested duration, including input validation and the slot-offering policy.

### Modified Capabilities
<!-- none: no existing specs -->

## Impact

- New greenfield Python 3.11+ package, standard library only (per `substrate.md`). No runtime
  dependencies, persistence, or network.
- New public API: one query function plus value types; one CLI entry point.


<!-- file: specs/slot-availability/spec.md -->

# Spec Delta

## Purpose

Tells a caller where a new booking of a given length can go for one resource on one day. It takes the
resource's working hours, that day's existing bookings, and the slot duration, and returns the bookable
slot start times.

## ADDED Requirements

### Requirement: Availability query inputs and output
The system SHALL accept an availability query made of: the resource's working hours for one day (a start
and end time of day), zero or more existing bookings for that day (each a start and end time of day), and a
slot duration. It SHALL return an ordered list of slot start times (times of day). All times are wall-clock
times of day on the same single day. The query SHALL NOT consider time zones, dates, or other days.

#### Scenario: Day with no bookings
- **WHEN** working hours are 09:00-17:00, there are no bookings, and the duration is 60 minutes
- **THEN** the result is 09:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 16:00

#### Scenario: Query is side-effect free
- **WHEN** the same query is made twice
- **THEN** both results are identical and no booking is created, held, or changed

### Requirement: Intervals are half-open
Every interval (working hours, bookings, and offered slots) SHALL be treated as half-open `[start, end)`.
A slot that ends exactly when a booking starts, or starts exactly when a booking ends, SHALL NOT be
considered overlapping. A slot ending exactly at the end of working hours SHALL be considered inside
working hours.

#### Scenario: Slot abuts a following booking
- **WHEN** working hours are 09:00-11:00, there is one booking 10:00-11:00, and the duration is 60 minutes
- **THEN** the result is 09:00

#### Scenario: Slot ends at close of working hours
- **WHEN** working hours are 09:00-10:00, there are no bookings, and the duration is 60 minutes
- **THEN** the result is 09:00

### Requirement: A slot fits only in free time inside working hours
A start time `s` SHALL be offered only if the whole interval `[s, s + duration)` lies inside working hours
and overlaps no existing booking.

#### Scenario: Gap too short for the duration
- **WHEN** working hours are 09:00-12:00, bookings are 09:00-10:00 and 10:20-12:00, and the duration is 30 minutes
- **THEN** the result is empty

#### Scenario: Duration longer than working hours
- **WHEN** working hours are 09:00-09:30 and the duration is 60 minutes
- **THEN** the result is empty, and this is not an error

### Requirement: Slots are laid back-to-back from the start of each free gap
The free time inside working hours SHALL be split into maximal free gaps: runs of time not covered by any
booking. Within each gap starting at `g`, candidate starts SHALL be `g`, `g + duration`,
`g + 2*duration`, and so on. A candidate SHALL be offered only while `candidate + duration` is not after
the end of the gap. The leftover time at the end of a gap that is shorter than the duration SHALL NOT
produce a slot. Alignment restarts at the start of each gap. It is not a fixed grid anchored to working
hours or to the clock.

#### Scenario: Alignment restarts after a booking that ends off-grid
- **WHEN** working hours are 09:00-17:00, bookings are 10:00-11:15 and 13:00-14:00, and the duration is 30 minutes
- **THEN** the result is 09:00, 09:30, 11:15, 11:45, 12:15, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30

#### Scenario: Leftover gap time is dropped
- **WHEN** working hours are 09:00-10:45, there are no bookings, and the duration is 30 minutes
- **THEN** the result is 09:00, 09:30, 10:00

### Requirement: Results are ordered earliest first without duplicates
The result SHALL be sorted in ascending time order and SHALL contain each start time at most once.
This holds whatever order the bookings are supplied in.

#### Scenario: Bookings supplied out of order
- **WHEN** working hours are 09:00-12:00, bookings are given as 11:00-12:00 then 09:00-10:00, and the duration is 60 minutes
- **THEN** the result is 10:00

### Requirement: Tolerant handling of overlapping and out-of-hours bookings
Existing bookings that overlap or touch each other SHALL be accepted and treated as their combined busy
time. Bookings that fall partly or entirely outside working hours SHALL be accepted. Only the part inside
working hours affects the result.

#### Scenario: Overlapping bookings
- **WHEN** working hours are 09:00-12:00, bookings are 09:30-10:30 and 10:00-11:00, and the duration is 30 minutes
- **THEN** the result is 09:00, 11:00, 11:30

#### Scenario: Booking extends before working hours
- **WHEN** working hours are 09:00-11:00, there is one booking 08:00-09:30, and the duration is 30 minutes
- **THEN** the result is 09:30, 10:00, 10:30

### Requirement: Invalid queries are rejected with a clear error
The system SHALL reject a query, and return no slots, when any of these hold: the working hours start is
not before their end; a booking's start is not before its end; the duration is zero or negative. The error
SHALL identify which input is invalid. A syntactically malformed time or duration given to the command-line
interface SHALL be rejected the same way.

#### Scenario: Non-positive duration
- **WHEN** the duration is 0 minutes
- **THEN** the query is rejected with an error naming the duration

#### Scenario: Inverted booking
- **WHEN** a booking has start 11:00 and end 10:00
- **THEN** the query is rejected with an error identifying that booking

#### Scenario: Empty working hours
- **WHEN** working hours are 09:00-09:00
- **THEN** the query is rejected with an error naming the working hours

### Requirement: Command-line access
The system SHALL provide a command-line entry point. It SHALL read one availability query as JSON (times as
`HH:MM` or `HH:MM:SS`, duration in whole minutes) and write the resulting start times as a JSON array of
`HH:MM` strings (with `:SS` when non-zero) to standard output. It SHALL exit with status 0 on success.
On an invalid query it SHALL write the error message to standard error and exit with a non-zero status.

#### Scenario: CLI success
- **WHEN** the CLI receives `{"working_hours": {"start": "09:00", "end": "10:00"}, "bookings": [], "duration_minutes": 30}`
- **THEN** it prints `["09:00", "09:30"]` and exits 0

#### Scenario: CLI invalid input
- **WHEN** the CLI receives a query whose duration is -5
- **THEN** it prints an error mentioning the duration to standard error and exits non-zero


<!-- file: design.md -->

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


<!-- file: tasks.md -->

# Tasks

## 1. Package scaffold

- [ ] 1.1 Create the `booking_availability` package (`model`, `intervals`, `slotting`, `availability`, `cli`, `__main__`) and a `tests/` directory, stdlib only; verify `python -m unittest discover` runs with zero tests and no import errors

## 2. Model and validation

- [ ] 2.1 Implement `Interval` over day offsets (frozen, `start < end` enforced, half-open `overlaps`/`contains`) and `InvalidQuery`; verify unit tests cover touching-is-not-overlapping and inverted/empty rejection
- [ ] 2.2 Implement `AvailabilityQuery` plus the `of(...)` helper that converts `datetime.time` values to offsets, with field-naming error messages; verify the tests for spec scenarios "Non-positive duration", "Inverted booking" and "Empty working hours" pass and check the error text

## 3. Interval algebra

- [ ] 3.1 Implement `merge` and `free_gaps` (clip busy to the window, merge, complement, ascending); verify unit tests for overlapping, touching, unordered, out-of-window, and fully covering busy sets

## 4. Slot policy and service

- [ ] 4.1 Implement `slotting.back_to_back`; verify unit tests for an exact fit, dropped leftover time, and a gap shorter than the duration
- [ ] 4.2 Implement `availability.find_slots`; verify one test per spec scenario (no bookings, abutting booking, ends at close, too-short gap, duration longer than working hours, off-grid realignment, leftover dropped, unordered bookings, overlapping bookings, booking before hours, idempotence), plus a property-style check that the output is strictly ascending
- [ ] 4.3 Add module docstrings stating the assumptions A1 to A5 where each rule lives; verify each assumption in design.md is referenced by exactly one owning module

## 5. CLI adapter

- [ ] 5.1 Implement `cli` JSON parsing (`HH:MM[:SS]`, `duration_minutes`) and output formatting, mapping `InvalidQuery` and parse errors to stderr with exit code 2; verify subprocess tests for the "CLI success" and "CLI invalid input" scenarios plus a malformed time string
- [ ] 5.2 Add a README section with the CLI usage and one example; verify the documented example command produces the documented output

## 6. Integration check

- [ ] 6.1 Run the full test suite and `the-method validate add-booking-availability --strict`; verify both pass
