# Stage 2: revised availability architecture (encapsulation axis)

Axis: **correct encapsulation**. Each rule has one enforced owner that cannot be forged. No
implementation type crosses the published seam. Callers tell objects what to do; they do not pull
state out to decide for them.

This document states only what changed against `DESIGN.md` (stage 1). Anything it does not mention
stays exactly as DESIGN.md states it.

Kind of change: **add-feature / adaptation**. Stage-1 behaviour is preserved bit-for-bit under default
settings. The work is done as a behaviour-preserving refactor first, then three behaviour-changing steps
(§9).

---

## 0. The resolution in five lines

1. **H1 Buffer.** `DaySchedule` stays the one owner of occupancy. It widens each booking to its
   occupancy (`TimeRange.extended_by`), clips it (R3), and **coalesces** the result (`TimeRange.joined`),
   so the stage-1 disjointness invariant holds again by construction. It then yields **bookable spans**
   instead of free gaps. A bookable span is a free gap shortened by the buffer when an occupancy block
   follows it, and not shortened when closing time follows it. A new booking fits (B2) **iff it lies
   inside a bookable span**. Neither the policies nor the entry ever see a buffer.
2. **H2 Slot policy.** There are two private policies, `_GapAligned` (R1) and `_GridAligned` (G1). Each
   says only *where a span's first candidate is* and *how to advance*. One shared loop, `_starts_in`,
   holds the fit test (`leading(duration)` inside a span). Neither policy contains a fit test.
3. **H3 Time model.** The date and the instant exist only in a new published value, `AsOf(day, now)`.
   `AsOf.remaining_day(notice)` converts them **once** into a time-of-day `TimeRange` of permitted
   starts, or `None` when the cutoff falls after the day. The core sees only `TimeRange` and `time`, as
   in stage 1.
4. **H4 Public seam.** The signature is
   `available_starts(working_hours, bookings, duration, *, rules=ResourceRules(), as_of=None)`.
   `ResourceRules` (buffer, minimum_notice, granularity) and `AsOf` are frozen value types. Each is
   validated in its own `__post_init__`, following the `TimeRange` grain. The one cross-object rule
   (notice > 0 needs `as_of`) belongs to the entry. Stage-1 calls are unchanged in source, results and
   errors.
5. **Every rule R1–R6 keeps its stage-1 owner.** The new rules B1–B3, G1, N1, N2, V1 and M1 each get
   exactly one owner (§4).

---

## 1. File tree (new / changed / unchanged)

```
availability/
  __init__.py      CHANGED   __all__ += "ResourceRules", "AsOf"
  errors.py        CHANGED   docstring only (InvalidAvailabilityRequest also covers V1/N2); no new type
  time_range.py    CHANGED   TimeRange gains 6 total members + __contains__; still the ONLY time-of-day arithmetic
  resource_rules.py NEW      ResourceRules (published): per-resource settings, V1 for buffer/notice/granularity
  as_of.py         NEW       AsOf (published): the query day + naive now; the ONLY date/instant arithmetic (N1 conversion)
  _day.py          CHANGED   DaySchedule(hours, bookings, buffer): occupancy (B1, M1 via TimeRange), coalescing (B3),
                             bookable_spans() (B2) replaces free_gaps()
  slots.py         CHANGED   available_starts gains keyword-only rules/as_of; _permitted_starts (N2),
                             _SlotPolicy/_GapAligned/_GridAligned (R1/G1), _starts_in (the one fit loop)
tests/
  test_time_range.py        CHANGED (rows added; T1–T10 untouched)
  test_available_starts.py  UNCHANGED (A1–A21 = stage-1 characterization, S3)
  test_query_values.py      NEW (ResourceRules, AsOf)
  test_stage2.py            NEW (S1–S16 at the entry seam)
  test_invariants.py        CHANGED (stage-1 generator untouched; stage-2 generator + oracle added)
  test_public_surface.py    CHANGED (P1, P2 re-pinned deliberately; P3 extended; P6 new)
```

The dependencies stay acyclic and point toward the stable leaf:

```
slots ──► _day ──► time_range ──► errors
  │ ├──► as_of ──────┘ ▲            ▲
  │ └──► resource_rules ────────────┤
  └────────────────────┴────────────┘
```

- `resource_rules` imports `errors` only. It does not need `TimeRange`.
- `as_of` imports `time_range` (it returns a `TimeRange`) and `errors`.
- `_day` imports `time_range` and `errors`. It does **not** import `resource_rules`: it receives the
  buffer as a `timedelta` (§3.4, ISP).
- `slots` imports all of the above. It is still the only importer of `_day`.
- No module imports an underscore-prefixed name from another module. This holds unchanged from stage 1.

---

## 2. The published seam (H4)

### 2.1 Signature

```python
def available_starts(
    working_hours: TimeRange,
    bookings: Iterable[TimeRange],
    duration: timedelta,
    *,
    rules: ResourceRules = ResourceRules(),
    as_of: AsOf | None = None,
) -> list[time]: ...
```

