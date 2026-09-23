# Booking availability — stage 2: architecture

A stage-2 architecture for a "bookable slots" service, in Python 3.11 with the standard library only. It is
written for the person who will build it and stands on its own. It **changes** the agreed stage-1 design
(nothing was built yet); every part of stage 1 that still holds is restated here, so no other file is needed.

---

## 0. The problem, in one paragraph

For one resource on one day we are given its working hours (one window), that day's existing bookings, a
requested duration, the resource's **rules** — a cleanup **buffer** after every booking, a **minimum notice**,
and an optional start-time **granularity** — and optionally **when** the question is asked (the calendar day
and a naive local "now"). We return every start time, earliest first, at which a new booking of that
duration lies inside working hours and, together with its own buffer, clear of existing occupancy (bookings
plus their buffers); aligned to the granularity grid, or laid back-to-back from the start of each free gap
when the resource has no granularity; and not earlier than now + notice.

---

## 1. Rules and assumptions

### 1.1 Decided product rules

Stage 1 (decisions/0002), unchanged unless marked:

- **R1 Gap-aligned stepping** — *now the no-granularity case only (decisions/0004 §7).* Within each place a
  new booking may lie, slots start at its start and step by the duration; a leftover shorter than the
  duration is not offered.
- **R2 Half-open intervals `[start, end)`.** Touching is not overlapping. A slot may end exactly at close.
- **R3 Only what lies inside working hours matters** — *now applied to occupancy (booking + buffer).*
- **R4 Bookings may arrive unsorted; the service sorts.** Overlapping bookings are rejected naming the pair,
  checked on the **raw** bookings. Touching bookings are fine.
- **R5 Clear errors:** a range with `end <= start`; duration `<= 0`. Nothing fits → `[]`, not an error.
- **R6 Time model:** naive wall-clock times within one local day; no zones, no DST; working hours do not
  cross midnight.

Stage 2 (decisions/0004):

- **B1 Buffer is occupancy.** Existing booking `[s, e)` occupies `[s, e + buffer)`. The buffer counts
  wherever it lies inside working hours — including a buffer from a booking that ended before opening. It is
  never returned and is never a booking.
- **B2 The new slot needs its own buffer.** `[t, t + d)` must lie inside working hours;
  `[t, t + d + buffer)` must not overlap in-hours occupancy. Its buffer may run to or past closing.
- **B3 Buffer-violating existing bookings are accepted.** Only true booking overlaps are rejected (R4).
- **G1 Granularity (optional).** With granularity `g`, candidates are `hours.start + k·g`, and **every**
  candidate that fits (B2) is offered. Without granularity, R1.
- **N1 Minimum notice.** With `now` and `day` supplied, start `t` is offered iff
  `datetime.combine(day, t) >= now + notice` (exactly at the cutoff is offered). Notice removes starts; it
  never moves the grid or the gap anchors.
- **N2 `now` is optional.** Without it there is no notice filter — but a resource whose notice is > 0 with
  no `now` is a caller error. With `now` and notice 0, starts before `now` are dropped.
- **V1 Validation.** Rejected: negative buffer, negative notice, granularity `<= 0`, tz-aware `now`, notice
  > 0 without `now`. Default rules without `now` behave exactly as stage 1.
- **M1** A buffer that would run past midnight is cut at the end of the day; nothing overflows.

### 1.2 Stated assumptions

Each answers a question the rules leave open; "lands in" names the single place that would change.

| # | Assumption | Why | Lands in |
|---|---|---|---|
| A1 | Overlapping bookings are rejected even when both lie wholly outside working hours (R4 runs on raw bookings, before buffers and clipping). | A calendar bug is a bug wherever it sits. Running R4 first is also what makes B3 hold: buffers never reach the check. | `DaySchedule.__init__` step order |
| A2 | Identical duplicate bookings are rejected as an overlapping pair. | They share every instant; deduplicating would be the merge 0002 rules out. | `DaySchedule.__init__` |
| A3 | Working hours cannot end at 24:00; the latest end is `time.max`. | `datetime.time` has no 24:00; R6 forbids crossing midnight. | `time_range.py` (`whole_day`) |
| A4 | Tz-aware `time` values are rejected. | "No zones" read as fail fast, not compare-by-offset. | `TimeRange.__post_init__` |
| A5 | No output cap and no minimum granularity/duration. g = 1 µs or d = 1 µs over 8 h returns ≈2.9·10¹⁰ starts. With a grid the work is proportional to the output; without one, and under a late notice cutoff, removed candidates are still enumerated. | Nobody asked for a cap (0004 lists it as a non-goal). | `available_starts`, beside the duration check |
| A6 | **Validation precedence** (deterministic, cheapest first). (1) Caller-side construction, in the caller's expression order: `TimeRange` type → tz → emptiness; `ResourceRules` buffer → notice → granularity; `AsOf` day type → `now` tz. (2) Inside `available_starts`: duration ≤ 0; then notice > 0 without `as_of`; then overlapping bookings (first adjacent pair in `(start, end)` order). (3) Only then may a cutoff after the day return `[]`. | An invalid request is rejected even when nothing would be offered (stage-1 C12 stance); an overlapping calendar is reported even for a past day. | statement order of `available_starts`; field order of the value types |
| A7 | Type guards only where a wrong type would be *silently accepted*: `TimeRange` guards `start`/`end` (a `datetime` would compare and build a cross-midnight range); `AsOf` guards `day` (A10). Everything else fails loudly with the stdlib `TypeError`/`AttributeError`, unwrapped. | A guard is only worth it where the failure would otherwise be silent. | the named `__post_init__`s |
| A8 | An invalid-range error does not say whether it was the hours or a booking. | It is raised in the caller's own `TimeRange(...)` expression; the traceback locates it. | a future parse point |
| A9 | Output is `time` objects; rendering is the caller's job. | Caller is an in-process UI or service. | — |
| A10 | `AsOf(day=<datetime>)` raises `TypeError`. `datetime` subclasses `date`, and `datetime.combine` would silently take its date part. A `date` passed as `now` fails loudly (no `.tzinfo`), so it needs no guard. | A7 applied: the one silent acceptance gets the guard. | `AsOf.__post_init__` |
| A11 | "End of day" is `time.max` (exclusive) — for the M1 cut and for the notice window. The last microsecond before midnight is not representable; this is unobservable because hours end at or before `time.max`. | A3's reading, applied again. | `TimeRange.whole_day` |
| A12 | With `as_of` supplied, a query about a day already past returns `[]` (every start is before `now`). A what-if query about any day omits `as_of`. | The literal N1/N2 rule. | `AsOf.eligible_starts` |
| A13 | The caller is responsible for `as_of.day` being the day the hours and bookings describe. | The core has no dates (R6); checking would need dates on ranges. | caller contract (docstring) |
| A14 | Offered starts may overlap each other's buffers (S2 offers 12:15 and 12:45 with a 15-min buffer). They are alternatives for **one** new booking, not a batch. | 0004 defines fit against existing occupancy only. A caller booking several at once must re-query. | — |

---

## 2. Module tree and dependency direction

```
availability/
  __init__.py      # published: __all__ = ["TimeRange", "ResourceRules", "AsOf", "available_starts",
                   #                       "InvalidAvailabilityRequest", "OverlappingBookingsError"]
  errors.py        # error vocabulary (published) — unchanged types
  time_range.py    # TimeRange (published): half-open wall-clock range; the ONLY time-of-day arithmetic
  rules.py         # NEW  ResourceRules (published): per-resource buffer / notice / granularity; V1 fields
  as_of.py         # NEW  AsOf (published): day + naive now; the ONLY date/instant arithmetic (N1 conversion)
  _day.py          # DaySchedule (package-private): occupancy (R3, R4, B1, B3, M1); bookable spans (B2)
  slots.py         # available_starts (published entry): R5-duration, N2, composition;
                   #   _aligned_starts (R1 + G1), _eligible_starts (N2) — module-private
tests/
  test_time_range.py  test_rules.py  test_available_starts.py  test_invariants.py  test_public_surface.py
```

