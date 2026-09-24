# Bookable slots — stage-1 architecture (Worker, axis: clean code)

Axis pull: as few moving parts as the rules allow, every rule in one place, no smell left standing
(feature envy, shotgun surgery, primitive obsession, lazy class, speculative generality), and **zero**
dependencies beyond the standard library, **including for tests** (no pytest, no pyproject needed).

---

## 1. The design

### 1.1 What each domain concept IS

| Concept | What it is in the design | Why this kind of thing |
|---|---|---|
| Working window | an `Interval` (the `hours` argument) | It is a half-open span of wall-clock time. Nothing it does differs from any other span. |
| A booking | an `Interval` given by the caller; the day's bookings together are a **`Bookings`** value | One booking is just a span. The *set* of bookings has an invariant of its own (sorted, pairwise disjoint: R4) and one behavior of its own (its complement inside a window). That set is the real concept. |
| Free time (a gap) | an `Interval` **produced by** `Bookings.free_within(window)`, always maximal | Free time is the complement of occupancy. It is never stored in `Bookings` and never looks like a booking, so it is not a fake booking. It is a span, so it is an `Interval`. |
| Candidate slot | **not materialized.** It exists only as a tile `[t, t+d)` inside `Interval.tile_starts`; the output is its start `time` | The product returns starts, and no rule acts on a slot as an object. A `Slot` type would be a data class that nobody asks anything of. |
| Requested duration | `datetime.timedelta`, checked to be positive once at the entry | `timedelta` is already the foundational value for a length of time. Its only rule (> 0) is a check on the request, which one line covers. A wrapper class would be a lazy class. |
| Slot policy (R1) | one line in `available_starts`: *tile each free gap from its own start* (`gap.tile_starts(duration)`) | The decision "gap-aligned, not day-grid" is a choice of **which span gets tiled from which origin**. The tiling mechanics are ordinary interval geometry and belong to `Interval`. Only one policy exists and a grid is ruled out (decision 0002), so there is no `SlotPolicy` protocol. |

### 1.2 File tree

```
availability/
  __init__.py     # public surface only: re-exports Interval, InvalidAvailabilityRequest, available_starts
  errors.py       # InvalidAvailabilityRequest — the package's one error type
  interval.py     # Interval — half-open naive wall-clock span; owns R2, R3 clipping, R5 (intervals), R6, all time arithmetic
  bookings.py     # Bookings — the day's bookings as a sorted, disjoint set; owns R4 and free-gap derivation
  slots.py        # available_starts — the public entry; owns R5 (duration) and the R1 policy decision
tests/
  test_interval.py
  test_available_starts.py
```

Why each file exists, in one sentence each:
- `errors.py`: every other module raises the same error. Putting it at the bottom of the dependency graph means no module imports upward just to raise it.
- `interval.py`: this is the time model. The half-open rule and the "one naive day" rule live here, and any change to how time is represented touches only this file.
- `bookings.py`: occupancy is the change axis that future buffers or breaks would move. Keeping it apart from the policy keeps those changes out of `slots.py`.
- `slots.py`: this is the single public operation and the one place the slot policy is chosen.
- `__init__.py`: this lets callers import from `availability` without learning the module layout.

Dependency graph, which is acyclic and points toward the more stable modules:
`slots → bookings → interval → errors`, and `slots → interval, errors`.
The stdlib imports are `dataclasses`, `datetime`, `itertools.pairwise`, `collections.abc`, and `unittest` for tests. There are no third-party packages.

### 1.3 Public surface and concrete signatures

```python
# availability/__init__.py
from .errors import InvalidAvailabilityRequest
from .interval import Interval
from .slots import available_starts
__all__ = ["Interval", "InvalidAvailabilityRequest", "available_starts"]
```

```python
# availability/errors.py
class InvalidAvailabilityRequest(ValueError):
    """The caller sent something the product rules reject (R4, R5, R6).
    Always a caller bug; the message names the offending value(s) in wall-clock terms."""
```