- **Stage-1 callers are unaffected.** The three positional parameters, their meaning, the result, the
  errors and the error precedence are all unchanged. `ResourceRules()` defaults to buffer 0, notice 0
  and no granularity, which is exactly stage 1 (V1's last line). Leaving out `as_of` means no notice
  filter.
- **The new parameters are keyword-only.** Adding them creates no positional connascence, so no future
  setting can shift an argument's meaning.
- **The default is a module-level `ResourceRules()` instance.** It is safe as a default because it is
  frozen and immutable. A `None` default with an `if rules is None` branch would give "stage-1 defaults"
  a second home. With the instance, the defaults live in one place: the field defaults of
  `ResourceRules`.
- **Everything on the seam is published.** The seam speaks only published types: `TimeRange`,
  `ResourceRules`, `AsOf`, `datetime.time/timedelta`, `collections.abc.Iterable`. `DaySchedule`,
  bookable spans as a concept, the policies and the permitted-starts window never appear in a public
  signature. P3 pins this.

### 2.2 `resource_rules.py`: `ResourceRules` (NEW, published)

```python
@dataclass(frozen=True, slots=True)
class ResourceRules:
    """One resource's stage-2 booking rules. The default instance means "no stage-2 rule" (stage 1).

    Invariant (established in __post_init__, the one construction path; frozen):
      buffer >= timedelta(0); minimum_notice >= timedelta(0);
      granularity is None or granularity > timedelta(0).
    """
    buffer: timedelta = timedelta(0)            # cleanup after every booking (B1, B2)
    minimum_notice: timedelta = timedelta(0)    # starts before now + notice are dropped (N1)
    granularity: timedelta | None = None        # grid step counted from working_hours.start (G1)

    def __post_init__(self) -> None:
        """Raises InvalidAvailabilityRequest, first failing check wins, in field order:
             1. buffer < 0          "buffer must not be negative, got -1 day, 23:45:00"
             2. minimum_notice < 0  "minimum notice must not be negative, got …"
             3. granularity <= 0    "granularity must be positive when given, got 0:00:00"
           No type guard (A7 grain): a non-timedelta field fails loudly on the first comparison
           (`15 < timedelta(0)` → TypeError). None is the only non-timedelta value accepted,
           and only for granularity."""
```

The public members are the three fields plus `==`/hash. The type has no methods. Its only rule is
validity, and each setting's *meaning* belongs to the one module that applies it:

| Setting | Module that applies it |
|---|---|
| buffer | `_day` |
| grid | `slots` |
| notice | `as_of` |

Putting behaviour here, for example `rules.occupancy_of(booking)`, would pull B1 out of the occupancy
owner and leak an internal concept onto a published type.

### 2.3 `as_of.py`: `AsOf` (NEW, published), and the conversion point (H3)

```python
@dataclass(frozen=True, slots=True)
class AsOf:
    """The query's calendar day and the moment of asking, both naive local (R6, decision 0004 §9).

    Invariant: type(day) is a date but not a datetime; now is a naive datetime.
    """
    day: date
    now: datetime

    def __post_init__(self) -> None:
        """Raises, in this order:
             TypeError                   day is a datetime, or not a date                  (A10)
             InvalidAvailabilityRequest  now.tzinfo is not None                             (V1)
               "now must be naive local time (no tzinfo), got 2026-09-23T08:00:00+02:00"
           `now` is not type-guarded (A7 grain): a date or str fails loudly at `.tzinfo`."""

    def remaining_day(self, notice: timedelta) -> TimeRange | None:
        """N1, the one conversion from date/instant to time-of-day. It is the part of `day` at which a
        start t satisfies datetime.combine(day, t) >= now + notice.

        Pre: none. It is total for every timedelta, including negative values and timedelta.max, and it
        never computes now + notice unless the sum is known to lie inside `day`.
        Algorithm (whole = TimeRange.whole_day(); first/last = combine(day, whole.start/.end)):
          if notice >  last  - now:  return None                  # cutoff after this day   → no start
          if notice <= first - now:  return whole                 # cutoff on an earlier day (or 00:00) → all
          return TimeRange.if_nonempty((now + notice).time(), whole.end)   # sum is in [first, last]
        Post: None, or a TimeRange R with R.start the cutoff time (inclusive) and R.end = end of day.
              A start exactly at the cutoff is permitted (`t in R` is start-inclusive).
        Differences of two datetimes always fit in a timedelta, so the guards cannot overflow."""
```

**Why the conversion lives here, and happens once.** `AsOf` owns `day` and `now`. Computing the cutoff
anywhere else would read both fields and decide outside the object (feature envy, Ask). The result is
expressed in the core's existing currency, a `TimeRange` of the day, so the core never sees a `date` or a
`datetime`.

"Cutoff on a later day" and "cutoff on an earlier day" both collapse into the returned window: `None` or
the whole day. Those cases therefore never reach the core as special cases.

`remaining_day` is public on a published type. This follows the stage-1 rule for `TimeRange` methods
(§3.2 of DESIGN.md): it is pure, total, fixed by a decided rule (N1), hides nothing that is likely to
change, and is pinned by P6.

### 2.4 Validation precedence (A6, amended; answers S13)

Nothing between the steps below can reorder them.

1. **Caller-side value construction, in the caller's own expression order.**
   - `TimeRange(...)`: type → tz → emptiness (stage 1).
   - `ResourceRules(...)`: buffer → notice → granularity.
   - `AsOf(...)`: day type → now tz.
   None of these can reach `available_starts` holding an invalid value.
2. **`available_starts`, statement 1:** `duration <= 0` (R5, stage-1 A6 unchanged).
3. **`available_starts`, statement 2:** notice > 0 and `as_of is None` (N2), raised by `_permitted_starts`.
4. **`available_starts`, statement 3:** R4 overlap, raised by `DaySchedule.__init__`. The reported pair
   is still the first adjacent overlapping pair in `(start, end)` order.

`[]` for "cutoff after the day" is returned only **after** step 4, so an overlapping calendar is still
reported even on a day already in the past.

---

## 3. Changed internals

### 3.1 `time_range.py`: `TimeRange` gains total members (CHANGED)

Every addition is pure and **total**: it has no precondition, and it raises nothing for any timedelta,
including zero, negative values and `timedelta.max`. Any length is compared against the available room
*before* anything is added, so no `OverflowError` is possible. A result that would be empty is `None`,
as in stage 1.

```python
    @classmethod
    def whole_day(cls) -> "TimeRange":
        """[00:00, end of day): the one home of the A3 end-of-day sentinel (time.max, exclusive).
        Used by AsOf (the day's window) and by extended_by's cap (M1)."""

    def __contains__(self, t: time) -> bool:
        """R2 for an instant: start <= t < end. Applies _require_wall_clock(t) (A4/A7 same errors)."""

    def joined(self, other: "TimeRange") -> "TimeRange | None":
        """The single range covering both, iff they overlap or touch (their union is one range):
        TimeRange(min(starts), max(ends)); else None. Symmetric. Used only by occupancy coalescing."""

    def extended_by(self, length: timedelta) -> "TimeRange":
        """B1/M1: [start, end + length), cut at the end of the day. Never None, never raises.
        Post: length <= 0 → self; length >= (end-of-day − end) → [start, time.max); else [start, end+length).
        The cut IS M1: a range cannot pass midnight (R6), so a buffer that would is cut, never wrapped."""

    def without_trailing(self, length: timedelta) -> "TimeRange | None":
        """[start, end − length): the part left when `length` is reserved at the end.
        Post: length <= 0 → self; length >= (end − start) → None; else [start, end − length)."""

    def after_leading(self, length: timedelta) -> "TimeRange | None":
        """The complement of leading(length): [start + length, end).
        Post: None when length <= 0 or length >= (end − start); else [start+length, end).
        (Returning None, not self, for length <= 0 is what lets every stepping loop terminate even if
        a caller bypassed validation, the same stance as leading.)"""

    def from_grid(self, origin: time, step: timedelta) -> "TimeRange | None":
        """G1 geometry: [p, end), where p is the first point origin + k·step (k ∈ ℕ₀) with p >= start.
        Pre: none. Applies _require_wall_clock(origin).
        Post: None when step <= 0, or when no such p lies before end. The arithmetic is
          delta = start − origin (as offsets); k = 0 if delta <= 0 else ceil(delta / step);
          jump = k·step (k = 1 whenever step >= delta, so the product never exceeds delta + step < 2 days);
          p = origin + jump only after checking jump < end − origin."""
```

Stage-1 members are unchanged: `start`, `end`, `if_nonempty`, `intersection`, `overlaps`, `leading`,
`__str__`. Stage 1's R1 loop used `if_nonempty(slot.end, gap.end)`. It now uses `after_leading`, which
gives the same value (§9 step 0a).

**Why these members are on the type, and public.** The stage-1 decision (DESIGN.md §3.2, decision 0003)
carries over unchanged. They are the type's own geometry. Written as free functions elsewhere, they would
be feature envy. Written as `_methods` called from sibling modules, they would be inappropriate intimacy.
They are total and fixed by rules (R2, R6, M1), and P2 pins the member set.

The only rule-bearing choice among them is the M1 cut in `extended_by`. It sits here because it *is* R6:
a day's range cannot pass midnight.

### 3.2 `_day.py`: `DaySchedule`, the one occupancy owner (CHANGED; answers H1)

```python
class DaySchedule:
    """One resource's day: working hours, the occupancy inside them, and where a new booking may lie.

    Invariant (established in __init__, the ONE construction path; no method assigns to self):
      I1 every block in _busy lies inside _hours
      I2 _busy is strictly ascending by start
      I3' consecutive blocks are separated by a non-empty free range (they neither overlap nor
          touch). This is strengthened from stage-1 I3 "non-overlapping, touching allowed". Stage-1
          outputs are unchanged, because touching busy ranges never produced a gap anyway.
      I4 every block is a valid, non-empty TimeRange
      I5 _buffer >= timedelta(0)  (trusted: its one producer is a validated ResourceRules;
          and extended_by/without_trailing are total even if it were not)
    """
    __slots__ = ("_hours", "_busy", "_buffer")

    def __init__(self, hours: TimeRange, bookings: Iterable[TimeRange], buffer: timedelta) -> None:
        """Steps, in this order (the order carries A1 and decision 0004 §2 and §5):
          1. ordered = sorted(bookings, key=lambda b: (b.start, b.end))                 # R4: service sorts
          2. first adjacent a.overlaps(b) → raise OverlappingBookingsError(a, b)          # R4/A1/B3: RAW bookings,
                                                                                         #   before buffers & clipping
          3. occupied = (b.extended_by(buffer) for b in ordered)                         # B1 (+ M1 via the type)
          4. clipped  = (c for o in occupied if (c := o.intersection(hours)) is not None) # R3, now on occupancy
          5. _busy    = _coalesced(clipped)                                               # B3: overlapping
                                                                                         #   occupancy is normal input
        Raises: OverlappingBookingsError only (stage 1, unchanged)."""

    def bookable_spans(self) -> Iterator[TimeRange]:
        """B2, the one owner of "a new booking fits". It yields the ranges within which a new booking
        [t, t+d) must lie wholly.
          cursor = _hours.start
          for block in _busy:
              gap = TimeRange.if_nonempty(cursor, block.start)        # None only for a block at opening
              if gap is not None and (span := gap.without_trailing(_buffer)) is not None:
                  yield span                                         # the new booking's buffer must end by block
              cursor = block.end
          tail = TimeRange.if_nonempty(cursor, _hours.end)
          if tail is not None:
              yield tail                                             # no reservation: buffer may run past close
        Post: spans are non-empty, strictly ascending, pairwise disjoint, each is inside one maximal
              free gap and starts at that gap's start. THEOREM (below): for d > 0, [t, t+d) satisfies
              B2 iff [t, t+d) ⊆ some span. Each call returns a fresh iterator."""

# module-private
def _coalesced(ranges: Iterable[TimeRange]) -> tuple[TimeRange, ...]:
    """Pre: ascending by start (steps 1+3+4 preserve the sort: extended_by keeps start, clipping
    takes max(start, hours.start)). Sweep: fold each range into the last block via joined(),
    else append. Post: I2, I3', union unchanged."""
```

**Theorem (why a span is exactly B2).** Take d > 0 and let `t` be a start with `[t, t+d) ⊆ H`.

- The part of the new booking's occupancy that counts under R3 is `F = [t, min(t+d+b, H.end))`. It is
  contiguous, it starts at `t`, and it must avoid every busy block. `t` is therefore in some maximal gap
  `g`, and since `g` is maximal, F avoids busy time iff `F ⊆ g`.
- If `g` ends at close (`g.end = H.end`): `F ⊆ g` iff `t + d ≤ H.end`. The span is `g` itself, so the
  condition is `[t, t+d) ⊆ span` (decision 0004 §3).
- If `g` ends at a busy block (`g.end < H.end`): `F ⊆ g` iff `t + d + b ≤ g.end` iff
  `[t, t+d) ⊆ [g.start, g.end − b)`, which is `g.without_trailing(b)` (decision 0004 §4).

With b = 0 every span equals its gap, which is exactly stage 1.

**Why coalescing, and why here.** Decision 0004 §5 makes overlapping occupancy normal input, which
breaks stage-1 I3. There are two places the breakage could go:

- Relax I3 and let the gap walk take "the later of cursor and block.end". That makes the core compare
  bounds, and it discards the stage-1 proof that the cursor never moves backwards.
- **Restore the invariant at the one construction path.** This design does that.

Merging here does *not* reintroduce the merging that decision 0002 forbids. That decision forbids
merging **bookings**, meaning silently accepting overlapping bookings. R4 has already run on the raw
bookings in step 2, and what is merged is busy time, where a union is the meaning.

### 3.3 `slots.py`: the entry, the policies, the one fit loop (CHANGED; answers H2)

```python
def available_starts(working_hours, bookings, duration, *, rules=ResourceRules(), as_of=None) -> list[time]:
    """Start times, earliest first, at which a booking of `duration` (and its buffer) fits (B2, R2, R3),
    aligned by the resource's slot policy (R1 or G1) and not earlier than as_of.now + notice (N1).
    Post (additions to stage 1):
      · every s: [s, s+d) ⊆ working_hours and [s, s+d+buffer) meets no occupancy inside working_hours;
      · granularity g: exactly the points hours.start + k·g that satisfy the line above and N1;
      · no granularity: stage-1 R1 over bookable spans (anchor = gap start, step = duration);
      · as_of given: every s has combine(day, s) >= now + notice; notice only removes starts.
    Raises: InvalidAvailabilityRequest (duration; notice without as_of), OverlappingBookingsError."""
    if duration <= timedelta(0):
        raise InvalidAvailabilityRequest(f"duration must be positive, got {duration}")   # R5
    permitted = _permitted_starts(rules.minimum_notice, as_of)                            # N2 (raises); N1
    day = DaySchedule(working_hours, bookings, rules.buffer)                              # R4, R3, B1, B3
    if permitted is None:                                                                 # cutoff after the day
        return []
    policy = _slot_policy(working_hours.start, duration, rules.granularity)              # R1 | G1
    return [start for span in day.bookable_spans()
                  for start in _starts_in(span, duration, policy)
                  if start in permitted]                                                  # N1 applied

# ---- module-private ---------------------------------------------------------------

def _permitted_starts(notice: timedelta, as_of: AsOf | None) -> TimeRange | None:
    """N2, the one owner. No as_of: notice > 0 → InvalidAvailabilityRequest("minimum notice is 2:00:00,
    so the query needs as_of=AsOf(day, now)"); else TimeRange.whole_day() (no filter).
    With as_of: as_of.remaining_day(notice) (N1's owner does the conversion)."""

class _SlotPolicy(Protocol):
    """Where candidate starts lie inside one bookable span. It never decides whether a slot fits."""
    def anchor(self, span: TimeRange) -> TimeRange | None: ...       # span from its first candidate on
    def advance(self, remaining: TimeRange) -> TimeRange | None: ... # remaining after its first candidate

class _GapAligned:                     # R1, the one owner (stage-1 _gap_aligned_starts' decision)
    def __init__(self, duration: timedelta) -> None: ...
    def anchor(self, span):  return span                             # each gap from its own start
    def advance(self, remaining): return remaining.after_leading(self._duration)   # back-to-back

class _GridAligned:                    # G1, the one owner (every grid point)
    def __init__(self, origin: time, step: timedelta) -> None: ...
    def anchor(self, span):  return span.from_grid(self._origin, self._step)
    def advance(self, remaining): return remaining.after_leading(self._step)

def _slot_policy(origin: time, duration: timedelta, granularity: timedelta | None) -> _SlotPolicy:
    """G1 optional + decision 0004 §8 (origin = working-hours start): the one place that chooses."""
    return _GapAligned(duration) if granularity is None else _GridAligned(origin, granularity)

def _starts_in(span: TimeRange, duration: timedelta, policy: _SlotPolicy) -> Iterator[time]:
    """The ONE fit loop, shared by both policies: a candidate is offered iff its slot fits the span.
      remaining = policy.anchor(span)
      while remaining is not None and (slot := remaining.leading(duration)) is not None:
          yield slot.start
          remaining = policy.advance(remaining)
    Stopping at the first misfit is complete: `remaining` only loses its head, so once
    leading(duration) fails no later candidate in this span can fit.
    Termination: advance() strictly shrinks `remaining`, or returns None, for every step, including one
    that is <= 0 (after_leading's contract). The loop cannot hang."""
```

**Why the notice filter is a filter, and why that is not the forbidden "trailing filter".** N1 says,
literally, that notice *removes* starts and never moves the grid or the gap anchors. A filter over the
starts is therefore the honest shape of that rule, and it has exactly one home: the comprehension's
`if start in permitted`. The rejected shortcut is a filter used for the **buffer**. That would re-derive
occupancy outside its owner.

The two tempting alternatives both give wrong results:

- **Notice as busy time `[00:00, cutoff)` inside `DaySchedule`.** This would move the gap anchor. S11's
  C1 case would offer 09:50 instead of 10:15.
- **Notice as an intersection with each span.** Same failure.

**Earliest first still needs no sort.** Spans are ascending and disjoint, and every start in a span lies
before `span.end`, which is at or before the next span's start. A filter keeps the order.

### 3.4 `errors.py` (docstring only) and `__init__.py`

```python
# __init__.py
from .errors import InvalidAvailabilityRequest, OverlappingBookingsError
from .time_range import TimeRange
from .resource_rules import ResourceRules
from .as_of import AsOf
from .slots import available_starts
__all__ = ["TimeRange", "ResourceRules", "AsOf", "available_starts",
           "InvalidAvailabilityRequest", "OverlappingBookingsError"]
```

Stage-2 use:

```python
available_starts(TimeRange(time(9), time(17)),
                 [TimeRange(time(9), time(9, 45)), TimeRange(time(11), time(12))],
                 timedelta(minutes=30),
                 rules=ResourceRules(buffer=timedelta(minutes=15), granularity=timedelta(minutes=15)))
# → [10:00, 10:15, 12:15, 12:30, …, 16:30]
```

---

## 4. Rule → owner (complete)

| Rule | Single owner | Why every path goes through it |
|---|---|---|
| R1 gap-aligned, back-to-back, leftover dropped (no-grid case) | `slots._GapAligned` (anchor = span start, advance = duration) | It is chosen only by `_slot_policy`. Its candidates are tested only by `_starts_in`. |
| R2 half-open; touching ≠ overlap | `time_range._nonempty` (stage 1). `__contains__` and `joined` use the same `<`/`<=` semantics inside the same file. | No bound comparison exists outside `time_range.py`. |
| R2 a slot may end exactly at its bound | `TimeRange.leading` (`<=`) | This is still the only "does it fit" test, now inside `_starts_in`. |
| R3 only the part inside the hours counts | `DaySchedule.__init__` step 4, now applied to **occupancy** | This is the only place where occupancy meets the hours. |
| R4 sort; reject overlaps naming the pair; touching fine | `DaySchedule.__init__` steps 1–2, on raw bookings | This is the single constructor. The check runs before `extended_by`, so buffers can never cause it to fire. |
| R5 range | `TimeRange.__post_init__` | Stage 1, unchanged. |
| R5 duration | `available_starts`, statement 1 | Stage 1, unchanged. |
| R5 no fit → `[]` | structural | Stage 1, plus N1's `None` guard. |
| R6 naive, one day | `TimeRange` (time-of-day), and `AsOf.__post_init__` for `now` | Date/instant values exist only inside `AsOf`. |
| **B1** booking occupies `[s, e+buffer)`; counts wherever it lies in the hours; never returned | `DaySchedule.__init__` step 3 (`extended_by`), then step 4 | Occupancy is computed once, before clipping, which is what makes decision 0004 §2 (the opening-edge buffer) hold. It lives in `_busy`, which is never returned. |
| **B2** new slot inside the hours; slot plus its buffer free of occupancy in the hours; buffer may pass close | `DaySchedule.bookable_spans` (reserve the buffer before a block, not before close), then `leading` in `_starts_in` | The theorem in §3.2. Policies only ever see spans. |
| **B3** buffer-violating bookings accepted; true overlaps still rejected | `DaySchedule.__init__`: step 2 (raw, unchanged) + step 5 (`_coalesced`) | Overlapping occupancy is folded in the constructor, so I3' holds for every consumer. |
| **G1** grid `hours.start + k·g`; every fitting point; optional | `slots._GridAligned` (policy) + `_slot_policy` (optional/origin) + `TimeRange.from_grid` (geometry) | Selection happens in one function, and the fit test in the one loop. |
| **N1** offered iff `combine(day,t) >= now + notice`; removes only | `AsOf.remaining_day` (the decision and the conversion), applied by the one `if start in permitted` | The core sees only the returned `TimeRange`. |
| **N2** `now` optional; notice > 0 without it → error; notice 0 with it → drop the past | `slots._permitted_starts` | This is the only place both settings are seen. The "drop the past" part falls out of N1 with notice 0. |
| **V1** negative buffer, negative notice, granularity ≤ 0 | `ResourceRules.__post_init__` | This is its only construction path. The type is the evidence. |
| **V1** aware `now` | `AsOf.__post_init__` | Same. |
| **V1** notice > 0 without `now` | `slots._permitted_starts` (= N2) | |
| **V1** defaults → exactly stage 1 | `ResourceRules` field defaults + `as_of=None` | There is one home for "the defaults". |
| **M1** a buffer past midnight is cut, never overflows | `TimeRange.extended_by` (cap at `whole_day().end`) | This is the only place a range is lengthened. |
| A3 end-of-day sentinel | `TimeRange.whole_day` | Used by `extended_by` and `AsOf`. It is no longer re-spelled as `time.max` anywhere else. |
| Earliest first | spans ascending and disjoint + loop ascending + order-preserving filter | By construction. |

---

## 5. Error vocabulary: delta

**No new error type.** Every new rejection is a caller bug that needs the same handling as the existing
ones: surface the message. A subtype per rule would be a dead subtype (DESIGN.md §3.1).

| Situation | Raised by | Type | Message (example) |
|---|---|---|---|
| negative buffer | `ResourceRules(...)` | `InvalidAvailabilityRequest` | `buffer must not be negative, got -1 day, 23:45:00` |
| negative notice | `ResourceRules(...)` | `InvalidAvailabilityRequest` | `minimum notice must not be negative, got …` |
| granularity 0 or negative | `ResourceRules(...)` | `InvalidAvailabilityRequest` | `granularity must be positive when given, got 0:00:00` |
| aware `now` | `AsOf(...)` | `InvalidAvailabilityRequest` | `now must be naive local time (no tzinfo), got …+02:00` |
| `day` is a `datetime` (or not a date) | `AsOf(...)` | `TypeError` (A10; not vocabulary) | `AsOf.day must be datetime.date (not datetime), got datetime.datetime` |
| notice > 0, no `as_of` | `available_starts` (`_permitted_starts`) | `InvalidAvailabilityRequest` | `minimum notice is 2:00:00, so the query needs as_of=AsOf(day, now)` |
| cutoff after the queried day | — | not an error: `[]` | — |

Rows unchanged from stage 1: invalid or aware range, `TypeError` for a non-`time` field, duration ≤ 0,
and `OverlappingBookingsError`. With a buffer set, the overlap error still names the **raw** pair.

---

## 6. Assumptions: delta to DESIGN.md §1.2

| # | Change | Lands in |
|---|---|---|
| A5 (extended) | There is no minimum granularity either. g = 1 µs over 8 h yields about 2.9·10¹⁰ grid candidates. Notice is applied as a filter, so the candidates it removes are still enumerated. The loops terminate; only the size is unbounded. | `ResourceRules.__post_init__`, if a floor is ever wanted |
| A6 (amended) | The precedence is as in §2.4. The notice-needs-now check sits between the duration check and the overlap check. | `available_starts` statement order |
| A7 (applied) | `ResourceRules` has no type guard: a wrong type fails loudly on the comparison. `AsOf.day` is guarded, see A10. | — |
| A10 (new) | `AsOf(day=<datetime>)` raises `TypeError`. `datetime` subclasses `date`, and `datetime.combine` would silently take its date part and drop the time. This is exactly the "silent acceptance" that A7 says earns a guard. | `AsOf.__post_init__` |
| A11 (new) | Occupancy that is cut at `time.max` does not cover the last µs before midnight, and a notice cutoff exactly at `time.max` permits nothing. Neither is observable: hours end at or before `time.max`, so every start is before `time.max`. | `TimeRange.whole_day` |

---

## 7. Trace of S1–S16

H = 09:00–17:00, d = 30 min, b = buffer, g = granularity, unless stated otherwise.

| Case | Path through the design | Result |
|---|---|---|
| S1 | R4 passes: 09:45 ≤ 11:00. Occupancy is 09:00–10:00 and 11:00–12:15, both inside H and apart, so coalescing changes nothing. Spans: the first gap `if_nonempty(09:00,09:00)` gives None. The gap 10:00–11:00 has 15 reserved, giving span **10:00–10:45**. The tail span is **12:15–17:00**. `_GridAligned(09:00, 15)`: span 1 `from_grid` → 10:00–10:45. `leading(30)` fits, so 10:00 is offered. `after_leading(15)` → 10:15–10:45 fits, so 10:15. Next is 10:30–10:45 < 30, so stop. Span 2: `from_grid` → 12:15 (on the grid). Starts step by 15 up to 16:30. At 16:45 the 15 minutes left are < 30, so stop. `as_of` is None, so the whole day is permitted. | `10:00, 10:15, 12:15 … 16:30` (18 after 12:00) ✓ |
| S2 | The spans are the same as S1. `_GapAligned(30)`: span 1 offers 10:00. `after_leading(30)` → 10:30–10:45 is too short. Span 2 offers 12:15, 12:45, …, 16:15. At 16:45, 15 min < 30. | `10:00, 12:15, 12:45, …, 16:15` ✓ |
| S3 | Defaults: `extended_by(0)` returns self. Coalescing merges only touching bookings, since overlapping ones were rejected in step 2. The spans are then exactly the stage-1 free gaps, because touching blocks never produced a gap and `without_trailing(0)` returns self. `_GapAligned.advance` = `after_leading(d)`, which gives the same value as stage 1's `if_nonempty(slot.end, gap.end)`. The permitted window is the whole day, and every start is before `time.max`. Errors and precedence are unchanged (N2 cannot fire with notice 0). C1–C14 re-trace to DESIGN.md §7 value for value. | bit-for-bit ✓ |
| S4 | No blocks. The tail span is H (no reservation before close). The grid runs 09:00 … 16:30: at 16:30, `leading(30)` gives exactly 16:30–17:00 ✓ (`<=`). The buffer to 17:15 is never looked at. | last start 16:30 ✓ |
| S5 | (a) 08:00–09:00 +15 → 08:00–09:15, clipped to 09:00–09:15. The span starts at 09:15. Grid: `from_grid(09:00, 15)` on 09:15–… → 09:15. Gap-aligned: 09:15. (b) 08:00–08:50 → 08:00–09:05, clipped to 09:00–09:05. The span starts at 09:05. Grid → 09:15. Gap-aligned → 09:05. (c) 07:00–08:00 → 07:00–08:15, whose intersection with H is None, so it is dropped. | 09:15/09:15; 09:15/09:05; no effect ✓ |
| S6 | 10:00–11:00 and 11:00–12:00 only touch, so R4 passes. Occupancy is 10:00–11:15 and 11:00–12:15. `joined` → **10:00–12:15**: one block, I3' holds. Spans: 09:00–09:45 (reserve 15 before 10:00) and 12:15–17:00. Nothing starts in [10:00, 12:15). With b = 60: 10:00–10:30 → 10:00–11:30, and 10:45–11:00 → 10:45–12:00. Joined → 10:00–12:00. Every gap is built by `if_nonempty` over a strictly ascending, strictly apart `_busy`, so no gap is negative or duplicated and the cursor only moves forward. | accepted; correct gaps ✓ |
| S7 | Step 2 runs on the raw bookings before `extended_by`, so a true overlap raises `OverlappingBookingsError(raw a, raw b)` whatever the buffer. Touching bookings behave as in S6. | ✓ |
| S8 | A block ends 10:00 and the next begins 11:00, so the gap is 10:00–11:00 and the span is 10:00–10:45. d = 45: `leading(45)`: 45 ≤ 45, so 10:00 is offered and the buffer ends exactly at 11:00 (touching). d = 60: 60 > 45 gives None, so nothing is offered, even though 10:00–11:00 fits inside the gap. | ✓ |
| S9 | 17:00–18:00 +15 → 17:00–18:15, whose intersection with H is None, so it is dropped. The tail span is H and 16:30 fits. | 16:30 offered ✓ |
| S10 | g = 20: the grid gives 09:00, 09:20, …, 16:20. At 16:40, 20 min < 30. g = 10 h: `from_grid` → 09:00–17:00, 09:00 is offered, and `after_leading(10 h)` → None. C1 bookings, b = 0, g = 15: the spans are 09:45–11:00 and 12:00–17:00, giving 09:45, 10:00, 10:15, 10:30 (10:30–11:00 fits), then 12:00 … 16:30. Hours 09:10–17:00: the origin is `working_hours.start` = 09:10, so the grid is 09:10, 09:25, …. | ✓ |
| S11 | No bookings, g = 15, now = day 08:00, notice 2 h. `remaining_day`: 2 h ≤ last − now (≈ 16 h), and 2 h > first − now (−8 h), so the window is `[10:00, end of day)`. 09:45 fails the `in` check and 10:00 passes (the start is inclusive). With notice 90 min the window starts at 09:30. The gap-aligned C1 case with now = 09:50, notice 0: the candidates are still 09:45, 10:15, 12:00, …, because the anchors are untouched. The filter drops 09:45. | 10:00 yes, 09:45 no; cutoff 09:30; first start 10:15 ✓ |
| S12 | now = previous day 20:00, notice 48 h: last − now ≈ 28 h < 48 h → None. `DaySchedule` is still built (R4 is checked), then `[]`. now = previous day 16:00, notice 16 h: first − now = 8 h < 16 h ≤ last − now, so the cutoff is `(now+16h).time()` = 08:00 and the window 08:00–end admits every start. now on the next day: last − now < 0 ≤ notice → None → `[]`. now = day 16:40, notice 0: window 16:40–end. The last candidate is 16:30, which is filtered out. | `[]`; no effect; `[]`; `[]` ✓ |
| S13 | Negative buffer, negative notice, g = 0 and g < 0: `ResourceRules.__post_init__`, first failure in field order. Aware now: `AsOf.__post_init__`. Notice > 0 without now: `_permitted_starts` (statement 2). Precedence as in §2.4, for example duration 0 plus notice without now gives the duration error, and notice without now plus overlapping bookings gives the notice error. | each a clear error; deterministic ✓ |
| S14 | now = day 10:00, notice 0: window `[10:00, …)`. 09:00 and 09:30 are dropped, 10:00 is kept (`start <= t`). | ✓ |
| S15 | d = `timedelta.max`: `leading` compares before adding and returns None, so `[]`. b = `timedelta.max`: `extended_by` compares with the room left before midnight and caps at `time.max`; `without_trailing(max)` → None, so only the tail span can offer. notice = `timedelta.max`: `remaining_day` checks `notice > last − now` first and never computes `now + notice`, so `[]`. A booking ending 23:50 with b = 30 is capped at `time.max` (M1). g = `timedelta.max`: `from_grid` uses k ∈ {0, 1} and a checked jump; `after_leading` returns None. No `OverflowError`, and every loop strictly shrinks. | ✓ |
| S16 | Everything downstream of `sorted(key=(start,end))` is a function of the sorted tuple. Coalescing computes a union, which does not depend on order. The reported R4 pair is still the first adjacent pair after sorting. The buffer-violating input of S6 gives the same block in every permutation. | identical ✓ |

**X × R re-trace, beyond the cases listed:**
- **Buffer × R4.** Buffers never cause a rejection. Duplicate and nested bookings are still rejected
  (A2), and step 2 runs before step 3.
- **Buffer × R3.** An occupancy that starts before opening and reaches into H counts (decision §2).
  Occupancy after close is dropped.
- **Buffer × R1.** Anchors are occupancy ends: in S2 the anchor is 12:15, not 12:00.
- **Buffer × R2.** A new slot's buffer may touch the next block (S8, d = 45).
- **Buffer × C10.** Covered by S16.
- **Buffer × M1.** Covered by S15.
- **Two pre-opening bookings whose buffers clip to the same start.** For example 07:00–08:00 and
  08:00–08:30 with b = 2 h clip to 09:00–10:00 and 09:00–10:30. `joined` merges them into 09:00–10:30,
  and I2 is restored.
- **Grid × R3/B1.** The grid ignores gap anchors. The origin is always `hours.start`, even when H starts
  at second precision.
- **Grid × duration.** Any relation works: g < d, g = d or g > d.
- **Notice × grid and notice × gap anchors.** Notice only removes starts (S11).
- **Notice × R4.** Validation still runs when the answer is `[]`.
- **Notice × a far-future or far-past day, including `date.max` and `datetime.min`.** Only differences
  are computed, never sums outside the day.
- **Every new setting × a generator of bookings.** The bookings are consumed once, by `sorted`.

---

## 8. Design reasoning

### 8.1 How H1–H4 were resolved, and the present force behind each element

- **H1.** The one owner of "a buffer is busy time" is `DaySchedule`. It owns the occupancy of existing
  bookings (B1) *and* where a new booking's own occupancy may lie (B2, via `bookable_spans`). Both
  halves of the buffer rule meet in one class, and no policy, filter or entry line can re-derive either
  half. The asymmetry (a slot must stay inside the hours, but its buffer may run past close) comes out
  as exactly one difference inside the walk: a span is shortened by the buffer before an occupancy
  block, and not before close. The broken invariant I3 is repaired where it is established (step 5),
  not tolerated downstream.
- **H2.** A policy is now a seam, because the stage-1 falsifier is met: a second real policy exists. The
  seam is **module-private**, since neither policy is a caller's concern. Its interface is deliberately
  weaker than "produce the starts": it has only `anchor` and `advance`. That makes it impossible for a
  policy to decide a fit, because only `_starts_in` calls `leading`. R1's stage-1 decision (each gap
  from its own start, back to back) moves unchanged into `_GapAligned`.