```
slots ──► _day ──► time_range ──► errors
  │ ├──► as_of ───────┘  ▲          ▲
  │ └──► rules ──────────┼──────────┘
  └──────────────────────┴──────────┘
```

- `errors` has no runtime imports from the package (annotations under `TYPE_CHECKING`).
- `rules` imports only `errors`: it holds `timedelta`s and does no time arithmetic.
- `as_of` imports `time_range` (it returns a `TimeRange`) and `errors`.
- `_day` imports `time_range` and `errors` — **not** `rules`: it receives the buffer as a `timedelta`, the
  one setting occupancy needs.
- `slots` imports all of the above and is the only importer of `_day`.
- No module imports an underscore-prefixed name from another module.
- Stdlib only: `dataclasses`, `datetime`, `itertools.pairwise`, `collections.abc`, `typing`. Tests:
  `unittest`, `random`, `inspect`, `itertools`. No pyproject, no pytest.

**Public entry point:** the local library function `availability.available_starts`. No CLI: no present
caller needs one (A8 names where a parse point would go).

**Why the time model is two files.** `time_range.py` is time *of day* — what the core computes with.
`as_of.py` is the calendar/instant world, which enters only to answer "which times of this day are at or
after now + notice". They change for different reasons (a 24:00 close reopens `time_range.py`; multi-day or
zones reopen `as_of.py` and the entry). The one fact they share, the end of the day, has one home
(`TimeRange.whole_day`).

---

## 3. Modules: responsibility, signatures, contracts

### 3.1 `errors.py` — unchanged types

```python
class InvalidAvailabilityRequest(ValueError):
    """The caller sent input that a product rule rejects (R4, R5, R6, V1, N2). A caller bug: fix the
    input, don't retry. The message names the offending value(s)."""

class OverlappingBookingsError(InvalidAvailabilityRequest):
    """R4: two supplied bookings overlap. Carries the RAW pair as data (.first, .second), earlier first
    in (start, end) order."""
    first: TimeRange
    second: TimeRange
    def __init__(self, first: TimeRange, second: TimeRange) -> None: ...
```

Exactly two types: one base so a caller can catch every rejection from this package; one subtype only
because it carries a payload. Every new stage-2 rejection is an `InvalidAvailabilityRequest` — no caller
handles a negative buffer differently from a negative notice, so a subtype per rule would never be caught
differently.

### 3.2 `time_range.py` — `TimeRange`, time of day (published)

**Responsibility.** What a range of wall-clock time is (R2, R5-range, R6), and the only place in the package
that does arithmetic on times of day. Every operation that could produce an empty range returns `None`;
every public operation is pure and **total** — no precondition, no argument makes it raise, overflow or hang.

```python
@dataclass(frozen=True, slots=True)
class TimeRange:
    """A non-empty half-open range [start, end) of naive wall-clock time within one day.
    Invariant (established in __post_init__, the one construction path; frozen):
      type(start), type(end) are datetime.time; neither has tzinfo; start < end."""
    start: time
    end: time

    def __post_init__(self) -> None:
        """Raises, in order: TypeError (not a time — A7); InvalidAvailabilityRequest (tzinfo — A4);
        InvalidAvailabilityRequest (not start < end — R5).
        "invalid time range 17:00–09:00: end must be after start"."""

    @classmethod
    def if_nonempty(cls, start: time, end: time) -> "TimeRange | None":
        """Non-raising form for derived ranges: cls(start, end) if start < end, else None.
        Same type/tz checks as the constructor."""

    @classmethod
    def whole_day(cls) -> "TimeRange":
        """[time.min, time.max): the one spelling of the end-of-day sentinel (A3, A11)."""

    def intersection(self, other: "TimeRange") -> "TimeRange | None":
        """if_nonempty(max(starts), min(ends)). None when apart OR touching (R2). Symmetric."""

    def overlaps(self, other: "TimeRange") -> bool:
        """R2: self.intersection(other) is not None."""

    def extended(self, by: timedelta) -> "TimeRange":
        """B1 + M1: [start, end + by), cut at the end of the day. Never None.
        by <= 0 → self. by >= (whole_day().end − end) → [start, time.max). Else [start, end + by).
        `by` is compared with the room left BEFORE adding: timedelta.max cannot overflow."""

    def trimmed(self, by: timedelta) -> "TimeRange | None":
        """B2: [start, end − by) — the part left when `by` is reserved at the end.
        by <= 0 → self. by >= (end − start) → None. Compared before subtracting."""

    def fitting_starts(self, length: timedelta, *, step: timedelta, origin: time) -> Iterator[time]:
        """Every lattice point t = origin + k·step (k any integer) with [t, t + length) inside self,
        strictly ascending.
        Nothing when length <= 0, step <= 0, or length > end − start.
        `t + length <= end` is R2's "a slot may end exactly at the end" and is the ONLY fit test in the
        package. The k-range is computed by floor division before any multiplication, so every product
        lies inside [start, end]: no OverflowError for any length/step (timedelta.max included), and the
        work is proportional to the number of points yielded. Fresh iterator per call."""

    def __contains__(self, t: time) -> bool:
        """R2 for an instant: start <= t < end."""

    def __str__(self) -> str:
        """"09:00–09:45"; HH:MM when seconds/µs are zero, else isoformat. Used by every error message."""

# module-private: _require_wall_clock (A7 + A4), _nonempty (`start < end`, the ONE strict comparison
# behind R5-range and R2 emptiness), _offset (time → timedelta since midnight), _at (inverse), _fmt.
```

Illustrative — the only new arithmetic worth pinning:

```python
    def fitting_starts(self, length, *, step, origin):
        lo, hi, base = _offset(self.start), _offset(self.end), _offset(origin)
        if not (timedelta(0) < length <= hi - lo and step > timedelta(0)):
            return
        first = -((base - lo) // step)             # ceil((lo − base) / step)
        last = (hi - length - base) // step        # floor((hi − length − base) / step)
        for k in range(first, last + 1):
            yield _at(base + k * step)
```

**Surface.** Public members: `{start, end, if_nonempty, whole_day, intersection, overlaps, extended,
trimmed, fitting_starts}` plus `__contains__`, `__str__`, `==`/hash. Stage-1 `leading` is **removed**: its
only consumer (the R1 loop) now uses `fitting_starts` with `step = length`, which yields exactly the stage-1
tiling. Every member stays on the type for the stage-1 reason — it is the type's own geometry (as free
functions elsewhere it would be feature envy; as `_methods` called from siblings, inappropriate intimacy),
it is total, and its meaning is fixed by decided rules (R2, R6, B1, B2, M1, G1). `test_public_surface.py`
pins the set so growing it is a reviewed act. No `order=True`: "less than" between ranges has no meaning.

`extended` and `trimmed` are two methods, not one signed `shift_end`: the direction is visible at each call
site, and their totality differs (growing never empties; shrinking may).

### 3.3 `rules.py` — `ResourceRules` (NEW, published)

```python
@dataclass(frozen=True, slots=True)
class ResourceRules:
    """One resource's booking rules. The default instance is exactly stage 1.
    Invariant (__post_init__, the one construction path; frozen):
      buffer >= 0; minimum_notice >= 0; granularity is None or granularity > 0."""
    buffer: timedelta = timedelta(0)            # B1/B2 cleanup after every booking
    minimum_notice: timedelta = timedelta(0)    # N1 lead time before an offered start
    granularity: timedelta | None = None        # G1 grid step from working-hours start; None → R1

    def __post_init__(self) -> None:
        """V1, first failure wins, in field order; InvalidAvailabilityRequest:
          "buffer must not be negative, got -1 day, 23:45:00"
          "minimum notice must not be negative, got …"
          "granularity must be positive when given, got 0:00:00"
        No type guard (A7): a non-timedelta fails loudly at the first comparison."""
```

