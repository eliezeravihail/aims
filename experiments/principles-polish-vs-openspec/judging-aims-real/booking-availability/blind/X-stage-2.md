# Design X — stage 2



<!-- file: proposal.md -->

# Proposal

## Why

Three per-resource rules now change what "bookable" means. Stage 1 cannot express them:
- a cleanup **buffer** after every booking
- a **minimum notice** relative to the current time
- a start-time **granularity** grid

A slot that stage 1 offers can now be unbookable because it falls inside a cleanup buffer, is too soon, or
is off-grid. The availability answer is wrong until the rules are part of the calculation.

## What Changes

- Introduce **resource rules** as an explicit input: `buffer` (≥ 0), `min_notice` (≥ 0) and optional
  `granularity` (> 0). Before this change, "resource" was only the carrier of working hours and bookings
  (stage-1 A7). Now it also carries this policy.
- **Buffer.** Each booking, existing or candidate, occupies `[start, end + buffer)`. Buffers are never
  returned, have no booker, and never count as bookings. A candidate is offered only if its buffer overlaps
  no existing booking, and no existing booking's buffer overlaps the candidate. A buffer may run past the
  end of working hours (assumption).
- **Minimum notice.** The query can carry a `now` (datetime) and the query `date`. Start times earlier than
  `now + min_notice` are not offered. The notice rule filters candidates and never moves them. When `now`
  is absent, no time-based filtering happens (stage-1 behavior).
- **Granularity.** When a resource has a granularity `g`, the offered starts are **every** point
  `working_start + k*g` where the slot (plus its buffer) fits. Adjacent offered slots may overlap each
  other. When there is no granularity, stage-1 back-to-back slotting is kept, with the step widened to
  `duration + buffer`.
- New validation rules: negative buffer or notice, non-positive granularity, and positive notice with no
  `now`/`date`.
- CLI: new optional JSON fields `buffer_minutes`, `min_notice_minutes`, `granularity_minutes`, `date` and
  `now`.
- Compatibility: a stage-1 query (no rules, no `now`) gives exactly the stage-1 result. Not breaking.
- Out of scope: time zones and DST (the stage-1 A4 assumption stands, and `now` is naive local wall-clock
  time of the resource), multi-day queries, buffers before bookings, and carry-over from a previous day's
  bookings that are not supplied in the input.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `slot-availability`: the query gains resource rules and an optional `now`/`date`. The fit rule accounts
  for buffers. The slotting rule becomes grid-or-back-to-back. The notice filter, new validation errors,
  and new CLI fields are added.

## Impact

- The `model` (new `ResourceRules`, query fields, validation), `slotting` (grid policy, policy
  selection), and `availability` (composition) modules change. New small modules own the buffer rule
  (`occupancy`) and the notice rule (`notice`). `intervals` is unchanged. The `cli` gets new optional
  fields.
- There are no new dependencies. The core stays pure: `now` is always an input and is never read from a
  clock.


<!-- file: specs/slot-availability/spec.md -->

# Spec Delta

## MODIFIED Requirements

### Requirement: Availability query inputs and output
The system SHALL accept an availability query made of these inputs:
- the resource's working hours for one day (a start and end time of day)
- zero or more existing bookings for that day (each a start and end time of day)
- a slot duration
- the resource's **rules**: a buffer (a non-negative duration, default 0), a minimum notice (a
  non-negative duration, default 0), and an optional granularity (a positive duration)
- optionally, the calendar **date** of the queried day and the current moment **now** (a date and a time
  of day). These are supplied together.

It SHALL return an ordered list of slot start times (times of day). Working hours, bookings, and results
are wall-clock times of day on the same single day. The date and now SHALL be used only to apply the
minimum-notice rule. They are in the same wall clock as the resource, and the query SHALL NOT consider
time zones or daylight-saving transitions.

#### Scenario: Day with no bookings
- **WHEN** working hours are 09:00-17:00, there are no bookings, the duration is 60 minutes, and the rules are left at their defaults
- **THEN** the result is 09:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 16:00

#### Scenario: Query is side-effect free
- **WHEN** the same query is made twice
- **THEN** both results are identical and no booking is created, held, or changed

#### Scenario: Default rules reproduce stage-1 results
- **WHEN** a query has buffer 0, no granularity, and no date or now
- **THEN** the result is exactly what the query without rules returned before this change

