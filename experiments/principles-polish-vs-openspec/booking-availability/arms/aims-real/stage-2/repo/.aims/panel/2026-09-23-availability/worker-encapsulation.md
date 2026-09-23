# Bookable slots, stage 1: design (Worker, axis: correct encapsulation)

Axis pull: every rule gets **one owner that cannot be bypassed**. A value type's constructor owns each
validity rule, so a value that breaks the rule cannot be built. The core accepts only those types and never
re-checks them. The public seam carries only stdlib `datetime` types and the package's own error
vocabulary. No internal type crosses it.

---

## 1. The design

### 1.1 File tree

```
availability/
  __init__.py      # the ONLY public surface: available_slots, Span, error types (re-exports, __all__)
  errors.py        # public error vocabulary (published; every module may raise these)
  _boundary.py     # available_slots(): parse raw input into trusted types → ask the day → return times
  _timeline.py     # foundational value types: TimeRange, SlotDuration; private RangeError; time arithmetic
  _schedule.py     # DaySchedule (a validated day's occupancy) and _FreeGap (free time; owns stepping)
tests/
  test_available_slots.py   # acceptance, through the public seam (C1–C14 + invariants)
  test_timeline.py          # owner tests for the foundational value types (R2, R5, R6 geometry/validity)
  test_public_surface.py    # the seam: what is exported, and that no internal type leaks
```

Dependencies are acyclic and point inward: `__init__ → _boundary → {_schedule, _timeline, errors}`,
`_schedule → {_timeline, errors}`, `_timeline → (stdlib only)`. `errors` depends only on `datetime`.
Underscore modules are package-private. Nothing outside the package imports them, and `__init__`
re-exports nothing from them except `available_slots`.

### 1.2 Public surface (`availability/__init__.py`)

```python
from datetime import time, timedelta
from collections.abc import Iterable

Span = tuple[time, time]          # (start, end), half-open [start, end), naive wall-clock, one local day

def available_slots(
    working_hours: Span,
    bookings: Iterable[Span],
    duration: timedelta,
) -> list[time]:
    """Start times at which a booking of `duration` fits inside `working_hours` without overlapping
    any of `bookings`, earliest first. Slots step back-to-back from the start of each free gap.

    Raises InvalidDuration, InvalidInterval, OverlappingBookings (all AvailabilityError / ValueError).
    Returns [] when nothing fits (not an error). Pure: no state, no I/O; `bookings` is consumed once.
    """

__all__ = ["available_slots", "Span",
           "AvailabilityError", "InvalidDuration", "InvalidSchedule",
           "InvalidInterval", "OverlappingBookings"]
```

**Entry point decision: a local function API, with no CLI.** The only stated callers are a scheduling UI and
another service in the same process (goals.md). A CLI would add string parsing of times, and no present
caller needs it.

**Why these seam types.**
- `datetime.time` is exactly the R6 concept: a naive wall-clock time within one day. A value that crosses
  midnight cannot be represented, and there is no date to cross-check.
- `timedelta` is the stdlib's duration type.
- `Span` is a type alias, not a class, so it adds no implementation type. Every caller already speaks
  `datetime` (base-dependencies.md).

### 1.3 Error vocabulary (`availability/errors.py`, published)

```python
class AvailabilityError(ValueError):           # base: the request breaks a stated input rule
    ...

class InvalidDuration(AvailabilityError):      # R5: duration <= 0 — the *requester's* choice is wrong
    duration: timedelta

class InvalidSchedule(AvailabilityError):      # the resource's *calendar data* is wrong (a caller bug)
    ...

class InvalidInterval(InvalidSchedule):        # R5/R6: end <= start, or a tz-aware time
    subject: str                               # "working hours" | "booking #3" (1-based, input order)
    span: Span
    reason: str                                # "end must be after start" | "times must be naive wall-clock"

class OverlappingBookings(InvalidSchedule):    # R4: names the offending pair (C9)
    first: Span
    second: Span                               # first.start <= second.start
```