A validated value with no other behaviour, deliberately. Each setting's *meaning* belongs to the module that
applies it — buffer to occupancy (`_day`), granularity to alignment (`slots`), notice to eligibility
(`as_of`). A method such as `rules.occupancy_of(booking)` would pull a private decision onto a published
type. Buffer 0 and notice 0 are genuine zero lengths; "no grid" is `None`, because a step of 0 has no meaning.

### 3.4 `as_of.py` — `AsOf`, the one date/instant conversion (NEW, published)

```python
@dataclass(frozen=True, slots=True)
class AsOf:
    """The calendar day asked about, and the naive local moment it is asked (N1). The caller keeps
    `day` equal to the day its hours and bookings describe (A13).
    Invariant: type(day) is date and not datetime; now.tzinfo is None."""
    day: date
    now: datetime

    def __post_init__(self) -> None:
        """Raises, in order: TypeError — day is a datetime or not a date (A10);
        InvalidAvailabilityRequest — now carries tzinfo (V1):
        "now must be a naive local date-time (no tzinfo), got 2026-09-23 08:00:00+02:00"."""

    def eligible_starts(self, notice: timedelta) -> TimeRange | None:
        """N1, the one owner: the times t of `day` with datetime.combine(day, t) >= now + notice, as a
        time-of-day window; None when no time of the day qualifies.
          first = combine(day, whole_day().start); last = combine(day, whole_day().end)
          notice >  last − now   → None                       (cutoff after the day: S12, S15)
          notice <= first − now  → TimeRange.whole_day()      (cutoff on an earlier day: no effect)
          otherwise              → TimeRange.if_nonempty((now + notice).time(), whole_day().end)
        `now + notice` is formed only once it is known to lie inside the day; a difference of two
        datetimes is always representable. Total for every timedelta."""
```

**Why here, once.** `AsOf` owns `day` and `now`; computing the cutoff anywhere else would read both fields
and decide outside the object. The result is in the core's existing currency — a `TimeRange` of the day —
so the core never sees a `date` or `datetime`, and R6 stays true inside it. "Cutoff on another day" collapses
into `None` or the whole day and never reaches the core as a special case. `day` and `now` are one type
because they must arrive together: "a day without a now" is unrepresentable. Notice is **not** a field of
`AsOf`: it is a per-resource rule, while `AsOf` belongs to one query.

### 3.5 `_day.py` — `DaySchedule`, the one occupancy owner (package-private)

**Responsibility.** Turn the caller's bookings plus the resource's buffer into the day's occupancy (R3, R4,
B1, B3, M1), then answer one question: **where may a new booking's own interval lie** (B2).

```python
class DaySchedule:
    """One resource's day: working hours, the buffer, and the occupancy inside the hours.
    Invariant (established in __init__, the ONE construction path; no method assigns to self):
      I1  every run in _busy lies inside _hours
      I2′ along _busy, starts are non-decreasing AND ends are non-decreasing
      I4  every run is a valid, non-empty TimeRange
      I5  _buffer >= 0 (its one producer is a validated ResourceRules; the geometry is total anyway)
    Stage-1 I2 "strictly ascending" and I3 "pairwise disjoint" no longer hold: under B3, occupancy runs
    may overlap or share a start. They are busy time, not bookings."""
    __slots__ = ("_hours", "_busy", "_buffer")

    def __init__(self, hours: TimeRange, bookings: Iterable[TimeRange], buffer: timedelta) -> None:
        """Steps, in this order (the order carries A1, B1 at the opening edge, and B3):
          1. ordered = sorted(bookings, key=lambda b: (b.start, b.end))              R4: service sorts
          2. first adjacent pair with a.overlaps(b) → OverlappingBookingsError(a, b)  R4 on RAW bookings
          3. _busy = tuple(o for b in ordered                                        B1 widen (M1 cut),
                           if (o := b.extended(buffer).intersection(hours)) is not None)   then R3 clip
        `bookings` is consumed exactly once."""

    def bookable_spans(self) -> Iterator[TimeRange]:
        """B2, the one owner. The stage-1 gap walk with one added call:
          cursor = _hours.start
          for run in _busy:
              gap = TimeRange.if_nonempty(cursor, run.start)          # None if run.start <= cursor
              if gap is not None and (span := gap.trimmed(_buffer)) is not None:
                  yield span                                          # closed by occupancy: the new
                                                                      # booking's buffer must clear it
              cursor = run.end                                        # never moves back (I2′)
          tail = TimeRange.if_nonempty(cursor, _hours.end)
          if tail is not None: yield tail                             # closed by closing: buffer may
                                                                      # run past it (B2, 0004 §3)
        Post: spans are non-empty, inside _hours, strictly ascending, pairwise disjoint; each starts at
        the start of a maximal free gap (the R1 anchor); with buffer 0 they are exactly the free gaps.
        THEOREM: for d > 0, [t, t+d) ⊆ some span ⇔ [t, t+d) ⊆ hours and [t, t+d+buffer) meets no run.
        Fresh iterator per call."""
```

**Why I2′ holds.** After step 2 the raw bookings are sorted by start and pairwise disjoint, so
`bᵢ.end ≤ bᵢ₊₁.start < bᵢ₊₁.end`: raw ends strictly increase. `extended(buffer)` with one buffer for every
booking, capped at `time.max`, is a non-decreasing map on ends and leaves starts alone. Clipping
(`max(start, H.start)`, `min(end, H.end)`) is non-decreasing on both. Dropping `None`s leaves a subsequence.
So starts and ends of `_busy` are both non-decreasing.

**Why the unchanged walk is exact under overlapping occupancy.** Because ends are non-decreasing, `cursor`
is always the latest end seen so far — every instant before it that lies after the previous gap is busy. A
run starting at or before `cursor` gives `if_nonempty → None`: no negative gap, no duplicate gap, no
zero-length gap. A run starting after `cursor` begins the earliest remaining busy time (starts are
non-decreasing), so `[cursor, run.start)` is a maximal free gap. S6 is the concrete case.

**Why no merge step.** Coalescing overlapping runs into their union would restore stage-1 I3 verbatim, but
the walk does not need it: I2′ is all it relies on, and I2′ is established here, in the one constructor,
from R4 plus the uniform buffer. A merge would add a public `joined` member to `TimeRange` and a fold with no
present consumer. **Falsifier:** per-booking buffers (a non-goal) would break monotone ends; the merge then
becomes necessary and lands in `DaySchedule.__init__` only. This is recorded so that change does not
silently break the walk.

**Proof of the theorem (B2).** Let `[t, t+d) ⊆ H` and let `G` be the maximal free gap containing `t`
(`t` must be free, since `t ∈ [t, t+d+b)`). The part of the new booking's occupancy that R3 counts is
`[t, min(t+d+b, H.end))`, contiguous from `t`; it avoids all runs iff it stays inside `G`.
- `G` ends at closing: the condition is `t + d ≤ H.end`, i.e. `[t, t+d) ⊆ G` — the untrimmed tail.
- `G` ends at a run starting at `r`: the condition is `t + d + b ≤ r`, i.e. `[t, t+d) ⊆ [G.start, r − b)`
  = `G.trimmed(b)`.
The asymmetry of B2 (the slot must stay inside hours; its buffer may pass close) is therefore absorbed
exactly where the walk already knows whether a gap ended at a run or at closing. No slot policy ever sees
the buffer.

