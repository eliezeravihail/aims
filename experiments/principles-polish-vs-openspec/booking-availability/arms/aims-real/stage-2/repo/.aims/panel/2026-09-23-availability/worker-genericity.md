# Worker result — axis: correct genericity

The design question behind every choice below: for each type and seam, what is the **floor**, meaning the least its consumer needs to be complete, and what is the **ceiling**, meaning the most every producer can honestly supply? Each type and seam sits between those two. Seams go only on the known change axes: R1–R6, and the stage-1 non-goals I name only as future absorption points.

---

## 1. The design

### 1.1 File tree

```
booking-availability/
  availability/
    __init__.py      # published surface: TimeRange, available_starts, InvalidInputError, OverlappingBookingsError
    errors.py        # error vocabulary (public)
    timerange.py     # TimeRange: the half-open wall-clock range value type (public)
    _clock.py        # private: wall-clock arithmetic that datetime.time lacks
    _schedule.py     # private: DaySchedule, the validated working day and its free gaps (pure core)
    _stepping.py     # private: gap_aligned_starts, the slot policy R1 (pure core)
    query.py         # available_starts: the public entry point (boundary + composition)
  tests/
    test_timerange.py
    test_available_starts.py
```

Dependencies are acyclic and point toward the stable leaves:
`query → _schedule, _stepping, timerange, errors`; `_schedule → timerange, errors`;
`_stepping → timerange, _clock`; `timerange → _clock, errors`; `_clock → (stdlib only)`; `errors → (nothing)`.

**Entry point: an in-process library function, with no CLI.** The only named consumer is "a scheduling UI or another service in the same process" (goals.md). A CLI would need a parser and a text format that nobody consumes, so no present force supports it.

### 1.2 What each concept IS

| Concept | What it is in this design | Why this kind of thing |
|---|---|---|
| Working window | a `TimeRange` (parameter role `working_hours`) | a half-open wall-clock range, and nothing more in stage 1 |
| Booking | a `TimeRange` (parameter role `bookings`) | a half-open range; in stage 1 a booking has no id, owner or state (storing bookings is a non-goal) |
| Free time between bookings | a `TimeRange` **produced by** `DaySchedule.free_gaps()` | a real range, derived and never supplied by callers; it is not a fake booking and not a "negative booking" |
| Candidate slot | **never materialized.** It exists only as `start + duration` inside the stepping arithmetic | the output is start times (spec), so a slot object would be a type nobody consumes |
| Requested duration | `datetime.timedelta` | the foundational stdlib type for a length of time; its one rule (> 0) is checked once, at one place |
| Slot policy | one function, `gap_aligned_starts(gap, duration)` | the rule that turns a gap into starts; its own module because it changes for a different reason than gap derivation |
| The day under query | `DaySchedule` (private) | the validated combination of working window and busy time; its type carries the "sorted, disjoint, clipped" invariant that the core trusts |

Window, booking and gap are **roles of one concept**, not three concepts. They have identical behavior (half-open semantics, intersection, length) and differ only in where they come from and who consumes them. The roles show in parameter names, in the field name `busy`, and in the name of the function that produces gaps. Concept fit holds: a gap is never built as a `Booking`, and nothing is a degenerate stand-in for its neighbour.

### 1.3 Public surface, with concrete signatures

```python
# availability/errors.py
class InvalidInputError(ValueError):
    """The caller supplied input that violates a product rule (R4, R5, R6). A caller bug:
    fix the input, don't retry. Message states what was wrong in the caller's terms."""

class OverlappingBookingsError(InvalidInputError):
    """R4: two supplied bookings overlap. Carries both, so the caller can locate them in its
    own data (TimeRange has no id)."""
    first: TimeRange
    second: TimeRange
    def __init__(self, first: TimeRange, second: TimeRange) -> None: ...
    # message: "bookings 10:00–11:00 and 10:30–11:30 overlap; bookings must not overlap
    #           (touching, e.g. 10:00–10:30 and 10:30–11:00, is allowed)"
```

