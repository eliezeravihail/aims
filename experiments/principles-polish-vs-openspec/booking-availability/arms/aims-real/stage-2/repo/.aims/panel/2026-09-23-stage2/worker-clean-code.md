# Stage 2: revised availability architecture (Worker, clean-code axis)

Axis: **clean code**, meaning few moving parts, no smells, and a lean dependency list. The stage-1 design
(`DESIGN.md`, decisions 0001–0003) is the ground truth. This document changes it and does not replace it.
Anything not mentioned here stays exactly as `DESIGN.md` says.

**Result: met.** (§9 lists what is still open.)

---

## 0. The change in one paragraph

A buffer is **occupancy**, so the occupancy owner (`DaySchedule`) absorbs it in two places. At
construction, each booking's range is extended by the buffer before it is clipped (B1). When the schedule
yields where a new booking may lie, a gap that is closed by occupancy is shortened by the new booking's own
buffer, and the tail gap that runs to closing is not shortened (B2). The stage-1 cursor walk is unchanged.
One restated invariant covers overlapping occupancy: the ends of the runs never decrease (§3.3). Both slot
policies are the same kind of thing, a **lattice** (an origin and a step). Gap-aligned is (the gap's start,
the duration) and grid is (the start of working hours, the granularity). So one total `TimeRange` method
lists the lattice points that fit, replacing `leading`, and a two-branch private function picks the lattice.
Notice is converted from an instant to a wall-clock `time` **once**, in a new published value `AsOf(day,
now)`. It is applied as the one filter `earliest <= start`, because by decision 0004 notice *removes*
starts. The entry gains two keyword-only parameters, `rules: ResourceRules` and `as_of: AsOf | None`, whose
defaults give stage-1 behaviour exactly.

---

## 1. File tree (N = new, C = changed, U = unchanged)

```
availability/
  __init__.py      C  __all__ += "ResourceRules", "AsOf"
  errors.py        C  docstring only (InvalidAvailabilityRequest now also covers V1); no new type
  time_range.py    C  TimeRange: − leading; + extended, trimmed, fitting_starts
                      + AsOf (published): the one instant → wall-clock conversion
  rules.py         N  ResourceRules (published): per-resource buffer / notice / granularity; V1; N2
  _day.py          C  DaySchedule(hours, bookings, buffer); occupancy = extended then clipped;
                      invariant I2/I3 restated; free_gaps → bookable_spans (B2 trim)
  slots.py         C  available_starts(..., *, rules, as_of); _gap_aligned_starts → _aligned_starts
tests/
  test_time_range.py     C  T8 migrated from leading to fitting_starts; T11–T13 added
  test_rules.py          N  ResourceRules validation + N2
  test_available_starts.py  C  A1–A21 UNCHANGED; B1–B20 added
  test_invariants.py     C  stage-1 properties unchanged; stage-2 generator + properties added
  test_public_surface.py C  P1/P2/P3 updated; P6 added
```

Runtime dependencies are still acyclic and still point toward `errors`:

```
slots ──► rules ──► time_range ──► errors
  │  └──► _day  ──►     ▲             ▲
  └─────────────────────┴─────────────┘
```

- `rules` imports `time_range` (for `AsOf` and `TimeRange` in annotations) and `errors`.
- `_day` does **not** import `rules`. It receives `buffer: timedelta`, which is the weakest coupling that
  works.
- **Dependency diet:** still the standard library only. The runtime uses no new stdlib *module*, only the
  names `date` and `datetime` from `datetime`, which it already imports. The tests add `inspect` (for P6).
  There is still no pyproject and no pytest.

---

## 2. Stage-2 assumptions added to DESIGN.md §1.2

| # | Assumption | Why | Change lands in |
|---|---|---|---|
| A10 | "Cut at end of day" (M1) means ending the range at `time.max`. The last microsecond `[23:59:59.999999, 24:00)` is not representable (A3). | Working hours end at or before `time.max`, so that microsecond is always outside the hours. R3 would drop it anyway, so the difference cannot be observed. | `TimeRange.extended` |
| A11 | `ResourceRules` and `AsOf` have **no type guards** beyond the tz check. `buffer=15` (an int) or `now=date(...)` fail loudly with the stdlib `TypeError`/`AttributeError` at the first comparison or attribute access, in `__post_init__`. A `datetime` passed as `day` is accepted and its date is used, which gives the same meaning. | This follows A7: a guard goes only where a wrong type would be *silently accepted with a wrong meaning*. The one such case is `TimeRange(datetime, datetime)`, and it keeps its guard. | `__post_init__` of each |
| A12 | **Validation precedence** (S13). Caller-side construction comes first, in the caller's expression order: `TimeRange` checks type, then tz, then emptiness; `ResourceRules` checks buffer, then notice, then granularity; `AsOf` checks tz. Inside `available_starts` the checks are (1) duration ≤ 0, (2) notice > 0 without `as_of`, (3) overlapping bookings. When the notice cutoff falls after the day, the result is `[]`, but **only after** check (3) has passed. | Extends stage-1 A6 and keeps it cheapest-first and deterministic. An overlap is a caller bug even on a day that is already past. | the order of statements in `available_starts` |
| A13 | Granularity makes **every** fitting grid point a start, so a small `g` can return many more starts than stage 1 did (g = 1 µs over 8 h gives about 2.9·10¹⁰). | There is still no output cap (A5, and 0004 lists a cap as a non-goal). | `available_starts`, next to the duration check (as in A5) |

---

## 3. Modules: responsibility, public surface, signatures

### 3.1 `errors.py` (docstring only)

No new type. Every V1/N2 violation raises `InvalidAvailabilityRequest`, because no caller handles them
differently (the reasoning of DESIGN §3.1: one subtype only where the payload differs). The docstring grows
from "(R4, R5, R6)" to "(R4, R5, R6, V1)".