**R4 proofs carried from stage 1.** Checking only adjacent pairs after sorting by `(start, end)` finds an
overlap iff one exists (if `a` overlaps a later `c`, the element between them overlaps `a`); the reported
pair is a true offending pair; the key is a total order on distinct values, so the pair and the whole output
are the same for every input permutation (C10, S16).

**One construction path.** A plain class with one `__init__`; no field-wise constructor, no public field;
the type is the evidence that R4 ran and B1/R3 were applied.

### 3.6 `slots.py` — the entry (published) and its private helpers

```python
def available_starts(
    working_hours: TimeRange,
    bookings: Iterable[TimeRange],
    duration: timedelta,
    *,
    rules: ResourceRules = ResourceRules(),
    as_of: AsOf | None = None,
) -> list[time]:
    """Start times, earliest first, at which a new booking of `duration` can be offered: inside
    `working_hours`; with the resource's buffer, clear of existing occupancy inside the hours (B2);
    on the resource's granularity grid, or gap-aligned without one (G1/R1); and, with `as_of`, not
    before as_of.now + minimum_notice (N1).
    Checked here, in this order (A6): duration > 0 (R5); notice needs as_of (N2); bookings do not
    overlap (R4, by building DaySchedule).
    Post: strictly ascending, no duplicates; [] when nothing fits or nothing is eligible.
    Default rules and no as_of → exactly the stage-1 result.
    Pure; `bookings` consumed once. Raises InvalidAvailabilityRequest, OverlappingBookingsError."""
    if duration <= timedelta(0):
        raise InvalidAvailabilityRequest(f"duration must be positive, got {duration}")
    eligible = _eligible_starts(rules.minimum_notice, as_of)              # N2 (may raise); N1 window
    day = DaySchedule(working_hours, bookings, rules.buffer)             # R4, R3, B1, B3, M1
    if eligible is None:                                                 # cutoff after this day
        return []
    return [start
            for span in day.bookable_spans()                             # B2
            for start in _aligned_starts(span, duration, working_hours.start, rules.granularity)
            if start in eligible]                                        # N1: removes, moves nothing


def _aligned_starts(span: TimeRange, duration: timedelta,
                    grid_origin: time, granularity: timedelta | None) -> Iterator[time]:
    """R1 and G1 — the one owner of slot alignment: it chooses the lattice; the fit is the span's.
      granularity None → span.fitting_starts(duration, step=duration, origin=span.start)     # R1
      granularity g    → span.fitting_starts(duration, step=g, origin=grid_origin)          # G1, 0004 §8"""


def _eligible_starts(notice: timedelta, as_of: AsOf | None) -> TimeRange | None:
    """N2, the one owner — the only place a resource's rules meet the query's context.
      as_of None, notice > 0  → InvalidAvailabilityRequest(
            "minimum notice is 2:00:00, so the query needs as_of=AsOf(day, now)")
      as_of None, notice == 0 → TimeRange.whole_day()          (no filter: stage 1)
      otherwise               → as_of.eligible_starts(notice)  (N1's owner converts)"""
```

**Earliest first without a sort.** Spans are ascending and disjoint; within a span the lattice points are
ascending and all before `span.end ≤` the next span's start; a filter preserves order.

**Why the two policies are data, not types (H2).** Gap-aligned and grid differ only in two values — the
lattice origin and the step. The fit rule is not part of either: `DaySchedule` computed it once (spans) and
`fitting_starts` tests it once (containment). Neither branch contains a comparison, so neither can
re-implement the fit. A `SlotPolicy` Protocol with two classes would be an interface whose variation is
data. **Falsifier:** a policy that is not a lattice ("preferred starts first", "grid plus the gap start")
would earn a policy seam — at this one call site.

**Why notice is a filter, and why that is not the forbidden trailing filter.** N1 says notice *removes*
starts and never moves the grid or gap anchors. Applying it as busy time `[00:00, cutoff)`, or intersecting
spans with the window, would move the gap-aligned anchor (S11 would offer 09:50 instead of 10:15). The
filter line has one job — apply the window that `AsOf` computed. The forbidden trailing filter is a filter
for the **buffer**, which would re-derive occupancy outside its owner.

**Why `ResourceRules()` as the default, not `None`.** It is frozen, so a shared default is safe, and the
defaults then live in one place — the field defaults of `ResourceRules` — instead of also in an
`if rules is None` branch.

### 3.7 `__init__.py`

```python
from .errors import InvalidAvailabilityRequest, OverlappingBookingsError
from .time_range import TimeRange
from .rules import ResourceRules
from .as_of import AsOf
from .slots import available_starts
__all__ = ["TimeRange", "ResourceRules", "AsOf", "available_starts",
           "InvalidAvailabilityRequest", "OverlappingBookingsError"]
```

`DaySchedule`, spans, the lattice choice and the eligibility helper appear in no public signature.

```python
from datetime import date, datetime, time, timedelta
from availability import TimeRange, ResourceRules, AsOf, available_starts

available_starts(TimeRange(time(9), time(17)),
                 [TimeRange(time(9), time(9, 45)), TimeRange(time(11), time(12))],
                 timedelta(minutes=30),
                 rules=ResourceRules(buffer=timedelta(minutes=15), granularity=timedelta(minutes=15)))
# → [10:00, 10:15, 12:15, 12:30, …, 16:30]

available_starts(hours, bookings, timedelta(minutes=30),
                 rules=ResourceRules(minimum_notice=timedelta(hours=2)),
                 as_of=AsOf(date(2026, 9, 24), datetime(2026, 9, 24, 8, 0)))   # starts from 10:00
```

**Stage-1 callers:** a three-argument call has the same meaning, result, errors and precedence. The new
parameters are keyword-only, so they add no positional connascence.

---

## 4. What each concept is

| Concept | What it is | Why this kind of thing (and the cram it avoids) |
|---|---|---|
| Working window | a `TimeRange` (`working_hours`) | a half-open range; its role (clip frame, grid origin) is a fact of the day |
| Booking | a `TimeRange` in `bookings` | no id or state (storage is a non-goal); the rules about bookings are rules of occupancy |
| Buffer | a `timedelta` on `ResourceRules`; its *effect* is occupancy | never a booking: it never passes R4 (a synthetic booking would make touching bookings "overlap" and break B3) and is never returned |
| Occupancy | `DaySchedule._busy`: `(booking extended by buffer) ∩ hours`, one run per booking | busy time, not bookings; runs may overlap (B3) and carry no disjointness claim |
| Bookable span | a `TimeRange` yielded by `DaySchedule.bookable_spans()` | where a new booking's own interval may lie. Not free time (the last `b` of a gap before a run is free but unbookable) and not a gap with a flag; with buffer 0 it is the free gap |
| The new booking's buffer | the `trimmed(buffer)` on gaps closed by occupancy | a reservation at the end of the room — not fake busy time padded before existing bookings (that would wrongly block 16:45–17:00 before an after-hours booking, S9) |
| Grid / R1 stepping | a lattice `(origin, step)` passed to `fitting_starts` | two parameters chosen at one site — not a type, not a filter over gap-aligned starts (which would keep only every d-th grid point), not a score |
| Candidate slot | never materialized; its fit is `t + length <= end` inside `fitting_starts` | the output is start times; a `Slot` type would have no consumer |
| Notice cutoff | the eligible-start window `TimeRange \| None` from `AsOf.eligible_starts` | a filter on starts by the rule's own words; not occupancy (moves anchors), not a clipped working window. `None` = nothing eligible; "no filter" is the honest whole-day window |
| Query context | `AsOf(day, now)` | the moment of asking and the day asked about; not part of the resource or the schedule |
| Resource settings | `ResourceRules` | per-resource configuration that validates itself; hours are **not** folded in — hours are per day |
| Duration | `timedelta` | its one rule (> 0) has one owner, the one entry that accepts it |

