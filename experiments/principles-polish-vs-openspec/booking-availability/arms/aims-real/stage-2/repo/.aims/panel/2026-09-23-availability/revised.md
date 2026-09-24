# Bookable slots, stage 1: architecture (revised after the review round)

A stage-1 architecture for a "bookable slots" service, written in Python 3.11 with the standard library
only. It is written for the person who will build it. This file stands on its own and does not rely on any
other file.

---

## 0. The problem, in one paragraph

We are given three things for one resource on one day: its working hours (one window), that day's existing
bookings (each a start/end interval), and a requested duration. We must return every start time at which a
new booking of that duration fits entirely inside the working hours and overlaps no booking. The list is
earliest first. Slots are laid back-to-back from the start of each free gap.

---

## 1. Assumptions and product rules

### 1.1 Decided product rules (not open to re-decision)

- **R1 Gap-aligned stepping.** Within each maximal free gap, slots start at the gap's start and step
  forward by the duration, back-to-back. A leftover shorter than the duration is not offered. This is not a
  fixed grid across the day.
- **R2 Half-open intervals `[start, end)`.** A slot may start exactly when a booking ends. A slot may end
  exactly at close. Touching is not overlapping.
- **R3 Only the part of a booking inside working hours matters.** A booking wholly outside the hours is
  irrelevant.
- **R4 Bookings may arrive unsorted, and the service sorts them.** Bookings that overlap each other are
  rejected with a clear error that names the pair. Touching bookings are fine.
- **R5 Clear errors for invalid input.** Working hours or a booking with `end <= start` is an error. A
  duration `<= 0` is an error. When no gap fits, the result is `[]`, which is not an error.
- **R6 Time model.** Times are naive wall-clock times within one local day. There are no time zones and no
  DST, and working hours do not cross midnight.

### 1.2 Stated assumptions

Each of these answers a question that R1–R6 leave open. The "change lands in" column names the single place
that would change if the owner decides otherwise.

| # | Assumption | Why this choice | Change lands in |
|---|---|---|---|
| A1 | **Bookings that overlap each other are rejected even when both lie wholly outside the working hours.** R4 is checked on the raw bookings, *before* R3 clips them. | Decision 0002 treats an overlap as a caller bug to surface, and a calendar bug is a bug wherever it sits. R3 says an outside booking is irrelevant to *which slots are offered*, not that its validity goes unchecked. | `DaySchedule.__init__`: swap step 2 (check overlap) and step 3 (clip). This is one owner, and R4 keeps that one owner. |
| A2 | **Identical duplicate bookings are rejected** as an overlapping pair. | Two copies of the same range share every moment, so under R2 they overlap. Silently removing duplicates would be the "merge" that 0002 rules out. | `DaySchedule.__init__` (dedupe before the overlap check). |
| A3 | **Working hours cannot end at 24:00.** `datetime.time` has no 24:00. The latest end that can be written is `time.max` (23:59:59.999999), so a slot ending exactly at midnight cannot be offered. | R6 forbids crossing midnight and does not mention *ending at* midnight. The simplest honest reading is "the day ends before midnight". | `time_range.py` only: an end-of-day sentinel for `end`, plus the private `_offset`/`_at` helpers. |
| A4 | **Time-zone-aware `time` values are rejected** (`InvalidAvailabilityRequest`). | "No time zones" (R6) is read as *fail fast*, not *compare by UTC offset*. Otherwise the error would be a stray `TypeError` from comparing a naive time with an aware one somewhere deep in the core. | `TimeRange.__post_init__` (the `_require_wall_clock` helper). |
| A5 | **There is no output cap and no minimum granularity.** Seconds and microseconds pass through untouched. A 1 µs duration over 8 h returns about 2.9·10¹⁰ starts. | Neither limit was asked for, and inventing one would be a product rule nobody decided. The loop always terminates (§3.3); only the output size is unbounded. | `available_starts`, next to the R5 duration check, because it owns request-level rules on the duration (for example "duration ≥ 1 min" or "at most N starts"). |
| A6 | **Validation precedence is fixed.** (1) Range validity (R5 and R6) is checked when the caller builds each `TimeRange`, before `available_starts` runs. (2) The duration is checked, as the first statement of `available_starts`. (3) Overlaps are checked. When several pairs overlap, the reported pair is the *first adjacent overlapping pair in `(start, end)` order*, and that pair does not depend on input order. | The order is deterministic and cheapest-first. The duration is rejected even when no gap exists (C12 with a fully booked day). | `available_starts` (the order of its statements) and `DaySchedule.__init__` (which pair is reported). |
| A7 | **Argument types.** `TimeRange` guards its field types: `start` and `end` must be `datetime.time`, otherwise it raises `TypeError`. `available_starts` does **not** type-guard its own arguments. A wrong type there fails loudly and immediately with the stdlib's `TypeError`/`AttributeError`, and that error is not wrapped. | A type guard goes exactly where a wrong type would otherwise be *silently accepted*. `TimeRange(datetime, datetime)` would construct without the guard, because datetimes compare and have `tzinfo`. It would then let a range cross midnight (breaking R6) and fail somewhere far from the cause. A `tuple`, `int` or `str` passed to `available_starts` cannot get past the first operation that touches it (`<=` against a `timedelta`, `.start` in the sort key, `.intersection`), so it already fails fast. §5 says to let an unactionable programming error fall rather than wrap it. | `TimeRange` (`_require_wall_clock`), or the first lines of `available_starts` if guards there are ever wanted. |
| A8 | **An invalid-range error does not say whether it was the working hours or a booking** (fix-list item 7). This is accepted. | The error is raised by the caller's own `TimeRange(...)` expression, before `available_starts` runs. The traceback therefore points at the caller's line that built *that* value, and the message shows its times. The service never holds an invalid range it could label. Adding a label would need either a role parameter on a value type (the type would know its callers) or a second validity check in `available_starts` (a second owner of R5). | If input ever arrives as raw data that this package parses (a CLI, or a tuple seam), the parse point knows the role and adds the label there, still by calling the one `TimeRange` constructor. |
| A9 | **Output is `time` objects, not strings.** Rendering them (for example as `HH:MM`) is the caller's job. | The caller is a UI or a service in the same process (goals.md). | Not applicable. |

---

## 2. Module tree and dependency direction

```
availability/
  __init__.py      # published surface; __all__ = ["TimeRange", "available_starts",
                   #   "InvalidAvailabilityRequest", "OverlappingBookingsError"]
  errors.py        # error vocabulary (published)
  time_range.py    # TimeRange (published): half-open naive wall-clock range; the ONLY time arithmetic
  _day.py          # DaySchedule (package-private): validated occupancy of one day; free gaps
  slots.py         # available_starts (published entry): R5-duration, R1 stepping (module-private helper)
tests/
  test_time_range.py
  test_available_starts.py
  test_invariants.py
  test_public_surface.py
```