### 3.2 `time_range.py`: the time model (changed)

**Responsibility (restated).** This module defines what wall-clock time on the queried day is. It holds the
range type, which is the only arithmetic on times of day, and the **one** conversion from an instant
(`datetime`) to that day's wall clock. Decision 0003 recorded that "time model (multi-day, zones, 24:00
close) → `time_range.py`", and the date and instant brought by notice land exactly there (H3).

```python
@dataclass(frozen=True, slots=True)
class TimeRange:
    start: time
    end: time
    # UNCHANGED: __post_init__, if_nonempty, intersection, overlaps, __str__

    # REMOVED: leading(length). Its one consumer is replaced by fitting_starts (see below).

    def extended(self, by: timedelta) -> "TimeRange":
        """B1 + M1: this range followed by `by` more, cut at the end of the day.
        Total. by <= 0 → self. Otherwise [start, min(end + by, time.max)).
        The room left before time.max is compared with `by` BEFORE any addition, so
        timedelta.max cannot overflow (S15)."""

    def trimmed(self, by: timedelta) -> "TimeRange | None":
        """This range with its last `by` removed: [start, end - by).
        Total. by <= 0 → self; by >= length → None (nothing is left).
        The comparison is made before the subtraction, so timedelta.max gives None."""

    def fitting_starts(self, length: timedelta, *, step: timedelta, origin: time) -> Iterator[time]:
        """Every lattice point t = origin + k·step (k any integer) such that [t, t + length) lies
        inside self, in ascending order.
        Total. length <= 0 or step <= 0 → yields nothing (it cannot hang).
        `origin` may lie before self.start (the first point is the lattice's ceiling at start).
        R2: a start may end exactly at self.end (`length <= end - t`).
        Overflow-safe: every addition is guarded by a comparison against the room left.
        Each call returns a fresh iterator."""
```

This is illustrative, to pin down the only arithmetic that is new:

```python
    def fitting_starts(self, length, *, step, origin):
        if length <= timedelta(0) or step <= timedelta(0):
            return
        start, end = _offset(self.start), _offset(self.end)
        skip = (_offset(origin) - start) % step          # distance to the first point at or after start
        if skip >= end - start:
            return
        at = start + skip
        while length <= end - at:
            yield _at(at)
            if step >= end - at:
                return
            at += step
```

With `step = length` and `origin = self.start`, `skip` is 0 and the loop is exactly stage-1 tiling. This is
how step 0 (§6) preserves behaviour.

```python
@dataclass(frozen=True, slots=True)
class AsOf:
    """The calendar day being asked about, and the local instant it is asked at (N1, N2).
    Invariant: now.tzinfo is None."""
    day: date
    now: datetime

    def __post_init__(self) -> None:
        """Raises InvalidAvailabilityRequest when `now` carries tzinfo (V1):
        "now must be a naive local date-time (no tzinfo), got 2026-09-23 08:00:00+02:00"."""

    def cutoff(self, lead: timedelta) -> time | None:
        """N1, the one owner: the earliest wall-clock time on `day` that is at least `lead` after `now`.
          · time.min  if now + lead is at or before the start of `day` (no effect)
          · None      if now + lead is after the end of `day` (no start can qualify)
          · otherwise (now + lead).time()
        Never computes now + lead until both day bounds have been compared as
        `lead` vs (bound - now). datetime - datetime cannot overflow, so notice=timedelta.max
        is safe (S15)."""
```

This is illustrative, to show the one conversion:

```python
    def cutoff(self, lead):
        if lead <= datetime.combine(self.day, time.min) - self.now:
            return time.min
        if lead > datetime.combine(self.day, time.max) - self.now:
            return None
        return (self.now + lead).time()
```

The private helper `_require_wall_clock` is split into `_require_time_type` and `_require_naive`.
`AsOf.__post_init__` reuses `_require_naive`, so there is one message shape for "no tzinfo". This happens
inside the module, and no private name crosses a module line.

**Public surface of `TimeRange`.** It is now `{start, end, if_nonempty, intersection, overlaps, extended,
trimmed, fitting_starts}`. `leading` is removed. The DESIGN §3.2 argument still applies to each new member:
it is the type's own behaviour (feature envy otherwise), it is **total**, and it is fixed by decided rules
(B1, M1, B2, R2, G1). Nothing is built, so removing `leading` breaks no caller. P2 pins the new set.

### 3.3 `_day.py`: `DaySchedule`, the day's occupancy (changed)

**Responsibility (restated).** This class turns the caller's bookings plus the resource's buffer into the
day's busy time (R3, R4, B1, B3, M1). It then answers one question: **where can a new booking lie** (B2)?

```python
class DaySchedule:
    """One resource's day: working hours, the buffer, and the occupancy inside the hours.

    Invariant (established in __init__, the one construction path; never changed):
      I1  every r in _busy lies inside _hours
      I2' along _busy, starts are non-decreasing AND ends are non-decreasing
      I4  every member is a valid, non-empty TimeRange
      (stage-1 I2 "strictly ascending" and I3 "pairwise disjoint" are DROPPED: under B3,
       occupancy runs may overlap or share a start. They are busy time, not bookings.)
    """
    __slots__ = ("_hours", "_busy", "_buffer")

    def __init__(self, hours: TimeRange, bookings: Iterable[TimeRange], buffer: timedelta) -> None:
        """Steps, in this order:
          1. ordered = sorted(bookings, key=(start, end))                      # R4 (unchanged)
          2. first adjacent overlapping pair → OverlappingBookingsError         # R4/A1/B3: on RAW
          3. _busy = tuple(o for b in ordered                                   # B1, M1, then R3
                           if (o := b.extended(buffer).intersection(hours)) is not None)
        Pre: buffer is not re-checked (ResourceRules owns V1); extended/trimmed are total anyway."""

    def bookable_spans(self) -> Iterator[TimeRange]:
        """B2, the one owner. Each maximal free gap inside the hours, shortened by the new
        booking's own buffer when occupancy closes it. The tail gap that runs to closing is not
        shortened, because the new booking's buffer may run past closing.
        Algorithm (the stage-1 cursor walk, with one added call):
          cursor = _hours.start
          for run in _busy:
              gap = TimeRange.if_nonempty(cursor, run.start)       # None if run.start <= cursor
              if gap is not None and (span := gap.trimmed(_buffer)) is not None: yield span
              cursor = run.end                                     # never moves back (I2')
          tail = TimeRange.if_nonempty(cursor, _hours.end); yield it when not None
        Post: spans are non-empty, strictly ascending, and disjoint, and
          [t, t+d) ⊆ some span  ⇔  [t, t+d) ⊆ hours  and  [t, t+d+buffer) misses all occupancy."""
```