```python
# availability/interval.py
@dataclass(frozen=True, slots=True)
class Interval:
    """A non-empty half-open span [start, end) of naive wall-clock time within one day.

    Invariant: start < end, and both times are naive (tzinfo is None).
    Because `time` cannot pass midnight, start < end also means the span never
    crosses midnight (R6 comes for free)."""
    start: time
    end: time

    def __post_init__(self) -> None: ...
        # raises InvalidAvailabilityRequest: "interval 17:00:00–09:00:00: end must be after start"
        #                                    "interval …: times must be naive wall-clock times (no tzinfo)"

    @classmethod
    def if_nonempty(cls, start: time, end: time) -> "Interval | None":
        """[start, end) if it has positive length, else None. The single emptiness decision
        (used by clipping and by gap derivation); never raises for start >= end."""

    def overlaps(self, other: "Interval") -> bool:
        """True iff the spans share an instant. Half-open: touching (a.end == b.start) is NOT overlap. (R2)"""

    def clipped_to(self, window: "Interval") -> "Interval | None":
        """The part of self inside window, or None if nothing is inside it (wholly outside or only touching). (R3)"""

    def tile_starts(self, size: timedelta) -> Iterator[time]:
        """Starts of back-to-back spans of `size` laid from self.start that fit wholly inside self
        (the last may end exactly at self.end; a remainder shorter than `size` is not covered).
        Precondition: size > timedelta(0). Earliest first."""

    def __str__(self) -> str:  # "09:00:00–09:45:00": the form used in every error message
        ...
```

All time arithmetic sits in `interval.py`, in one private helper. It borrows `datetime`'s arithmetic by
pinning the times to a fixed reference date (`datetime.combine(date.min, t)`), which is correct only
because of R6. The tile count is `length // size` (`timedelta // timedelta → int`). Starts are
`origin + k*size`, turned back with `.time()`. Every offset is under one day, so a huge `size` just gives
zero tiles and never overflows. For the same reason the loop always ends and needs no `while`.

```python
# availability/bookings.py
class Bookings:
    """The day's existing bookings, held sorted by start and pairwise non-overlapping (R4).
    Construction is the only validation; every method trusts the invariant."""

    def __init__(self, bookings: Iterable[Interval]) -> None:
        """Sorts by start. Rejects the first adjacent pair for which `overlaps` is true:
        InvalidAvailabilityRequest("bookings 10:00:00–11:00:00 and 10:30:00–11:30:00 overlap; bookings must not overlap (touching is fine)").
        After sorting by start, checking adjacent pairs is enough to prove every pair disjoint."""

    def free_within(self, window: Interval) -> Iterator[Interval]:
        """Maximal free spans of `window` not covered by any booking, earliest first.
        Each booking is first clipped to the window; bookings with nothing inside are skipped (R3)."""
```

Algorithm of `free_within`, in prose: set a cursor at `window.start`. For each booking in order, clip it
to the window. If nothing is left, skip it. Otherwise yield `Interval.if_nonempty(cursor, busy.start)`
when that is not None, then move the cursor to `busy.end`. At the end, yield
`Interval.if_nonempty(cursor, window.end)` when that is not None. The gaps are maximal because the
bookings are disjoint and sorted, so the cursor never goes backwards.

```python
# availability/slots.py
def available_starts(
    hours: Interval, bookings: Iterable[Interval], duration: timedelta
) -> list[time]:
    """Start times, earliest first, at which a booking of `duration` fits inside `hours`
    without overlapping any of `bookings`. Empty list when nothing fits (not an error).
    Raises InvalidAvailabilityRequest for duration <= 0 or overlapping bookings.
    (Reversed/empty/tz-aware intervals are already rejected when the caller builds the Interval.)"""
```

The body is three steps, and the last one is the R1 decision stated once:

```python
    # 1. reject duration <= 0 (R5), before any other work, so the check runs even when no gap exists
    # 2. occupied = Bookings(bookings)                                  (R4)
    # 3. return [t for gap in occupied.free_within(hours) for t in gap.tile_starts(duration)]   (R1)
```

### 1.4 The public boundary

The boundary is the package's public surface: **the `Interval` constructor plus `available_starts`**.
The caller turns its raw times into `Interval`s, and that is where R5 (intervals) and R6 are checked.
`available_starts` checks the duration and builds `Bookings`, which checks R4. Beyond that point,
`free_within`, `clipped_to` and `tile_starts` never validate anything; they rely on the invariants the
types carry.

The core does build `Interval`s itself (clipped bookings and gaps). It builds them only through
`if_nonempty`, so it never builds an invalid one, and `__post_init__` re-checking the invariant there is
an invariant check, not a second validation.

