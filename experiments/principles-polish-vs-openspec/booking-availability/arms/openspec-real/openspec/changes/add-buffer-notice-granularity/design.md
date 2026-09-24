# Design

## Context

Stage 1 is archived at `openspec/changes/archive/2026-09-23-add-booking-availability/design.md`. Its
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