Runtime dependencies are acyclic and point toward the stable leaf:

```
slots ──► _day ──► time_range ──► errors
  │                    ▲            ▲
  └────────────────────┴────────────┘
```

- `errors` has **no runtime imports** from the package. It annotates `first`/`second` as `TimeRange` under
  `typing.TYPE_CHECKING`, with `from __future__ import annotations`. It builds its messages with `str(...)`
  on the objects it is given, which needs no import.
- `time_range` imports `errors`, because it raises `InvalidAvailabilityRequest`.
- `_day` imports `time_range` and `errors`.
- `slots` imports `_day`, `time_range` and `errors`.
- No module imports an underscore-prefixed *name* from another module. `_day.py` is a package-private
  module whose one class, `DaySchedule`, is imported by exactly one sibling, `slots.py`.
- Standard library only: `dataclasses`, `datetime`, `itertools.pairwise`, `collections.abc`, `typing`.
  Tests use `unittest` and `random`. There is no pyproject and no pytest.

**Public entry point: a local library function, `availability.available_starts`, with no CLI.** The only
stated caller is a scheduling UI or another service in the same process that wants a pick-list (goals.md).
A CLI would add a second boundary (parsing strings into times, formatting output, mapping errors to exit
codes) that no present caller consumes. §1.2 A8 says where a CLI's parsing would land if one is ever
needed.

---

## 3. Modules: responsibility, signatures, contracts

### 3.1 `errors.py`: the error vocabulary (published)

```python
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .time_range import TimeRange

class InvalidAvailabilityRequest(ValueError):
    """The caller sent input that a product rule rejects (R4, R5, R6). This is a caller bug:
    fix the input, don't retry. The message names the offending value(s) in wall-clock terms."""

class OverlappingBookingsError(InvalidAvailabilityRequest):
    """R4: two supplied bookings overlap. Carries the pair as data, so a caller can locate
    them in its own records (a TimeRange has no id)."""
    first: TimeRange    # the earlier of the pair in (start, end) order
    second: TimeRange
    def __init__(self, first: TimeRange, second: TimeRange) -> None: ...
        # message: "bookings 10:00–11:00 and 10:30–11:30 overlap; bookings must not overlap
        #           (touching, e.g. 10:00–10:30 and 10:30–11:00, is fine)"
```

**Why exactly two types.**
- One base type, so a caller can catch every rejection from this package and tell it apart from unrelated
  `ValueError`s. It subclasses `ValueError`, so idiomatic generic handlers still work.
- One subtype, because it carries a payload the others do not have: the offending pair, which C9 requires.
  A caller that wants to highlight two calendar entries catches this subtype. Everything else is handled
  the same way (surface the message), so a subtype per rule would be a dead subtype that nobody catches
  differently.

`TypeError` for a wrong field type (A7) is **not** part of this vocabulary. It is the standard Python signal
for a programming error, and it is left as that.

### 3.2 `time_range.py`: `TimeRange`, the time model (published)

**Responsibility.** This module defines what a range of wall-clock time is (R2, R5 for ranges, R6), and it
is the only place in the package that does arithmetic on times of day. Every operation that could produce an
empty range returns `None` instead, so an empty range cannot be represented anywhere.

```python
@dataclass(frozen=True, slots=True)
class TimeRange:
    """A non-empty half-open range [start, end) of naive wall-clock time within one day.

    Invariant (established in __post_init__, the one construction path; holds forever, frozen):
      type(start), type(end) are datetime.time (or a subclass); start.tzinfo is None and
      end.tzinfo is None; start < end.
    """
    start: time
    end: time

    def __post_init__(self) -> None:
        """Pre: none (this IS the validation).
        Raises, in this order:
          TypeError                   start or end is not a datetime.time            (A7)
          InvalidAvailabilityRequest  start or end carries tzinfo                     (R6, A4)
          InvalidAvailabilityRequest  not start < end — empty or reversed             (R5, C11)
        Messages: "invalid time range 17:00–09:00: end must be after start";
                  "invalid time range 09:00+02:00–17:00: times must be naive wall-clock (no tzinfo)"."""

    @classmethod
    def if_nonempty(cls, start: time, end: time) -> "TimeRange | None":
        """The non-raising form used for derived ranges (clipped bookings, gaps, remainders).
        Pre: none. Applies the same type and naive checks as the constructor (same private helper,
        same errors). Then: returns cls(start, end) if start < end, else None (never raises for
        start >= end).
        Post: result is None or a valid TimeRange equal to TimeRange(start, end)."""

    def intersection(self, other: "TimeRange") -> "TimeRange | None":
        """The shared part of two ranges.
        Pre: none (both are valid by construction). Total.
        Post: if_nonempty(max(self.start, other.start), min(self.end, other.end)).
          → None when they are apart OR only touch (R2: a.end == b.start shares no instant).
          → otherwise a range inside both. Symmetric."""

    def overlaps(self, other: "TimeRange") -> bool:
        """R2: True iff the ranges share at least one instant. Touching is not overlapping.
        Defined as: self.intersection(other) is not None. Total, symmetric."""

    def leading(self, length: timedelta) -> "TimeRange | None":
        """The first `length` of this range: [start, start + length), if it fits inside self.
        Pre: none. Total for every timedelta, including zero, negative and timedelta.max.
        Post: returns [start, start+length) iff timedelta(0) < length <= (end - start);
              else None.
          · `<=` is the R2 fact "a slot may end exactly at the range's end" (C14).
          · length is compared with (end - start) BEFORE any addition, so a huge length cannot
            overflow past midnight (C4); length <= 0 yields None, so no caller can loop on it."""

    def __str__(self) -> str:
        """"09:00–09:45" (en dash). Each time is HH:MM when its seconds and microseconds are
        zero, else time.isoformat(). This is the one wall-clock rendering used by every error
        message."""

# module-private (used only inside time_range.py):
def _require_wall_clock(t: object, field: str) -> None: ...   # the A7 type guard + A4 naive check
def _nonempty(start: time, end: time) -> bool: ...            # `start < end`: the ONE strict comparison
                                                                #  behind R5-range and R2 emptiness
def _offset(t: time) -> timedelta: ...                          # time → offset from midnight
def _at(offset: timedelta) -> time: ...                         # offset → time; Pre: 0 <= offset < 1 day
def _fmt(t: time) -> str: ...                                   # HH:MM or isoformat, for __str__ and errors
```

Illustrative, to pin down the one place that does arithmetic:

```python
    def leading(self, length):
        if not timedelta(0) < length <= _offset(self.end) - _offset(self.start):
            return None
        return TimeRange(self.start, _at(_offset(self.start) + length))
```

**Frozen and single-path.** `TimeRange` has exactly one construction path, `__init__` → `__post_init__`.
`if_nonempty` and `dataclasses.replace` both go through it. It has no `order=True`: "is one range less than
another" has no domain meaning, so the sort key lives in the one place that sorts (`DaySchedule`).

**The published surface of `TimeRange` (fix-list item 3).** Which members does a *caller* need?
- A caller needs only construction, `start`, `end`, `==`/hash (a `TimeRange` is a hashable value), and
  `str` (it appears in error messages).
- No stated caller needs `if_nonempty`, `intersection`, `overlaps` or `leading`.

These four are still public methods. The decision rests on three points:

1. **They are the type's own behaviour.** Written as free functions in another module, they would read
   only a range's fields. That is feature envy (§8). Written as underscore members called from sibling
   modules, they would be inappropriate intimacy. Either way they would also pull the reference-date
   arithmetic out of this file, which is shotgun surgery against the time model. On the type, one class owns
   R2, emptiness and all time arithmetic.
2. **They hide no decision likely to change (§5, information hiding).** Each one is pure and **total**: it
   has no precondition a caller could violate, and so no input on which it gives a wrong answer or builds an
   invalid state. Their meaning is fixed by the decided rules R2 and R6. They would change only if the time
   model changes, and that change also changes `TimeRange`'s field types, so it reaches callers anyway.
3. **What stays hidden is what is likely to change:** occupancy normalization (R3, R4), gap derivation, the
   R1 stepping policy, and the time representation behind `_offset`/`_at`.

`test_public_surface.py` pins the exact public member set of `TimeRange`. Growing it is then a deliberate,
reviewed act.

**Correction to the earlier merge.** The merge had a module-level `tile_starts(span, size)` that was
neither exported nor underscored and was imported across modules. If it had been published, it would have
carried an unchecked precondition (`size > 0`) on a public operation. A zero size would raise
`ZeroDivisionError`. A *negative* size would silently return `[]`, because `length // negative` is negative
and `range(negative)` is empty. So the merge's claim that "a bypassed precondition fails loudly" was false
for negative sizes. Tiling is therefore re-expressed as the total `leading` (on the type) plus the R1
stepping loop (in `slots.py`, §3.4). `length` is cut from the public surface because no caller and no
sibling module needs it.

### 3.3 `_day.py`: `DaySchedule`, the day's occupancy (package-private)

**Responsibility.** This class turns the caller's bookings into the day's *busy time*, meaning the validated,
sorted, clipped occupancy inside the working hours. It owns R4 and R3. It then answers one question: which
maximal free gaps remain. Its type is the evidence that R4 was checked and R3 applied, and `free_gaps`
trusts that without re-checking.

```python
class DaySchedule:
    """One resource's day: working hours plus the busy time inside them.

    Invariant (established in __init__ — the ONE construction path — and never changed after;
    no method assigns to self):
      I1 every r in _busy lies inside _hours  (r.intersection(_hours) == r)
      I2 _busy is strictly ascending by start
      I3 members of _busy are pairwise non-overlapping (touching allowed)
      I4 every member is a valid, non-empty TimeRange (by TimeRange's own invariant)
    """
    __slots__ = ("_hours", "_busy")
    _hours: TimeRange
    _busy: tuple[TimeRange, ...]

    def __init__(self, hours: TimeRange, bookings: Iterable[TimeRange]) -> None:
        """Pre: hours and each booking are TimeRange (hence individually valid).
                `bookings` is any iterable; it is consumed exactly once.
        Steps, in this order (the order IS assumption A1):
          1. ordered = sorted(bookings, key=lambda b: (b.start, b.end))          # R4: service sorts
          2. for a, b in pairwise(ordered):                                      # R4: on RAW bookings
                 if a.overlaps(b): raise OverlappingBookingsError(a, b)          #     first pair only
          3. _busy = tuple(c for b in ordered                                    # R3: clip; drop
                            if (c := b.intersection(hours)) is not None)         #     outside/touching
        Post: I1–I4 hold.
        Raises: OverlappingBookingsError(first, second) with first ≤ second in (start, end) order —
                the first adjacent overlapping pair after sorting; a true overlapping pair."""

    def free_gaps(self) -> Iterator[TimeRange]:
        """Pure core; validates nothing; trusts I1–I4.
        Algorithm: cursor = _hours.start; for b in _busy: yield if_nonempty(cursor, b.start)
                   when not None; cursor = b.end.  Finally yield if_nonempty(cursor, _hours.end)
                   when not None.
        Post: the yielded gaps are
          · non-empty and inside _hours;
          · strictly ascending and pairwise disjoint;
          · maximal: consecutive gaps are separated by at least one non-empty busy range, so no two
            gaps touch;
          · exactly the free time: ⋃gaps ∪ ⋃_busy = _hours, and no gap overlaps any busy range.
        Each call returns a fresh iterator (restartable)."""
```

**Why step 2 checking only adjacent pairs is enough.** Sort by start (ties broken by end). Suppose `a = oᵢ`
overlaps some later `c = oⱼ` with `j > i + 1`, and let `b = oᵢ₊₁`. By the sort, `a.start ≤ b.start ≤
c.start`. Because `a` overlaps `c`, `c.start < a.end`, so `b.start < a.end`. Also `a.start ≤ b.start <
b.end`. Together these give `a.start < b.end` and `b.start < a.end`, so `a` overlaps `b`. The contrapositive
is that no adjacent overlap implies every pair is disjoint. The reported pair is always a true offending pair,
because it is exactly the pair on which `overlaps` returned `True`.

**Why the error does not depend on input order (C10).** The key `(start, end)` is a total order on the
distinct values of `TimeRange`. Two elements with equal keys are equal values. So the sorted sequence, and
therefore the first adjacent overlapping pair, is the same for every permutation of the input.

**Why the invariant survives clipping (step 3 after step 2).**
- I3: each clipped range is a subset of its original, and the originals are pairwise disjoint, so the
  clipped ranges are too.
- I2: the clipped start is `max(b.start, hours.start)`. This is non-decreasing along the sorted order. It is
  also strictly increasing: two clipped ranges that shared a start would share that instant and overlap,
  which I3 excludes.
- I1 holds by the definition of intersection. I4 holds because empty results are `None` and are dropped.
  That covers a booking wholly outside the hours and a booking that only touches the opening or closing
  edge (C6).