The entry point is a **library function with no CLI**. The only stated caller (goals.md) is a UI or
service in the same process that wants a pick-list. A CLI would add a second boundary (parsing strings
into times, translating errors, formatting output) that no present caller needs.

### 1.5 Rule → owner

| Rule | Single owner | All paths go through it because… |
|---|---|---|
| R1 gap-aligned stepping | `available_starts` picks it (tile **each free gap**, from **its own start**). The mechanics (step by size, drop the remainder) are `Interval.tile_starts`; gap maximality is `Bookings.free_within` | Free time only reaches the tiler through that one line. The two helpers are generic span operations and neither encodes the policy choice. A grid policy would change only that line. |
| R2 half-open | `Interval`: `overlaps` (strict `<`), `if_nonempty` (emptiness), and `tile_starts` (a tile may end exactly at the end) | Overlap (R4), clipping (R3), gap emission and fitting all call these methods. No other module compares interval bounds. |
| R3 clip to hours | `Interval.clipped_to`, called only from `Bookings.free_within` | This is the only place bookings meet the window. |
| R4 sort + reject overlaps | the `Bookings` constructor (it uses `Interval.overlaps` for what "overlap" means) | `free_within` exists only on a constructed `Bookings`. |
| R5 intervals (end ≤ start) | `Interval.__post_init__` | Every `Interval` passes through it. |
| R5 duration ≤ 0 | `available_starts`, first statement | This is the only public operation that takes a duration. |
| R5 "no fit → []" | follows from the structure: no gaps, or `length // size == 0` | No special case exists that could drift. |
| R6 naive, single day, no midnight crossing | `Interval` (naive check in `__post_init__`; midnight crossing cannot be written because `time` wraps and start < end is required; the reference-date arithmetic is private to `interval.py`) | Time is represented in only one file. |

### 1.6 Error vocabulary

There is one type: `InvalidAvailabilityRequest(ValueError)`. Every rejection is handled the same way (a
caller bug to surface), so any subtype would be a subtype nobody catches differently. Subclassing
`ValueError` keeps generic handlers working, and having our own type lets a caller tell our rejections
apart from unrelated `ValueError`s. The messages are in wall-clock terms and name the offending values:
- a reversed or empty interval,
- a tz-aware interval,
- an overlapping **pair** (C9),
- a non-positive duration (showing the value).

"No slot fits" is a normal empty list, never an error.

### 1.7 Trace of C1–C14

The hours are 09:00–17:00 unless stated otherwise.

- **C1** Bookings `[09:00–09:45, 11:00–12:00]`, 30 min. `Bookings` sorts them; the pair only has 09:45 < 11:00, so no overlap. `free_within`: cursor 09:00, clip b1 → 09:00–09:45, `if_nonempty(09:00, 09:00)` → None, cursor 09:45. Clip b2 → 11:00–12:00, yield **09:45–11:00**, cursor 12:00. Tail: yield **12:00–17:00**. Tiles: first gap length 75 min // 30 → 2 → 09:45, 10:15. Second gap 300 // 30 → 10 → 12:00 … 16:30. The output matches.
- **C2** No bookings. `free_within` yields only the tail 09:00–17:00. 480 // 30 = 16 → 09:00 … 16:30.
- **C3** Booking 09:00–17:00 (or 08:00–18:00, clipped to 09:00–17:00). The leading and tail `if_nonempty` calls both give None, so there are no gaps → `[]`.
- **C4** A 6 h duration is longer than both of C1's gaps (75 min and 300 min): 75 // 360 = 0 and 300 // 360 = 0 → `[]`. A 9 h duration with no bookings is longer than the working hours: 480 // 540 = 0 → `[]`. A huge duration such as `timedelta(days=10**6)` also gives 0 with no overflow, because the count is computed before any addition.
- **C5** Gap exactly 30 min: 30 // 30 = 1 → one start. Gap 75 min with 30 min: 75 // 30 = 2 → two starts, 15 min unused.
- **C6** Booking 08:00–09:00: `clipped_to` → `if_nonempty(09:00, 09:00)` → None → skipped. Booking 17:00–18:00: `if_nonempty(17:00, 17:00)` → None → skipped. The output equals C2.
- **C7** Booking 08:30–09:30 → clipped 09:00–09:30; booking 16:30–17:30 → clipped 16:30–17:00. The gap is 09:30–16:30 → 09:30 … 16:00.
- **C8** Bookings 10:00–10:30 and 10:30–11:00: `overlaps` needs 10:30 < 10:30, which is false, so they are accepted. In `free_within`, after the first booking the cursor is 10:30 and `if_nonempty(10:30, 10:30)` → None, so there is no gap between them.
- **C9** Bookings 10:00–11:00 and 10:30–11:30: after sorting they are adjacent and `overlaps` is true → `InvalidAvailabilityRequest("bookings 10:00:00–11:00:00 and 10:30:00–11:30:00 overlap; …")`.
- **C10** Any permutation of the bookings gives the same sorted tuple in `Bookings`, so the downstream computation is identical and so is the output.
- **C11** `Interval(time(10), time(10))` and `Interval(time(17), time(9))` raise in `__post_init__`, for bookings and hours alike, at the boundary before `available_starts` runs.
- **C12** `duration=timedelta(0)` or a negative value → `available_starts` raises before building `Bookings` or computing anything. This holds even when the bookings cover the whole day.
- **C13** Hours 09:00–11:00 (or a 2 h gap), 45 min: 120 // 45 = 2 → 09:00, 09:45. The last 30 min is unused.
- **C14** In C2, the last tile has k = 15 → 16:30, and 16:30 + 30 = 17:00 = end is allowed because the count uses `//` on the full length. The start is offered.