### Requirement: A slot fits only in free time inside working hours
A start time `s` SHALL be offered only if all of these hold:
- the booked interval `[s, s + duration)` lies inside working hours
- the booked interval overlaps no existing booking and no existing booking's buffer
- the new slot's own buffer `[s + duration, s + duration + buffer)` overlaps no existing booking

The new slot's buffer MAY extend past the end of working hours.

#### Scenario: Gap too short for the duration
- **WHEN** working hours are 09:00-12:00, bookings are 09:00-10:00 and 10:20-12:00, and the duration is 30 minutes
- **THEN** the result is empty

#### Scenario: Duration longer than working hours
- **WHEN** working hours are 09:00-09:30 and the duration is 60 minutes
- **THEN** the result is empty, and this is not an error

#### Scenario: Slot plus buffer does not fit before the next booking
- **WHEN** working hours are 09:00-11:00, there is one booking 10:00-11:00, the buffer is 15 minutes, and the duration is 50 minutes
- **THEN** the result is empty, because 09:00-09:50 plus its buffer runs until 10:05, into the booking

### Requirement: Slots are laid back-to-back from the start of each free gap
This requirement applies only when the resource has **no granularity**. Busy time is every existing
booking together with its buffer. The free time inside working hours SHALL be split into maximal free
gaps: runs of time not covered by busy time. Within each gap starting at `g`, candidate starts SHALL be
`g`, `g + step`, `g + 2*step`, and so on, where `step = duration + buffer`. A candidate SHALL be offered
only if it satisfies the fit rule. Leftover time at the end of a gap SHALL NOT produce a slot. Alignment
restarts at the start of each gap. It is not a fixed grid anchored to working hours or to the clock.

#### Scenario: Alignment restarts after a booking that ends off-grid
- **WHEN** working hours are 09:00-17:00, bookings are 10:00-11:15 and 13:00-14:00, and the duration is 30 minutes
- **THEN** the result is 09:00, 09:30, 11:15, 11:45, 12:15, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30

#### Scenario: Leftover gap time is dropped
- **WHEN** working hours are 09:00-10:45, there are no bookings, and the duration is 30 minutes
- **THEN** the result is 09:00, 09:30, 10:00

#### Scenario: Back-to-back slots leave room for the buffer
- **WHEN** working hours are 09:00-11:00, there is one booking 09:00-10:00, the buffer is 15 minutes, and the duration is 30 minutes
- **THEN** the result is 10:15

### Requirement: Invalid queries are rejected with a clear error
The system SHALL reject a query, and return no slots, when any of these hold:
- the working hours start is not before their end
- a booking's start is not before its end
- the duration is zero or negative
- the buffer is negative
- the minimum notice is negative
- the granularity is supplied and is zero or negative
- only one of date and now is supplied
- the minimum notice is positive and now is not supplied

The error SHALL identify which input is invalid. A syntactically malformed time, date, or duration given
to the command-line interface SHALL be rejected the same way.

#### Scenario: Non-positive duration
- **WHEN** the duration is 0 minutes
- **THEN** the query is rejected with an error naming the duration

#### Scenario: Inverted booking
- **WHEN** a booking has start 11:00 and end 10:00
- **THEN** the query is rejected with an error identifying that booking

#### Scenario: Empty working hours
- **WHEN** working hours are 09:00-09:00
- **THEN** the query is rejected with an error naming the working hours

#### Scenario: Negative buffer
- **WHEN** the buffer is -5 minutes
- **THEN** the query is rejected with an error naming the buffer

#### Scenario: Zero granularity
- **WHEN** the granularity is 0 minutes
- **THEN** the query is rejected with an error naming the granularity

#### Scenario: Minimum notice without now
- **WHEN** the minimum notice is 120 minutes and no date or now is supplied
- **THEN** the query is rejected with an error naming now

### Requirement: Command-line access
The system SHALL provide a command-line entry point. It SHALL read one availability query as JSON with:
- times as `HH:MM` or `HH:MM:SS`
- the duration in whole minutes
- optional whole-minute fields `buffer_minutes`, `min_notice_minutes`, and `granularity_minutes`
- optional `date` (`YYYY-MM-DD`) and `now` (`YYYY-MM-DDTHH:MM[:SS]`)