**Why `free_gaps` never compares bounds itself.** The cursor walk calls only `TimeRange.if_nonempty`. The
cursor never moves backwards, because I2, I3 and I1 give `cursor ≤ b.start` and `b.end ≤ hours.end`. When a
busy range starts exactly at the cursor (a touching booking, or a booking at opening), `if_nonempty(cursor,
cursor)` returns `None`. So there is no zero-length gap (C8), and no bound comparison appears outside
`time_range.py`.

**One construction path (fix-list item 2).** `DaySchedule` is a plain class with a single `__init__` that
takes the caller's `hours` and `bookings`. There is no field-wise constructor, no `build` classmethod, and
no public field. An unvalidated `DaySchedule` therefore cannot be built through any intended path. The
statement "the type is evidence that R4 was checked and R3 was applied" is true by construction.
Immutability is by design: `__slots__` is set, the attributes are private, `_busy` is a tuple, and no
method assigns to them. Python cannot seal attributes against `obj._busy = …`, and deliberately
circumventing this is out of scope, the same as monkey-patching.

### 3.4 `slots.py`: `available_starts`, the public entry (published)

**Responsibility.** This module is the product operation. It owns the request-level rule on the duration
(R5), composes the day with the stepping policy, and owns R1.

```python
def available_starts(
    working_hours: TimeRange,
    bookings: Iterable[TimeRange],
    duration: timedelta,
) -> list[time]:
    """Start times, earliest first, at which a booking of `duration` fits entirely inside
    `working_hours` without overlapping any of `bookings`. Slots step back-to-back from the start
    of each maximal free gap (R1).

    Pre (caller's side, already enforced): working_hours and every booking are TimeRange, so each
      is individually valid (R5-range, R6).
    Checked here, in this order (A6):
      1. duration > timedelta(0), else InvalidAvailabilityRequest("duration must be positive,
         got -1 day, 23:30:00")                                                      (R5, C12)
      2. bookings pairwise non-overlapping — by constructing DaySchedule              (R4, C9)
    Post:
      · strictly ascending, no duplicates;
      · every s satisfies working_hours.start <= s and s + duration <= working_hours.end;
      · [s, s + duration) overlaps no booking;
      · complete under R1: within every maximal free gap g, exactly
        (g.end − g.start) // duration starts, namely g.start + k·duration for k = 0, 1, ...;
      · [] when nothing fits (not an error).
    Pure: no state, no I/O; `bookings` consumed exactly once.
    Raises: InvalidAvailabilityRequest (duration), OverlappingBookingsError (R4).
    Wrong argument types are not guarded (A7): they raise the stdlib TypeError/AttributeError."""
```

The body is three statements at one level of abstraction:

```python
    if duration <= timedelta(0):
        raise InvalidAvailabilityRequest(f"duration must be positive, got {duration}")
    day = DaySchedule(working_hours, bookings)
    return [start for gap in day.free_gaps() for start in _gap_aligned_starts(gap, duration)]
```

```python
def _gap_aligned_starts(gap: TimeRange, duration: timedelta) -> Iterator[time]:
    """R1, the one owner: tile `gap` back-to-back from its own start; drop the short leftover.
    Pre: duration > 0 (established by available_starts; not re-checked — core trusts).
    Algorithm: remaining = gap
               while remaining is not None and (slot := remaining.leading(duration)) is not None:
                   yield slot.start
                   remaining = TimeRange.if_nonempty(slot.end, gap.end)
    Post: yields gap.start + k·duration for k = 0 .. (gap length // duration) − 1, strictly
          ascending; the last slot may end exactly at gap.end (R2, via leading's `<=`);
          a leftover shorter than duration yields nothing.
    Termination: every yielded slot is non-empty, so `remaining` strictly shrinks; even if the
          precondition were bypassed, leading() returns None for duration <= 0 and the loop ends
          at once. It cannot hang."""
```

**Why this helper is module-private and where it sits.** It is used only by `available_starts`, in the same
module, so no private name crosses a module line. It *tells* the range what to do (`leading`,
`if_nonempty`) and never reads `start`/`end` to do its own arithmetic, so it is not feature envy. It owns
the one decision R1 makes: *each gap, from its own start, back-to-back*. That decision changes for a
different reason than gap derivation does. A fixed grid, the one alternative that decision 0002 rejected,
would replace this function and leave `DaySchedule` untouched.

**Why "earliest first" holds without a sort.** `free_gaps` yields gaps in strictly ascending order, and they
are disjoint. Within a gap, `_gap_aligned_starts` yields strictly ascending starts, all `< gap.end ≤ next
gap.start`. Concatenating them is therefore strictly ascending, with no duplicates.

### 3.5 `__init__.py`: the published surface

```python
from .errors import InvalidAvailabilityRequest, OverlappingBookingsError
from .time_range import TimeRange
from .slots import available_starts
__all__ = ["TimeRange", "available_starts", "InvalidAvailabilityRequest", "OverlappingBookingsError"]
```

`DaySchedule` and `_gap_aligned_starts` are not exported and appear in no public signature. Illustrative
use by a caller:

```python
from datetime import time, timedelta
from availability import TimeRange, available_starts
available_starts(TimeRange(time(9), time(17)),
                 [TimeRange(time(11), time(12)), TimeRange(time(9), time(9, 45))],
                 timedelta(minutes=30))
# → [09:45, 10:15, 12:00, 12:30, …, 16:30]
```

---

## 4. What each concept is

| Concept | What it is | Why this kind of thing |
|---|---|---|
| Working window | a `TimeRange` in the role `working_hours` / `DaySchedule._hours` | A half-open range with no rule of its own. Its role (the clipping frame, R3) is a fact about the day, owned by `DaySchedule`. A `WorkingHours` class would be a lazy class. |
| Booking | a `TimeRange` in the role `bookings` | In stage 1 a booking has no id, owner or state, because storing bookings is a non-goal. The rules *about* bookings (R3, R4) are rules of the day's occupancy. |
| Busy time | `DaySchedule._busy`, a tuple of clipped ranges | These are no longer the caller's bookings once clipped, so the name is `busy`. Breaks, if they ever come, would be busy time without being bookings. |
| Free gap | a `TimeRange` **produced by** `DaySchedule.free_gaps()` | Free time is emitted explicitly as its own value. It is never a synthetic booking and never stored in `_busy`. It is a range, so it is a `TimeRange`. |
| Candidate slot | a transient `TimeRange` from `gap.leading(duration)`. It is never returned. | Its fitting rule is R2 containment, which `TimeRange` owns. The output is start times, so a `Slot` type would have no consumer. |
| Requested duration | `datetime.timedelta` | The foundational stdlib length type. Its one rule (> 0) has one owner, the one entry that accepts a duration. |
| Slot policy (R1) | `slots._gap_aligned_starts` | A stepping behaviour, not a score, not a filter over a grid, and not a Strategy object (only one policy exists). |