**Full input-space pass** (every change axis crossed with every rule, beyond the listed cases):
- A booking wholly outside the hours that sorts between or around in-hours bookings is still skipped by clipping, and the cursor does not move.
- A booking that covers the whole window leaves no gaps.
- Bookings that overlap each other but lie wholly **outside** the hours are **rejected**, because R4 applies to the bookings as given (see §5).
- An identical duplicate booking counts as an overlap and is rejected.
- Times with seconds or microseconds work unchanged; nothing rounds to minutes.
- A tz-aware time is rejected (R6) instead of leaking a `TypeError` from mixed comparisons.

---

## 2. Design reasoning

**Why one `Interval` type for window, booking and gap (and not three).** These are all half-open spans
with exactly the same behavior: overlap, clip, tile. Three classes with the same fields and methods would
be *alternative classes with the same interface* plus duplicated invariants, so a change to R2 would need
the same edit in three places.

Concept fit is kept because the roles differ in **provenance and holder**, not in kind:
- the window is the `hours` argument,
- bookings live only inside `Bookings`,
- gaps only come out of `free_within` and never go back into `Bookings`.

The concept-fit failure the objective warns about, "free time as a fake booking", would mean inserting or
subtracting synthetic bookings. That never happens here. The one concept that *does* have its own rules,
the set of bookings, gets its own type.

**Why `Bookings` is a type and not a sort-and-check function.** The gap derivation is correct only on
sorted, disjoint input. As a bare `list[Interval]`, that precondition would be invisible (primitive
obsession on a collection) and the code would be one refactor away from "validate inside the core". The
constructor is the boundary and the method is the core. That makes "validated once, core trusts"
*structural*. Tell-don't-ask: the entry asks `occupied.free_within(hours)` rather than pulling the list
out and walking it.

**Why the time arithmetic is on `Interval` (`tile_starts`) rather than in a policy function.** A private
`_gap_aligned_starts(gap, duration)` in `slots.py` would read `gap.start` and `gap.end` and do date
arithmetic on them. That is **feature envy**. It would also spread the reference-date trick (knowledge
that depends on R6) over two files, so a later change to the time model (for example multi-day, with
`datetime` fields) would be **shotgun surgery**. Putting tiling on `Interval` keeps the whole time model
in `interval.py`.

The *policy* stays out of `Interval`. `tile_starts` does not know about gaps, bookings or alignment
choices; it is left-aligned tiling of whatever span it is given. The product decision is which spans get
tiled, and that is the one line in `available_starts`.

**Why `time`, not `datetime`, at the public boundary.** R6 says one naive day with no midnight crossing.
With `time`, "crosses midnight" cannot be expressed: `22:00–02:00` is simply `end < start` → rejected by
R5's own owner. Bookings from other days cannot be expressed either. With `datetime`, both would need
extra guards (same date, no crossing), and the caller would have to invent a date the product does not
care about. Arithmetic needs a date, so it is borrowed privately (`date.min`) inside `interval.py`, where
R6 makes that correct.