Omitted rule fields SHALL take their defaults. The CLI SHALL NOT read the system clock. It SHALL write the
resulting start times as a JSON array of `HH:MM` strings (with `:SS` when non-zero) to standard output, and
exit with status 0 on success. On an invalid query it SHALL write the error message to standard error and
exit with a non-zero status.

#### Scenario: CLI success
- **WHEN** the CLI receives `{"working_hours": {"start": "09:00", "end": "10:00"}, "bookings": [], "duration_minutes": 30}`
- **THEN** it prints `["09:00", "09:30"]` and exits 0

#### Scenario: CLI with rules
- **WHEN** the CLI receives `{"working_hours": {"start": "09:00", "end": "11:00"}, "bookings": [], "duration_minutes": 60, "granularity_minutes": 30, "buffer_minutes": 10, "date": "2026-10-01", "now": "2026-10-01T08:00", "min_notice_minutes": 90}`
- **THEN** it prints `["09:30", "10:00"]` and exits 0

#### Scenario: CLI invalid input
- **WHEN** the CLI receives a query whose duration is -5
- **THEN** it prints an error mentioning the duration to standard error and exits non-zero

### Requirement: Tolerant handling of overlapping and out-of-hours bookings
Existing bookings that overlap or touch each other SHALL be accepted and treated as their combined busy
time. Bookings that fall partly or entirely outside working hours SHALL be accepted. Such a booking
affects the result only through:
- the part of it, together with its buffer, that falls inside working hours
- a new slot's buffer that would reach into it

#### Scenario: Overlapping bookings
- **WHEN** working hours are 09:00-12:00, bookings are 09:30-10:30 and 10:00-11:00, and the duration is 30 minutes
- **THEN** the result is 09:00, 11:00, 11:30

#### Scenario: Booking extends before working hours
- **WHEN** working hours are 09:00-11:00, there is one booking 08:00-09:30, and the duration is 30 minutes
- **THEN** the result is 09:30, 10:00, 10:30

#### Scenario: Booking entirely after working hours without buffer
- **WHEN** working hours are 09:00-10:00, there is one booking 10:00-11:00, the buffer is 0, and the duration is 60 minutes
- **THEN** the result is 09:00

## ADDED Requirements

### Requirement: Cleanup buffer after every booking
Every booking SHALL be followed by a cleanup buffer. The buffer's length is the resource's buffer. This
applies both to existing bookings and to a slot being offered. During a buffer the resource SHALL NOT be
free. A buffer SHALL NOT be treated as a booking: it is never returned in the result, has no booker, and
exists only as an effect of its booking. Buffers apply only after a booking, never before. The buffer of
an existing booking that starts before working hours SHALL still block the time inside working hours that
it covers. A booking outside working hours SHALL still block a new slot's buffer. Existing bookings whose
buffers overlap other bookings SHALL be accepted, and their combined busy time is used.

#### Scenario: Existing booking's buffer blocks the time after it
- **WHEN** working hours are 09:00-10:00, there is one booking 09:00-09:30, the buffer is 30 minutes, and the duration is 30 minutes
- **THEN** the result is empty

#### Scenario: Buffer of a booking before working hours
- **WHEN** working hours are 09:00-11:00, there is one booking 08:00-09:00, the buffer is 20 minutes, and the duration is 30 minutes
- **THEN** the result is 09:20, 10:10

#### Scenario: New slot's buffer may run past closing
- **WHEN** working hours are 09:00-10:00, there are no bookings, the buffer is 15 minutes, and the duration is 60 minutes
- **THEN** the result is 09:00

#### Scenario: New slot's buffer may not overlap a booking after closing
- **WHEN** working hours are 09:00-10:00, there is one booking 10:00-11:00, the buffer is 15 minutes, and the duration is 60 minutes
- **THEN** the result is empty

### Requirement: Minimum notice before a slot may start
When now is supplied, a start time `s` on the queried date SHALL be offered only if `date + s` is not
earlier than `now + minimum notice`. A start exactly at that cutoff SHALL be offered. The notice rule SHALL
only remove candidate starts. It SHALL NOT shift or re-anchor the remaining ones. The cutoff MAY fall on
an earlier day (every slot passes) or a later day (no slot passes). When now is not supplied, no
time-based filtering SHALL occur.