---

## 5. Rule → owner

| Rule | Single owner | Why every path goes through it |
|---|---|---|
| R1 gap-aligned (no grid) | `slots._aligned_starts` (lattice = span start, duration) | the one composition line calls it for every span |
| R2 touching ≠ overlap | `time_range._nonempty`, behind `if_nonempty`/`intersection`/`overlaps`/`trimmed` | the only strict bound comparison |
| R2 a slot may end exactly at the end | `TimeRange.fitting_starts` (`t + length <= end`) | the only fit test (`leading` removed) |
| R3 only in-hours occupancy counts | `DaySchedule.__init__` step 3 (`.intersection(hours)` after widening) + the untrimmed tail span | the only place occupancy meets the hours |
| R4 sort; raw overlap rejected naming the pair | `DaySchedule.__init__` steps 1–2 | one constructor; buffers enter only at step 3 |
| R5 range / duration / `[]` | `TimeRange.__post_init__` / `available_starts` statement 1 / structural | unchanged |
| R6 naive one-day time in the core | `TimeRange` (field types, `_require_wall_clock`); `AsOf.eligible_starts` is the only exit from date/instant to time of day | the core receives no `date`/`datetime` |
| **B1** booking occupies `[s, e+b)`; counts wherever it lies in hours | `DaySchedule.__init__` step 3 (`extended` before `intersection`) | occupancy is built only here |
| **B2** slot inside hours; slot + buffer clear of occupancy; may pass close | `DaySchedule.bookable_spans` (`trimmed(buffer)` on occupancy-closed gaps, not on the tail) | policies see only spans; no other code knows the buffer |
| **B3** buffer-violating bookings accepted | `DaySchedule.__init__`: R4 on raw bookings (step 2), never on occupancy; I2′ replaces I3 | occupancy is never checked for overlap |
| **G1** optional grid from hours start; every fitting point | `slots._aligned_starts` (lattice = hours start, g) | same single alignment owner as R1 |
| **N1** `combine(day, t) >= now + notice`; removes only | `AsOf.eligible_starts` (decision + conversion), applied by the one `if start in eligible` | the core sees only the returned window |
| **N2** `now` optional; notice > 0 without it → error; notice 0 with it → past dropped | `slots._eligible_starts` | the only place `rules` meets `as_of`; "past dropped" falls out of N1 with notice 0 |
| **V1** negative buffer / notice; granularity ≤ 0 | `ResourceRules.__post_init__` | one construction path |
| **V1** aware `now` | `AsOf.__post_init__` | one construction path |
| **V1** notice > 0 without `now` | `slots._eligible_starts` (= N2) | |
| **V1** defaults = stage 1 | structural: `extended(0)`/`trimmed(0)` are identities, spans = gaps, lattice `(gap.start, d)` is R1, window = whole day | no special-case path |
| **M1** buffer past midnight cut | `TimeRange.extended` (cap at `whole_day().end`) | the only operation that grows a range |
| Earliest first | spans ascending/disjoint + `fitting_starts` ascending + order-preserving filter | no sort to forget |
| Validated once; core trusts | constructors (`TimeRange`, `ResourceRules`, `AsOf`) + `available_starts` (duration, N2) + `DaySchedule.__init__` (R4) | `bookable_spans`, `_aligned_starts`, `fitting_starts`, `eligible_starts` validate nothing |

---

## 6. Error vocabulary

| Situation | Raised by | Type | Message (example) |
|---|---|---|---|
| range `end <= start` | `TimeRange(...)` (caller) | `InvalidAvailabilityRequest` | `invalid time range 17:00–09:00: end must be after start` |
| aware `time` in a range | `TimeRange(...)` | `InvalidAvailabilityRequest` | `…: times must be naive wall-clock (no tzinfo)` |
| non-`time` range field | `TimeRange(...)` | `TypeError` (A7) | `TimeRange.start must be datetime.time, got datetime.datetime` |
| negative buffer | `ResourceRules(...)` | `InvalidAvailabilityRequest` | `buffer must not be negative, got -1 day, 23:45:00` |
| negative notice | `ResourceRules(...)` | `InvalidAvailabilityRequest` | `minimum notice must not be negative, got …` |
| granularity 0 / negative | `ResourceRules(...)` | `InvalidAvailabilityRequest` | `granularity must be positive when given, got 0:00:00` |
| `day` is a `datetime` / not a date | `AsOf(...)` | `TypeError` (A10) | `AsOf.day must be datetime.date (not datetime), got datetime.datetime` |
| aware `now` | `AsOf(...)` | `InvalidAvailabilityRequest` | `now must be a naive local date-time (no tzinfo), got …+02:00` |
| `duration <= 0` | `available_starts` | `InvalidAvailabilityRequest` | `duration must be positive, got 0:00:00` |
| notice > 0, no `as_of` | `available_starts` (`_eligible_starts`) | `InvalidAvailabilityRequest` | `minimum notice is 2:00:00, so the query needs as_of=AsOf(day, now)` |
| bookings overlap (incl. duplicates, outside hours, any buffer) | `DaySchedule.__init__` | `OverlappingBookingsError` (`.first`, `.second` raw) | `bookings 10:00–11:00 and 10:30–11:30 overlap; …` |
| other wrong argument types | stdlib, at first use | `TypeError`/`AttributeError`, unwrapped (A7) | stdlib |
| nothing fits / nothing eligible | — | `[]` | — |

---

## 7. Traces

H = 09:00–17:00, d = 30 min, b = buffer, g = granularity, unless stated. "occ" = `_busy`; "sp" = spans.

### 7.1 Stage-1 cases under default rules (S3)

With `ResourceRules()` and no `as_of`: `extended(0)` returns self, so occ is the stage-1 clipped busy time
(disjoint, strictly ascending — a special case of I2′); `trimmed(0)` returns self, so sp are exactly the
stage-1 free gaps; `_aligned_starts` yields `gap.fitting_starts(d, step=d, origin=gap.start)` =
`gap.start + k·d` for `k = 0 … len//d − 1` — the stage-1 R1 postcondition; the window is the whole day and
contains every start; N2 cannot fire with notice 0. Hence, value for value:

| Case | Result |
|---|---|
| C1 worked example (09:00–09:45, 11:00–12:00) | `09:45, 10:15, 12:00, 12:30, …, 16:30` |
| C2 no bookings | 09:00 … 16:30 (16 starts) |
| C3 day fully covered (incl. 08:00–18:00, touching tiling) | `[]` |
| C4 duration longer than every gap; `timedelta.max` | `[]` (compared before any arithmetic) |
| C5 gap = d → 1 start; gap = 2.5·d → 2 | ✓ |
| C6 booking touching open/close edge | no effect (`intersection` → None) |
| C7 straddling open/close | clipped: 09:30 … 16:00 |
| C8 touching bookings | accepted, no slot between |
| C9 overlap | `OverlappingBookingsError` naming the pair |
| C10 any input order | identical output and error |
| C11 `end <= start` | rejected in the caller's `TimeRange(...)` |
| C12 duration 0 / negative | rejected first (A6), even with full cover or overlaps |
| C13 45 min in a 2 h gap | 2 starts |
| C14 last slot ends at close | 16:30 offered |

### 7.2 Stage-2 cases