Messages speak the caller's terms, for example `booking #2 10:00–10:00: end must be after start` and
`bookings 10:00–11:00 and 10:30–11:30 overlap; bookings must not overlap (touching is fine)`.

There are two handling classes, and each gets a type. `InvalidDuration` is the requester's input, so a UI
asks the user for a positive duration. `InvalidSchedule` is corrupt calendar data from the caller, so it is
logged or alerted. The two leaves under `InvalidSchedule` exist because their structured payloads differ:
one span versus a pair. Merging them would produce a bag with optional fields.

A non-`time` / non-`timedelta` argument is a programming error. It falls through as the stdlib's
`TypeError` and is not wrapped (§5: let unactionable failures fall).

### 1.4 Internal modules: responsibility, surface, rules owned

#### `_timeline.py`: foundational value types (the package's working currency)

This module owns the time representation. It is the only place that does arithmetic on times of day.

```python
class RangeError(ValueError):                  # private; carries `reason`; translated at the boundary
    reason: str

@dataclass(frozen=True, slots=True)
class TimeRange:
    """A non-empty half-open interval [start, end) of naive wall-clock time within one day."""
    start: time
    end: time
    def __post_init__(self) -> None: ...       # R5: start < end, else RangeError; R6: tzinfo is None, else RangeError

    @staticmethod
    def spanning(start: time, end: time) -> "TimeRange | None": ...   # the non-raising form: None when empty
    def overlaps(self, other: "TimeRange") -> bool: ...               # R2: self.start < other.end and other.start < self.end
    def intersection(self, other: "TimeRange") -> "TimeRange | None": ...  # R2: None when they only touch or are apart
    def leading(self, length: "SlotDuration") -> "TimeRange | None": ...   # R2: [start, start+length) if it ends <= self.end
    def after(self, prefix: "TimeRange") -> "TimeRange | None": ...        # [prefix.end, self.end), None when empty
    def as_span(self) -> Span: ...                                          # for error payloads / output only

@dataclass(frozen=True, slots=True)
class SlotDuration:
    """A strictly positive requested booking length."""
    _length: timedelta
    def __post_init__(self) -> None: ...       # R5: length > 0, else errors.InvalidDuration
```

Rules owned:
- **R2, the half-open rule, whole.** Every "does it overlap / fit / touch" question in the package is one of
  `overlaps`, `intersection`, `leading`, or `spanning`. No other module compares an end with a start.
- **R5 validity of intervals.** Only the constructor checks it. `spanning`/`after`/`intersection` route
  the same predicate into `None`, which makes an empty interval impossible to represent.
- **R5 validity of duration.** Only `SlotDuration`'s constructor checks it.
- **R6, tz-aware rejection.** This is the only place `tzinfo` is checked.

A hidden decision: `leading` converts `time` to an offset from midnight (`timedelta`) through two private
helpers, `_offset(t)` and `_at(offset)`. This is the only time arithmetic in the package. It cannot overflow
past midnight, because it converts back only a value `<= self.end`.

#### `_schedule.py`: the day's occupancy and its free time

```python
class DaySchedule:
    """One resource's day: a working window plus its bookings, clipped to the window,
    sorted, pairwise non-overlapping. Answers which slot starts fit."""
    def __init__(self, window: TimeRange, bookings: Iterable[TimeRange]) -> None: ...
        # R4: sort by (start, end); reject the first overlapping adjacent pair → errors.OverlappingBookings
        # R3: keep only b.intersection(window) for each booking; drop None (wholly outside / touching the edge)
    def slot_starts(self, length: SlotDuration) -> list[time]: ...
        # earliest-first: walks its maximal free gaps in order, tells each gap to step

@dataclass(frozen=True, slots=True)
class _FreeGap:                                # module-private; constructed only by DaySchedule
    """A maximal interval of free time inside the window (not a booking, not a slot)."""
    _range: TimeRange
    def slot_starts(self, length: SlotDuration) -> Iterator[time]: ...
        # R1: remaining = _range; while (slot := remaining.leading(length)): yield slot.start;
        #     remaining = remaining.after(slot)  — the leftover shorter than length is never offered
```