#### Scenario: Slots within the notice period are dropped, not shifted
- **WHEN** working hours are 09:00-13:00, there are no bookings, the duration is 60 minutes, the date is 2026-10-01, now is 2026-10-01 08:30, and the minimum notice is 120 minutes
- **THEN** the result is 11:00, 12:00

#### Scenario: Start exactly at the cutoff is offered
- **WHEN** working hours are 09:00-13:00, there are no bookings, the duration is 60 minutes, the date is 2026-10-01, now is 2026-10-01 08:00, and the minimum notice is 120 minutes
- **THEN** the result is 10:00, 11:00, 12:00

#### Scenario: Notice carried over from the previous day
- **WHEN** working hours are 09:00-13:00, there are no bookings, the duration is 60 minutes, the date is 2026-10-02, now is 2026-10-01 22:00, and the minimum notice is 12 hours
- **THEN** the result is 10:00, 11:00, 12:00

#### Scenario: Notice reaches beyond the queried day
- **WHEN** working hours are 09:00-13:00, the duration is 60 minutes, the date is 2026-10-02, now is 2026-10-01 12:00, and the minimum notice is 48 hours
- **THEN** the result is empty

#### Scenario: Zero notice still excludes the past
- **WHEN** working hours are 09:00-13:00, there are no bookings, the duration is 60 minutes, the date is 2026-10-01, now is 2026-10-01 10:30, and the minimum notice is 0
- **THEN** the result is 11:00, 12:00

### Requirement: Start times align to the resource granularity
When the resource has a granularity `g`, the candidate starts SHALL be exactly the points
`working_hours.start + k*g` (for k = 0, 1, 2, ...) inside working hours. Every candidate that satisfies
the fit rule and the minimum-notice rule SHALL be offered. As a result, offered slots MAY overlap each
other. Candidates SHALL NOT be re-anchored to the end of a booking or buffer: the grid is fixed for the
day. In this mode the back-to-back rule does not apply.

#### Scenario: Every grid point that fits is offered
- **WHEN** working hours are 09:00-11:00, there are no bookings, the granularity is 15 minutes, and the duration is 60 minutes
- **THEN** the result is 09:00, 09:15, 09:30, 09:45, 10:00

#### Scenario: Grid anchored at the start of working hours
- **WHEN** working hours are 09:10-10:40, there are no bookings, the granularity is 30 minutes, and the duration is 30 minutes
- **THEN** the result is 09:10, 09:40, 10:10

#### Scenario: Free time starting off-grid waits for the next grid point
- **WHEN** working hours are 09:00-12:00, there is one booking 09:00-10:05, the granularity is 15 minutes, and the duration is 30 minutes
- **THEN** the result is 10:15, 10:30, 10:45, 11:00, 11:15, 11:30

#### Scenario: Granularity with buffer
- **WHEN** working hours are 09:00-11:00, there is one booking 10:00-10:30, the buffer is 10 minutes, the granularity is 15 minutes, and the duration is 30 minutes
- **THEN** the result is 09:00, 09:15

### Requirement: The three rules apply together
Buffer, minimum notice, and granularity SHALL all apply to the same query at once. A start time SHALL be
offered only if it is a candidate of the active slotting rule (grid or back-to-back), satisfies the fit
rule including buffers, and satisfies the minimum-notice rule. The order in which the rules are checked
SHALL NOT affect the result.

#### Scenario: All three rules combined
- **WHEN** working hours are 09:00-12:00, there is one booking 09:30-10:00, the buffer is 15 minutes, the granularity is 15 minutes, the duration is 30 minutes, the date is 2026-10-01, now is 2026-10-01 08:00, and the minimum notice is 150 minutes
- **THEN** the result is 10:30, 10:45, 11:00, 11:15, 11:30


<!-- file: design.md -->

# Design

## Context

Stage 1 is archived at `the-method/changes/archive/2026-09-23-add-booking-availability/design.md`. Its
architecture has five modules:
- `model`: value types and validation
- `intervals`: `merge` and `free_gaps`
- `slotting`: back-to-back alignment
- `availability`: composition
- `cli`: adapter

Time inside the system is a `timedelta` offset from midnight of the queried day (D2). Availability is
computed by subtracting busy time from working hours, then slicing the free gaps (D3).

See `proposal.md` for why the three rules are needed, and `specs/slot-availability/spec.md` for the
behavior contract. The substrate still applies: standard library only, pure, and no persistence. The
caller still supplies all data, including the resource's rules.