```python
# availability/timerange.py
@dataclass(frozen=True, slots=True)
class TimeRange:
    """A non-empty half-open range [start, end) of naive wall-clock time within one day.
    Invariant (checked in __post_init__, the single owner of R5-for-ranges and of R6):
      start < end; start.tzinfo is None and end.tzinfo is None.
    Raises InvalidInputError otherwise."""
    start: time
    end: time

    @property
    def length(self) -> timedelta: ...
    def overlaps(self, other: "TimeRange") -> bool:
        """R2: True iff they share a moment. Touching ranges (a.end == b.start) do not overlap.
        The only place the half-open comparison is written: self.start < other.end and other.start < self.end."""
    def intersection(self, other: "TimeRange") -> "TimeRange | None":
        """The shared part, or None when they do not overlap (so touching → None).
        Defined via overlaps(), so half-openness has one owner."""
```

```python
# availability/query.py   (re-exported from availability/__init__.py)
def available_starts(
    working_hours: TimeRange,
    bookings: Iterable[TimeRange],
    duration: timedelta,
) -> list[time]:
    """Start times, earliest first, at which a booking of `duration` fits entirely inside
    `working_hours` without overlapping any of `bookings`.
    Pre (checked here — this is the public boundary): duration > 0 (R5); bookings pairwise
      non-overlapping (R4, checked in DaySchedule.build). TimeRange validity was already
      enforced when the caller constructed each TimeRange.
    Post: strictly ascending; each s satisfies working_hours.start <= s and s + duration <= working_hours.end,
      and [s, s+duration) overlaps no booking; [] when nothing fits (not an error).
    Raises: InvalidInputError (duration <= 0), OverlappingBookingsError (R4)."""
```

The published surface has four names: `TimeRange`, `available_starts`, `InvalidInputError` and `OverlappingBookingsError`.

### 1.4 Private core, with concrete signatures

```python
# availability/_clock.py — datetime.time has no arithmetic; this is the one place it is supplied.
def shift(t: time, delta: timedelta) -> time:
    """t + delta. Pre: the result is on the same day (callers guarantee it stays < some range end)."""
def span(start: time, end: time) -> timedelta:
    """end - start as a timedelta. Pre: start <= end."""
```

```python
# availability/_schedule.py
@dataclass(frozen=True, slots=True)
class DaySchedule:
    """One resource's day: the working window and the busy time inside it.
    Invariant: every range in `busy` lies inside `hours`, `busy` is sorted by start,
    and its members are pairwise non-overlapping (touching allowed)."""
    hours: TimeRange
    busy: tuple[TimeRange, ...]

    @classmethod
    def build(cls, hours: TimeRange, bookings: Iterable[TimeRange]) -> "DaySchedule":
        """The one construction path. Owns R4 (sort; reject an overlapping pair, found by
        checking neighbours after sorting by (start, end)) and R3 (keep only each booking's
        intersection with hours; drop those with none)."""

    def free_gaps(self) -> Iterator[TimeRange]:
        """Pure core. The maximal free ranges inside hours, ascending and disjoint.
        Trusts the invariant; performs no validation. A gap is yielded only when
        cursor < next busy start, so touching busy ranges produce no zero-length gap."""
```

```python
# availability/_stepping.py
def gap_aligned_starts(gap: TimeRange, duration: timedelta) -> Iterator[time]:
    """R1, the one owner. Starts at gap.start, then gap.start + duration, ...: exactly
    gap.length // duration of them, so a leftover shorter than duration is not offered.
    Pre: duration > 0 (guaranteed by available_starts). Uses a count rather than a
    while-loop, so no sequence of calls can make it loop forever."""
```

Composition inside `available_starts` is three steps at one level of abstraction:

```python
    if duration <= timedelta(0):
        raise InvalidInputError(f"duration must be positive, got {duration}")
    day = DaySchedule.build(working_hours, bookings)
    return [s for gap in day.free_gaps() for s in gap_aligned_starts(gap, duration)]
```

"Earliest first" requires no sort step. It follows from two postconditions: `free_gaps` is ascending and disjoint, and `gap_aligned_starts` is ascending within a gap.

### 1.5 Rule ownership