- **H3.** There is one conversion point, `AsOf.remaining_day`. It is total and overflow-proof, and the
  core sees a `TimeRange`. The alternative of a `datetime` core would change the stage-1 time model
  everywhere. The alternative of passing `day`, `now` and `notice` into the core would put date
  arithmetic in two places.
- **H4.** Two published value types sit at the seam, each validated by its constructor as `TimeRange`
  is (the grain), and the new parameters are keyword-only with stage-1 defaults. There is one owner per
  validation rule: `ResourceRules` holds three V1 rules, `AsOf` holds one, and the entry holds the
  cross-object N2 rule.

### 8.2 Alternatives rejected

- **Buffer as a trailing filter over candidate starts.** This creates a second owner of occupancy. It
  would have to re-read the bookings, re-add the buffer and re-apply R3, all outside `DaySchedule`.
- **Buffer as a synthetic booking.** This is a concept cram, ruled out by decision 0004. S6's
  touching-with-buffer input would also trip R4, which is observably wrong.
- **Relaxing I3 and using a "later of" cursor in the gap walk.** This puts bound comparisons in the core
  and gives up the "cursor never moves backwards" proof.
- **A `fits(slot)` query on `DaySchedule` called per candidate.** This is Ask-style. It costs O(n) per
  candidate, and the gap-aligned policy would still need the gaps, so there would be two concepts
  answering one question.