## Goals / Non-Goals

**Goals:**
- Each new rule has exactly **one owning module**:
  - buffer: `occupancy`
  - notice: `notice`
  - granularity: `slotting.Grid`
- Rules combine by **composition**, not by modules knowing about each other's rules. `slotting` does not
  know that buffers or notice exist. `intervals` stays free of domain words and is unchanged.
- A stage-1 query gives a stage-1 result. The defaults are neutral, and the stage-1 scenarios remain as
  regression tests.
- The core stays pure. `now` is data. Nothing reads a clock.

**Non-Goals:**
- Buffers before bookings, per-booking buffers, and different buffers for different booking types.
- Time zones or DST in `now`. The stage-1 A4 assumption stands.
- Knowing about bookings on adjacent days whose buffers spill into the queried day, unless the caller
  supplies those bookings.
- A resource repository. Rules arrive in the query, as working hours already do.

## Assumptions (product questions answered by default)

These add to the stage-1 assumptions A1 to A8. A1 (gap-anchored back-to-back) now applies only when the
resource has no granularity.

| # | Question | Assumption |
|---|----------|------------|
| B1 | May the new slot's buffer run past the end of working hours? | **Yes.** Cleanup after closing is fine. It may not reach into a booking, even one outside working hours. |
| B2 | Does an existing booking's buffer count when the booking is outside, or partly outside, working hours? | Yes. Busy time is booking plus buffer, clipped to the search window. A booking 08:00-09:00 with a 20-minute buffer blocks 09:00-09:20. |
| B3 | Existing bookings that already break the buffer rule with each other? | Tolerated and merged, as in stage-1 D5. It is a query, not an integrity checker. |
| B4 | What does granularity mean? | A **fixed grid** `working_start + k*g`. **Every** grid point where the slot fits is offered, so offered slots may overlap (09:00, 09:15, 09:30 for 60-minute slots). The grid does not re-anchor after bookings. |
| B5 | A resource with no granularity? | Stage-1 back-to-back slotting from the start of each gap, with step `duration + buffer`, so consecutive offers are each bookable in turn. |
| B6 | Minimum notice: filter or shift? | A **filter**. Candidates earlier than `now + X` are dropped, and the rest keep their alignment. The cutoff is inclusive. |
| B7 | What is "now" when it is not supplied? | There is no notice filtering (stage-1 behavior). If notice is positive but `now` is missing, the query is invalid, so the rule is never silently ignored. `now` and `date` come together. |
| B8 | Which clock are `now` and `date` in? | Naive local wall-clock time of the resource, the same clock as working hours. |
| B9 | Units for X ("hours") at the CLI? | Whole minutes (`min_notice_minutes`), like every other duration in the wire format. The core takes a `timedelta`, so hours are simply `timedelta(hours=X)`. |
| B10 | Must the granularity divide the duration or the working hours? | No. The grid is independent of both. |

## Architecture

```
  JSON --> +-------+  AvailabilityQuery   +--------------------------------------+
           |  cli  | -------------------> | availability.find_slots(query)       |
  <------- +-------+ <------------------- |   composes the rules; owns no rule    |
                        list[time]        +---+----------+-----------+-------+---+
                                              |          |           |       |
                  +---------------------------+   +------+     +-----+       +------+
                  v                               v            v                    v
        +-------------------+   +------------------+   +---------------+   +------------------+
        | occupancy  (NEW)  |   | intervals        |   | slotting      |   | notice   (NEW)   |
        | BUFFER rule       |   | merge, free_gaps |   | BackToBack    |   | MIN-NOTICE rule  |
        | occupied()        |   | (unchanged)      |   | Grid   (NEW)  |   | earliest_start() |
        | search_window()   |   |                  |   | policy_for()  |   | the only code    |
        | footprint()       |   |                  |   |               |   | touching dates   |
        +---------+---------+   +--------+---------+   +-------+-------+   +--------+---------+
                  |                      |                     |                    |
                  +----------------------+----------+----------+--------------------+
                                                     v
                                    +----------------------------------+
                                    | model: Interval, ResourceRules,  |
                                    | AsOf, AvailabilityQuery,         |
                                    | InvalidQuery (all validation)    |
                                    +----------------------------------+
```

Dependencies still point only downward. None of the four rule modules imports another.

### Data flow of one query