**Why `timedelta` and not a `Duration` type.** Its one rule (> 0) is a request check with one owner (the
entry, which is the only public operation that takes a duration). `tile_starts` states `size > 0` as a
precondition (Design by Contract). A wrapper class would add a type, a constructor and an import only to
move one comparison, so it would be a lazy class.

**Errors inside `Interval`'s constructor, not in the entry.** An `Interval` with end ≤ start is not an
interval. Making it impossible to construct removes a whole class of "did anyone check?" questions, and
it gives C11 exactly one owner whether the span is the hours or a booking.

The cost is that the message does not say "booking" or "hours". The caller built that value a line
earlier, so the message's `str(interval)` identifies it well enough. Adding a role parameter to thread
into the message would be connascence for cosmetics.

**Alternatives rejected** (each fails the subtractive test: no present force):
- `SlotPolicy` Protocol / Strategy. Fixed-grid is ruled out in decision 0002, so no change-axis item would use the seam (the §7 tie-break says over-build). The single call site is the place a second policy would plug in if one were ever decided.
- `WorkingHours`, `FreeGap`, `Slot` classes. They add no behavior beyond `Interval`: they would be data classes and duplicate the interval rules.
- `AvailabilityRequest` DTO. Three parameters of three different types are not a long parameter list, and a DTO would be a data clump bundling nothing.
- Merging overlapping bookings. R4 says reject, and decision 0002 rules merging out.
- A CLI or string parsing layer. No caller needs it (see §1.4).
- `dataclass(order=True)` on `Interval` for sorting. "Is one interval less than another" has no domain meaning. Sort with `key=start` inside `Bookings`.
- pytest or a pyproject. `unittest` covers this, and the dependency diet stays at zero.

**Seams a later stage would use (named only, nothing built).**
- Buffers and breaks change **occupancy**, so they would be absorbed in `bookings.py`. Breaks would become a busy span fed to `free_within`. At that point `Bookings` would probably be renamed and generalized to `Occupancy`, so that a break is not modeled as a synthetic booking.
- Multi-day or time zones change the time model → `interval.py` only.
- Multiple resources means calling `available_starts` once per resource.

**Principles that do not apply at this scale:**
- Ports & adapters: there is no I/O, so the whole package is the functional core and the caller is the shell.
- Security (§14): this is an in-process caller, not a trust boundary beyond input validation.
- Performance (§13): no requirement is stated. The cost is O(n log n) for the sort and linear for everything else.

**Subtractive pass (element → present force):**
- `InvalidAvailabilityRequest` → R4/R5/R6 "clear error".
- `Interval` → R2/R3/R5/R6 are all rules about spans.
- `if_nonempty` → one emptiness decision shared by clipping and gap derivation. Without it the `start < end` test would be copied into `bookings.py`.
- `overlaps` → R2 and R4.
- `clipped_to` → R3.
- `tile_starts` → R1 mechanics and C5/C13/C14, and it keeps the time arithmetic in one file.
- `__str__` → C9 "error names the pair" in wall-clock terms.
- `Bookings` → R4 invariant and C10.
- `free_within` → free time as its own concept.
- `available_starts` → the product operation.
- `errors.py` → an acyclic home for the shared error.

Nothing was cut in the final pass. `Duration`, `Slot`, `SlotPolicy`, a request DTO and the CLI were cut earlier.

**Concept-fit pass:**
- Free time is the complement, returned and never stored as a booking.
- A candidate slot is not materialized as a fake interval with a role flag; it is implicit in tiling.
- A duration is a length (`timedelta`), not an `Interval` anchored at midnight.
- The working window is a span, not a special booking-like "closed" region.
- No inert stand-ins exist anywhere.

---

## 3. Test plan (test-first, stdlib `unittest`, pure and fast, no fixtures or mocks)

There are two seams, both public. **`Interval`** is a published type, so its contract is tested
directly. **`available_starts`** is tested for everything composed behind it. `Bookings` is internal, and
every one of its decisions can be seen through the entry, so testing it there keeps the tests off the
internal layout (a refactor inside the package breaks no test).

`tests/test_interval.py` (the time-model and half-open contract):