- **Passing the duration into `DaySchedule` so that spans are "fit-ready".** It is not needed: spans do
  not depend on d. It would also make occupancy a function of the request.
- **Fit logic inside each policy (a `starts(span)` method per policy).** This is H2's explicit trap: B2
  would be re-implemented once per policy.
- **A public `SlotPolicy`.** No caller chooses a policy. The resource's granularity does, so publishing
  it would leak an internal decision.
- **Notice as busy time `[00:00, cutoff)`, or as an intersection with each span.** Both move the anchors
  (S11 would give 09:50).
- **A long primitive list** such as `available_starts(..., buffer=, notice=, granularity=, day=, now=)`.
  It is a data clump. V1 would land inside the entry, and `day` without `now` would be representable.
- **`now` only, with the day inferred as `now.date()`.** S12 queries a day other than today.
- **An `AsOf` carrying the notice.** Notice is a per-resource setting (brief), not a property of the
  query.
- **`rules: ResourceRules | None = None`.** It creates a second home for "the defaults".
- **Conversion as a free function reading `as_of.day` and `as_of.now`.** This is feature envy.
- **An `_as_of_window()` underscore method called from `slots`.** This is inappropriate intimacy (the
  stage-1 stance).
- **One error subtype per V1 rule.** Nobody catches them differently.
- **`AsOf` placed in `time_range.py`.** A date/instant is a different kind of time with a different
  reason to change (the clock). The one fact the two share, the end of day, is owned by
  `TimeRange.whole_day`.