```
 bookings --occupied(b, buffer)--> busy intervals  [b.start, b.end + buffer)
 working hours --search_window--> [wh.start, wh.end + buffer)
                                         |
                    free_gaps(window, busy)   (intervals, unchanged)
                                         v
                    gaps (ascending, disjoint)
                                         |
      policy = policy_for(rules, wh)     |   fp = footprint(duration, buffer) = duration + buffer
                                         v
                    policy.starts(gap, fp)   yields s with gap.start <= s, s + fp <= gap.end
                                         |
      cutoff = earliest_start(as_of, rules.min_notice)   (None: no filter)
                                         v
                    keep s >= cutoff  -->  to_time(s)  -->  result
```

### Components (changes only)

**`model`: gains the rule and context types (still the single owner of validity)**
- `ResourceRules(buffer: timedelta = 0, min_notice: timedelta = 0, granularity: timedelta | None = None)`:
  a frozen dataclass. It rejects a negative buffer or notice, and a granularity ≤ 0.
- `AsOf(date: datetime.date, now: datetime.datetime)`: a frozen dataclass holding the query-time facts.
  Pairing them in one type makes "only one of date/now" impossible to represent. The CLI and `of(...)`
  report that case when they build it.
- `AvailabilityQuery` gains `rules: ResourceRules = ResourceRules()` and `as_of: AsOf | None = None`. It
  rejects `rules.min_notice > 0 and as_of is None`. That is a cross-field rule, so it lives on the query.
- Why rules are separate from `as_of`: the rules are **resource configuration** and change rarely. `as_of`
  is a **fact about the moment of asking**. When a later stage adds resource lookup, `ResourceRules`
  travels with working hours, and `as_of` stays with the caller.

**`occupancy` (new): the buffer rule, the single owner of B1 and B2**
- `occupied(booking: Interval, buffer) -> Interval`: returns `[start, end + buffer)`.
- `footprint(duration, buffer) -> timedelta`: returns `duration + buffer`, the span a new slot claims.
- `search_window(working_hours, buffer) -> Interval`: returns `[wh.start, wh.end + buffer)`.
- Why this is correct: a new slot at `s` claims `[s, s + fp)`. The requirement "`[s, s+d)` inside working
  hours, the booked part clear of busy time, and the buffer clear of bookings" is equivalent to
  "`[s, s + fp)` lies inside one free gap of `search_window` minus busy". The window end
  `wh.end + buffer` turns `s + d <= wh.end` into `s + fp <= window.end`. A gap that ends before the window
  end ends where a booking starts (buffers only extend bookings forward), so `s + fp <= gap.end` is
  exactly "my buffer does not reach the next booking". Buffer-to-buffer overlap cannot happen once
  booking/buffer overlap is excluded. So buffers never become objects the caller sees. They are only a
  widening of busy time and of the new slot's footprint.
- B1 is a single line here. If the product owner says "the buffer must end by closing time", the fix is
  `search_window = working_hours`. Nothing else changes.

**`slotting`: the policy is now selected, not fixed (the owner of A1, B4, B5)**
- The interface changes from `back_to_back(gap, duration)` to a small protocol:
  ```python
  class SlotPolicy(Protocol):
      def starts(self, gap: Interval, footprint: timedelta) -> Iterator[timedelta]: ...
  ```
  The contract is: ascending, `gap.start <= s`, and `s + footprint <= gap.end`.
- `BackToBack()`: `gap.start + k*footprint`. With buffer 0, this is exactly stage 1.
- `Grid(anchor, step)`: the first point `anchor + k*step` that is `>= gap.start` (ceiling division on
  offsets), then every `step` while it fits.
- `policy_for(rules, working_hours) -> SlotPolicy`: returns `Grid(working_hours.start, g)` if a
  granularity is set, otherwise `BackToBack()`. This is the only place that turns "granularity is set"
  into behavior.
- The policy sees a gap and a length. It does not know that the length includes a buffer, and it does not
  know about notice.

**`notice` (new): the minimum-notice rule, the single owner of B6 to B8**
- `earliest_start(as_of: AsOf | None, min_notice) -> timedelta | None`: returns
  `(as_of.now + min_notice) - datetime.combine(as_of.date, time.min)`, or `None` when `as_of` is `None`.