| Decision | Test | Case |
|---|---|---|
| R5 invariant | `Interval(10:00, 10:00)` raises; `Interval(17:00, 09:00)` raises; message contains the times | C11 |
| R6 naive | an interval with `tzinfo` on either end raises `InvalidAvailabilityRequest` | R6 |
| R2 overlap | overlapping → True; containment → True; touching in both orders → False | C8, C9 |
| R3 clip | straddling open → clipped start; straddling close → clipped end; wholly outside → None; touching the open or close edge → None; wholly inside → equal to self | C6, C7 |
| emptiness | `if_nonempty(t, t)` → None; `if_nonempty(later, earlier)` → None, not raise | C3, C8 |
| tiling | size == length → 1 start; 2.5× → 2; 45 min in 2 h → 2 (09:00, 09:45); last tile ends exactly at end → offered; size > length → none; `timedelta(days=10**6)` → none, no `OverflowError` | C4, C5, C13, C14 |
| sub-minute | 7 min 30 s tiles keep seconds | input space |

`tests/test_available_starts.py` (composition, R1 policy, R4, R5 duration):

| Decision | Test | Case |
|---|---|---|
| worked example | the exact C1 list | C1 |
| empty day | 16 starts 09:00…16:30 | C2, C14 |
| full cover | booking 09:00–17:00 → `[]`; booking 08:00–18:00 → `[]` | C3, C7 |
| nothing fits | 6 h duration against C1 bookings → `[]`; 9 h with no bookings → `[]` | C4 |
| gap-aligned (not grid) | C1 result contains 09:45 and 10:15 (a grid would give 10:00) | C1, R1 |
| exact / partial gaps | 30 min gap → one; 75 min gap → two | C5 |
| edge-touching bookings | 08:00–09:00 and 17:00–18:00 → same as C2 | C6 |
| straddling | 08:30–09:30 and 16:30–17:30 → 09:30…16:00 | C7 |
| touching bookings | 10:00–10:30 and 10:30–11:00 accepted; no start in [10:00, 11:00) | C8 |
| overlap rejection | raises; `str(error)` contains both intervals' `str` | C9 |
| duplicate booking | the same interval twice → raises | R4 |
| overlap outside hours | two overlapping bookings wholly before opening → raises (pins the assumption in §5) | R4 × R3 |
| order independence | reversed and shuffled C1 bookings → equal to the C1 list | C10 |
| duration ≤ 0 | 0 → raises; −30 min → raises; 0 with full-cover bookings → still raises (check not skipped when there are no gaps) | C12 |
| remainder unused | hours 09:00–11:00, 45 min → [09:00, 09:45] | C13 |
| input is any iterable | a generator of bookings works (consumed once) | signature contract |

No coverage percentage. Every row is a decision someone could get wrong.

---

## 4. Result

**met.** Every rule R1–R6 has one named owner (§1.5). Validation happens once at the public surface
(`Interval` construction, `available_starts`, `Bookings` construction), and the core (`free_within`,
`clipped_to`, `tile_starts`) trusts typed invariants. The core is pure and made of four small concepts
(`Interval`, `Bookings`, `timedelta`, `time`). The module skeleton and signatures are concrete Python 3.11
stdlib, and C1–C14 are traced. Nothing invalidates the objective.

## 5. New facts, risks, open product questions

1. **Working hours ending at midnight cannot be written.** `time` has no 24:00, so `Interval(22:00, 00:00)` is rejected as end ≤ start. **Assumption:** stage-1 resources close before midnight. If the owner needs "open until midnight", the fix belongs in `interval.py` only (e.g. an end-of-day sentinel or a `datetime`-based representation).
2. **Overlapping bookings wholly outside working hours are rejected.** R4 is read as applying to the input as given; R3's "irrelevant" is read as about slot computation, not validation. **Assumption:** a caller bug is a caller bug wherever it sits. The owner may prefer to ignore them. That change would stay inside `Bookings`, which would then take the window at construction and check overlaps after clipping. R4 would still have one owner.
3. **Identical duplicate bookings are rejected** as an overlap. This is a sensible reading of R4, but a caller that double-reports a booking will get an error, not deduplication.
4. **The error message for a bad interval does not say "hours" vs "booking".** This is accepted, because the caller built that value itself (§2).
5. **Non-`time` arguments are not type-guarded.** For example, passing a `datetime` where a `time` is expected leaks a `TypeError` from the date arithmetic. Type hints and a type checker cover this, and a runtime `isinstance` guard answers no stated rule.
6. **Sub-minute precision is kept** (seconds and microseconds pass through). The output format is `time` objects. Rendering, such as `HH:MM`, is the caller's job. If the owner expects minute granularity only, that is a new rule and it would belong in `Interval`.