---

## 5. Rule → owner

| Rule | Single owner | Mechanism, and why every path goes through it |
|---|---|---|
| R1 gap-aligned, back-to-back, leftover dropped | `slots._gap_aligned_starts` | Free gaps reach the result only through the one composition line in `available_starts`, which calls this function. |
| R2 half-open: touching ≠ overlap | `time_range._nonempty` (`start < end`), used by `if_nonempty` → `intersection` → `overlaps` | This is the only strict bound comparison in the package. No other module compares an end with a start. |
| R2 a slot may end exactly at the end | `TimeRange.leading` (`length <= end − start`) | This is the only "does it fit" test. |
| R3 only the portion inside the hours counts | `DaySchedule.__init__` step 3 (the decision), via `TimeRange.intersection` (the geometry) | This is the only place bookings meet the hours. |
| R4 service sorts; overlap rejected naming the pair; touching fine | `DaySchedule.__init__` steps 1–2 | `free_gaps` exists only on a constructed `DaySchedule`, and there is one constructor. |
| R5 range `end <= start` | `TimeRange.__post_init__` | Every `TimeRange`, whether supplied or derived, is built through it. |
| R5 duration `<= 0` | `available_starts`, first statement | This is the only operation that accepts a duration. |
| R5 no fit → `[]` | structural | No gaps, or `leading` returns `None` on the first try. There is no special-case path that could drift. |
| R6 naive, one day, no midnight crossing | `TimeRange`: field type `time` (a range cannot pass midnight, since `start < end` is required), `_require_wall_clock` (rejects a non-`time` or an aware time) | Time is represented in one file only. |
| Earliest first | composition of the `free_gaps` postcondition with the `_gap_aligned_starts` postcondition | Holds by construction; there is no final sort to forget. |
| Input validated once; core trusts | `TimeRange` constructor (caller side) + `available_starts` (duration) + `DaySchedule.__init__` (the set) | `free_gaps`, `_gap_aligned_starts`, `intersection` and `leading` validate nothing. The `TimeRange` check that re-runs on derived ranges is a value type's invariant, not a second validation, and it never fails there. |

---

## 6. Error vocabulary (summary)

| Situation | Raised by | Type | Message (example) |
|---|---|---|---|
| range with `end <= start` (hours or booking) | `TimeRange(...)`, at the caller's construction | `InvalidAvailabilityRequest` | `invalid time range 17:00–09:00: end must be after start` |
| aware time in a range | `TimeRange(...)` | `InvalidAvailabilityRequest` | `invalid time range 09:00+02:00–17:00: times must be naive wall-clock (no tzinfo)` |
| non-`time` field (for example a `datetime`) | `TimeRange(...)` | `TypeError` (not package vocabulary) | `TimeRange.start must be datetime.time, got datetime.datetime` |
| `duration <= 0` | `available_starts` | `InvalidAvailabilityRequest` | `duration must be positive, got 0:00:00` |
| two bookings overlap (including duplicates, nesting, and pairs outside the hours) | `DaySchedule.__init__` | `OverlappingBookingsError` (`.first`, `.second`) | `bookings 10:00–11:00 and 10:30–11:30 overlap; bookings must not overlap (touching, e.g. 10:00–10:30 and 10:30–11:00, is fine)` |
| wrong argument type to `available_starts` | stdlib, at first use | `TypeError` / `AttributeError`, unwrapped (A7) | stdlib message |
| nothing fits | — | not an error: `[]` | — |

---

## 7. Trace of C1–C14

Hours are 09:00–17:00 and the duration is 30 min unless stated otherwise. H = hours, d = duration.

| Case | Path through the design | Result |
|---|---|---|
| C1 | d > 0 ✓. `DaySchedule`: sorted `[09:00–09:45, 11:00–12:00]`; adjacent pair: `intersection` = `if_nonempty(11:00, 09:45)` → None, so no overlap. Clip: both lie inside H and are unchanged. `free_gaps`: cursor 09:00, `if_nonempty(09:00, 09:00)` → None; cursor 09:45; yield 09:45–11:00; cursor 12:00; tail yields 12:00–17:00. Stepping on 09:45–11:00: `leading` → 09:45–10:15 (yield 09:45), remaining 10:15–11:00 → 10:15–10:45 (yield 10:15), remaining 10:45–11:00: 30 min > 15 min → None, stop. Stepping on 12:00–17:00 yields 12:00 … 16:30 (10 starts). | `09:45, 10:15, 12:00, 12:30, …, 16:30` ✓ |
| C2 | `_busy = ()`. `free_gaps` yields H only. Stepping yields 09:00, 09:30, …, 16:30: 16 starts. | ✓ |
| C3 | Booking 09:00–17:00, or 08:00–18:00 clipped to 09:00–17:00, or touching bookings that tile H. Every `if_nonempty(cursor, b.start)` and the tail `if_nonempty(17:00, 17:00)` return None, so there are no gaps. | `[]` ✓ |
| C4 | d = 6 h against C1's gaps (75 min and 5 h): each first `leading` returns None because `length > end − start`. d = 9 h with no bookings: `leading` on H returns None. d = `timedelta.max`: the comparison is made before any addition, so there is no overflow. | `[]` ✓ |
| C5 | Gap 10:00–10:30, d = 30 min: `leading` gives 10:00–10:30 (`30 ≤ 30`, R2). Remaining is `if_nonempty(10:30, 10:30)` → None, stop. One slot. Gap of 75 min (2.5·d): 10:00, 10:30, then 15 min are left → None. Two slots. | 1 and 2 ✓ |
| C6 | 08:00–09:00 ∩ H = `if_nonempty(09:00, 09:00)` → None, so it is dropped. 17:00–18:00 ∩ H = `if_nonempty(17:00, 17:00)` → None, dropped. The output equals C2. | no effect ✓ |
| C7 | 08:30–09:30 clips to 09:00–09:30, so the first gap starts at 09:30. 16:30–17:30 clips to 16:30–17:00. The gap is 09:30–16:30, giving 09:30 … 16:00. | clipped ✓ |
| C8 | 10:00–10:30 and 10:30–11:00: `intersection` = `if_nonempty(10:30, 10:30)` → None, so they do not overlap and both are accepted. In `free_gaps` the cursor is 10:30 at the second booking, and `if_nonempty(10:30, 10:30)` → None, so there is no gap and no slot between them. | ✓ |
| C9 | 10:00–11:00 and 10:30–11:30 are adjacent after sorting, and `overlaps` is True. The error is `OverlappingBookingsError(first=10:00–11:00, second=10:30–11:30)`. | rejected, pair named ✓ |
| C10 | `sorted(key=(start, end))` gives the same tuple for every permutation (§3.3). Everything downstream reads only `_busy`, so the output and the reported overlap pair are identical. A one-shot generator is consumed once, by `sorted`. | identical ✓ |
| C11 | `TimeRange(time(10), time(10))`, `TimeRange(time(11), time(10))`, and `TimeRange(time(17), time(9))` used as the hours all raise `InvalidAvailabilityRequest` in `__post_init__`, in the caller's expression, before `available_starts` runs. A zero-length booking is exactly `end <= start`. | rejected ✓ |
| C12 | `timedelta(0)` or a negative duration raises in `available_starts`' first statement, before `DaySchedule` is built. This also happens when bookings cover the whole day (no gaps), and when the bookings overlap (A6 precedence). | rejected ✓ |
| C13 | 2 h gap 10:00–12:00, d = 45 min: 10:00–10:45 (yield 10:00), 10:45–11:30 (yield 10:45), then 30 min are left < 45 → None. | 2 slots, 30 min unused ✓ |
| C14 | Tail gap …–17:00: `leading(30 min)` on 16:30–17:00 holds because `30 ≤ 30`, so 16:30 is yielded. | offered ✓ |