Rules owned:
- **R4** (sort, reject overlaps) is enforced in the constructor.
- **R3** (clipping) is also enforced in the constructor.
- **Gap maximality and ordering.** `_free_gaps()` is private. It walks a cursor from `window.start` across
  the sorted, clipped bookings. Each gap is `TimeRange.spanning(cursor, booking.start)`, and `None` means
  there is no gap: the bookings touch, or a booking sits at the window's start. After the last booking the
  final gap is `spanning(cursor, window.end)`.
- **"Earliest first."** Gaps come out ascending and disjoint, and starts ascend within each gap. That makes
  the concatenation sorted by construction, with no final sort.
- **`_FreeGap` owns R1.**

The invariant *occupied ranges are sorted, disjoint and inside the window* is established once in
`__init__` and trusted by `slot_starts`.

#### `_boundary.py`: the one public seam

```python
def available_slots(working_hours: Span, bookings: Iterable[Span], duration: timedelta) -> list[time]:
    length = SlotDuration(duration)                                   # R5 (duration)
    window = _parse(working_hours, subject="working hours")           # R5, R6
    occupied = [_parse(b, subject=f"booking #{i}") for i, b in enumerate(bookings, 1)]
    return DaySchedule(window, occupied).slot_starts(length)          # R4, R3 at construction; R1 inside

def _parse(span: Span, *, subject: str) -> TimeRange:
    # the single translation point: TimeRange(*span), RangeError → errors.InvalidInterval(subject, span, reason)
```

The boundary checks no rules itself. It turns raw values into trusted types, whose constructors own the
rules. It adds the one thing those constructors cannot know, which is the caller's label for the value
(`"booking #3"`). Validation order is deterministic: duration, working hours, bookings in input order, then
overlaps.

### 1.5 Rule → owner map (each rule has exactly one home)