| Case | Path | Result |
|---|---|---|
| S1 | R4 passes. occ `[09:00,10:00) [11:00,12:15)`. Walk: gap(09:00,09:00) None; gap `[10:00,11:00)` trimmed(15) → `[10:00,10:45)`; tail `[12:15,17:00)`. Lattice (09:00, 15): span 1 → 10:00, 10:15 (10:45 ≤ 10:45); tail → 12:15 … 16:30 (18 points). Window whole day. | `10:00, 10:15, 12:15, …, 16:30` ✓ |
| S2 | Same spans; lattice (span.start, 30): span 1 → 10:00 only; tail → 12:15, 12:45, …, 16:15. | ✓ |
| S3 | §7.1 | bit-for-bit ✓ |
| S4 | occ empty; tail = H, untrimmed; grid last point 16:30 (17:00 ≤ 17:00). Its buffer to 17:15 is never looked at. | 16:30 ✓ |
| S5 | 08:00–09:00+15 → `[08:00,09:15)` ∩ H = `[09:00,09:15)` → tail from 09:15: 09:15 both modes. 08:00–08:50+15 → `[09:00,09:05)` → tail from 09:05: grid first ≥ 09:05 → 09:15; R1 → 09:05. 07:00–08:00+15 → `[07:00,08:15)` ∩ H = None. | 09:15/09:15; 09:15/09:05; no effect ✓ |
| S6 | 10–11 and 11–12 touch: R4 passes (B3). occ `[10:00,11:15) [11:00,12:15)` — overlapping, I2′ holds. Walk: `[09:00,10:00)` trimmed → `[09:00,09:45)`; cursor 11:15; gap(11:15,11:00) None; cursor 12:15; tail `[12:15,17:00)`. Nothing in [10:00, 12:15). b = 60 with 10:00–10:30, 10:45–11:00: occ `[10:00,11:30) [10:45,12:00)`; `[09:00,10:00)` trimmed(60) None; gap(11:30,10:45) None; cursor 12:00; tail from 12:00. | no negative/duplicate gap; cursor only forward ✓ |
| S7 | step 2 on raw ranges before widening → `OverlappingBookingsError(10:00–11:00, 10:30–11:30)` whatever b. | ✓ |
| S8 | e.g. 09:00–09:45 (+15 → 10:00) and 11:00–12:00: gap `[10:00,11:00)` → span `[10:00,10:45)`. d 45 → 10:00 offered (buffer touches 11:00). d 60 → not offered, though `[10:00,11:00)` itself is free. | ✓ |
| S9 | 17:00–18:00+15 ∩ H = None; tail = H. | 16:30 ✓ |
| S10 | g 20 → 09:00, 09:20, …, 16:20. g 10 h → k-range {0} → 09:00, no overflow. C1 bookings, b 0, g 15: spans `[09:45,11:00)`, `[12:00,17:00)` → 09:45, 10:00, 10:15, 10:30, 12:00, …. H 09:10–17:00 → origin 09:10: 09:10, 09:25, …. | ✓ |
| S11 | now = day 08:00, notice 2 h → window `[10:00, …)`: 09:45 out, 10:00 in. 90 min → `[09:30, …)`. C1, no grid, now 09:50, notice 0: starts 09:45, 10:15, … unchanged; filter drops 09:45. | first 10:15 ✓ |
| S12 | prev 20:00 + 48 h > last − now → None → `[]` (after R4). prev 16:00 + 16 h → window from 08:00 → no effect. now next day: last − now < 0 ≤ notice → None → `[]`. now day 16:40, notice 0 → window from 16:40; last start 16:30 → `[]`. | ✓ |
| S13 | `ResourceRules` negatives / g 0 / g < 0 → at construction, field order. Aware now → `AsOf`. Notice > 0, no `as_of` → `_eligible_starts`. Precedence A6: duration beats N2; N2 beats overlap; overlap beats "past day". | ✓ |
| S14 | now = day 10:00, notice 0 → window `[10:00, …)`: 10:00 kept, 09:30 dropped. | ✓ |
| S15 | d max → `fitting_starts` compares first → nothing. b max → `extended` caps at `time.max`; `trimmed(max)` → None, only the tail may offer. notice max → `notice > last − now` → None; `now + notice` never formed. 23:50 + 30 → `[…, time.max)`. g max → k-range {0} or empty. No loop is unbounded: `fitting_starts` iterates a finite k-range; the walk is linear in `_busy`. | no OverflowError, no hang ✓ |
| S16 | everything downstream of `sorted((start, end))` is a function of the sorted tuple; S6's input included. | identical ✓ |

### 7.3 Interactions no S-case lists (new rule × existing rule)

| Crossing | Outcome |
|---|---|
| buffer × R3, booking straddling close (16:50–17:30, b 15) | occ `[16:50,17:00)`; the gap before it is trimmed → last start 16:05 (d 30). Correct: it is in-hours occupancy. |
| buffer × R3, straddling open (08:30–09:30, b 15) | occ `[09:00,09:45)` → first span from 09:45 |
| buffer × A1/A2 | overlaps and duplicates outside hours still rejected on raw bookings |
| buffer larger than a run-closed gap | that gap yields no span; later spans unaffected |
| buffer × hours ending at `time.max` | M1 cut coincides with the hours end |
| two pre-opening bookings whose occupancy clips to the same start (07:00–08:00, 08:00–08:30, b 2 h) | occ `[09:00,10:00) [09:00,10:30)`: same start, non-decreasing ends (I2′); walk → first span from 10:30 |
| grid × d not a multiple of g; g < d; g > d | every fitting grid point |
| grid × second-precision hours start | origin keeps its seconds; integer arithmetic |
| notice × grid / × gap anchors | filter only; neither moves |
| notice × µs in `now` | exact window start |
| `AsOf(date.max, datetime.max)`, notice 0 | `last − now = 0 ≥ notice` → window from `now.time()`; nothing overflows |
| N2 × a past day with overlaps | overlap error (A6) |

---

## 8. Design reasoning

### 8.1 How the four hard decisions were resolved

- **H1 Buffer.** `DaySchedule`, already the occupancy owner, owns both halves: existing bookings' buffers
  (widen before clipping, B1) and the new booking's buffer (trim gaps closed by occupancy, B2). The walk is
  unchanged but for one call; the stage-1 disjointness invariant is replaced by I2′, which this constructor
  establishes. R4 still runs on raw bookings first, so B3 and S7 both follow from step order.
- **H2 Slot policy.** One alignment owner chooses a lattice `(origin, step)`; one total operation enumerates
  the lattice points that fit inside a span. Both policies are data; the fit rule is upstream of both.
- **H3 Time model.** One conversion, `AsOf.eligible_starts`, maps `(day, now, notice)` to a time-of-day
  window or `None`. The core stays in R6's one-day world. `now + notice` is formed only once proved in range.