### 8.3 Supersessions (to record; §10)

- **DESIGN.md §8.3, "A `SlotPolicy` Protocol or Strategy" rejected.** Superseded by its own falsifier: a
  second policy now exists. The seam is module-private.
- **DESIGN.md §3.3 I3 "touching allowed".** Strengthened to I3', "strictly apart", established by
  coalescing. The observable result is unchanged.
- **DESIGN.md §3.3 `free_gaps`.** Replaced by `bookable_spans`, which is identical when the buffer is 0.
- **A6.** Amended precedence (§2.4).
- **Decision 0002 §1** was already superseded in part by decision 0004. R1 is now the no-grid case.

### 8.4 Principles that do not apply

- **add-feature §8 migration.** Nothing is persisted. The one exposed-shape change (the signature) is
  additive, with defaults, so old and new callers coexist without a transition.
- **Ports & adapters, concurrency, security, performance.** These stay out of scope, as in DESIGN.md
  §8.4. A5 records the unbounded output.
- **Grain.** Every new structure copies an existing pattern:
  - value types validated in `__post_init__`, as `TimeRange` is;
  - total `TimeRange` methods that return `None` for an empty result;
  - module-private helpers in `slots.py`;
  - one package-private class for occupancy.

  No foreign style is imported.

### 8.5 Subtractive pass, on what was added or changed