| Rule | Owner (the only place it is decided) | Why there |
|---|---|---|
| R1 gap-aligned stepping, leftover dropped | `_FreeGap.slot_starts` | Stepping belongs to free time and needs nothing outside the gap (Tell-Don't-Ask) |
| R2 half-open: overlap, touch, fit-to-end | `TimeRange.overlaps / intersection / leading / spanning` | The interval semantics belong to the interval. Every other owner *asks* it, so one comparison operator decides touching everywhere |
| R3 only the in-window portion counts | `DaySchedule.__init__` (the decision), using `TimeRange.intersection` (the geometry) | "What counts as occupancy of this day" is a fact about the day, not about an interval |
| R4 sort; reject overlapping pair | `DaySchedule.__init__` | It is the invariant of a day's occupancy; the aggregate that relies on it establishes it |
| R5 interval `end <= start` | `TimeRange.__post_init__` | An empty or negative `TimeRange` cannot be represented; subject label added at `_boundary._parse` |
| R5 duration `<= 0` | `SlotDuration.__post_init__` | The stepping loop only terminates when length > 0, and the type carries that precondition |
| R5 empty result is not an error | `DaySchedule.slot_starts` returns `[]` | There is no error path for "nothing fits" anywhere |
| R6 naive single-day time | Public seam type `time` (no midnight crossing) + `TimeRange.__post_init__` (no tzinfo) | The seam type makes crossing midnight unrepresentable, and the constructor rejects the rest |
| Earliest-first ordering | `DaySchedule.slot_starts` (ordered gaps × ascending steps) | Holds by construction, with no sort to forget |
| Input validated once | `_boundary.available_slots`: the only place raw input becomes value types | The core only accepts types that cannot hold invalid values |

---

## 2. Trace of C1–C14

Notation: W = window, g = free gap, `lead` = `TimeRange.leading`.

- **C1.** W = [09:00, 17:00). Bookings [09:00, 09:45) and [11:00, 12:00) are sorted, do not overlap, and
  are unchanged by clipping.
  - Gap walk: cursor 09:00. `spanning(09:00, 09:00)` gives `None`. Cursor moves to 09:45, then g1 =
    [09:45, 11:00). Cursor moves to 12:00, then g2 = [12:00, 17:00).
  - g1: lead gives 09:45, then 10:15. The next candidate would be [10:45, 11:15), and 11:15 > 11:00 gives
    `None`, so the 15-minute leftover is dropped.
  - g2: 12:00, 12:30, and so on up to 16:30, where [16:30, 17:00) ends at 17:00 <= 17:00 and is offered.
  - Output: 09:45, 10:15, 12:00, …, 16:30. ✓
- **C2.** No bookings, so there is one gap equal to W. It yields 09:00 through 16:30 (16 starts). ✓
- **C3.** For example, one booking [08:00, 18:00) clips to [09:00, 17:00). Or several touching bookings tile
  W. The cursor reaches 17:00, `spanning(17:00, 17:00)` gives `None`, there are no gaps, and the result is
  `[]`. ✓
- **C4.** Duration 3h with every gap under 3h: the first `lead` on each gap returns `None`, so `[]`.
  Duration 9h > W: the single gap's `lead` returns `None`, so `[]`. The arithmetic stays in `timedelta`, so
  there is no midnight overflow. ✓
- **C5.** g = [10:00, 10:30), d = 30 min: `lead` gives [10:00, 10:30), which is allowed because
  end == end. `after` gives `spanning(10:30, 10:30)`, which is `None`. That is 1 slot. g = 75 min: 10:00 and
  10:30, then [11:00, 11:30) exceeds 11:15, giving 2 slots. ✓
- **C6.** [08:00, 09:00).intersection(W) = `spanning(09:00, 09:00)` → `None`, so the booking is dropped.
  [17:00, 18:00) is dropped the same way. Output equals C2. ✓
- **C7.** [08:30, 09:30) clips to [09:00, 09:30), and the first gap starts at 09:30. [16:30, 17:30) clips
  to [16:30, 17:00). ✓
- **C8.** [10:00, 10:30) and [10:30, 11:00): `overlaps` evaluates `10:30 < 10:30`, which is false, so both
  are accepted. The gap walk gives `spanning(10:30, 10:30)` → `None`, so there is no slot between them. ✓
- **C9.** [10:00, 11:00) and [10:30, 11:30) are adjacent after sorting and `overlaps` is true. The result
  is `OverlappingBookings(first=(10:00, 11:00), second=(10:30, 11:30))`. ✓
- **C10.** The `(start, end)` sort in `DaySchedule` makes every later step order-independent. This covers
  identical output and also which overlap error is reported. ✓
- **C11.** Booking (10:00, 10:00): `TimeRange` raises `RangeError`, and `_parse` turns it into
  `InvalidInterval("booking #1", …, "end must be after start")`. Hours (17:00, 09:00) give
  `InvalidInterval("working hours", …)`. ✓
- **C12.** `SlotDuration(timedelta(0))` or a negative value raises `InvalidDuration`. This is checked first,
  before any schedule is looked at. ✓
- **C13.** g = [10:00, 12:00), d = 45 min: 10:00, then 10:45, then [11:30, 12:15) exceeds 12:00. That is
  2 slots, with 30 minutes unused. ✓
- **C14.** The last `lead` in C1/C2 is [16:30, 17:00), and `leading`'s test is `end <= self.end`. It is
  offered. ✓

**Cases beyond C1–C14.** I crossed each input dimension (booking position, count, order, duration size)
with each rule. That surfaces these cases, which the list above does not name:
- **Duplicate identical bookings.** They overlap, so they are rejected (R4).
- **A booking wholly outside W that is invalid.** It is still rejected, because R5 says "any booking".
- **Two bookings that overlap each other entirely outside W.** They are rejected: the overlap check runs on
  raw bookings, before clipping. This is an open question; see §6.
- **A booking strictly inside a gap near close.** For example, with d = 30 min, a gap [16:45, 17:00) yields
  nothing.
- **A generator passed as `bookings`.** It is consumed exactly once, in `_boundary`.

---

## 3. Design reasoning

### 3.1 What each concept IS (the hard decision)

| Concept | What it is | Why |
|---|---|---|
| Interval semantics | `TimeRange`, the foundational value type | R2 needs one owner, and every other concept is built from intervals |
| Working window | A `TimeRange` in the role `DaySchedule.window` | Its only rule is being the clipping frame, and that rule belongs to the day (R3). A `WorkingHours` class would own nothing (a lazy class) |
| Booking | A `TimeRange` in the role of an occupied range inside `DaySchedule` | In stage 1 a booking has no identity or attributes and owns no rule. The rules *about* bookings (R3, R4) are rules of the day's occupancy |
| Free gap | `_FreeGap`, its own type | This is the concept-fit decision. Free time is not a booking, and not a "negative booking". It has its own invariant (maximal, inside W, produced only by the day) and owns R1 |
| Candidate slot | A transient `TimeRange` from `leading` | It has no rules of its own. Its fitting rule is R2 containment, which `TimeRange` already owns. Output is starts only (the product asks for start times), so there is no `Slot` type |
| Duration | `SlotDuration` | It owns R5-duration, and positivity is what guarantees the stepping loop terminates |
| Slot policy | A behaviour (`_FreeGap.slot_starts`), not an object | Stage 1 has exactly one policy and no present variation. A Strategy would be indirection with no force (§9) |

Criterion used consistently: a role gets its own type **only when it owns a rule or an invariant**.
`_FreeGap` and `SlotDuration` qualify. The window role and the booking role do not.

### 3.2 Where the public boundary sits, and why nothing leaks

- The seam is one function. In: `time`, `timedelta`, `tuple`. Out: `list[time]` plus the published error
  types. `TimeRange`, `SlotDuration`, `DaySchedule` and `_FreeGap` never appear in a public signature,
  return value, or error payload. Error payloads use `Span`, not `TimeRange`.
- The representation (time-of-day plus a private offset conversion) can therefore change freely. For
  example, it could switch to integer microseconds or to anchored `datetime`s without touching a caller.
- The boundary does not re-implement checks. It asks trusted types to be constructed, so "validated once"
  and "one owner per rule" are the same act. A future path into the core cannot skip validation, because the
  core has no parameter that accepts an unvalidated value.
- On unforgeability in Python: the language cannot seal constructors. The design routes every legitimate
  path through one place:
  - underscore modules and `_FreeGap`;
  - `__all__` limited to the seam;
  - frozen `slots` dataclasses;
  - every invariant checked in `__post_init__`, so even an internal caller cannot build a bad `TimeRange`.
  
  `test_public_surface.py` guards the seam.

### 3.3 Error translation policy

A core type raises the **public** error directly when it has everything the message needs:
`SlotDuration` raises `InvalidDuration`, and `DaySchedule` raises `OverlappingBookings`. `TimeRange` cannot
know the caller's label ("booking #3"), so it raises a private `RangeError`. `_boundary._parse` is the one
place that translates it. No implementation exception crosses the seam.

### 3.4 Alternatives rejected

- **Public `TimeRange` / `Booking` input classes.** These would publish behaviour (`overlaps`, `leading`)
  and the representation, which couples callers to internals. Stdlib `time` pairs are complete for the
  consumer and are its own vocabulary.
- **Public `datetime` instead of `time`.** This needs extra rules (same date, what a booking on another
  day means) that the product does not have. `time` makes R6 structural.
- **Integer minutes.** This is primitive obsession, it silently truncates seconds, and it pushes
  conversion onto every caller.
- **If-checks in the boundary with plain internal tuples.** The rules would live in a function that any
  new path could skip, so the owner would be forgeable. This was rejected for constructor-owned invariants.
- **Checking "fits" as `start + d <= gap.end` inside the stepping loop.** That is a second, hidden owner of
  R2. It was rejected: stepping asks `TimeRange.leading`.
- **Free time as the complement of bookings, or bookings padded into gaps.** Both are concept cram. Free
  gaps are produced as their own type.
- **Fixed day grid, or a pluggable `SlotPolicy` Strategy.** The grid is a decided non-goal. A Strategy
  interface serves no present force; see §3.5 for where it would go.
- **Merging overlapping bookings.** This is ruled out by decisions/0002.
- **A CLI.** No present caller needs one.

### 3.5 Where the stage-1 non-goals would land (named only, nothing built)

| Non-goal | Where it would go |
|---|---|
| Buffers / breaks | `DaySchedule.__init__`, as more occupied ranges or inflated occupancy. This is the one occupancy owner, so there would be no trailing filter |
| Grid alignment | `DaySchedule.slot_starts` would take a policy in place of `_FreeGap`'s fixed stepping. That is the one R1 owner, and the rule would be replaced there, not duplicated |
| Time zones / multi-day | Only the boundary's seam type and `_parse` |
| Multiple resources | The caller calls `available_slots` once per resource |

### 3.6 Principles that do not apply at this scale

- **Ports and adapters, and dependency inversion toward I/O.** There is no I/O. The whole package is a
  functional core, and the caller is the shell.
- **Concurrency.** There is no shared state; everything is immutable or local.
- **Security.** There is no trust boundary beyond input validation, which §1 covers.
- **Performance.** No requirement is stated. The algorithm is O(n log n) in bookings plus O(output); see
  the risk noted in §6.

### 3.7 Subtractive pass (each element, and the present force that keeps it)

| Element | Force that keeps it |
|---|---|
| `Span` alias | Names the public input and payload shape; no runtime cost |
| `TimeRange` | Sole owner of R2, R5-interval and R6-tz; used by every other owner |
| `SlotDuration` | Sole owner of R5-duration; guarantees stepping terminates |
| `RangeError` (private) | The only way to add the caller's subject label without `TimeRange` knowing its callers. Cutting it would force either a second validity check in the boundary or a label parameter on a value type |
| `DaySchedule` | Owns R3, R4 and ordering; holds the occupancy invariant that `slot_starts` trusts. As a bare function it would validate and compute in one body with no named invariant |
| `_FreeGap` | Concept fit (free time is not a booking) and sole owner of R1. It is the lightest element; kept because cutting it turns stepping into a function that pulls `start`/`end` out of a range (ask, not tell) |
| `errors`: 5 classes | Base (catch-all), two handling classes (`InvalidDuration` vs `InvalidSchedule`), and two leaves with distinct payloads |
| Removed during the pass | A `WorkingHours` class and a `Booking` class (they owned nothing), a `Slot` type (the output is starts), a `SlotPolicy` protocol (no present variation), a CLI (no caller) |

**Concept-fit pass.** No element is a degenerate instance of a neighbour:
- Free time is its own type.
- The window is not a big booking.
- An empty interval is `None`, never a zero-length range.
- "Nothing fits" is `[]`, never an error or a sentinel.

---

## 4. Test plan (test-first; behaviour at the seams)

The builder writes these in order. Each test names the decision it pins.

**A. `test_timeline.py`: owner tests for the foundational types.** These are stable value-type contracts,
so testing them directly is testing behaviour, not implementation.
1. `TimeRange` rejects `end == start` and `end < start` (R5), and rejects tz-aware `start`/`end` (R6).
2. `overlaps`: an overlap is true; touching on either side is false; containment is true (R2; C8, C9).
3. `intersection`: straddling clips (C7); touching the edge gives `None` (C6); wholly outside gives
   `None` (R3 geometry).
4. `leading`: an exact fit is returned, ending at the end (C5, C14); one microsecond too long gives
   `None`; a length greater than 24h gives `None` without overflow (C4).
5. `spanning`/`after`: an empty result gives `None`; a non-empty result gives a range.
6. `SlotDuration`: 0 and negative raise `InvalidDuration`; 1 µs is accepted (C12).

**B. `test_available_slots.py`: acceptance through the public function.** One test per case.
- C1 exact list; C2 16 starts, 09:00…16:30; C3 full cover (single straddling booking, and touching
  bookings tiling the day) → `[]`.
- C4 longest gap < d → `[]`, and d > W → `[]`.
- C5 gap == d → 1 slot, gap = 2.5d → 2 slots.
- C6 bookings ending at open or starting at close → equals C2.
- C7 straddling at open and at close.
- C8 touching accepted, no slot between.
- C9 `OverlappingBookings` with `.first` / `.second` equal to the pair, and the message names both.
- C10 every permutation of C1's bookings plus two others (`itertools.permutations`) gives the same output.
  An unsorted overlap reports the same pair in every order.
- C11 `InvalidInterval` for a zero-length booking, a reversed booking (subject `"booking #k"`), and
  reversed working hours (subject `"working hours"`).
- C12 zero and negative durations.
- C13 45 min in 2h gives 2 slots.
- C14 16:30 is present.

Extra cases from the full-input trace:
- duplicate bookings are rejected;
- an invalid booking wholly outside W is rejected;
- a generator input works;
- the error precedence order is duration → hours → bookings → overlap;
- `InvalidInterval` and `OverlappingBookings` are `InvalidSchedule`, and everything is `ValueError`.

**Invariant test** (seeded `random`, stdlib), over random non-overlapping bookings, windows and durations.
Every returned start:
- fits inside W;
- overlaps no booking;
- produces a sorted output;
- is either a gap start or exactly `d` after the previous start in the same gap;
- and no gap's leftover after its last start is `>= d`.

This checks R1 to R3 across the whole input space, beyond the listed cases.

**C. `test_public_surface.py`: the encapsulation seam.**
- `availability.__all__` equals exactly the seven names in §1.2.
- For `available_slots`' signature, and the error classes' annotated attributes, every annotation resolves
  to `datetime` / builtins / `Span` / errors. No `_timeline` or `_schedule` type appears.
- No public name is defined in an underscore module other than `available_slots` itself.

`DaySchedule` and `_FreeGap` are tested only through the public seam (B), so refactoring them does not
break tests.

---

## 5. Result

**met.** Every product rule R1–R6 has exactly one owner (table §1.5). Input is turned into trusted types
once, at the single public function, and the core never re-checks. The slot computation is pure: immutable
value types and no state or I/O. The skeleton gives concrete Python 3.11 stdlib signatures for every module.
No internal type crosses the public seam. All of C1–C14 trace through it.

---

## 6. New facts, risks and open product questions

1. **Overlap outside working hours (open).** R3 says bookings wholly outside hours are irrelevant, and R4
   says overlapping bookings are rejected. When two bookings overlap *only* outside the window, these
   conflict.
   - **Assumption:** reject. The overlap check runs on raw bookings, because a violation is a calendar
     bug wherever it sits.
   - **Where it would change:** `DaySchedule.__init__` (clip before checking) — one line in one owner.
2. **Close at midnight is not representable.** `datetime.time` has no 24:00, so hours like 18:00–24:00
   cannot be expressed, and `time.max` loses the final slot.
   - **Assumption:** R6 ("do not cross midnight") means the window ends at or before 23:59:59.999999.
   - **If 24:00 is needed:** only the seam type and `_parse` change, for example accepting an
     end-of-day marker.
3. **Tiny durations can produce a huge output.** For example, 1 µs over 8h gives about 2.9e10 starts.
   No minimum granularity or output cap is stated, so none was added. This needs a product answer if the
   UI may pass arbitrary durations.
4. **Rejecting tz-aware `time` inputs** is my reading of R6: "no time zones" means "fail fast", not
   "silently compare by UTC offset". It is owned in `TimeRange`.
5. **Error precedence** when several inputs are bad at once (duration → hours → bookings → overlap) is my
   choice. The product did not specify one.
6. **Python cannot seal constructors.** "Unforgeable" here means that every intended path goes through one
   owner and every invariant is checked in `__post_init__`. The surface test guards the seam.
   Monkey-patching is out of scope.