### 7.1 Beyond the listed cases

These come from crossing the input axes (position, count, order, duration size, precision, type) with each
rule.

| Case | Path | Result |
|---|---|---|
| Duplicate identical bookings | adjacent after sorting; `overlaps` True | `OverlappingBookingsError` (A2) |
| Booking nested inside another | adjacent pair overlaps, by the sufficiency proof | rejected |
| Same start, different end | the key `(start, end)` puts the shorter first; they overlap | rejected, same pair in every order |
| Two bookings overlapping each other wholly before opening (07:00–08:00, 07:30–08:30) | step 2 runs before clipping | rejected (A1) |
| An outside booking overlapping a straddling one (08:00–08:30, 08:15–10:00) | step 2 | rejected (A1) |
| A booking wholly outside, sorted between in-hours bookings | dropped by clipping; the cursor never sees it | no effect |
| Booking touching the edge at open and another at close, plus in-hours bookings | edge bookings are dropped | same as without them |
| Duration exactly equal to H, no bookings | `leading` fits (`≤`) | `[09:00]` |
| H of 1 µs, duration 1 µs | one gap, one slot | `[H.start]` |
| Duration `timedelta.max` | compared before adding; None | `[]`, no `OverflowError` |
| Sub-minute values (d = 7 min 30 s; bookings with seconds) | integer `timedelta` arithmetic, no rounding | exact starts with seconds |
| d = 1 µs over 8 h | loop terminates after about 2.9·10¹⁰ steps | correct but huge (A5) |
| Aware `time` in a booking | `TimeRange` raises | `InvalidAvailabilityRequest` (A4) |
| `datetime` values in a `TimeRange` | type guard | `TypeError` (A7), and never a silent cross-midnight range |
| `bookings` is a generator | consumed once in `sorted` | works |
| Tuples instead of `TimeRange` in `bookings` | `AttributeError` in the sort key | loud, unwrapped (A7) |
| `duration` as an `int` | `TypeError` at `<=` | loud, unwrapped (A7) |
| Negative duration with bypassed validation (only internal code could do this) | `leading` returns None | loop ends at once; it cannot hang |
| Working hours ending at `time.max` | valid; a final slot ends at or before 23:59:59.999999 | a slot ending at 24:00 cannot be expressed (A3) |

---

## 8. Design reasoning and rejected alternatives

### 8.1 Placement of each element, and the present force behind it

- **`TimeRange` (published).** It answers R2, R5 for ranges and R6, and it is the one owner of time
  arithmetic. It removes primitive obsession at the seam: a `(time, time)` tuple would be a data clump whose
  rule owner is invisible to the caller. It also makes empty, reversed, aware and cross-midnight ranges
  impossible to construct on the caller's side (§4, illegal states unrepresentable). It is published because
  it is a foundational value type defined as part of the interface (§0).
- **`DaySchedule` (private).** It answers the objective's demand that input be validated once and trusted by
  the core. The type is the evidence. It has behaviour (validation at construction, `free_gaps`), so it is
  not an anemic bag. It is private because its representation and its normalization order (A1, A2) are
  decisions likely to change.
- **`_gap_aligned_starts` (module-private).** R1 is its own change axis, separate from gap derivation.
- **`available_starts`.** This is the product operation and the owner of the duration rule.
- **Two errors.** They answer "clear error" and C9's pair as data (§3.1).

### 8.2 Splits decided in the panel, and how this revision stands on them

- **Publish `TimeRange` rather than tuples at the seam.** The decision stands (reasons in §8.1).
  Encapsulation's concern was that internal *mechanics* would be published. That concern is now answered
  more precisely: the public methods are total, pure and fixed by decided rules, and the decisions likely to
  change stay private (§3.2).
- **The owner of R1.** The decision stands, with one change. The mechanics that sit on the type are now
  `leading` (total) rather than `tile_starts` (which had an unguarded precondition). The policy and the
  stepping loop are one module-private function in `slots.py`. A `_FreeGap` wrapper stays cut: it would be a
  class whose only content is one method over a range.
- **`timedelta`, not a `SlotDuration` type.** The decision stands. The positivity rule has one owner. The
  merge argued "a bypass fails loudly", which was wrong for negative sizes. That argument is replaced by a
  stronger one: every core operation is total and the loop cannot hang (§3.2, §3.4). The falsifier for this
  decision: a second public operation that accepts a duration would earn the type.
- **`DaySchedule` rather than a `Bookings` set.** The decision stands. Its construction changes from a
  dataclass plus `build` to a single `__init__` (fix-list item 2).
- **Two error types.** The decision stands.

### 8.3 Alternatives rejected

- **A frozen dataclass `DaySchedule(hours, busy)` plus a `build` classmethod.** It has two construction
  paths, and the field-wise one forges an unvalidated schedule. Private-constructor tricks such as a
  sentinel token or a `__new__` guard would add machinery to imitate what a single validating `__init__`
  already gives.
- **Geometry as free functions (`clip`, `tile_starts`) in `time_range.py`, imported across modules.** This
  is feature envy, and it leaves an ambiguous public/private status (§3.2).
- **Underscore methods on `TimeRange` called from sibling modules.** This is inappropriate intimacy, and it
  hides nothing that is likely to change.
- **A private geometry module separate from `TimeRange`.** It would split the time model across two files,
  which is shotgun surgery when the time model changes.