- **H4 Public seam.** Two published, validated, frozen values — `ResourceRules` (the resource's lifetime)
  and `AsOf` (the query's) — as keyword-only parameters with stage-1 defaults. One owner per validation:
  settings at `ResourceRules`, the instant at `AsOf`, the cross rule N2 at `_eligible_starts`.

### 8.2 Alternatives rejected

- **Buffer as a trailing filter over starts** — a second owner of occupancy; also wrong for R1 (anchors
  would start at the booking's end, so S2 would offer 09:45).
- **Buffer as a synthetic booking** — the concept cram 0004 rules out; it would trip R4 on S6 and reject B3
  input.
- **Widening before the R4 check** — rejects B3 input.
- **Padding occupancy backwards by the buffer** — models the new booking's buffer as fake busy time; wrong
  at S9 (a 17:00 after-hours booking would block 16:45).
- **A footprint length `d + b` in the fit test** — buffer knowledge in `slots` (a second owner), overflow for
  large values, and a wrong closing edge.
- **Coalescing occupancy into its union** — restores I3 but pays a public `TimeRange.joined` and a fold the
  walk does not need (§3.5 falsifier).
- **A `max()` cursor / relaxed walk** — unnecessary under I2′.
- **A `SlotPolicy` Protocol with `_GapAligned`/`_GridAligned`** — its variation is two values. Its genuine
  strength, "a policy cannot decide a fit", is kept more strongly by data (no policy code exists at all).
- **Grid as a filter over gap-aligned starts** — would keep only every d-th grid point (0004 §6 rules it
  out).
- **A per-candidate `DaySchedule.fits(t, d)` query** — an Ask-style second fit path; O(n) per candidate.
- **Keeping `leading`** — no consumer left.
- **One signed `shift_end`** — hides direction at the call site; the two operations differ in totality.
- **Notice as occupancy `[00:00, cutoff)` or as an intersection with spans** — moves anchors (S11 → 09:50).
- **A cutoff `time` with `time.min` meaning "no filter"** — a sentinel in a comparison outside
  `time_range.py`; the window keeps the comparison on the type and names "nothing eligible" as `None`.
- **A `datetime` core** — dates on every range; midnight crossing representable.
- **`now` only, day inferred from `now.date()`** — cannot ask about another day (S12).
- **Notice on `AsOf`, or `now` on `ResourceRules`** — mixes the resource's and the query's lifetimes.
- **N2 as `ResourceRules.earliest_start(as_of)`** — puts query logic on the published settings type and
  makes `rules` depend on `as_of`.
- **Five loose keyword primitives** — a long parameter list with hidden co-requirements (`day` without
  `now`).
- **One `AvailabilityQuery` bundling everything; hours inside `ResourceRules`** — mixes per-request,
  per-resource and per-day data.
- **`Buffer`/`Notice`/`Granularity`/`Lattice` types** — each would own one rule already owned elsewhere.
  Falsifier: a second operation accepting one of them.
- **New error subtypes** — no caller would catch them differently.
- **`AsOf` inside `time_range.py`** — a calendar instant changes for a different reason than time of day.

### 8.3 Supersessions of the stage-1 design (decisions/0003)

- `TimeRange.leading` → removed; R2 "may end at the end" moves to `fitting_starts` on the same type.
- `DaySchedule.free_gaps` → `bookable_spans` (identical when buffer is 0).
- `DaySchedule` I2 (strict) and I3 (disjoint) → I2′ (starts and ends non-decreasing).
- A6 precedence → amended (§1.2).
- A5 → extended to granularity.
- The stage-1 rejection of a slot-policy seam **stands**, with a sharper falsifier (a non-lattice policy).
- decisions/0002 §1 (gap-aligned only) was already superseded in part by decisions/0004.

### 8.4 Subtractive pass (what was added or changed)

| Element | Present force | Verdict |
|---|---|---|
| `ResourceRules` | V1 field rules; three per-resource settings that travel together | keep |
| `AsOf` | N1 needs day + now together; aware-`now` owner; the H3 conversion home | keep |
| `AsOf` `day` type guard | A10 silent acceptance | keep |
| `AsOf.eligible_starts` | N1, cross-day, overflow safety | keep |
| `TimeRange.whole_day` | A3/A11 sentinel spelled once (used by `extended`, `AsOf`, `_eligible_starts`) | keep |
| `TimeRange.extended` | B1, M1 | keep |
| `TimeRange.trimmed` | B2 | keep |
| `TimeRange.fitting_starts` | the one enumeration + fit for both policies; R2 end-fit; overflow safety | keep |
| `TimeRange.__contains__` | applies the N1 window without a bound comparison outside `time_range.py` | keep |
| `TimeRange.leading` | no consumer | **cut** |
| `TimeRange.joined` / coalescing | walk correct under I2′ | **not added** |
| `DaySchedule` `buffer` / `_buffer` | B1, B2 | keep |
| rename `free_gaps` → `bookable_spans` | the yielded ranges are no longer free gaps | keep |
| `_aligned_starts` | R1 + G1 lattice choice | keep |
| `_eligible_starts` | N2 | keep |
| early `return []` | nothing eligible, after validation (A6) | keep |
| `*` keyword-only marker | stage-1 calls unaffected; new arguments cannot be mispositioned | keep |
| `SlotPolicy` Protocol, policy classes, `Lattice`/`Grid`/`Notice`/`Buffer` types, error subtypes | none | **not added** |

### 8.5 Principles that do not apply at this scale

Ports and adapters, DIP, repositories (no I/O); concurrency (all immutable or local); security (no trust
boundary beyond validation); performance (no requirement; A5 records the unbounded output); add-feature
migration (nothing persisted or built; the signature change is additive with defaults).

---

## 9. Test plan (test-first, stdlib `unittest`, pure, no mocks)

Tests assert contracts at the **published** seams: `TimeRange`, `ResourceRules`, `AsOf`,
`available_starts`, the package surface. `DaySchedule` and the helpers are covered through
`available_starts`. Every row names the decision it pins; there is no coverage percentage.

### 9.1 Characterization — kept unchanged (S3)

- `test_available_starts.py` **A1–A21** (stage-1 product contract; three-argument calls → defaults path):
  C1 exact list; gap-aligned not grid (09:45, 10:15 present, 10:00 absent); no bookings → 16 starts; full
  cover → `[]`; oversize durations incl. `timedelta.max` → `[]`; exact-fit gaps; edge-touching bookings;
  straddling bookings; touching bookings; overlap error with `.first/.second`; nested and same-start
  overlaps; duplicates; overlap wholly before opening (A1); all permutations identical; generator input;
  duration 0/negative incl. precedence; 45 min in 2 h; last slot at close; ascending across gaps;
  sub-minute durations; `duration=30` → `TypeError`.
- `test_time_range.py` T1–T7, T9, T10 (range validity, tz, type guard, constructor precedence,
  `if_nonempty`, `overlaps`, `intersection`, `__str__`, frozen/hash).
- `test_invariants.py` stage-1 generator and properties 1–7, run with default rules.
- `test_public_surface.py` P4 (`DaySchedule` not reachable), P5 (error hierarchy).

These must pass **unedited** after every build step (§10).

### 9.2 Changed, and why

- **T8** (`leading`) → **T8′** (`fitting_starts` with `step = length`, `origin = start`): same decisions —
  exact fit ends at `end`; 1 µs too long → nothing; length 0/negative → nothing; `timedelta.max` → nothing,
  no `OverflowError`; 7 min 30 s keeps seconds. Reason: `leading` is removed.
- **P1** `__all__` = the six names of §3.7. **P2** `TimeRange` public members = §3.2's set.
  **P3** type hints of `available_starts`, `ResourceRules`, `AsOf`, `AsOf.eligible_starts` resolve only to
  `datetime`/`date`/`time`/`timedelta`, builtins, `collections.abc`, `TimeRange`, `ResourceRules`, `AsOf`,
  error types — no `_day` type. These are deliberate surface changes, which P1/P2 exist to force.

### 9.3 New — published value seams

| # | Seam | Test | Pins |
|---|---|---|---|
| T11 | `fitting_starts` | origin before start → first point ≥ start (09:00/15 over `[09:05,10:00)` → 09:15 …); origin after start (k < 0); origin = start; step > span → ≤ 1 point; step ≤ 0 → nothing; `step=timedelta.max` → no overflow; every point has `t + length ≤ end` | G1, S10, S15 |
| T12 | `extended` | +15; 0/negative → self; 23:50 + 30 → end `time.max`; `timedelta.max` → `time.max`, no error | B1, M1, S15 |
| T13 | `trimmed` | 15 off 60 → 45; exactly length → None; more → None; 0/negative → self; `timedelta.max` → None | B2, S15 |
| T14 | `__contains__` | start in; end out; before out | N1 inclusive cutoff, R2 |
| T15 | `whole_day` | equals `TimeRange(time.min, time.max)` | A3/A11 |
| Q1 | `ResourceRules` | defaults (0, 0, None); frozen, hashable | V1 defaults |
| Q2 | `ResourceRules` | buffer −1 µs, notice −1 µs, g 0, g −15 min → `InvalidAvailabilityRequest` naming setting and value; 0 buffer/notice accepted | V1, S13 |
| Q3 | `ResourceRules` | negative buffer + g 0 → buffer message (field order) | A6 |
| Q4 | `AsOf` | aware now → `InvalidAvailabilityRequest`; `day=datetime(...)` → `TypeError` | V1, A10 |
| Q5 | `AsOf.eligible_starts` | same day 08:00 + 2 h → from 10:00; + 90 min → from 09:30; prev 16:00 + 16 h → from 08:00; prev 20:00 + 48 h → None; now next day → None; far past → whole day; cutoff exactly `time.max` → None; `timedelta.max` → None, no error; `AsOf(date.max, datetime.max)` notice 0 → no error | N1, S11, S12, S15 |
| P6 | surface | `rules` and `as_of` are `KEYWORD_ONLY` with defaults `ResourceRules()` and `None`; three positional args work; `ResourceRules`/`AsOf` public members are their fields (+ `eligible_starts` on `AsOf`) | H4 |

### 9.4 New — product contract at `available_starts` (`test_available_starts.py`, rows B1–B22)

| # | Test | Covers |
|---|---|---|
| B1 | S1 exact list (the goals.md stage-2 anchor) | S1 |
| B2 | S2 exact list | S2 |
| B3 | explicit `rules=ResourceRules(), as_of=None` equals the three-argument call on C1–C14 inputs | S3 |
| B4 | no bookings, b 15, g 15 → last start 16:30 | S4 |
| B5 | three opening-edge inputs × {grid 15, no grid} | S5 |
| B6 | touching 10–11, 11–12 with b 15 → accepted, exact list, nothing in [10:00, 12:15); the b 60 pair → exact list | S6, B3 |
| B7 | true overlap with b 30 → `OverlappingBookingsError` with the raw pair | S7 |
| B8 | d 45 offered / d 60 not, against a run at 11:00 | S8 |
| B9 | booking 17:00–18:00, b 15 → 16:30 present | S9 |
| B10 | g 20; g 10 h; C1 with g 15 (09:45, 10:00, 10:15, 10:30 present); hours 09:10 with g 15 | S10, G1 |
| B11 | notice 2 h and 90 min; C1 no grid, now 09:50 → first 10:15 | S11 |
| B12 | the four cross-day rows | S12, A12 |
| B13 | notice > 0 without `as_of` → error; precedence: duration beats N2; N2 beats overlap; overlap beats past day | S13, A6 |
| B14 | now exactly at a start → kept; earlier dropped | S14 |
| B15 | `timedelta.max` for d, b, notice, g separately; booking ending 23:50 with b 30 in hours 20:00–`time.max` | S15, M1 |
| B16 | all permutations of S1's and S6's inputs with b > 0 → identical | S16 |
| B17 | booking straddling close 16:50–17:30, b 15 → last start 16:05 | §7.3 |
| B18 | buffer larger than a run-closed gap → that gap offers nothing; later spans unaffected | §7.3 |
| B19 | two pre-opening bookings clipping to the same start (b 2 h) → first start 10:30 | I2′ |
| B20 | d 60, g 15, no bookings → 29 starts (every grid point, not every d-th) | G1 |
| B21 | notice + grid → exactly the no-notice starts that are ≥ cutoff | N1 |
| B22 | generator of bookings with b > 0 | signature contract |

### 9.5 `test_invariants.py` — second seeded generator (`random.Random(20260924)`, ≈2 000 cases)

**Generation:** hours and bookings as in stage 1, plus a deliberate share of buffer-violating neighbours
(gaps shorter than b) and bookings just before opening and after closing; b ∈ {0, 1–90 min, occasionally
≥ the hours' length}; g ∈ {None, 1–90 min, sometimes with seconds}; `as_of` ∈ {None with notice 0; `now`
within ±1 day of `day` with notice 0–10 h}.

**Independent oracle** in integer microseconds (its own arithmetic, none of the package's):
`occ_i = [s_i, min(e_i + b, EOD)) ∩ H`; `fits(t)` ⇔ `H.start ≤ t`, `t + d ≤ H.end`, and
`[t, min(t + d + b, H.end))` meets no `occ_i`; `eligible(t)` ⇔ µs(day, t) ≥ µs(now) + notice (Python ints
cannot overflow).

**Properties:**
1. **Grid exactness (G1):** with g, `S == [t for t on H.start + k·g if fits(t) and eligible(t)]`.
2. **No grid, soundness:** every `s ∈ S₀` (same call without `as_of`) satisfies `fits`; ascending.
3. **No grid, alignment and completeness (R1 over spans):** each `s` is a span anchor (H.start or the end
   of an occupancy component, and free) or `s − d ∈ S₀`; every anchor `p` with `fits(p)` is in `S₀`, and
   `s + d ∈ S₀` whenever `fits(s + d)` and `s + d` lies in the same free gap.
4. **Notice only removes (N1):** `S == [t for t in S₀ if eligible(t)]`, grid and no grid.
5. **S3 reduction:** b 0, no grid, no `as_of` → stage-1 properties 1–7 hold, and the result equals the call
   with `rules=` omitted.
6. **C10/S16:** a reshuffle gives an identical `S`, including buffer-violating input.
7. **R3 with buffer:** adding a non-overlapping booking whose `[s, e+b)` misses H leaves `S` identical.
8. **Buffer monotonicity (grid only):** `S(b′) ⊆ S(b)` for `b′ > b`. Not claimed without a grid, where
   anchors legitimately move.
9. **Overlap generator with random b > 0:** raises with the same raw pair across shuffles and as with b 0;
   inputs with only buffer-level conflicts never raise (B3).

---

## 10. Build order — make the change easy, then make the easy change

Each step is its own commit; every §9.1 characterization test stays green, unedited, throughout.

0. **Refactor, no behaviour change.** Add `fitting_starts`; replace the R1 loop with
   `_aligned_starts` (R1 branch only); remove `leading`; migrate T8 → T8′. Rename `free_gaps` →
   `bookable_spans`.
1. **Buffer (B1–B3, M1).** Add `whole_day`, `extended`, `trimmed`; `DaySchedule(…, buffer)` with step 3
   widening and the trim in the walk; restate I2′. Add `rules.py` with `buffer`; `rules=` keyword.
2. **Granularity (G1).** `granularity` field and its V1 check; the G1 branch of `_aligned_starts`.
3. **Notice (N1, N2).** `__contains__`; `as_of.py`; `minimum_notice` field and its V1 check;
   `_eligible_starts`; `as_of=` keyword.

---

## 11. Result, open items and risks

**Result: met** against the design goal — each new rule has one owner (buffer → `DaySchedule`; granularity
→ `_aligned_starts`; notice → `AsOf.eligible_starts` applied by one filter, N2 → `_eligible_starts`; V1 at
construction); every stage-1 rule keeps its owner (R2's end-fit moved within `TimeRange`); default settings
reproduce stage 1 by structure, not by a special case; every signature is concrete stdlib Python 3.11.

Risks and notes:
1. **I2′ rests on a uniform buffer.** Per-booking buffers (a non-goal) would require the occupancy merge,
   in `DaySchedule.__init__` only.
2. **Unbounded output** (A5), widened by granularity.
3. **Offered starts may overlap each other's buffers** (A14) — they are alternatives for one booking.
4. **Past-day queries with `as_of` return `[]`** (A12) — literal decision 0004; worth telling the owner.
5. **`as_of.day` coherence with hours/bookings** is a caller contract (A13).