| Rule | Single owner | Mechanism |
|---|---|---|
| R1 gap-aligned stepping; leftover not offered | `_stepping.gap_aligned_starts` | `range(gap.length // duration)` |
| R2 half-open; touching ≠ overlapping; may end at close | `TimeRange.overlaps` (and `intersection`, defined through it) | a single strict comparison; `free_gaps` emits only non-empty gaps; the stepping count uses `//`, which admits `start + duration == gap.end` |
| R3 only the part inside working hours matters | `DaySchedule.build` (decides to clip) via `TimeRange.intersection` (mechanism) | a wholly-outside or merely touching booking gives `None` and is dropped |
| R4 unsorted accepted; overlap rejected naming the pair; touching fine | `DaySchedule.build` | `sorted(key=(start,end))`, then `overlaps` on each neighbouring pair raises `OverlappingBookingsError(a, b)` |
| R5 range end <= start | `TimeRange.__post_init__` | raises `InvalidInputError` |
| R5 duration <= 0 | `available_starts` | raises `InvalidInputError` |
| R5 no fit gives [] | structural | a zero count everywhere yields an empty list |
| R6 naive, one day, no midnight crossing | `TimeRange` (field type `time`, plus the naive check) | a `time` cannot cross midnight; `end > start` rules out wrap; an aware time is rejected |

The neighbour check after sorting is sufficient. Sort by start. If a overlaps some later c, and b lies between them, then b.start ≤ c.start < a.end and a.start ≤ b.start < b.end, so a overlaps b as well. Any overlap therefore shows up as a neighbouring pair, and that pair really does overlap, so the error always names a true offending pair.

### 1.6 Where validation happens: the boundary and the trusted core

Untrusted input becomes domain values in exactly three places, each validating one rule family once:
1. `TimeRange(...)`, which the caller constructs. This is the boundary for single-range validity (R5-range, R6).
2. `available_starts`. This is the boundary for the request-level scalar (R5-duration).
3. `DaySchedule.build`, the one construction path, reached only from `available_starts`. This is the boundary for relational validity across the booking set (R4), and it normalizes (R3).

After that point, `free_gaps` and `gap_aligned_starts` validate nothing. They trust the `DaySchedule` invariant and the duration precondition.

The `TimeRange` check also runs when the core constructs gaps and intersections, and it never fails there. That is an invariant of a public value type, not a second validation of input. The type is published, so its constructor is the only place the rule can have one owner.

### 1.7 Trace of C1–C14