- **A count-based `range(length // size)` tiler as a public method.** Its precondition is unchecked on a
  public operation, and it silently returns `[]` for a negative size (§3.2).
- **Validating inside the core (`free_gaps(hours, bookings)` validating and computing in one body).** This
  mixes the boundary with the core and leaves the precondition implicit in a bare list.
- **Merging overlapping bookings, or deduplicating.** Ruled out by decision 0002 (A1, A2).
- **Role types (`WorkingHours`, `Booking`, `FreeGap`) and a `Slot` type.** They would own no rule and have no
  consumer. Subclassing `TimeRange` for roles would invite the "gap as a synthetic booking" cram. The
  falsifier: a booking that gains an id or a status earns a `Booking` that *has* a `TimeRange`.
- **A `SlotPolicy` Protocol or Strategy.** It has one implementation, and the grid is a rejected product
  choice. Under the §7 tie-break no present change-axis item uses this seam, so it is over-build. The single
  call site is where a second policy would plug in.
- **`datetime` instead of `time`.** It would force callers to invent a date, and it would make "same date"
  and midnight crossing representable, which needs two extra rules that R6 removes.
- **Integer minutes.** This is primitive obsession, and it silently truncates seconds.
- **A CLI.** No present caller needs it (§2).
- **`order=True` on `TimeRange`.** "Less than" has no domain meaning between ranges.
- **pytest or a pyproject.** `unittest` is enough, and the project keeps zero dependencies.
- **A role label in range errors.** See A8.

### 8.4 Principles that do not apply at this scale

- **Ports and adapters, DIP, Repository.** There is no I/O, persistence or framework. The whole package is
  a functional core, and the caller is the shell.
- **§11 concurrency.** Everything is immutable or local, and there is no shared state.
- **§14 security.** There is no trust boundary beyond correctness validation.
- **§13 performance.** No requirement is stated. The cost is O(n log n) for the sort plus O(n + output); A5
  records the unbounded output.

### 8.5 Subtractive pass (rerun on this revision)

| Element | Present force | Verdict |
|---|---|---|
| `TimeRange` | R2, R5-range, R6; the one owner of time arithmetic | keep |
| `TimeRange.if_nonempty` | the one non-raising path for derived ranges (clip, gaps, remainder); without it, bound comparisons would leak into `_day.py` and `slots.py` | keep |
| `TimeRange.intersection` | R3 geometry; also defines `overlaps` | keep |
| `TimeRange.overlaps` | R4's meaning of "overlap", in one line of intent | keep (it costs one line; it names the rule where `DaySchedule` uses it) |
| `TimeRange.leading` | R1 fitting, R2 ends-at-end, C4 overflow safety, loop totality | keep |
| `TimeRange.length` (from the merge) | no consumer outside `leading` | **cut** |
| `tile_starts` (from the merge) | replaced by the total `leading` plus the R1 loop | **cut** |
| `clip` (from the merge) | same thing as `intersection` | **cut** (renamed into the method) |
| `_range_if_nonempty` (from the merge) | same thing as `if_nonempty` | **cut** (merged) |
| `_require_wall_clock` type guard | A7: prevents the one silent acceptance (`datetime`) | keep |
| `DaySchedule.build` | a second construction path | **cut** (folded into `__init__`) |
| `DaySchedule` | R3, R4, trust by construction | keep |
| `DaySchedule.free_gaps` | free time as its own produced concept | keep |
| `_gap_aligned_starts` | R1, its own axis | keep |
| `OverlappingBookingsError` | C9 pair as data | keep |
| `InvalidAvailabilityRequest` | clear-error vocabulary | keep |
| `__str__` / `_fmt` | C9 and R5 messages in wall-clock terms | keep |
| `test_public_surface.py` | pins the §3.2 surface decision | keep |

### 8.6 Concept-fit pass (rerun)

- Free time is its own emitted value (`free_gaps`). It is not a synthetic booking, and it is not the
  implicit absence of busy time.
- Busy time is named `busy`, not `bookings`, once clipped. A future break would be busy time, not a fake
  booking.
- The candidate slot is a transient `TimeRange` used only for its fit test, and it is not returned. It
  carries no role flag.
- The duration is a length (`timedelta`), not a range anchored at midnight.
- The empty range is `None`, never a zero-length stand-in.
- "Nothing fits" is `[]`, never an error or a sentinel.
- `leading` returning `None` for a non-positive length is the honest answer to "what is the non-empty
  leading part of this length?" It is not a disguised validation. R5 rejection has one owner,
  `available_starts`.

No inert stand-ins remain.

---

## 9. Where the stage-2 non-goals would land (named only; nothing is built)

| Non-goal | Where it would land |
|---|---|
| Breaks inside working hours | `DaySchedule.__init__`: an extra input folded into `_busy`, which is the occupancy owner. `_busy` already names occupancy, not bookings. |
| Buffers between bookings | `DaySchedule.__init__`: widen occupancy there, the one owner. It would not be a trailing filter. |
| Fixed-grid alignment | `slots._gap_aligned_starts`, the one R1 owner, which would be replaced or given the origin. |
| Multiple resources | the caller, or a thin new entry, calls `available_starts` once per resource. The core is unchanged. |
| Recurrence, multi-day, time zones | `time_range.py` (field types, `_offset`/`_at`) and the entry signature. This change reaches callers, because it changes R6 itself. |
| Creating, cancelling or storing bookings | outside this package. A `Booking` entity would *have* a `TimeRange` and pass its range in. |

---

## 10. Test plan (test-first, stdlib `unittest`, pure and fast, no mocks)

Tests assert observable contracts at the **published** seams: `TimeRange`, `available_starts` and the
package surface. `DaySchedule` and `_gap_aligned_starts` are covered through `available_starts`, so they
can be refactored freely. Write the tests in the order below. Each row names the decision it pins.

### 10.1 `tests/test_time_range.py`: the published value type