- The result is a day offset, like everything else. It may be negative (every candidate passes) or larger
  than a day (none pass). No clamping is needed, because offsets are unbounded `timedelta`s.
- This is the only module that handles `date` or `datetime`. The core outside `notice` and the adapters
  stays date-free.

**`availability`: composition only**
- `find_slots` follows the data flow above. The ordering and uniqueness guarantee is still structural:
  - gaps are ascending and disjoint
  - each policy yields ascending starts inside its gap
  - the notice filter keeps order

  No final sort is needed.
- `AvailabilityQuery.of(...)` gains keyword arguments `buffer`, `min_notice`, `granularity`, `date`, and
  `now`.

**`cli`: wire format only**
- New optional fields: `buffer_minutes`, `min_notice_minutes`, `granularity_minutes`, `date`
  (`YYYY-MM-DD`), and `now` (`YYYY-MM-DDTHH:MM[:SS]`). Omitted fields map to the `ResourceRules`
  defaults.
- The CLI does **not** read the system clock (D12).

## Decisions

**D7. The buffer is modeled as a widening of occupancy, not as pseudo-booking intervals.**
Existing bookings become `[start, end + buffer)`, and a candidate claims `duration + buffer`. The whole
buffer rule then reduces to the unchanged `free_gaps` plus one length.
*Alternative:* insert buffer intervals into the busy list, then separately check each candidate's tail
against "the next booking". That needs two mechanisms and a next-booking lookup. It also creates
buffer objects that could leak into output or be confused with bookings, which the rule explicitly forbids.
Rejected.

**D8. The search window extends past closing by the buffer (B1).**
This expresses "the buffer may spill past close but never into a booking" without a special case. A
booking just after closing still blocks the slot, because it is busy inside the extended window.
*Alternative:* keep the window equal to working hours, which means the buffer must finish by closing.
That is plausible but stricter, and it loses a valid last slot of the day. It remains a one-line switch
(see Risks).

**D9. Slotting becomes a selected strategy, with back-to-back kept as the no-granularity policy (B4, B5).**
Stage-1 D3 already isolated alignment in `slotting` for this purpose.
- *Alternative:* default granularity = duration, anchored at opening. This breaks the stage-1
  "alignment restarts after an off-grid booking" scenario, so stage-1 behavior would change without the
  new rule being configured. Rejected.
- *Alternative:* "back-to-back, but snapped up to the grid". This is harder to explain, and it is not what
  "offered start times must align to a granularity, *not merely back-to-back*" asks for. Rejected, and
  recorded as B4.

**D10. Minimum notice is a filter on candidates, not busy time (B6).**
If the notice period were busy time `[open, cutoff)`, the first free gap would start at an arbitrary
cutoff such as 10:37. Back-to-back slotting would then re-anchor there and shift every slot of the
morning. The spec says slots earlier than the cutoff "are not offered", not that others move. A filter
also keeps dates out of `intervals` and `slotting`.
*Alternative:* pass the cutoff into policies as a lower bound. For `Grid` that is equivalent and saves
iterations, but for `BackToBack` it risks exactly the re-anchoring above. The filter's cost is O(slots),
which is negligible. Rejected as premature optimization.

**D11. `now` and `date` travel together in `AsOf`, and there is a single cutoff formula.**
The spec supports cutoffs on a previous or following day, so the rule needs the queried date, not just a
time of day. Converting once to a day offset keeps D2 (offsets everywhere) intact.
*Alternative:* `now` as a time of day, assumed to be on the queried day. This cannot express "booking
tomorrow with 24 h notice". Rejected.

**D12. Neither the core nor the CLI reads a clock.**
The core must be reproducible, and every spec scenario is a fixed-`now` test. For the CLI, a caller who
wants "now" passes `"now": "$(date +%FT%T)"`.
*Alternative:* the CLI defaults `now` to `datetime.now()`. That makes CLI output time-dependent, and it
quietly turns notice on for every stage-1 CLI query. Rejected.

**D13. Validation stays at construction (stage-1 D4).**
The rules are validated in `ResourceRules`, and the cross-field rule on `AvailabilityQuery`. `occupancy`,
`notice`, and `slotting` take `buffer >= 0`, `granularity > 0`, and "notice without now cannot happen"
for granted.

## Risks / Trade-offs

- [B4: the product may mean "one slot per grid step, non-overlapping" rather than every grid point.] →
  This is isolated in `slotting.Grid`. The alternative is `step = ceil(footprint / g) * g`, a
  one-class change plus scenario updates.