| Element | Present force | Verdict |
|---|---|---|
| `ResourceRules` | V1 (three rules); the per-resource settings as one validated value; removes a primitive clump from the seam | keep |
| `AsOf` | N1's conversion point; tz-naive `now` (V1); `day` ≠ `now.date()` (S12) | keep |
| `AsOf.remaining_day` | N1 (one conversion, overflow-proof) | keep |
| `TimeRange.whole_day` | one home for A3/M1's end of day (used by `extended_by`, `AsOf` and `_permitted_starts`) | keep |
| `TimeRange.__contains__` | applies N1's window; keeps the `<=` comparison inside `time_range.py` | keep |
| `TimeRange.joined` | B3 coalescing → I3' | keep |
| `TimeRange.extended_by` | B1, M1 | keep |
| `TimeRange.without_trailing` | B2 (reserving the new booking's buffer) | keep |
| `TimeRange.after_leading` | the grid step (G1); also replaces the stage-1 loop's `if_nonempty` so that both policies advance the same way | keep |
| `TimeRange.from_grid` | G1 origin and alignment arithmetic, which must stay in the time-of-day file | keep |
| `DaySchedule._buffer` and the `buffer` parameter | B2 in `bookable_spans` | keep |
| `_coalesced` | B3 / I3' | keep |
| `_SlotPolicy` Protocol | documents the two-method seam, so a policy has no path to `leading` | keep (typing only, zero runtime) |
| `_GapAligned`, `_GridAligned` | R1 and G1, which change for different reasons | keep |
| `_slot_policy` | G1 optional + decision 0004 §8 origin, in one place | keep |
| `_starts_in` | the one fit loop (H2) | keep |
| `_permitted_starts` | N2 | keep |
| a `Grid` value type | its rule is G1 geometry, which already has a home (`from_grid`), and it would have one consumer | **cut** |
| a `BookableSpan` type (a subclass or wrapper of `TimeRange`) | no rule of its own; the concept is carried by the producer (`bookable_spans`) | **cut** (the stage-1 `_FreeGap` reasoning) |
| a `now: datetime | None` field on `ResourceRules` | `now` is not a property of the resource | **cut** |
| an `if permitted is None` branch inside the comprehension | the guard clause does it once | **cut** |
| a public `free_gaps` kept alongside the spans | no consumer | **cut** (renamed) |

### 8.6 Concept-fit pass, on each new concept

- **Buffer.** A length (`timedelta`) that is a setting of the resource. It enters the model only as
  occupancy and as a span reservation. It is never a booking and never a range standing on its own.
- **Occupancy.** A transient `TimeRange` (booking extended by the buffer), folded into `_busy`. `_busy`
  was named for occupancy in stage 1 precisely so that this would fit.
- **Bookable span.** It is **not** free time: the last `b` minutes before a block are free but cannot be
  booked into. It is modelled as what it is, the range a new booking may cover, and it is produced by
  the occupancy owner. It is not a free gap with a flag.
- **Grid.** An alignment policy (`_GridAligned`), not a filter over fixed slots and not a score. Its
  geometry lives on the range.
- **Notice cutoff.** A filter on starts, because that is the rule's literal nature. It is represented
  as a window of permitted starts (`TimeRange`), not as busy time and not as a moved anchor.
- **Query context (`AsOf`).** A value: the day, and the moment the question is asked. It is not a clock
  service, since nothing reads the wall clock (the function stays pure).
- **Resource settings (`ResourceRules`).** A validated value with no behaviour. Each setting's meaning
  lives with the module that applies it.
- **"Nothing permitted today".** Represented as `None`, which becomes `[]`. It is never a zero-length
  window stand-in and never an error.

No inert stand-ins.

---

## 9. Build order: make the change easy, then make the easy change

Each step is a separate commit, and every stage-1 test stays green throughout.

- **Step 0: refactor only, no behaviour change. Tests: stage-1 suite unchanged, plus new T-rows.**
  - 0a: Add `after_leading` and `joined`. The R1 loop advances with `after_leading(d)`.
  - 0b: `DaySchedule` coalesces with `joined`, I3 becomes I3', and `free_gaps` is renamed
    `bookable_spans`. There is no buffer yet, so the spans equal the gaps.
  - 0c: Introduce `_SlotPolicy`, `_GapAligned` and `_starts_in`, replacing `_gap_aligned_starts`.
- **Step 1: buffer (B1–B3, M1).**
  - Add `whole_day`, `extended_by` and `without_trailing`.
  - Add `ResourceRules` with the `buffer` field only, and its V1 check.
  - Add the `DaySchedule` buffer steps and the `rules=` keyword.
- **Step 2: granularity (G1).** Add `from_grid`, `_GridAligned`, `_slot_policy`, the `granularity`
  field and its V1 check.
- **Step 3: notice (N1, N2).**
  - Add `__contains__`, `AsOf` and `remaining_day`.
  - Add the `minimum_notice` field and its V1 check.
  - Add `_permitted_starts` and the `as_of=` keyword.

---

## 10. Test plan: delta against DESIGN.md §10 (test-first, `unittest`, no mocks)

### 10.1 Kept unchanged, as characterization (S3)

- **`test_available_starts.py` A1–A21: every row, untouched.** They call with three positional
  arguments, so they exercise the defaults path. This is the S3 guarantee: they must pass unedited
  after every step in §9.
- **`test_time_range.py` T1–T10.**
- **`test_invariants.py`: the stage-1 generator and properties 1–7.**
- **`test_public_surface.py` P4 and P5.**

### 10.2 Changed, and why

- **P1.** `__all__` is now exactly the 6 names in §3.4. This is a deliberate growth of the surface.
- **P2.** The public `TimeRange` members are exactly:
  `{start, end, if_nonempty, whole_day, intersection, overlaps, joined, leading, after_leading, without_trailing, extended_by, from_grid}`,
  plus `__contains__` asserted explicitly. This is deliberate: the growth is reviewed through this test.
- **P3.** `get_type_hints` of `available_starts`, `ResourceRules`, `AsOf` and `AsOf.remaining_day`
  resolve only to `datetime`/`date`/`time`/`timedelta`, builtins, `collections.abc`, `TimeRange`,
  `ResourceRules`, `AsOf` or the error types. No `_day` or `slots` private type appears.

### 10.3 New: `test_time_range.py` rows (the published geometry)

| # | Test | Pins |
|---|---|---|
| T11 | `extended_by`: +15 gives the end +15. 0 and negative → self. A booking ending 23:50 extended by 30 → end `time.max`. `timedelta.max` → end `time.max`, no `OverflowError`. | B1, M1, S15 |
| T12 | `without_trailing`: 15 off a 60 → 45. Exactly the length → None. More → None. 0 or negative → self. `timedelta.max` → None. | B2 |
| T13 | `after_leading`: equals `if_nonempty(start+l, end)` for 0 < l < length. `l = length` → None. 0 and negative → None. `timedelta.max` → None. | loop totality, grid |
| T14 | `joined`: overlap → hull; touching → hull; apart → None; nested → outer; symmetric | B3 |
| T15 | `from_grid`: start on the grid → self. Off-grid start 09:05 with origin 09:00, step 15 → 09:15. The next point at or past the end → None. Step > span → only if the origin is inside. Step 0 or negative → None. `timedelta.max` → no overflow. An origin with seconds (09:10:30) → exact. | G1, S10, S15 |
| T16 | `__contains__`: start in, end out, before out; an aware time raises `InvalidAvailabilityRequest` | N1 inclusivity, R2 |
| T17 | `whole_day()` equals `TimeRange(time.min, time.max)` | A3/A11 |

### 10.4 New: `test_query_values.py` (the published settings)

| # | Test | Pins |
|---|---|---|
| Q1 | `ResourceRules()` has buffer 0, notice 0 and granularity None; it is frozen and hashable | V1 defaults |
| Q2 | a negative buffer, a negative notice, granularity 0 and granularity −15 each raise `InvalidAvailabilityRequest` with the value in the message; buffer 0 and notice 0 are accepted | V1, S13 |
| Q3 | a negative buffer together with granularity 0 → the buffer message (field-order precedence) | S13 |
| Q4 | `AsOf` with an aware `now` → `InvalidAvailabilityRequest`; `day=datetime(...)` → `TypeError` | V1, A10 |
| Q5 | `remaining_day` rows: same day 08:00 + 2 h → `[10:00, …)`. Previous day 16:00 + 16 h → `[08:00, …)`. Previous day 20:00 + 48 h → None. `now` on the next day → None. A cutoff before the day → `whole_day()`. `timedelta.max` → None, no `OverflowError`. `date.max` and `date.min` days → no error. A negative lead → total. | N1, S11, S12, S15 |

### 10.5 New: `test_stage2.py` (the product contract at `available_starts`)

| # | Test | Covers |
|---|---|---|
| U1 | the exact S1 list (the stage-2 anchor from goals.md) | S1, G1, B1, B2 |
| U2 | the exact S2 list | S2, R1 × buffer |
| U3 | explicit `rules=ResourceRules()`, `as_of=None` equals the three-argument call on the C1 to C14 inputs | S3, V1 defaults |
| U4 | no bookings, b 15, g 15 → last start 16:30 | S4 |
| U5 | the three opening-edge inputs × grid/no-grid | S5 |
| U6 | touching bookings with b 15 are accepted, with no start in [10:00, 12:15); the b 60 overlapping-occupancy input; output ascending with no duplicates | S6, B3 |
| U7 | a true overlap with b 30 → `OverlappingBookingsError` whose `.first`/`.second` are the **raw** ranges | S7 |
| U8 | d 45 offered and d 60 not, against a block at 11:00 | S8 |
| U9 | a booking 17:00–18:00 with b 15 → 16:30 offered | S9 |
| U10 | g 20; g 10 h; C1 with g 15 (09:45, 10:00, 10:15, 10:30 present); hours 09:10 with g 15 | S10 |
| U11 | notice 2 h and 90 min; the gap-aligned C1 case with now 09:50 → first 10:15 | S11, N1 anchors |
| U12 | the four across-days rows | S12 |
| U13 | notice without `as_of` → error. Precedence pairs: duration beats N2; N2 beats overlap; N2 and an aware `now` cannot co-occur, because `AsOf` rejects first. | S13, A6 |
| U14 | now 10:00 with notice 0 → 10:00 kept, 09:30 dropped | S14, N2 |
| U15 | `timedelta.max` for duration, buffer, notice and granularity, and a booking 23:50 with b 30 → no exception, with the expected result | S15, M1 |
| U16 | permutations of the S1 and S6 inputs with b > 0 → identical | S16 |
| U17 | a cutoff after the day with overlapping bookings → still `OverlappingBookingsError` | §2.4, validation before `[]` |
| U18 | two pre-opening bookings whose buffers clip to the same start → correct first start | coalescing edge |

### 10.6 `test_invariants.py`: extended with a second seeded generator (`random.Random(20260924)`, about 2 000 cases)

**Generation.**
- Hours and bookings as in stage 1, but some bookings are placed with gaps shorter than the buffer
  (buffer-violating input).
- Buffer: 0, or 1–90 min, and occasionally at least the length of H.
- Granularity: None, or 1–90 min, sometimes with seconds.
- `as_of`: None (with notice 0), or `now` within ±1 day of `day` with a notice of 0–10 h.

**Independent oracle.** It uses integer µs offsets with its own arithmetic and none of the package's:
- `occ_i = [s_i, min(e_i + b, EOD)) ∩ H`.
- `fits(t)` holds iff `H.start ≤ t`, `t + d ≤ H.end`, and `[t, min(t + d + b, H.end))` meets no
  `occ_i`.
- `permitted(t)` holds iff the µs-since-epoch of `(day, t)` is ≥ that of `now` + notice. Python
  integers make overflow impossible.

**Properties.**
- **G (grid, exact).** `S == [t for t in grid points of H if fits(t) and permitted(t)]`. This is
  complete and sound in one assertion.
- **B (no grid).** Take `S₀` as the same call without `as_of`.
  - Soundness: `fits` for every element.
  - Order.
  - Alignment: each `s` is an anchor, meaning `H.start` or an `occ` block's end, not covered, or else
    `s − d ∈ S₀`.
  - Completeness: every free anchor `p` with `fits(p)` is in `S₀`, and `s + d` is in `S₀` whenever
    `fits(s + d)` and `s + d` is in the same gap.
- **N (notice only removes).** `S == [t for t in S₀ if permitted(t)]`, for both grid and no-grid.
- **C10.** A shuffle gives an identical `S`.
- **R3 (restricted).** Adding a booking whose *occupancy* stays wholly outside H, and which overlaps no
  booking, gives an identical `S`.
- **S3 metamorphic.** When b = 0, no grid and `as_of` is None, the result equals the stage-1
  generator's property set. It is also asserted equal to the result with `rules=` omitted.
- **Overlap generator.** Rerun with a random buffer. It must raise the same raw pair across shuffles.

No coverage percentages. Every row pins a decision someone could get wrong.

---

## 11. Records the Guide should write

These are not created here.

- **`decisions/0005-stage2-architecture.md`.**
  - Record H1–H4 as resolved in §0.
  - Record the supersessions in §8.3: SlotPolicy is now a private seam; I3 becomes I3'; `free_gaps`
    becomes `bookable_spans`; A6 is amended.
  - Record A10 and A11 as new, A5 as extended, and the rejected alternatives in §8.2.
- **`architecture.md`.**
  - Seams: add `ResourceRules` and `AsOf` to the published seam.
  - Invariants: coalesced busy (I3'); the date/instant exists only in `AsOf`, and the core is
    time-of-day only.
  - Change axes: "slot policy → a private `_SlotPolicy` implementation in `slots.py`"; "occupancy →
    `DaySchedule.__init__`" (unchanged); "time model → `time_range.py` and `as_of.py`, plus the entry
    signature".
- **`goals.md`.** The "Non-goals (stage 1)" list still names buffers. That line should now read as
  stage 1 only.

---

## 12. Result

**met.**
- Every stage-1 rule keeps its stage-1 owner.
- Each of the new rules B1–B3, G1, N1, N2, V1 and M1 has one owner (§4).
- The stage-1 path is preserved bit-for-bit under the defaults, and the stage-1 tests run unedited.
- No internal type crosses the seam (P3).
- S1–S16 are traced (§7).
- Every signature is concrete Python 3.11 stdlib.

## 13. New facts and risks

1. **`datetime` is a `date`.** `AsOf(day=datetime(...))` would be silently accepted by `combine`,
   losing the time. The guard is A10. Without it, S12-style queries built from a `now` value would pass
   type checks and still be wrong.
2. **`now + notice` overflows `datetime` for large notices, even for realistic dates** (for example
   `timedelta.max`). This is resolved by comparing differences first (§2.3). A naive
   `combine(day, t) >= now + notice` implementation would crash in S15.
3. **Offered starts may overlap each other's buffers.** This happens under both policies, for example
   in S2, where 12:15 and 12:45 are offered with a 15-minute buffer. The starts are alternatives, not
   simultaneous bookings, so this is consistent with decision 0004. A UI that books several of them in
   one go would need the buffer re-checked per booking. That is outside this package, but worth telling
   the product owner.
4. **The output bound (A5) widens with granularity.** Notice is a filter, so on a late `now` the loop
   still enumerates the removed candidates. This is correct but not optimal. A future cap or floor lands
   in `ResourceRules.__post_init__` / `available_starts`.
5. **No product question remains open** for the stated rules. A11, the unobservable last µs, is recorded
   for completeness only.