| # | Decision | Test | Covers |
|---|---|---|---|
| T1 | R5-range | `TimeRange(10:00, 10:00)` and `TimeRange(11:00, 10:00)` raise `InvalidAvailabilityRequest`; the message contains both times | C11 |
| T2 | R6/A4 | tz-aware `start`, and separately `end`, raise `InvalidAvailabilityRequest` | A4 |
| T3 | A7 | `TimeRange(datetime, datetime)` and `TimeRange("09:00", "17:00")` raise `TypeError` | A7 |
| T4 | precedence inside the constructor | a reversed *aware* range reports the tz reason (type → tz → emptiness) | A6 |
| T5 | `if_nonempty` | `(t, t)` → None; `(later, earlier)` → None, with no raise; `(a, b)` equals `TimeRange(a, b)`; an aware input raises | C3, C8 |
| T6 | R2 overlap | overlapping → True; containment → True; identical → True; touching in both orders → False; symmetric | C8, C9 |
| T7 | R3 intersection | straddling open, and straddling close, give the clipped range; wholly outside → None; touching the open or close edge → None; inside → equal to self | C6, C7 |
| T8 | `leading` | exact fit returns a range ending at `end`; 1 µs too long → None; 0 and negative → None; `timedelta.max` → None with no `OverflowError`; with seconds (7 min 30 s) keeps the seconds | C4, C5, C14 |
| T9 | `__str__` | `09:00–09:45`; seconds shown only when non-zero | C9 message |
| T10 | frozen | assigning to `start` raises `FrozenInstanceError`; equal values are equal and hash equal | value semantics |

### 10.2 `tests/test_available_starts.py`: the product contract

| # | Test | Covers |
|---|---|---|
| A1 | the exact worked-example list | C1 |
| A2 | gap-aligned, not grid: the C1 result contains 09:45 and 10:15 and does not contain 10:00 | R1 |
| A3 | no bookings → 16 starts, 09:00 … 16:30 | C2 |
| A4 | booking 09:00–17:00 → `[]`; booking 08:00–18:00 → `[]`; touching bookings tiling H → `[]` | C3, C7 |
| A5 | 6 h against C1's bookings → `[]`; 9 h with no bookings → `[]`; `timedelta.max` → `[]` | C4 |
| A6 | 30 min gap → one start; 75 min gap → two | C5 |
| A7 | bookings 08:00–09:00 and 17:00–18:00 → equals C2 | C6 |
| A8 | 08:30–09:30 and 16:30–17:30 → 09:30 … 16:00 | C7 |
| A9 | 10:00–10:30 and 10:30–11:00 accepted; no start in [10:00, 11:00) | C8 |
| A10 | overlap → `OverlappingBookingsError`; `.first`/`.second` equal the pair in `(start, end)` order; `str(e)` contains both ranges | C9 |
| A11 | nested pair, and a same-start pair, → rejected with that pair | R4, §7.1 |
| A12 | duplicate booking → rejected | A2 |
| A13 | two overlapping bookings wholly before opening → rejected (pins A1) | A1 |
| A14 | every permutation of C1's bookings plus two more (`itertools.permutations`) gives identical output; with an overlapping set, every permutation reports the same pair | C10 |
| A15 | a generator of bookings works | signature contract |
| A16 | `timedelta(0)` and −30 min raise `InvalidAvailabilityRequest`; 0 with full-cover bookings still raises; 0 with overlapping bookings raises the *duration* error (precedence) | C12, A6 |
| A17 | hours 09:00–11:00, 45 min → `[09:00, 09:45]` | C13 |
| A18 | the last start, 16:30, is present and 16:30 + 30 min == 17:00 | C14 |
| A19 | output strictly ascending across several gaps | earliest first |
| A20 | sub-minute: 7 min 30 s over 09:00–10:00 → 8 starts carrying seconds | A5, precision |
| A21 | `duration=30` (int) → `TypeError` (pins "not wrapped") | A7 |

C11 is pinned in T1, where the rejection happens. The caller cannot reach `available_starts` with an
invalid range.

### 10.3 `tests/test_invariants.py`: seeded random, the whole input space

Use `random.Random(20260923)` over about 2 000 generated cases. Generation:
- Hours: random with a start of 00:00–20:00 and a length of 1 min–4 h. Some cases use second precision.
- Bookings: 0–8 non-overlapping ranges, built from sorted random cut points over [H.start − 2 h,
  H.end + 2 h] clamped to the day, so they include ones outside, straddling and touching. They are then
  shuffled.
- Duration: 1 min to 1.2 × the length of H.

The test computes every property with its **own** arithmetic (`datetime.combine(date.min, t)`), independent
of the package's. For each result `S`:

1. **Fits.** For every `s ∈ S`, `H.start ≤ s` and `s + d ≤ H.end`.
2. **Free.** No `[s, s + d)` overlaps any booking (half-open).
3. **Order.** `S` is strictly ascending.
4. **Aligned (R1, soundness).** Every `s` is either a gap origin (`H.start`, or the end of some booking,
   and not covered by any booking) or `s − d ∈ S`.
5. **Complete (R1, completeness).** For every gap origin `p` where `[p, p + d)` is free and inside H,
   `p ∈ S`. For every `s ∈ S` where `[s + d, s + 2d)` is free and inside H, `s + d ∈ S`. Together these
   mean no leftover ≥ d is ever dropped.
6. **Metamorphic, C10.** A reshuffled input gives an identical `S`.
7. **Metamorphic, R3.** Adding a booking wholly outside H that overlaps no other booking gives an identical
   `S`.

A second generator injects exactly one overlapping pair and asserts that `OverlappingBookingsError` is
raised, that the pair it carries really overlaps, and that the pair is the same across shuffles.

### 10.4 `tests/test_public_surface.py`: the seam

| # | Test | Pins |
|---|---|---|
| P1 | `availability.__all__` is exactly the four names in §3.5 | published surface |
| P2 | the public members of `TimeRange` (names not starting with `_`) are exactly `{start, end, if_nonempty, intersection, overlaps, leading}`, plus dunders | the §3.2 surface decision |
| P3 | `typing.get_type_hints(available_starts)` and the annotations of both error classes resolve only to `datetime`, builtins, `collections.abc`, `TimeRange` or the error types. No `_day` type appears. | no internal type leaks |
| P4 | `DaySchedule` is not reachable as `availability.DaySchedule` | privacy |
| P5 | `OverlappingBookingsError` is a subclass of `InvalidAvailabilityRequest`, which is a subclass of `ValueError` | error vocabulary |

There is no coverage percentage. Every row is a decision someone could get wrong.

---

## 11. Result

**met**, against the design goal:
- Every rule R1–R6 has exactly one owner (§5).
- Input is validated once: in the `TimeRange` constructor, in the first statement of `available_starts`,
  and in the single `DaySchedule` constructor. The core (`free_gaps`, `_gap_aligned_starts`, and the total
  `TimeRange` operations) trusts it.
- The slot computation is pure, over well-chosen value types.
- Every operation has a concrete Python 3.11 standard-library signature and a stated
  pre/postcondition/invariant.
- C1–C14 and the cases beyond them are traced (§7).
- Every open product question is a stated assumption with its landing point (§1.2).

Items that still need the product owner's confirmation, all of them pinned by tests and each a one-owner
change: A1 (overlap outside the hours → reject), A3 (no 24:00 close), A5 (no output cap or granularity).