- [B1: the product may require cleanup to finish by closing time.] → Change `search_window` in
  `occupancy` to return working hours. Two spec scenarios flip.
- [A booking late on the previous day whose buffer crosses midnight is invisible unless supplied.] →
  This is inherent to a single-day query (stage-1 A4). Times of day cannot express "yesterday", so the
  caller cannot pass such a booking today. It is documented as a non-goal. A multi-day stage would move the
  window to datetimes, and `occupancy` would be unchanged.
- [Small granularity with long days gives many candidates.] → At most (day length / g) candidates, for
  example 1,440 at one minute. This is trivial.
- [`now` is naive, so DST days can be off by an hour near the transition.] → This is consistent with A4.
  A zone-aware edge layer can convert to naive local time before building `AsOf`.

## Migration Plan

This is additive and not breaking. Every new field has a neutral default: buffer 0, no granularity, and
no `as_of`. Stage-1 library calls and CLI JSON produce identical output. The stage-1 scenarios stay in the
spec and are the regression suite. Rollback means removing the new optional fields. No data migration
exists, because there is no persistence.


<!-- file: tasks.md -->

# Tasks

## 1. Model: rules and query-time context

- [ ] 1.1 Add `ResourceRules(buffer, min_notice, granularity)` with defaults 0/0/None. Validate that buffer and notice are not negative and that granularity is positive, with messages that name the field. Verify with unit tests for the "Negative buffer" and "Zero granularity" scenarios.
- [ ] 1.2 Add `AsOf(date, now)`. Add `rules` and `as_of` to `AvailabilityQuery`, reject positive notice without `as_of`, and extend `AvailabilityQuery.of(...)` with the new keywords, rejecting "only one of date/now". Verify with the "Minimum notice without now" test, and check that the stage-1 construction tests still pass unchanged.

## 2. Buffer rule (`occupancy`)

- [ ] 2.1 Implement `occupied`, `footprint` and `search_window`, with a module docstring stating assumptions B1 to B3 and the equivalence argument from design.md. Verify with unit tests for buffer 0 (identity), a booking before hours, and a booking after closing.

## 3. Slotting policies

- [ ] 3.1 Refactor `back_to_back` into the `SlotPolicy` protocol with `BackToBack` (step = footprint). Verify that the existing slotting tests pass when footprint equals duration, and add a test with a footprint larger than the duration.
- [ ] 3.2 Implement `Grid(anchor, step)` with a ceiling to the first grid point at or after `gap.start`, plus `policy_for(rules, working_hours)`. Verify with unit tests for a gap starting on the grid, a gap starting off the grid, a gap shorter than the footprint, and anchoring to a working-hours start that is not on the hour.

## 4. Notice rule (`notice`)

- [ ] 4.1 Implement `earliest_start(as_of, min_notice)` returning a day offset or `None`, with a docstring stating assumptions B6 to B8. Verify with unit tests for a same-day cutoff, a previous-day `now` (negative or small offset), a cutoff beyond the day, and `as_of=None`.

## 5. Composition

- [ ] 5.1 Rewire `availability.find_slots` to follow the design's data flow: occupancy, then free_gaps, then policy, then notice filter. Verify with one test per new spec scenario (buffer, notice, granularity, combined, tolerant-after-hours), and check that every stage-1 scenario test still passes unmodified.
- [ ] 5.2 Add a property-style test over random small queries. It checks that the output is strictly ascending, and that each offered start satisfies the spec's fit rule when checked by brute force (booked part in hours, no overlap with booking+buffer, own buffer clear of bookings, on-grid, not before the cutoff). Verify that the test passes for several hundred generated cases.

## 6. CLI

- [ ] 6.1 Parse `buffer_minutes`, `min_notice_minutes`, `granularity_minutes`, `date` and `now`. Map omitted fields to the defaults, and never read the clock. Verify with subprocess tests for "CLI with rules", an existing stage-1 CLI scenario, and a malformed `now`.
- [ ] 6.2 Update the README CLI section with the new fields and the "CLI with rules" example. Verify that the documented command gives the documented output.

## 7. Integration check

- [ ] 7.1 Run the full test suite and `the-method validate add-buffer-notice-granularity --strict`. Verify that both pass.