| Case | Path through the design | Result |
|---|---|---|
| C1 | build: sorted [09:00–09:45, 11:00–12:00], neighbours don't overlap, both clip to themselves. free_gaps: cursor 09:00; the first busy range starts at the cursor so no gap, cursor 09:45; gap 09:45–11:00, cursor 12:00; tail gap 12:00–17:00. Stepping: 75m//30m = 2 gives 09:45, 10:15; 5h//30m = 10 gives 12:00…16:30 | `09:45, 10:15, 12:00, 12:30, …, 16:30` ✓ |
| C2 | busy = (); one gap 09:00–17:00; 8h//30m = 16 | 09:00…16:30 ✓ |
| C3 | busy covers 09:00–17:00 (directly, or after a wider booking is clipped); the cursor reaches 17:00; no gap | `[]` ✓ |
| C4 | every `gap.length // duration` = 0 (including 8h // 9h) | `[]` ✓ |
| C5 | a 30m gap with 30m duration: 1 → exactly one start. A 75m gap: 75//30 = 2 → two starts | ✓ |
| C6 | 08:00–09:00 ∩ 09:00–17:00: `overlaps` is false (09:00 < 09:00 fails), so `None` and dropped. 17:00–18:00 is dropped the same way | no effect ✓ |
| C7 | 08:30–09:30 ∩ hours = 09:00–09:30; 16:30–17:30 clips to 16:30–17:00 | clipped ✓ |
| C8 | 10:00–10:30 vs 10:30–11:00: `overlaps` is false, so accepted; in free_gaps the cursor equals the next start, so no gap is emitted | no slot between ✓ |
| C9 | 10:00–11:00, 10:30–11:30: the neighbour check hits and raises `OverlappingBookingsError(first=10:00–11:00, second=10:30–11:30)` | rejected, pair named ✓ |
| C10 | `sorted` in build; everything downstream depends only on `busy` | identical ✓ |
| C11 | `TimeRange(time(10), time(10))` or a reversed range raises `InvalidInputError` at construction, whether it is a booking or the working hours | rejected ✓ |
| C12 | `available_starts(..., timedelta(0))` or a negative duration raises `InvalidInputError` before any work | rejected ✓ |
| C13 | 2h gap, 45m: 120//45 = 2, giving start and start+45m; the last 30m is unused | 2 slots ✓ |
| C14 | tail gap …–17:00; the count admits `start + duration == end` (R2), so 16:30 is offered | ✓ |

### 1.8 Tracing the input space beyond C1–C14

These are change axes crossed with rules. Each case is resolved by the design as it stands; none needs new machinery.
- **Duplicate identical bookings.** They overlap, so R4 rejects them. This is consistent with "surface, don't merge."
- **Booking identical to working hours, or a superset of it.** It clips to the hours, giving `[]`.
- **A booking nested inside another.** Its neighbour after sorting overlaps it, so it is rejected.
- **Same start, different end.** The sort key `(start, end)` is deterministic, and the pair overlaps, so it is rejected.
- **Duration longer than 24h.** The count is 0, giving `[]`. There is no overflow, because `shift` is only called with k·duration < gap.length.
- **Sub-minute or microsecond durations and times.** `timedelta // timedelta` is exact integer arithmetic, so there is no float drift.
- **Aware `time` values.** `TimeRange` rejects them (R6), so the failure is not a stray `TypeError` from comparing aware and naive values deep in the core.
- **`bookings` passed as a one-shot generator.** It is consumed exactly once, by `sorted` in `build`.
- **Overlapping bookings that both lie outside working hours.** These are rejected: R4 is checked on the raw bookings, before R3 clipping. See the open question in §5.

---

## 2. Design reasoning

### 2.1 Calibration of each seam: floor and ceiling

| Seam | Chosen | Floor (consumer needs) | Ceiling (every producer can supply) | Rejected: too specific | Rejected: too generic |
|---|---|---|---|---|---|
| `bookings` param | `Iterable[TimeRange]` | the core reads every booking once (it sorts) | lists, tuples, generators, query rows mapped to ranges | `list[TimeRange]`, or a *sorted* `Sequence`, because R4 says the service sorts | `Iterable[tuple[time,time]]`, a data clump with no home for R5 |
| `working_hours` | `TimeRange` | one start and end, with the same half-open semantics as bookings | any caller knows its window | a `WorkingHours` newtype: same behavior, no extra rule | separate `open`/`close` params, which duplicate TimeRange's validation |
| `duration` | `timedelta` | a positive length | any caller can build one from minutes or anything else | `int` minutes, which is primitive obsession and truncates seconds | a custom `SlotDuration` (see §2.3) |
| Return | `list[time]` | an ordered, finite, re-readable pick-list of start times (goals.md) | the core produces exactly this | `list[TimeRange]` slots: a shape nobody asked for, since ends are derivable | `Iterator[time]`: a UI needs `len`/re-reading, and the spec says "empty list" |
| Time currency | `datetime.time` | wall-clock times of one day (R6) | every caller has wall-clock times; a *date* would be invented data | n/a | `datetime`: it forces callers to invent a date, and makes same-date checks and midnight crossing representable, which adds two rules that R6 removes |
| Range type | a concrete `TimeRange` over `time` | overlap, intersection, length | n/a | three role types (`Booking`, `FreeGap`, `Window`) | `Interval[T]` generic over an ordered `T`: no second `T` exists, and `length` needs `T - T → delta` |
| Slot policy | one function | the stepping rule R1 | only one policy exists (0002 rejected the grid) | inlining it into `free_gaps`, which would mix two change axes in one owner | a `SlotPolicy` Protocol or Strategy with a single implementation |
| Error types | base + one subtype | a clear message; the offending pair as data (C9) | n/a | a subtype per rule (`EmptyRange`, `BadDuration`): no caller handles them differently, so they would be dead subtypes | a single type: it loses the pair as structured data |

### 2.2 Each abstraction and the present force behind it

- **`TimeRange`** answers R2 (one owner of half-openness), R5 for ranges, and R6. It prevents primitive obsession across a published seam. Illegal states (empty, reversed or aware ranges) cannot be represented.
- **`DaySchedule`** answers the boundary/core split the objective demands. Its type is evidence that R4 has been validated and R3 normalized, so `free_gaps` can trust its input by construction rather than by comment. It has behavior (`build`, `free_gaps`), so it is not an anemic bag. Its field is named `busy`, not `bookings`, because after clipping these are occupied spans, not the caller's bookings.
- **`gap_aligned_starts`** answers R1, and it is a separate owner because it is a separate change axis. Grid alignment, the one alternative anyone has proposed (0002), would replace this function and leave gap derivation untouched. Gap derivation changes for other reasons, such as breaks or buffers (non-goals).
- **`_clock`** answers a gap in the foundation: `time` has no `+ timedelta`. The arithmetic lives in one private place instead of ad-hoc `datetime.combine` calls in several modules.
- **`InvalidInputError` / `OverlappingBookingsError`** answer "clear error" (R4, R5) and "names the offending pair" (C9). The base subclasses `ValueError`, so idiomatic callers catch it without importing anything.

### 2.3 Alternatives rejected

- **A `SlotDuration` value type.** Its only rule (> 0) is checked once, in the one entry that receives it, and its only consumer is one private function. `timedelta` is already a foundational value object, not a primitive. A wrapper would force every caller to learn a new type and would buy nothing. The falsifier: a second public entry that takes a duration would make this type worth adding.
- **Role types (`Booking`, `FreeGap`, `WorkingHours`) wrapping or subclassing `TimeRange`.** In stage 1 no role has behavior or data the others lack. They would be decorative types, and subclassing would invite exactly the "gap as a synthetic booking" cram that concept fit forbids. The falsifier: a booking gaining an id, status or owner would earn a real `Booking` type that *has* a `TimeRange`. Storing bookings is a non-goal, so that force is absent.
- **A `Slot` type.** The output contract is start times. A materialized slot would have no consumer.
- **Validation inside the core, as a free function `free_gaps(hours, bookings)` that validates and computes.** This mixes the boundary with the core, and its precondition would be implicit in a bare tuple.
- **Merging overlapping bookings.** Ruled out by 0002.
- **A CLI or text adapter.** There is no consumer (§1.1).
- **A `while start + d <= end` stepping loop.** It is correct only if d > 0, and it hangs silently otherwise. The integer count `gap.length // duration` states R1 directly ("how many whole durations fit") and cannot loop.

### 2.4 Change axes: what the design would absorb, and where (nothing is built for these)

- **Breaks inside working hours.** Extra busy spans enter `DaySchedule.build`, one owner. A break is not a booking, and `busy` already names the right concept.
- **Buffers.** Widen spans inside `DaySchedule.build`, the single owner of busy time, not as a trailing filter.
- **Fixed-grid alignment.** Replace or parameterize `gap_aligned_starts`, the one owner of R1.
- **Multiple resources.** The caller calls `available_starts` once per resource. The core is unaffected.
- **Multi-day or time zones.** The field types of `TimeRange` and `_clock` change. This is the one axis whose change reaches callers, which is acceptable because it changes the product's time model (R6) itself.

### 2.5 Principles that do not apply at this scale

- **Ports and adapters, DIP, Repository.** There is no I/O, persistence or framework, so the whole library is the functional core. A port with no adapter would be decorative.
- **§11 concurrency and §14 trust boundaries.** Everything is immutable, there is no shared state, and there is no security boundary. The "boundary" here is correctness validation (§1 of the principles), not a security boundary.
- **§13 performance.** No requirement is stated. The design is O(n log n), dominated by the sort, which is the natural cost.

### 2.6 Subtractive pass and concept-fit pass (done)

**Subtractive pass.** Every element was checked against a present force.

Kept:
- `TimeRange` (R2, R5, R6).
- `DaySchedule` (R3, R4, trust by construction).
- `gap_aligned_starts` (R1, its own axis).
- `_clock` (the stdlib gap).
- Two error types (the clear-error requirement and C9's pair).
- The naive-time check in `TimeRange` (R6, fail fast instead of a stray `TypeError`).

Removed during the pass:
- A `SlotDuration` type.
- Role newtypes.
- A `Slot` type.
- A `SlotPolicy` Protocol.
- A CLI.
- Per-rule error subtypes.
- `order=True` on `TimeRange`: a public `<` between ranges would have an ambiguous meaning, so the sort key lives in the one place that sorts.
- A `contains` method, which had no caller.

**Concept-fit pass.**
- Free time is its own produced value from `free_gaps()`. It is not a synthetic booking, and not the *absence* of busy time either: it is emitted explicitly.
- The slot policy is a stepping rule. It is not a score or a filter over a grid.
- A booking outside the hours is dropped by intersection, not modelled as a zero-length range. Zero-length ranges are unrepresentable.
- Duration is a length, not a range.

No stand-ins remain.

---

## 3. Test plan (test-first, stdlib `unittest`)

Tests assert observable contracts at the two **published** seams. The private modules are covered through `available_starts`, so the internals stay free to refactor.

**`tests/test_timerange.py`**: the published value type's contract.

| Decision | Test | Case |
|---|---|---|
| R5 range: end == start rejected | `TimeRange(10:00, 10:00)` raises `InvalidInputError` | C11 |
| R5 range: end < start rejected | `TimeRange(11:00, 10:00)` raises | C11 |
| R6: aware time rejected | a `time` with `tzinfo` raises | R6 |
| R2: touching is not overlapping | `overlaps` is false for 10:00–10:30 and 10:30–11:00, in both orders | C8 |
| R2: overlapping detected, including nested and identical ranges | `overlaps` is true | C9 |
| R2/R3: intersection of touching ranges is `None` | 08:00–09:00 ∩ 09:00–17:00 | C6 |
| R3: intersection clips a straddling range | 08:30–09:30 ∩ 09:00–17:00 → 09:00–09:30 | C7 |
| length | 09:45–11:00 → 75 min | supports C5 and C13 |

**`tests/test_available_starts.py`**: the public entry point. Every product case is tested here.

| Test | Covers |
|---|---|
| worked example exact list | C1 |
| no bookings → 09:00 … 16:30 (16 starts) | C2 |
| a whole-day booking, and a wider-than-day booking → `[]` | C3, C7 |
| duration > every gap; duration > working hours → `[]` | C4 |
| gap == duration → one start; gap = 2.5× → two | C5 |
| a booking ending at opening and one starting at close → same as no bookings | C6 |
| a booking straddling opening; one straddling close → first/last start shifted | C7 |
| touching bookings accepted; no start between them | C8 |
| overlapping bookings → `OverlappingBookingsError` with `.first` and `.second` equal to the pair; also nested and duplicate pairs | C9 |
| a shuffled permutation of the bookings gives identical output; a generator input works | C10 |
| (C11 is covered in the TimeRange tests, where the rejection happens) | C11 |
| `timedelta(0)` and a negative duration → `InvalidInputError` | C12 |
| 45 min in a 2 h gap → exactly 2 starts | C13 |
| the last start ends exactly at close (16:30 offered) | C14 |
| output is strictly ascending across several gaps (regression guard for "earliest first") | output contract |
| overlapping bookings wholly outside hours → rejected (pins the open-question decision) | §5 Q1 |

---

## 4. Result

**met.** Every rule R1–R6 has exactly one owner (§1.5). Input is validated once, where it becomes a domain value, and the core (`free_gaps`, `gap_aligned_starts`) trusts it (§1.6). The computation is pure over two value types, `TimeRange` and `DaySchedule`, plus the foundational `time`/`timedelta` (§1.3, §1.4). The concrete module skeleton and signatures leave the builder nothing to invent (§1.1–§1.4). C1–C14 are traced (§1.7).

## 5. New facts, risks and open questions

1. **Open product question (the rules conflict).** Take two bookings that overlap each other but lie wholly outside working hours, for example 07:00–08:00 and 07:30–08:30 with hours 09:00–17:00. R3 says they are irrelevant; R4 says overlapping bookings are rejected. **Chosen:** R4 on the raw bookings, which means rejection, because 0002 frames an overlap as a caller bug to *surface*, independent of the query window. The choice is pinned by a test, and switching it is a one-line change of order inside `DaySchedule.build`, its single owner. This needs the owner's confirmation.
2. **Closing at midnight cannot be expressed.** `datetime.time` has no 24:00, so working hours such as 18:00–24:00 cannot be stated. The nearest option is an end of 23:59:59.999999, which leaves a final slot ending "at midnight" unofferable. R6 says hours "do not cross midnight" but is silent on *ending at* midnight. If that must be supported, the fix is local to `TimeRange` and `_clock`, for example an explicit end-of-day sentinel. This needs the owner's confirmation.
3. **Risk (accepted).** Choosing `time` over `datetime` means the multi-day or time-zone axis (a non-goal) will change the published `TimeRange` field types and so reach callers. This is deliberate: making callers supply an invented date now would be more specific than any producer can honestly supply.
4. **Minor.** The error message format (`HH:MM`, or showing seconds when they are non-zero) is a presentation detail. It is owned by `errors.py` and needs no product decision.