**Why I2' holds (the H1(a) answer: no merge step is needed).** The raw bookings are sorted by start and,
after step 2, are pairwise disjoint. So `bᵢ.end ≤ bᵢ₊₁.start < bᵢ₊₁.end`, and the raw ends strictly
increase. Extending every booking by the **same** buffer and capping at `time.max` is a non-decreasing map.
Clipping to the hours (`max(start, H.start)`, `min(end, H.end)`) is non-decreasing too. Dropping the `None`s
leaves a subsequence. So both starts and ends of `_busy` are non-decreasing.

**Why the unchanged walk is still exact under overlap.** `cursor` is always the largest end seen so far,
because the ends are non-decreasing. A run that starts at or before `cursor` gives `if_nonempty → None`, so
there is no negative gap and no duplicate gap. A run that starts after `cursor` begins the earliest
remaining busy time, because the starts are non-decreasing. So each yielded gap is exactly a maximal free
range. S6 is the concrete case.

**Why B2 is exact (the H1(b) answer).** Let `[t, t+d) ⊆ hours` and let G be the maximal free gap that
contains it. If G ends at closing, `[t+d, t+d+b)` meets only free time or lies past closing, where
occupancy is ignored (R3), so the slot fits iff `[t, t+d) ⊆ G`. If G ends at a run's start `r`,
`[t, t+d+b)` misses that run iff `t+d+b ≤ r`, which holds iff `[t, t+d) ⊆ G.trimmed(b)`. Nothing else can
be hit, because G is free. So the asymmetry ("the slot is inside the hours, and the slot plus its buffer
avoids occupancy") is absorbed in the one place that knows whether a gap is closed by occupancy or by
closing. No slot policy ever sees the buffer.

### 3.4 `rules.py`: `ResourceRules` (new, published)

```python
@dataclass(frozen=True, slots=True)
class ResourceRules:
    """One resource's booking rules. The defaults are the stage-1 behaviour."""
    buffer: timedelta = timedelta(0)            # B1: cleanup after every booking
    notice: timedelta = timedelta(0)            # N1: minimum lead time before a start
    granularity: timedelta | None = None        # G1: None → gap-aligned stepping (R1)

    def __post_init__(self) -> None:
        """V1, the one owner for settings. Raises InvalidAvailabilityRequest, in field order:
          buffer < 0          "buffer must not be negative, got -1 day, 23:45:00"
          notice < 0          "minimum notice must not be negative, got …"
          granularity <= 0    "granularity must be positive when given, got 0:00:00" """

    def earliest_start(self, as_of: AsOf | None) -> time | None:
        """N2, the one owner: the earliest start this resource allows for the query.
          as_of given        → as_of.cutoff(self.notice)       (N1, may be None)
          no as_of, notice 0 → time.min                         (no filter: stage 1)
          no as_of, notice>0 → InvalidAvailabilityRequest(
              "a minimum notice of 2:00:00 needs as_of (the day and the current time)")"""
```

### 3.5 `slots.py`: the entry (changed)

```python
def available_starts(
    working_hours: TimeRange,
    bookings: Iterable[TimeRange],
    duration: timedelta,
    *,
    rules: ResourceRules = ResourceRules(),
    as_of: AsOf | None = None,
) -> list[time]:
    """Start times, earliest first, at which a new booking of `duration` fits inside
    `working_hours` with its own buffer clear of existing occupancy (B2). Starts are
    gap-aligned (R1) or on the granularity grid (G1), and no start comes before the notice
    cutoff (N1).
    Checked here, in this order (A12): duration > 0 (R5); notice needs as_of (N2);
    bookings do not overlap (R4, by building DaySchedule).
    Post: strictly ascending; [] when nothing fits or the cutoff is after the day.
    Default rules and no as_of → identical to stage 1 (S3)."""
    if duration <= timedelta(0):
        raise InvalidAvailabilityRequest(f"duration must be positive, got {duration}")
    earliest = rules.earliest_start(as_of)                          # N2 checked; N1 converted once
    day = DaySchedule(working_hours, bookings, rules.buffer)        # R4 checked; R3, B1, B3, M1
    if earliest is None:
        return []                                                   # the cutoff is after this day
    return [start
            for span in day.bookable_spans()                        # B2
            for start in _aligned_starts(span, duration, rules.granularity, working_hours.start)
            if earliest <= start]                                   # N1: removes starts, moves no anchor
```

```python
def _aligned_starts(span: TimeRange, duration: timedelta,
                    granularity: timedelta | None, opens: time) -> Iterator[time]:
    """R1 and G1, the one owner of slot policy: the lattice that candidate starts in `span` lie on.
    The fit test is not here. It is TimeRange.fitting_starts, and the buffer is already in `span`."""
    if granularity is None:
        return span.fitting_starts(duration, step=duration, origin=span.start)   # R1
    return span.fitting_starts(duration, step=granularity, origin=opens)         # G1, 0004 §8
```

**Earliest first still holds without a sort.** The spans are ascending and disjoint. Within each span the
lattice points are ascending and all fall before `span.end`, which is at or before the next span's start.
A filter keeps order.

### 3.6 `__init__.py`

```python
__all__ = ["TimeRange", "AsOf", "ResourceRules", "available_starts",
           "InvalidAvailabilityRequest", "OverlappingBookingsError"]
```

**Effect on stage-1 callers (H4): none.** A positional three-argument call keeps its meaning. The new
parameters are keyword-only, so they cannot be mispositioned, and their defaults are stage 1. No internal
type (`DaySchedule`, the lattice) appears in any public signature. The illustrative stage-2 call:

```python
available_starts(TimeRange(time(9), time(17)), bookings, timedelta(minutes=30),
                 rules=ResourceRules(buffer=timedelta(minutes=15), notice=timedelta(hours=2),
                                     granularity=timedelta(minutes=15)),
                 as_of=AsOf(date(2026, 9, 24), datetime(2026, 9, 23, 18, 0)))
```

---

## 4. Rule → owner

| Rule | Single owner | Every path goes through it because |
|---|---|---|
| R1 gap-aligned, back-to-back, leftover dropped | `slots._aligned_starts` (policy, `granularity is None` branch). The mechanics are in `TimeRange.fitting_starts` | the one composition line calls it for every span. **Owner kept**: the helper was renamed and gained a sibling branch, which is exactly the "slot policy → the R1 helper only" axis that 0003 recorded |
| R2 touching ≠ overlap | `time_range._nonempty` | unchanged |
| R2 a slot may end exactly at the end | `TimeRange.fitting_starts` (`length <= end − at`) | the only fit test. **Moved** from `leading`, in the same file and on the same type. `leading` is removed (§8) |
| R3 only the part inside the hours counts | `DaySchedule.__init__` step 3 (`.intersection(hours)`) | unchanged. It now clips *occupancy*, so a buffer past closing is ignored too (B2, S9) |
| R4 sort; overlap rejected naming the pair | `DaySchedule.__init__` steps 1–2 | unchanged, still on raw bookings |
| R5 range / duration / `[]` | `TimeRange.__post_init__` / first statement of `available_starts` / structural | unchanged |
| R6 naive, one day | `TimeRange` (`time` fields, `_require_*`) + `AsOf` (the only place an instant enters) | the time model is still one file |
| **B1** buffer is busy time, counted wherever it lies in the hours (including from before opening) | `DaySchedule.__init__` step 3: `extended(buffer)` *before* clipping | order of step 3: extend, then clip |
| **B2** new slot inside the hours; slot + buffer misses occupancy; may run past closing | `DaySchedule.bookable_spans` (`trimmed(buffer)` on gaps closed by occupancy, not on the tail) | policies see only spans; no other code knows the buffer |
| **B3** buffer-violating bookings accepted; true overlaps rejected | `DaySchedule.__init__`: the overlap check runs on raw bookings (step 2) and never on occupancy; I2' replaces I3 | occupancy is never checked for overlap |
| **G1** grid from hours start, every fitting point; no grid → R1 | `slots._aligned_starts` (policy) + `fitting_starts` (enumeration + fit) | one call site |
| **N1** `combine(day, t) >= now + notice`; cross-day; removes starts only | `AsOf.cutoff` (conversion, inclusive bound, cross-day) + the one filter `earliest <= start` in `available_starts` | the filter is the last clause of the one composition. The anchors come from `span`/`opens`, which notice never touches |
| **N2** `now` optional; notice > 0 without `now` → error; `now` + notice 0 → no past starts | `ResourceRules.earliest_start` | the entry's only path to a cutoff |
| **V1** negative buffer / notice; granularity ≤ 0 | `ResourceRules.__post_init__` | one construction path (frozen) |
| **V1** tz-aware `now` | `AsOf.__post_init__` | one construction path (frozen) |
| **V1** notice > 0 without `now` | `ResourceRules.earliest_start` | = N2 |
| **M1** buffer past midnight is cut, never overflows | `TimeRange.extended` | the only place an end grows |
| earliest first | composition of the postconditions of `bookable_spans` and `fitting_starts` | there is no sort to forget |

---

## 5. Error vocabulary delta

No new types. New `InvalidAvailabilityRequest` situations:

| Situation | Raised by | Message (example) |
|---|---|---|
| negative buffer | `ResourceRules(...)`, caller side | `buffer must not be negative, got -1 day, 23:45:00` |
| negative notice | `ResourceRules(...)` | `minimum notice must not be negative, got -1 day, 23:00:00` |
| granularity 0 or negative | `ResourceRules(...)` | `granularity must be positive when given, got 0:00:00` |
| tz-aware `now` | `AsOf(...)` | `now must be a naive local date-time (no tzinfo), got 2026-09-23 08:00:00+02:00` |
| notice > 0 without `as_of` | `available_starts` → `ResourceRules.earliest_start` | `a minimum notice of 2:00:00 needs as_of (the day and the current time)` |
| cutoff after the day | not an error: `[]` | — |
| wrong type in `ResourceRules`/`AsOf` | stdlib, in `__post_init__` | unwrapped `TypeError`/`AttributeError` (A11) |

---

## 6. Order of work (make the change easy, then make the easy change)

Each step keeps every characterization test green.

0. **Refactor (behaviour-preserving).** Add `TimeRange.fitting_starts` and remove `leading`. Turn
   `_gap_aligned_starts` into `_aligned_starts` with only the R1 branch (`step=duration,
   origin=span.start`). Migrate T8 to `fitting_starts`. A1–A21 and the invariant test stay unchanged and
   green.
1. **Buffer.** Add `extended` and `trimmed`; `DaySchedule(…, buffer)`; rename `free_gaps` →
   `bookable_spans`; restate I2'. Add `ResourceRules(buffer)`, `rules=` and `rules.py`.
2. **Granularity.** Add the `ResourceRules.granularity` field and V1 check, and the G1 branch in
   `_aligned_starts`.
3. **Notice.** Add `AsOf`, `ResourceRules.notice`, `earliest_start`, `as_of=` and the entry filter.

---

## 7. Trace

Hours are 09:00–17:00 and d = 30 min unless stated. "occ" means occupancy after extend and clip. "sp" means
the bookable spans.

| Case | Path | Result |
|---|---|---|
| S1 | occ `[09:00,10:00) [11:00,12:15)`. Walk: gap(09:00,09:00) None; gap `[10:00,11:00)` trimmed(15) → `[10:00,10:45)`; tail `[12:15,17:00)`. Grid (15, 09:00). Span 1: skip 0 → 10:00 (10:30 ≤ 10:45), 10:15 (10:45 ≤ 10:45), 10:30 fails. Tail: skip = (09:00−12:15) % 15 = 0 → 12:15 … 16:30, 18 starts. earliest = time.min | `10:00, 10:15, 12:15 … 16:30` ✓ |
| S2 | same sp. R1 lattice (30, span.start): span 1 gives 10:00 (10:30 then fails at 11:00 > 10:45); tail gives 12:15, 12:45 … 16:15 (16:45 + 30 > 17:00) | ✓ |
| S3 | buffer 0: `extended(0)` = self and `trimmed(0)` = self, so occ = stage-1 `_busy` and sp = stage-1 free gaps. `earliest_start(None)` = time.min, so the filter keeps everything. `fitting_starts(d, step=d, origin=span.start)` has skip 0 and is exactly the stage-1 `leading` loop. C1–C14 take the DESIGN §7 paths with `leading(d)` read as "the next lattice point fits". The errors are the same types, order and messages | bit-for-bit ✓ |
| S4 | no occ; tail = hours untrimmed; grid gives the last point 16:30 (17:00 ≤ 17:00) | 16:30 ✓ |
| S5 | 08:00–09:00+15 → occ `[09:00,09:15)`; tail `[09:15,17:00)` → 09:15 in both modes. 08:00–08:50+15 → occ `[09:00,09:05)`; tail `[09:05,…)`: grid skip = (09:00−09:05) % 15 = 10 → **09:15**; R1 → **09:05**. 07:00–08:00+15 → `[07:00,08:15)` ∩ H = None, dropped | ✓ |
| S6 | 10–11 and 11–12 touch, so step 2 accepts them (B3). occ `[10:00,11:15) [11:00,12:15)`: starts and ends are non-decreasing (I2'). Walk: `[09:00,10:00)` trimmed → `[09:00,09:45)`; cursor 11:15; gap(11:15, 11:00) = None; cursor 12:15 (forward); tail `[12:15,17:00)`. Starts: 09:00, then 12:15 …. Nothing is offered in `[10:00,12:15)` (09:30 is dropped because its buffer reaches 10:15). Buffer 60 with 10:00–10:30 and 10:45–11:00: occ `[10:00,11:30) [10:45,12:00)`; `[09:00,10:00)` trimmed(60) = None; gap(11:30,10:45) = None; cursor 11:30 → 12:00; tail from 12:00 | no negative or duplicate gap; the cursor only moves forward ✓ |
| S7 | step 2 runs on raw bookings before step 3 | `OverlappingBookingsError(raw pair)` ✓; touching is accepted (S6) |
| S8 | the gap before the booking at 11:00 is `[10:00,11:00)` → trimmed `[10:00,10:45)`. d = 45: 10:45 ≤ 10:45, so 10:00 is offered. d = 60: 11:00 > 10:45, so it is not | ✓ |
| S9 | 17:00–18:00+15 → `[17:00,18:15)` ∩ H = if_nonempty(17:00,17:00) = None; the tail stays untrimmed | 16:30 ✓ |
| S10 | g = 20: 09:00, 09:20 … 16:20 (16:40 + 30 > 17:00). g = 10 h: skip 0 → 09:00; step ≥ room → stop. C1 with buffer 0, g = 15: span `[09:45,11:00)` skip 0 → 09:45, 10:00, 10:15, 10:30 (11:00 ≤ 11:00). Hours 09:10–17:00: origin = `opens` = 09:10 | ✓ |
| S11 | now = day 08:00, notice 2 h: cutoff → 10:00. 09:45 < 10:00 is filtered and 10:00 is kept. 90 min → cutoff 09:30. C1, now = 09:50, notice 0: span `[09:45,11:00)` gives 09:45 and 10:15; the filter drops 09:45. The anchor is still 09:45 | `10:15` first ✓ |
| S12 | previous day 20:00 + 48 h is later than day@time.max, so cutoff = None → `[]` (after the overlap check). Previous day 16:00 + 16 h = day 08:00 → 08:00 → no effect. `now` on the next day → None → `[]`. Day 16:40, notice 0 → 16:40 → every start ≤ 16:30 is filtered | ✓ |
| S13 | `ResourceRules(notice=2h)` without `as_of` → `earliest_start` raises. Aware `now` → `AsOf` raises. Negative buffer, negative notice, g = 0, g < 0 → `ResourceRules` raises in field order. Precedence is A12 | ✓ |
| S14 | `as_of` given, notice 0 → cutoff = now's time (when now is on the day). `earliest <= start` keeps a start that equals now | ✓ |
| S15 | d = max: `length <= end − at` is false → nothing. buffer = max: `extended` caps at time.max, `trimmed` → None, and only the untrimmed tail can remain. notice = max: `cutoff` compares `lead > day@max − now` without adding → None. A booking ending at 23:50 with buffer 30 → `[s, time.max)`. g = max: at most one point, and `%` works on microsecond integers. Every loop has step > 0 | no OverflowError, no hang ✓ |
| S16 | `sorted` on raw `(start, end)`; occ, sp and output depend only on that order, including S6's input | identical ✓ |

**Further crossings (a new rule against each existing rule).**
- Buffer × R3 at close: a booking 16:50–17:30 gives occ `[16:50,17:00)`. The gap before it is trimmed,
  because it is real occupancy inside the hours.
- Buffer × A1/A2: duplicates and overlaps outside the hours are still rejected on raw bookings.
- Notice × R4: the day is past but the bookings overlap → error, because `DaySchedule` is built before the
  guard.
- Grid × opening edge: S5. Grid × notice: S11. The filter never moves the grid.
- Hours ending at `time.max`: the tail is untrimmed, so a slot may end at `time.max` (A3 unchanged).
- Sub-minute buffer, notice or granularity: integer `timedelta` arithmetic, no rounding.

---

## 8. Design reasoning

### H1: the buffer

The buffer has **one owner, `DaySchedule`**. The existing-booking side is `extended` before clipping, in
`__init__`. The new-slot side is `trimmed` on gaps that occupancy closes, in `bookable_spans`. The
asymmetry at closing lives exactly where the code already knows whether a gap ended at a run or at closing.
Stage-1 invariant I3 (disjoint) is **replaced**, not patched. I2' (starts and ends both non-decreasing)
follows from R4 plus the uniform buffer, and it is all the unchanged cursor walk needs. So the stage-1
algorithm survives line for line, and `trimmed` is the one added call.

Rejected alternatives:
- **A trailing filter over starts.** This would make a second owner of occupancy. It is also *wrong* for
  R1: gaps would begin at the booking's end rather than after its buffer (S2 would offer 09:45).
- **The buffer as a synthetic booking.** This is the concept cram that 0004 forbids. It would also trip the
  R4 check on S6 and wrongly reject B3 input.
- **Padding occupancy backwards by the buffer (`[s − b, e + b)`) for B2.** It is value-correct but models
  the new booking's buffer as fake busy time before existing bookings, which are a non-goal. That busy time
  is an inert stand-in.
- **A footprint length `d + b` in the fit test.** This would put buffer knowledge in `slots` (a second
  owner). `d + b` overflows for `timedelta.max`. And at the tail it wrongly rejects a slot whose own buffer
  runs past midnight (M1).
- **Merging overlapping occupancy (`TimeRange.joined` plus a fold).** It would restore stage-1 I3 verbatim,
  but it costs a public method and a loop that I2' makes unnecessary. **Falsifier:** per-booking buffers
  (a non-goal) would break the monotone ends. Then the merge becomes necessary, and it lands in
  `DaySchedule.__init__` only.
- **A `max()` cursor.** Unnecessary for the same reason.

### H2: slot policy

The two policies are **the same kind of thing**: a lattice of candidate starts, with every point that fits
kept. Gap-aligned is (origin = the gap's start, step = duration). With step = duration, "every point that
fits" *is* back-to-back tiling with the leftover dropped. Grid is (origin = opening, step = g). So there is
**one** enumeration-and-fit mechanism, `TimeRange.fitting_starts`, which replaces `leading`, and **one**
policy owner, `_aligned_starts`, a two-branch choice of lattice. The fit rule cannot be re-implemented per
policy, because neither branch contains a comparison, and the buffer is already inside the span.

Rejected alternatives:
- **A `SlotPolicy` Protocol or Strategy with two classes.** Its implementations would differ only in two
  parameters, which is a pattern with no force behind it (design-principles §9).
- **A grid as a filter over whole-day grid points, matched against spans.** That is a second fit test.
- **Keeping `leading` alongside.** It would be dead, with no consumer (subtractive pass).

### H3: the time model

`AsOf` is the **only** place a `date` or `datetime` enters. `AsOf.cutoff(lead)` converts `now + lead` once
into a `time` on `day`, or into `time.min` (no effect) or `None` (nothing qualifies). The core
(`DaySchedule`, spans, lattice) still sees only times of one day. It lives in `time_range.py`, because
decision 0003 already routes time-model changes there. It is overflow-safe because it compares `lead` with
`bound − now` and adds only once the sum is known to land on the day.

Rejected alternatives:
- **A `datetime` core.** Rejected in stage 1 (R6), and the cost of reopening it is every module.
- **Notice as occupancy `[opening, cutoff)`.** It would move gap anchors (S11 would give 09:50). That is a
  cram of a filter rule as busy time.
- **Intersecting each span with a "start window" range.** It is correct, but it needs a whole-day sentinel
  range and a policy helper with five parameters. The single filter has fewer parts, and by 0004 notice *is*
  a removal of starts, so the filter is concept-fit and is the rule's one home. It is not the "trailing
  filter" smell, which is about a rule that already has an owner elsewhere.

### H4: the public seam

There are two published values and keyword-only defaults.
- **`ResourceRules`** replaces a long list of primitive parameters (three settings that travel together per
  resource). It is a value that validates itself, which matches the `TimeRange` grain.
- **`AsOf`** makes "a day without a now" unrepresentable. It is the data clump `(day, now)` made into a
  type.

The cross-object rule N2 is owned by `ResourceRules.earliest_start` (tell the rules what you know, and they
answer). Stage-1 callers are unaffected (P6). V1 has three owners, one per fact: settings, the instant, and
the combination of the two.

Rejected alternatives:
- **Loose `day=`, `now=`, `buffer=`, `notice=`, `granularity=` keywords.** A long parameter list, and
  `day` without `now` would be representable.
- **One `AvailabilityQuery` object holding everything.** It would bundle per-request, per-resource and
  per-day data that change at different rates.
- **A `Resource` type holding hours and rules.** Hours are per day and rules are per resource.
- **`Buffer`, `Notice` or `Granularity` value types.** Each has one rule, and it already has one owner
  (`ResourceRules`). The falsifier: a second operation accepting one of them.
- **New error subtypes.** No caller would handle them differently.

### 8.1 Subtractive pass (only what was added or changed)

| Element | Present force | Verdict |
|---|---|---|
| `ResourceRules` | three per-resource settings; V1; N2 | keep |
| `ResourceRules.earliest_start` | N2 needs both the notice and `as_of`; its alternative is a branch in the entry | keep |
| `AsOf` | `day` and `now` travel together; the one instant → wall-clock conversion; tz V1 | keep |
| `AsOf.cutoff` | N1 inclusivity, cross-day, overflow safety | keep |
| `TimeRange.extended` | B1, M1 | keep |
| `TimeRange.trimmed` | B2 | keep. A single signed "move the end" method was rejected: it hides the direction at the call site, and the two operations have different totality (one never empties, the other may) |
| `TimeRange.fitting_starts` | the one fit and enumeration for both policies; R2 end-inclusive | keep |
| `TimeRange.leading` | no consumer after step 0 | **cut** |
| `DaySchedule._buffer` | B2 in `bookable_spans` | keep |
| rename `free_gaps` → `bookable_spans` | the yielded ranges are no longer free gaps (they are trimmed) | keep; an honest name |
| I3 | false under B3 | **cut**, replaced by I2' |
| `joined` / merge fold, `max` cursor | made unnecessary by I2' | **cut** (never added) |
| `_aligned_starts` (four parameters) | R1/G1 policy. A parameter object would be a one-use class | keep |
| `if earliest is None: return []` | the cutoff is after the day; keeps the overlap check first | keep |
| `*` keyword-only marker | stage-1 positional calls are safe; the new arguments cannot be mispositioned | keep |
| a whole-day `TimeRange` sentinel | only needed by the rejected intersection design | **cut** (never added) |
| `_require_naive` split | avoids duplicating the tz message in `AsOf` | keep |

### 8.2 Concept-fit pass

- **Buffer.** It is a resource setting (`timedelta`), and its effect is occupancy in `_busy`. It is never a
  `TimeRange` posing as a booking, and never checked by R4.
- **Occupancy.** It is busy time from a booking plus its buffer. It may overlap, because it is not a
  booking, so it has no disjointness invariant.
- **The new booking's own buffer.** It is a shortening of the room before occupancy. It is not fake busy
  time before existing bookings.
- **Grid.** It is a lattice (origin, step), not a type. R1 is the same kind of lattice with different
  parameters. It is not a filter over a day-wide grid.
- **Notice cutoff.** It is a wall-clock bound that *removes* starts (a filter). It is not occupancy and not
  a score. `time.min` means "no bound", and it is the honest earliest instant, not an inert stand-in.
- **Query context `AsOf`.** It is a value: the day being asked about, and when it is asked.
- **Resource settings `ResourceRules`.** It is a value that validates itself, with stage-1 defaults.

No inert stand-ins remain.

### 8.3 Principles that do not apply

The DESIGN §8.4 list is unchanged: no I/O, no concurrency and no trust boundary. Add-feature §8 (migration
of a persisted shape) does not apply either: nothing is persisted or built, and the surface change (the
removal of `leading`) has no callers.

---

## 9. Test plan (delta against DESIGN.md §10, test-first)

**Characterization (kept unchanged).** A1–A21 are kept verbatim. They are S3, and they run first, green
before step 0 and after every step. T1–T7, T9 and T10 are kept verbatim. The stage-1 properties 1–7 in
`test_invariants.py` are kept verbatim for inputs with default rules.

**Changed, with the reason.**
- **T8** (`leading`) becomes **T8′** (`fitting_starts`), because the method is removed in step 0. It keeps
  every stage-1 meaning: exact fit, where the last start ends at `end`; 1 µs too long gives nothing;
  length 0 or negative gives nothing; length `timedelta.max` gives nothing and no OverflowError; seconds
  are preserved. It adds: step 0 or negative gives nothing (totality, no hang); `origin` before `start`
  gives the lattice ceiling (origin 09:00, step 15 over `[09:05,10:00)` → 09:15 …); `origin` after
  `start` (k < 0); step `timedelta.max` gives at most one point.
- **P1** now lists the six names. **P2** is the new `TimeRange` member set. **P3** allows `ResourceRules`,
  `AsOf`, `date` and `datetime` in the hints, and still no `_day` type.

**New unit tests at the published value seams.**

| # | Seam | Test | S |
|---|---|---|---|
| T11 | `extended` | 0 or negative → equal to self; +15; ending 23:50 +30 → end `time.max`; `timedelta.max` → no error | M1, S15 |
| T12 | `trimmed` | 0 or negative → self; by < length; by == length → None; `timedelta.max` → None | B2, S15 |
| T13 | `AsOf` | aware `now` → error; `cutoff`: same-day 08:00 + 2 h → 10:00; 90 min → 09:30; previous day 16:00 + 16 h → 08:00; previous day 20:00 + 48 h → None; `now` on the next day → None; previous day far back → `time.min`; exactly at day end → None; notice `timedelta.max` → None with no error; `now` = `datetime.max` | N1, S11, S12, S15 |
| R1 | `ResourceRules` (`test_rules.py`) | defaults are 0, 0 and None; negative buffer, negative notice, g = 0 and g < 0 each raise, with the field named in the message; two invalid fields → the first in field order is reported | V1, S13 |
| R2 | `earliest_start` | None with notice 0 → `time.min`; None with notice > 0 → error; `as_of` → delegates (notice 0 → now's time) | N2, S13, S14 |
| P6 | surface | `rules` and `as_of` are `KEYWORD_ONLY` with defaults `ResourceRules()` and `None`; a 3-argument positional call works | H4 |

**New product tests (`test_available_starts.py`, at `available_starts`).**

| # | Test | S |
|---|---|---|
| B1 | the anchor: exact list (buffer 15, g 15) | S1 |
| B2 | same without granularity: exact list | S2 |
| B3 | `rules=ResourceRules()`, `as_of=None` gives the same output as omitting both, over C1–C14 inputs | S3 |
| B4 | no bookings, buffer 15, g 15 → last start 16:30 | S4 |
| B5 | the three opening-edge bookings × {grid 15, no grid} | S5 |
| B6 | touching 10–11 and 11–12 with buffer 15 → accepted; exact list; nothing in `[10:00,12:15)`. The buffer-60 pair → exact list | S6 |
| B7 | true overlap with buffer 30 → `OverlappingBookingsError` with `.first`/`.second` = the raw pair | S7 |
| B8 | d = 45 / d = 60 with buffer 15: 10:00 offered / not offered | S8 |
| B9 | booking 17:00–18:00, buffer 15 → 16:30 present | S9 |
| B10 | g = 20; g = 10 h; C1 with g = 15 (09:45, 10:00, 10:15, 10:30 present); hours 09:10–17:00 with g = 15 | S10 |
| B11 | notice cases, including gap-aligned with now 09:50 → first start 10:15 | S11 |
| B12 | the four cross-day cases | S12 |
| B13 | the full precedence table (A12): each pair of simultaneous violations reports the earlier one; a past day with overlapping bookings → overlap error | S13 |
| B14 | `now` exactly on a gap start → that start is kept, an earlier one is dropped | S14 |
| B15 | d, buffer, notice and g each `timedelta.max`, plus 23:50 + 30 buffer with hours ending at `time.max` → no exception; results as traced | S15 |
| B16 | all permutations of the S6 input plus C1's bookings, with buffer 15 and g 15 → identical | S16 |
| B17 | booking straddling close (16:50–17:30) with buffer 15 → last start 16:05 (d = 30) | X×R |
| B18 | a buffer ending exactly at a later booking's start (a chain) → no zero-length span | B2 |
| B19 | `ResourceRules(buffer=15)` with `duration=0` → duration error (A12) | S13 |
| B20 | a small g gives every grid point (no stepping by d): d = 60, g = 15, no bookings → 29 starts | G1 |

**The seeded random test (`test_invariants.py`), extended.** Keep `random.Random(20260923)` and the stage-1
generator. Add a second generator of about 2 000 cases. Buffer is 0 (a quarter of cases), 1 min–90 min, or
occasionally `timedelta.max`. Granularity is None (half of cases) or 1 min–2 h. `as_of` is None (with
notice 0), or `now` uniform in ±2 days around the day with notice 0–10 h. Bookings are generated as in
stage 1, so they include touching chains, whose buffers overlap. The test computes every property with its
**own** `datetime.combine(date.min, t)` arithmetic. That arithmetic cuts at midnight naturally, independent
of the package's.

1. **Fits.** `H.start ≤ s` and `s + d ≤ H.end`.
2. **Buffer-free (B2).** `[s, s+d+b)` misses every `[sᵢ, eᵢ+b) ∩ H`.
3. **Notice (N1).** When `as_of` is given, `combine(day, s) ≥ now + notice` (oracle in `datetime`,
   skipped when the sum overflows, because then S must be `[]`).
4. **Order.** Strictly ascending.
5. **Aligned.** Grid: `(s − H.start) % g == 0`. No grid: `(s − p) % d == 0`, where p is the start of the
   maximal free gap (under occupancy) containing s.
6. **Complete.** Every lattice point satisfying 1–3 is in S. For the grid, the lattice is all of
   `H.start + k·g`. With no grid, it is `p + k·d` for every gap start p.
7. **Metamorphic C10.** A shuffle gives an identical S.
8. **Metamorphic R3 + B1.** Adding a booking that lies after `H.end`, or that ends at or before
   `H.start − b`, gives an identical S. (A booking whose buffer reaches into H is *expected* to change S.)
9. **Metamorphic N1.** A larger notice (same `now`) gives a suffix of S.
10. **Metamorphic, grid only.** A larger buffer gives a subset of S. (This is not claimed for R1, whose
    anchors legitimately move.)

The overlap generator is extended with buffer > 0: an injected true overlap still raises with the same pair
across shuffles. An input with only buffer-level conflicts never raises (B3).

There is no coverage percentage. Every row pins a decision.

---

## 10. Result, new facts and risks

**Result: met.**
- Each new rule has exactly one owner: buffer → `DaySchedule`; granularity → `_aligned_starts`; notice →
  `AsOf.cutoff` plus the one filter, with N2 on `ResourceRules`.
- Every stage-1 rule keeps its owner, except R2-end-inclusive, which moves from `leading` to
  `fitting_starts` on the same type. That move is recorded.
- Default settings give stage-1 output bit for bit.
- Every signature is concrete, stdlib-only Python 3.11.

**New facts and risks**
1. **I2' rests on a uniform buffer.** Per-booking buffers (a non-goal) would break the monotone ends. The
   fix is then an occupancy merge in `DaySchedule.__init__` only. This should be recorded in
   architecture.md as the falsifier.
2. **Output size.** A small granularity multiplies the starts (A13). There is still no cap, by decision.
3. **Surface change.** `TimeRange.leading` leaves the published surface and three total methods join it.
   This is harmless because nothing is built, but P2 must be updated deliberately.
4. **For the Guide's records (not written here, by the objective's rule):** architecture.md "Likely change
   axes" — the occupancy change landed in the `DaySchedule` *class* (`__init__` for B1 and
   `bookable_spans` for B2), not only in `__init__`. Slot policy landed in the R1 helper as predicted. The
   time model landed in `time_range.py` plus the entry signature as predicted. A decision 0005 (stage-2
   architecture) should record H1–H4 and the I2' falsifier.
5. **Open product question (minor).** A12 makes an overlapping-bookings error beat a notice cutoff that is
   after the day, so a past day is still validated. If the owner prefers "a past day → `[]` without
   validation", only the statement order in `available_starts` changes. The change stays in one owner.
