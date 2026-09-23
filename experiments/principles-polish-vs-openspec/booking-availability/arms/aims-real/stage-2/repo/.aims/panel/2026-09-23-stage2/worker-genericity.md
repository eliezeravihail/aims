# Stage 2: revised availability architecture (genericity worker)

Axis: **correct genericity**. Each abstraction is set from both ends. The floor is what its consumer
needs to be complete. The ceiling is what every producer can honestly supply. The known change axes are
absorbed and nothing beyond them is built. This file is self-contained for what changed. Anything it
does not restate stays exactly as DESIGN.md says.

Kind of change: **add-feature / adaptation.** There is one behavior-preserving refactor step (§0.2)
before the behavior-changing step.

---

## 0. Summary of the change

### 0.1 The central observation (it drives H1 and H2)

The three new rules are three different kinds of thing. Each goes to the owner whose kind it matches:

| New rule | What kind of thing it is | Owner it goes to |
|---|---|---|
| Buffer (B1–B3, M1) | **occupancy**: when the resource is busy, and how much free room a new booking needs | `DaySchedule`. Stage 1 already named this the occupancy owner (architecture.md, "Occupancy → `DaySchedule.__init__` only"). |
| Granularity (G1) | **alignment**: which candidate points are tried inside a room where a slot fits | the slot-alignment policy in `slots.py`. Stage 1 named this the R1 owner ("Slot policy → the R1 stepping helper only"). |
| Notice (N1–N2) | **eligibility of a start instant**: it removes starts and never moves anchors | a new owner, `QueryTime`. This is the one place where the calendar/instant world meets the time-of-day core. |

Once B2 is absorbed into occupancy, it produces the one concept the policies need, an **opening**: a
span inside which a new booking's *own* interval may lie, with its trailing buffer already accounted
for. After that, the two alignment policies differ **only in data**:

- gap-aligned (R1): lattice origin = opening start, step = duration
- grid (G1): lattice origin = working-hours start, step = granularity

Both reduce to one total geometric operation, "every lattice point at which a length fits inside this
range" (`TimeRange.fitting_starts`). So the policy seam is a pair of values, not a Strategy interface.
The fit rule (B2) is computed once, upstream of both policies.

### 0.2 The two moves, kept apart

1. **Refactor (behavior-preserving; every stage-1 test except the ones named in §9.1 stays green):**
   - Replace `TimeRange.leading` + the R1 loop with `TimeRange.fitting_starts(length, step, origin)`.
     R1 becomes the call `fitting_starts(d, step=d, origin=gap.start)`.
   - `DaySchedule` coalesces its busy ranges into their canonical union. For stage-1 inputs this only
     joins *touching* ranges, which produced no gap before either.
   - `free_gaps()` is renamed `openings()`. With buffer 0 an opening equals a free gap.
   - Outputs are bit-for-bit identical (C1–C14).
2. **Behavior change** at the seams that now exist:
   - `ResourceRules` and `QueryTime` are added.
   - `DaySchedule` takes `buffer`: it widens occupancy (B1, M1) and shrinks openings closed by
     occupancy (B2).
   - The alignment policy gains the grid branch (G1).
   - The entry gains the eligible-start window (N1, N2).

---

## 1. Assumptions (delta against DESIGN.md §1.2)

Stage-1 A1–A4, A7–A9 are unchanged. A5 and A6 are amended. A10–A15 are new.

| # | Assumption | Why | Change lands in |
|---|---|---|---|
| A5′ | No output cap. *Granularity now exists as an optional per-resource setting (0004 §6–7).* Without it, sub-minute precision still passes through untouched. With a grid, the work is proportional to the number of lattice points that fit, not to the whole day's grid (§3.2). | 0004 decided granularity. The output cap is still undecided. | Output cap: `available_starts`, next to the duration check. |
| A6′ | **Validation precedence** (S13). Checks run in two phases, and each phase has a fixed order. **Caller-side construction runs first, in the caller's own expressions, before the call:** `TimeRange` (type → tz → emptiness); `ResourceRules` (buffer → notice → granularity, in field order); `QueryTime` (`day` type → `now` type → `now` aware). **Then, inside `available_starts`, in statement order:** (1) duration ≤ 0; (2) notice > 0 with no `when`; (3) overlapping raw bookings. Computation starts only after all three. So `[]` from an out-of-day cutoff is returned only for otherwise valid input. | This keeps stage-1 A6's cheapest-first order and its rule that "an invalid request is rejected even when nothing would fit" (C12). | Statement order of `available_starts`; field order of the two new value types. |
| A10 | **Buffered occupancy is coalesced into its union** inside `DaySchedule`, after R4 runs on the raw bookings. This is *not* the "merge" that decision 0002 rules out. 0002 forbids merging overlapping **bookings**, because that would hide a caller bug. Overlapping **occupancy** is normal input under 0004 §5, and the busy time really is the union. | It restores the stage-1 invariant that busy ranges are pairwise disjoint (now strengthened to "separated"). The free-time walk and its proof then survive unchanged. | `DaySchedule.__init__` step 5. |
| A11 | **"End of day" is `time.max`** (23:59:59.999999, exclusive), the same sentinel as A3. A buffer cut at midnight (M1) ends at `time.max`. The last microsecond is unrepresentable, and that cannot matter: occupancy is clipped to hours, and hours end at or before `time.max`. | This is A3's reading, applied again. | `TimeRange.shift_end`. |
| A12 | **With `when` supplied, a query about a past day returns `[]`** (cutoff on a later day, N1). A "what-if" query about any day omits `when` (N2). | This is the literal 0004 §9–10 rule. It is stated here because a caller could be surprised by it. | `QueryTime.eligible_starts`. |
| A13 | **The caller is responsible for `day` matching the day of `working_hours`/`bookings`.** The core only ever sees times of day. `day` is used only to place `now + notice` onto that day. | The core has no date. Checking consistency would require dates on the ranges (an R6 change). | Not applicable (a caller contract, stated in the docstring). |
| A14 | **`QueryTime` type-guards `day` and `now`.** A `datetime` passed as `day` compares *unequal* to a `date` without raising. A `date` passed as `now` silently drops the time of day in `+ timedelta`. Both are silent acceptances, so under A7's own principle each gets a `TypeError` guard. `ResourceRules` gets no type guards: an `int`/`float`/`str` field already fails loudly at the first `<`/`<=` against a `timedelta` in its own `__post_init__`. | This applies A7 consistently: add a guard exactly where a wrong type would otherwise be silently accepted. | `QueryTime.__post_init__`. |
| A15 | **Buffer 0 and notice 0 are real lengths, not "absent"**. Granularity *absent* is `None`, and granularity 0 is an error. | "No buffer" *is* a zero-length buffer: every rule reads correctly with 0. "No grid" is not a grid of step 0: a step of 0 has no meaning and would never terminate. The asymmetry follows what each concept is (see §7). | `ResourceRules` field types. |

---

## 2. Module tree and dependency direction

```
availability/
  __init__.py      CHANGED  __all__ += "ResourceRules", "QueryTime"
  errors.py        UNCHANGED in shape (docstring of InvalidAvailabilityRequest lists V1/N2 too)
  time_range.py    CHANGED  TimeRange: − leading; + fitting_starts, shift_end, joined, contains
                            (still the ONLY time-of-day arithmetic)
  rules.py         NEW      ResourceRules (published): per-resource buffer / notice / granularity; owns V1 field rules
  query_time.py    NEW      QueryTime (published): day + naive now; the ONLY date/instant arithmetic;
                            maps now + notice onto the day ONCE (H3)
  _day.py          CHANGED  DaySchedule(hours, bookings, buffer): occupancy (R3, R4, B1, B3, M1) and
                            openings (B2)
  slots.py         CHANGED  available_starts(..., *, rules, when): R5-duration, N2, composition;
                            _aligned_starts (R1 + G1 policy)
tests/
  test_time_range.py        CHANGED (T8 re-pointed; new T11–T14)
  test_available_starts.py  UNCHANGED rows A1–A21; NEW stage-2 rows B1–B24
  test_rules.py             NEW (ResourceRules, QueryTime)
  test_invariants.py        EXTENDED (random buffer / grid / notice; stage-1 properties kept verbatim)
  test_public_surface.py    CHANGED (P1, P2, P3 widened; P6 new)
```

Runtime dependencies are acyclic and point toward the stable leaf:

```
slots ──► _day ──► time_range ──► errors
  │  └──► query_time ──┘   ▲          ▲
  └──► rules ─────────────────────────┘
```

- `rules` imports only `errors`. It holds `timedelta`s and does no time arithmetic.
- `query_time` imports `time_range` (to return a `TimeRange`) and `errors`.
- `_day` imports `time_range` and `errors`. It does **not** import `rules`, because it receives the
  buffer as a `timedelta` (see §5, floor calibration).
- No module imports an underscore-prefixed *name* from another module. `_day.DaySchedule` is still
  imported only by `slots`.
- Stdlib only: `dataclasses`, `datetime`, `itertools.pairwise`, `collections.abc`, `typing`.

---

## 3. Modules: responsibility, signatures, contracts (changed or new only)

### 3.1 `errors.py`: unchanged types

The vocabulary stays **exactly two types**. Every new rejection (V1, N2, aware `now`) is an
`InvalidAvailabilityRequest`. No caller handles a negative buffer differently from a negative notice:
each is "fix your configuration, surface the message". A subtype per rule would be a dead subtype, and
none carries a payload. `TypeError` from the `QueryTime` guards stays outside the vocabulary (A7).

### 3.2 `time_range.py`: `TimeRange` (changed)

The responsibility is unchanged: this module is the one place that does arithmetic on times of day.
Every operation that could produce an empty range returns `None`. Every public operation is pure and
**total**: it has no precondition, and no argument makes it overflow or hang.

```python
@dataclass(frozen=True, slots=True)
class TimeRange:
    start: time
    end: time
    # __post_init__, if_nonempty, intersection, overlaps, __str__ — UNCHANGED (DESIGN.md §3.2)

    def fitting_starts(self, length: timedelta, step: timedelta, origin: time) -> Iterator[time]:
        """Every lattice point t = origin + k·step (k any integer) at which [t, t + length) lies
        inside self, ascending.
        Pre: none. Total for every timedelta, including 0, negative and timedelta.max.
        Post: yields exactly {t : t ≡ origin (mod step), start <= t, t + length <= end}, strictly
              ascending; nothing when length <= 0, step <= 0 or length > (end − start).
          · `t + length <= end` is the R2 fact "a slot may end exactly at the range's end" (C14);
            it is the ONLY "does a slot fit" test in the package (it replaces `leading`).
          · The k-range is computed by floor division BEFORE any multiplication, so every product
            lies inside [start, end]: no OverflowError for any length/step, including
            step = timedelta.max (S10 g = 10 h, S15).
          · The work is proportional to the number of starts yielded, never to the size of the
            lattice outside self.
        Each call returns a fresh iterator."""

    def shift_end(self, by: timedelta) -> "TimeRange | None":
        """This range with its end moved by `by` (either sign), cut at the end of the day.
        Pre: none. Total for every timedelta.
        Post: if_nonempty(start, min(end + by, END_OF_DAY)), where END_OF_DAY = time.max (A3, A11).
          · Growing never crosses midnight (M1): `by` is compared with (END_OF_DAY − end) BEFORE
            adding, so by = timedelta.max gives [start, time.max) with no OverflowError (S15).
          · Shrinking to or past start gives None; `-by` is compared with the length before
            subtracting."""

    def joined(self, other: "TimeRange") -> "TimeRange | None":
        """The single range covering both, when they overlap or touch; None when a non-empty gap
        separates them.
        Pre: none. Total, symmetric.
        Post: None iff if_nonempty(min(ends), max(starts)) is not None (a real gap between them);
              otherwise TimeRange(min(starts), max(ends))."""

    def contains(self, t: time) -> bool:
        """R2 membership: start <= t < end. Total."""
```

Illustrative lines, to pin the one place where lattice arithmetic happens:

```python
    def fitting_starts(self, length, step, origin):
        lo, hi, base = _offset(self.start), _offset(self.end), _offset(origin)
        if not (timedelta(0) < length <= hi - lo and step > timedelta(0)):
            return
        first = -((base - lo) // step)              # ceil((lo − base) / step)
        last = (hi - length - base) // step         # floor((hi − length − base) / step)
        for k in range(first, last + 1):
            yield _at(base + k * step)
```

**Why the public members changed, and why each new one is on the type.** Stage 1 held that the
published geometry is the type's own behavior, total, and fixed by decided rules (DESIGN.md §3.2). Each
addition meets the same three tests:

- `fitting_starts` replaces `leading`. It is `leading` generalized to the one axis stage 2 actually
  adds: *where the tried points are*. `leading` answered "does length fit at `start`". Both present
  policies ask "at which points of a lattice does length fit". A lattice is exactly as general as the
  two present producers need, and no more. It is not a predicate, not a candidate iterable, and not a
  policy object. `leading` has no remaining consumer, so it is **cut** (subtractive pass, §8).
- `shift_end` is the only operation that grows or shrinks a range. It owns the M1 cut. Growing (B1) and
  shrinking (B2) are the same fact, "move the end by a length", so one signed operation carries both.
  Two methods would duplicate the clamp and the emptiness rule. A signed `timedelta` is the stdlib's own
  word for a displacement.
- `joined` is union geometry for coalescing occupancy (A10).
- `contains` is R2 membership for the notice window (§3.6).

All four keep the stage-1 guarantee that no bound comparison appears outside `time_range.py`.

### 3.3 `rules.py`: `ResourceRules` (new, published)

```python
@dataclass(frozen=True, slots=True)
class ResourceRules:
    """One resource's booking rules. The defaults are exactly stage 1.

    buffer       cleanup time after every booking (B1). Zero means none.
    notice       minimum time between `now` and an offered start (N1). Zero means "not in the past".
    granularity  step of the start-time grid counted from the working-hours start (G1);
                 None means no grid: gap-aligned stepping (stage-1 R1).

    Invariant (established in __post_init__, the one construction path; frozen):
      buffer >= 0; notice >= 0; granularity is None or granularity > 0.
    """
    buffer: timedelta = timedelta(0)
    notice: timedelta = timedelta(0)
    granularity: timedelta | None = None

    def __post_init__(self) -> None:
        """Raises, in this order (field order, A6′):
          InvalidAvailabilityRequest  buffer < 0          "buffer must not be negative, got -1 day, 23:45:00"
          InvalidAvailabilityRequest  notice < 0          "minimum notice must not be negative, got …"
          InvalidAvailabilityRequest  granularity <= 0    "granularity must be positive when given, got 0:00:00"
        A non-timedelta field fails loudly at the first comparison with the stdlib TypeError (A7, A14)."""
```

**What it is.** It is a *parameter object* for configuration that belongs to a resource and outlives a
single query. It is not a request. It owns the V1 field rules, and it has no other behavior. That is
deliberate. Each field is consumed by a different owner (buffer by occupancy, granularity by the
alignment policy, notice by eligibility). Methods on it that used those fields would pull those
private decisions onto a published type. This is the same reason `DaySchedule` and the policy stay
private in stage 1. So it is a validated value, like `TimeRange`'s fields, not an anemic bag with its
logic kept elsewhere: its one rule (the field ranges) lives on it.

### 3.4 `query_time.py`: `QueryTime` (new, published). H3 is decided here.

```python
@dataclass(frozen=True, slots=True)
class QueryTime:
    """When the question is asked (`now`, naive local date-time) and which calendar day it is
    about (`day`). Supplying it enables the notice rule (N1); omitting it is a what-if query (N2).

    Invariant (established in __post_init__; frozen): type(day) is date and not datetime;
      now is a datetime; now.tzinfo is None.
    """
    day: date
    now: datetime

    def __post_init__(self) -> None:
        """Raises, in this order:
          TypeError                   day is not a date, or is a datetime     (A14)
          TypeError                   now is not a datetime                   (A14)
          InvalidAvailabilityRequest  now carries tzinfo                      (V1, R6)
             "now must be a naive local date-time (no tzinfo), got 2026-09-23 08:00:00+02:00" """

    def eligible_starts(self, notice: timedelta) -> TimeRange | None:
        """N1, the one owner: the times of `day` at which a start is at least `notice` after `now`,
        i.e. {t : datetime.combine(day, t) >= now + notice}, as a time-of-day window.
        Pre: none. Total for every timedelta (the core only ever passes notice >= 0).
        Post:
          · cutoff after the day's last instant   → None           (nothing is eligible: S12)
          · cutoff before the day begins           → TimeRange(time.min, time.max)  (no effect)
          · cutoff on the day at time c            → TimeRange.if_nonempty(c, time.max)
        Overflow: now + notice is never formed until it is known to be representable:
          until_end = combine(day, time.max) − now      (a datetime difference: always representable)
          since_start = now − combine(day, time.min)
          notice > until_end    → None                  (S15 notice = timedelta.max, S12 48 h)
          notice < −since_start → whole day
          otherwise cutoff = now + notice lies within the day → window from cutoff.time()."""
```

**H3, decided.** The date and the instant are converted **once**, in `QueryTime.eligible_starts`, into
the only thing the core can use: a `TimeRange` of eligible start times, or `None` when nothing on that
day is eligible. The core (`DaySchedule`, the policy, `fitting_starts`) never sees a `date` or a
`datetime`. R6's "one local day of wall-clock times" stays true inside the core. `query_time.py` is the
single home of calendar/instant arithmetic, just as `time_range.py` is the single home of time-of-day
arithmetic. The time model now has two files, and each changes for its own reason: multi-day queries
or time zones would reopen `query_time.py` and the entry. A 24:00 close would reopen `time_range.py`.

**Why `day` and `now` form one type and not two keyword parameters.** They are a data clump that must
arrive together (0004 §10: "`now` (with `day`)"). With one optional value, "`now` without `day`" cannot
be represented. The aware-`now` rule gets a single owner at construction, which mirrors `TimeRange`'s
A4. And the one operation that needs both has a natural home, so the logic does not sit in the entry as
feature envy on two loose values.

**Why notice is not a field of `QueryTime`.** Notice is a per-resource rule (the brief). `QueryTime`
belongs to one call. Putting them together would mix two lifetimes. `eligible_starts(notice)` takes the
length, so `QueryTime` depends on nothing in `rules`.

### 3.5 `_day.py`: `DaySchedule` (changed, package-private). H1 is decided here.

**Responsibility.** Stage 1: turn bookings into the day's busy time, then say where free time remains.
Stage 2 adds that busy time includes each booking's buffer, and that free time is reported as
*openings*: where a new booking's own interval may lie, given that its trailing buffer must clear
existing occupancy but may run past closing.

```python
class DaySchedule:
    """One resource's day: working hours, the occupancy inside them, and the openings left.

    Invariant (established in __init__, the ONE construction path, and never changed after):
      I1 every r in _busy lies inside _hours
      I2 _busy is strictly ascending by start
      I3′ consecutive members of _busy are SEPARATED: a non-empty gap lies between them
          (strengthened from stage-1 "non-overlapping, touching allowed"; A10)
      I4 every member is a valid, non-empty TimeRange
      I5 _buffer >= 0 (trusted: established by ResourceRules; not re-checked)
    """
    __slots__ = ("_hours", "_busy", "_buffer")

    def __init__(self, hours: TimeRange, bookings: Iterable[TimeRange], buffer: timedelta) -> None:
        """Pre: hours and each booking are TimeRange; buffer >= 0. `bookings` is consumed once.
        Steps, in this order (the order IS A1 and 0004 §2, §5):
          1. ordered = sorted(bookings, key=(start, end))                          R4 service sorts
          2. first adjacent pair with a.overlaps(b) → OverlappingBookingsError(a, b)
                                                         R4 on RAW bookings (A1 kept; B3, S7)
          3. occupied = (b.shift_end(buffer) for b in ordered)               B1, M1 (cut at midnight)
          4. clipped  = (c for o in occupied if (c := o.intersection(hours)) is not None)   R3
          5. _busy    = coalesce(clipped) using TimeRange.joined              B3 accepted: union
        Post: I1–I5 hold."""

    def openings(self) -> Iterator[TimeRange]:
        """B2, the one owner: the maximal spans in which a new booking's OWN interval may lie.
        Algorithm (the stage-1 cursor walk; the asymmetry of B2 appears exactly once):
          cursor = _hours.start
          for block in _busy:
              gap = TimeRange.if_nonempty(cursor, block.start)
              if gap is not None and (o := gap.shift_end(-_buffer)) is not None:
                  yield o                  # a gap closed by OCCUPANCY: the new booking's buffer
                                           # must clear the block, so its own interval must end
                                           # `buffer` before it
              cursor = block.end
          tail = TimeRange.if_nonempty(cursor, _hours.end)
          if tail is not None:
              yield tail                   # a gap closed by CLOSING: the buffer may run past it
        Post:
          · openings are non-empty, inside _hours, strictly ascending, pairwise disjoint;
          · every opening's start is the start of a maximal free gap (the R1 anchor, unmoved);
          · FIT (B2): for any t and d > 0, ([t, t+d) ⊆ _hours and [t, t+d+buffer) overlaps no
            member of _busy)  ⇔  [t, t+d) lies inside exactly one opening.
          · buffer == 0 ⇒ openings are exactly the stage-1 free gaps.
        Each call returns a fresh iterator."""
```

**Proof of the FIT postcondition.** Start with (⇒). The instant t is in `[t, t+d+b)`, so t is free and
in hours. It therefore lies in some maximal free gap `[a, c)`. There are two cases.

- If `c` is the start of a block, then `[t, t+d+b)` avoids that block iff `t+d+b ≤ c`, i.e.
  `t+d ≤ c−b`. That is containment in `[a, c−b)`, which is `gap.shift_end(−b)`.
- If `c = hours.end`, no block lies after `c`, so the only constraint is `t+d ≤ hours.end`. That is
  containment in the tail gap.

(⇐) is the same argument read backwards. With b = 0, `shift_end(0)` returns the gap itself.

**Why coalescing (step 5) keeps the walk correct.** The stage-1 cursor walk relied on I2/I3 to show that
the cursor never moves backwards. Buffered occupancies may overlap (S6), so I3 is restored by
construction.

- Clipped starts are non-decreasing along the sorted order: `max(s, hours.start)`.
- Coalescing sorted-by-start ranges with `joined` is the standard interval union. Its result is
  strictly ascending and separated (I2, I3′).
- The walk and its "no zero-length gap, no negative gap, cursor never moves backwards" argument
  (DESIGN.md §3.3) then apply unchanged.
- Coalescing touching ranges changes nothing observable for stage-1 inputs: a touching pair produced
  `if_nonempty(c, c) → None`, which means no gap either way.

**Why the stage-1 invariants that R4 needs are untouched.** Steps 1–2 are byte-identical to stage 1 and
run on the raw bookings. Buffers enter only at step 3. So B3 (buffer-violating input is accepted) and
S7 (a true overlap is still rejected, naming the raw pair) both follow from the step order alone.

### 3.6 `slots.py`: `available_starts` (changed, published). H2 and H4 are decided here.

```python
def available_starts(
    working_hours: TimeRange,
    bookings: Iterable[TimeRange],
    duration: timedelta,
    *,
    rules: ResourceRules = ResourceRules(),
    when: QueryTime | None = None,
) -> list[time]:
    """Start times, earliest first, at which a new booking of `duration` can be offered on this
    resource: inside `working_hours`; its interval plus the resource's buffer clear of existing
    occupancy (bookings plus their buffers) inside the hours; aligned by the resource's granularity
    grid, or gap-aligned without one; and, when `when` is given, not before now + notice.

    Pre (caller side, already enforced): working_hours and bookings are TimeRange; rules is a
      ResourceRules; when is a QueryTime or None. `when.day` is the day of the hours and bookings (A13).
    Checked here, in this order (A6′):
      1. duration > 0, else InvalidAvailabilityRequest                                  (R5)
      2. rules.notice == 0 or when is not None, else InvalidAvailabilityRequest         (N2)
      3. raw bookings pairwise non-overlapping, by constructing DaySchedule             (R4)
    Post:
      · strictly ascending, no duplicates;
      · every s: [s, s+d) ⊆ working_hours, [s, s+d+buffer) overlaps no in-hours occupancy;
      · with granularity g: exactly the points hours.start + k·g satisfying the line above;
        without: exactly R1 over the openings (opening.start + k·d);
      · with `when`: exactly those of the above with combine(day, s) >= now + notice;
      · defaults (buffer 0, notice 0, no granularity, when None): the stage-1 postcondition verbatim.
    Raises: InvalidAvailabilityRequest (duration, N2), OverlappingBookingsError (R4)."""
```

The body is one level of abstraction:

```python
    if duration <= timedelta(0):
        raise InvalidAvailabilityRequest(f"duration must be positive, got {duration}")
    eligible = _eligible_starts(rules.notice, when)
    day = DaySchedule(working_hours, bookings, rules.buffer)
    if eligible is None:
        return []
    return [start
            for opening in day.openings()
            for start in _aligned_starts(opening, duration, working_hours.start, rules.granularity)
            if eligible.contains(start)]
```

```python
def _aligned_starts(opening: TimeRange, duration: timedelta,
                    grid_origin: time, granularity: timedelta | None) -> Iterator[time]:
    """R1 and G1, the one alignment owner: choose the lattice; the fit is the opening's.
      granularity None → lattice (opening.start, duration): back-to-back from each gap start (R1)
      granularity g    → lattice (grid_origin, g): every grid point that fits (G1, 0004 §6, §8)
    Returns opening.fitting_starts(duration, step, origin)."""

def _eligible_starts(notice: timedelta, when: QueryTime | None) -> TimeRange | None:
    """N2, the one owner: without `when`, a configured notice is a caller error and a zero notice
    means every start of the day is eligible; with `when`, delegate to when.eligible_starts (N1).
      when None, notice > 0 → InvalidAvailabilityRequest(
          "this resource requires 2:00:00 minimum notice; pass when=QueryTime(day, now)")
      when None, notice == 0 → TimeRange(time.min, time.max)   (every start of the day, A11)
      otherwise              → when.eligible_starts(notice)"""
```

**H2, decided: the two policies are data, not types.** The variation between gap-aligned and grid is
two values, the lattice origin and the step. The fit rule, "the slot lies inside an opening", is not
part of either policy. `DaySchedule.openings` computed it once (B2), and `fitting_starts` tests it once
(containment). So neither policy can re-implement it. The selector is a single `None` check on
`granularity`, and it sits exactly where the product decision sits (0004 §7: optional granularity keeps
R1).

A `SlotPolicy` Protocol with `GapAligned` and `Grid` classes would have two implementations, but each
would contain nothing except its choice of `(origin, step)`. That is an interface whose variation is
data (§9 pattern abuse, decorative). **Falsifier:** a policy that is not a lattice (for example
"preferred starts first", or "a grid, but also the gap start") would earn a policy seam. No decided or
foreseen rule is such a policy.

**H4, decided: the shape of the seam.**
- Two optional **keyword-only** value parameters are added. Each is a published, validated type, and
  each carries one lifetime: `rules` belongs to the resource, `when` belongs to the query. There is no
  long primitive list: three settings plus two context values would otherwise be five loose optional
  parameters with hidden co-requirements.
- No internal type appears. `DaySchedule` and openings stay private.
- **Stage-1 callers are unaffected.** `available_starts(h, b, d)` is the same call with the same
  result. The new parameters are keyword-only, so no positional connascence is added.
- **Where each new validation has its one owner:** V1 field rules → `ResourceRules.__post_init__`.
  Aware `now` → `QueryTime.__post_init__`. N2 "notice without now" → `slots._eligible_starts`, the only
  place where a resource's rules meet a query's context. Precedence is A6′.

**Why an early `return []` after `DaySchedule`.** When nothing is eligible, validation still finishes
first: overlapping bookings are still reported (A6′), like stage-1 C12. After that, "nothing is
eligible" is a normal empty result, not an error.

**Why notice is a filter and not a clip, and why that is not a second owner.** 0004 §9 says notice
*removes* starts and never moves anchors. Clipping the hours, or inserting busy time `[00:00, cutoff)`,
would move the gap-aligned anchors (S11: 09:50 would be offered instead of 10:15). That would be a
concept cram, "notice as occupancy". Notice is not an occupancy rule. It has its own single owner
(`QueryTime.eligible_starts`), and the filter line only applies its result. Contrast the buffer: a
trailing filter for it *would* be a second owner, because the buffer's fit is an occupancy rule already
owned by `DaySchedule`.

### 3.7 `__init__.py`: the published surface

```python
from .errors import InvalidAvailabilityRequest, OverlappingBookingsError
from .time_range import TimeRange
from .rules import ResourceRules
from .query_time import QueryTime
from .slots import available_starts
__all__ = ["TimeRange", "ResourceRules", "QueryTime", "available_starts",
           "InvalidAvailabilityRequest", "OverlappingBookingsError"]
```

Illustrative stage-2 call (the S1 anchor):

```python
available_starts(TimeRange(time(9), time(17)),
                 [TimeRange(time(9), time(9, 45)), TimeRange(time(11), time(12))],
                 timedelta(minutes=30),
                 rules=ResourceRules(buffer=timedelta(minutes=15), granularity=timedelta(minutes=15)))
# → [10:00, 10:15, 12:15, 12:30, …, 16:30]
```

---

## 4. Rule → owner

| Rule | Single owner | Mechanism, and why every path goes through it |
|---|---|---|
| R1 gap-aligned stepping (no grid) | `slots._aligned_starts` (policy: lattice = opening start, duration); mechanics in `TimeRange.fitting_starts` | Openings reach the result only through the one composition line, which calls this function. |
| R2 touching ≠ overlap | `time_range._nonempty`, behind `if_nonempty` → `intersection`/`overlaps`/`joined`/`shift_end` | Still the only strict bound comparison. |
| R2 slot may end exactly at the end | `TimeRange.fitting_starts` (`t + length <= end`) | The only fit test (`leading` is cut). |
| R3 only in-hours occupancy counts (for existing bookings, their buffers, and the new slot's buffer) | `DaySchedule.__init__` step 4 (clip after widening) + `openings` (the tail gap is not shrunk) | The only place occupancy meets the hours. |
| R4 sort; raw overlap rejected naming the pair | `DaySchedule.__init__` steps 1–2 (unchanged) | One constructor; buffers enter after step 2. |
| R5 range | `TimeRange.__post_init__` (unchanged) | |
| R5 duration | `available_starts`, first statement (unchanged) | |
| R6 naive one-day time-of-day in the core | `TimeRange` (unchanged) + `QueryTime.eligible_starts` as the only exit from date/instant into time of day | The core receives no `date` or `datetime`. |
| **B1** buffer after every booking; counts inside hours wherever it falls (including a booking before opening) | `DaySchedule.__init__` step 3 (widen), placed before step 4 (clip) | Occupancy is built only here. |
| **B2** new slot inside hours; slot + buffer clear of occupancy; buffer may run past close | `DaySchedule.openings` | Policies see only openings, and the asymmetry is the one `shift_end(-buffer)` on block-closed gaps. |
| **B3** buffer-violating existing bookings accepted | `DaySchedule.__init__` step order (R4 on raw) + step 5 (coalesce) | |
| **G1** optional grid from hours start; every fitting grid point | `slots._aligned_starts` (lattice = hours.start, g) | The same single alignment owner as R1. |
| **N1** start t offered iff combine(day, t) >= now + notice | `QueryTime.eligible_starts` (the decision); applied by the one filter line in `available_starts` | The only conversion from instant to time of day. |
| **N2** no `now` → no filter; notice > 0 without `now` → error; `now` with notice 0 → past dropped | `slots._eligible_starts` | The only place where `rules` and `when` meet. |
| **V1** negative buffer / negative notice / granularity <= 0 | `ResourceRules.__post_init__` | One construction path. |
| **V1** aware `now` | `QueryTime.__post_init__` | One construction path. |
| **V1** notice > 0 without `now` | `slots._eligible_starts` (= N2) | |
| **V1** defaults = stage 1 | structural: `ResourceRules()` defaults + `when=None` → `shift_end(0)` is the identity, openings equal gaps, lattice `(gap.start, d)` is R1, eligible = whole day | No special-case path. |
| **M1** buffer cut at end of day | `TimeRange.shift_end` (the only operation that grows a range) | |
| Earliest first | composition: openings ascending and disjoint; `fitting_starts` ascending within each; the filter preserves order | No final sort. |
| Validated once; core trusts | constructors (`TimeRange`, `ResourceRules`, `QueryTime`) + `available_starts` (duration, N2) + `DaySchedule.__init__` (R4) | `openings`, `_aligned_starts`, `fitting_starts`, `eligible_starts` validate nothing. |

---

## 5. Genericity calibration of every crossing type (floor / ceiling)

| Crossing | Type chosen | Floor (what the consumer needs to be complete) | Ceiling (what every producer can supply) |
|---|---|---|---|
| entry ← caller: settings | `ResourceRules` | buffer, notice, and optional granularity; nothing else | Every caller can build `ResourceRules()` (the defaults are stage 1). |
| entry ← caller: context | `QueryTime \| None` | `day` + naive `now`, only together | A what-if caller has neither, so `None`. |
| `slots` → `DaySchedule` | `buffer: timedelta` (not `ResourceRules`) | occupancy needs only the buffer | Every `ResourceRules` has one. Passing the whole rules object would let the day read notice and granularity it must not own. |
| `DaySchedule` → policy | `Iterator[TimeRange]` of openings | the policy needs "where the slot's own interval may lie", with the anchor at its start | The day can always produce this. Free gaps plus a separate "reach" length would push B2 into every policy. |
| policy → `TimeRange` | `fitting_starts(length, step, origin)` | the two present policies are lattices | A lattice with any origin is total and needs no precondition. A general candidate iterable or predicate would be speculative. |
| `QueryTime` → core | `TimeRange \| None` (eligible window) | the core needs "which times of this day are eligible" | Every (day, now, notice) maps to this. A `datetime` cutoff would leak the calendar into the core. |
| entry → caller | `list[time]` | unchanged | unchanged |

What is **not** generalized, because no present force needs it: per-booking buffers (non-goal); a
buffer before bookings (non-goal); a policy seam (see H2); a `Lattice`/`Grid` value type (two
arguments consumed at one call site would make it a lazy class); a `Notice` type (one rule, one owner,
a `timedelta` is enough, the same argument as stage 1's `timedelta` over `SlotDuration`); dates on
`TimeRange` (multi-day is a non-goal).

---

## 6. Error vocabulary delta

| Situation | Raised by | Type | Message (example) |
|---|---|---|---|
| buffer < 0 | `ResourceRules(...)` | `InvalidAvailabilityRequest` | `buffer must not be negative, got -1 day, 23:45:00` |
| notice < 0 | `ResourceRules(...)` | `InvalidAvailabilityRequest` | `minimum notice must not be negative, got -1 day, 23:00:00` |
| granularity 0 or negative | `ResourceRules(...)` | `InvalidAvailabilityRequest` | `granularity must be positive when given, got 0:00:00` |
| non-timedelta setting | `ResourceRules(...)` comparison | stdlib `TypeError` (A7) | stdlib message |
| aware `now` | `QueryTime(...)` | `InvalidAvailabilityRequest` | `now must be a naive local date-time (no tzinfo), got 2026-09-23 08:00:00+02:00` |
| `day` is a datetime or not a date; `now` is not a datetime | `QueryTime(...)` | `TypeError` (A14) | `QueryTime.day must be datetime.date (not datetime), got datetime.datetime` |
| notice > 0 with `when=None` | `available_starts` (`_eligible_starts`) | `InvalidAvailabilityRequest` | `this resource requires 2:00:00 minimum notice; pass when=QueryTime(day, now)` |
| cutoff after the day / all starts past | — | not an error: `[]` | — |

Every stage-1 row of DESIGN.md §6 is unchanged.

---

## 7. What each new concept is (concept-fit pass)

| Concept | What it is | Why this kind of thing, and the cram it avoids |
|---|---|---|
| Buffer | a length (`timedelta`) on `ResourceRules`. Its *effect* is occupancy in `DaySchedule._busy`. | It is never a booking: it never passes through R4 (a synthetic booking would make touching bookings' buffers "overlap" other bookings and so break B3), and it is never returned. A buffer of 0 is a genuine zero length, not a stand-in (A15). |
| Occupancy | `DaySchedule._busy`, the canonical union of (booking + buffer) ∩ hours | Stage 1 named it `busy` for exactly this. It is not "bookings". Overlap between buffers is absorbed by the union, not by weakening the invariant. |
| Opening | a `TimeRange` produced by `DaySchedule.openings()` | Its own concept: where a new booking's interval may lie. It is not a gap with a flag, and not a gap plus a "reach" that each policy must remember to add. With buffer 0 it *is* the free gap. |
| Grid / lattice | `(origin, step)` arguments of `fitting_starts`, chosen by `_aligned_starts` | The grid is a set of candidate points, not a filter over gap-aligned starts (that would offer only every d-th grid point, which 0004 §6 rules out), and not a score. |
| Notice cutoff | the eligible-start window, `TimeRange \| None`, from `QueryTime.eligible_starts` | It is the time-of-day image of "at or after now + notice on this day". It is not occupancy (that would move anchors, S11) and not a clipped working window. `None` means *nothing eligible*. "No filter" is the honest whole-day window, and the two are never confused. |
| Query context | `QueryTime(day, now)`, published | The moment of asking plus the day asked about. It is not part of the resource's rules and not part of the day's schedule. `now` without `day` cannot be represented. |
| Resource settings | `ResourceRules`, published | A per-resource configuration value that owns its range rules. Hours are **not** folded in: hours are per day, while the settings belong to the resource. |

No inert stand-ins remain. `shift_end(0)`, the whole-day window and `ResourceRules()` are exact
identities under the rules, not placeholders.

---

## 8. Subtractive pass (what was added or changed)

| Element | Present force | Verdict |
|---|---|---|
| `ResourceRules` | V1 field rules have one owner; replaces three loose optional parameters | keep |
| `ResourceRules` default instance as a parameter default | V1 "defaults = stage 1"; stage-1 callers unchanged | keep (frozen, so a shared default is safe) |
| `QueryTime` | N1 needs day + now together; aware-`now` owner; H3 conversion home | keep |
| `QueryTime` type guards (A14) | two silent acceptances (`datetime` as day compares unequal; `date` as now loses the time of day) | keep |
| `QueryTime.eligible_starts` | N1, the one owner; S12/S15 overflow safety | keep |
| `TimeRange.fitting_starts` | R1 + G1 mechanics, R2 end-fit, overflow safety, work proportional to output | keep |
| `TimeRange.leading` | no consumer left | **cut** (§9.1: T8 re-pointed) |
| `TimeRange.shift_end` | B1 widening, B2 opening shrink, M1 cut, S15 | keep (one op, two present uses) |
| `TimeRange.joined` | A10 coalescing (B3 input, S6) | keep |
| `TimeRange.contains` | applying the eligible window without a time comparison outside `time_range.py` | keep |
| `DaySchedule` `buffer` parameter / `_buffer` | B1, B2 | keep |
| `DaySchedule` step 5 (coalesce) | restores I3 under B3; keeps the walk's proof | keep |
| `DaySchedule.free_gaps` | superseded; the only consumer now needs openings | **renamed** `openings` (the stage-1 gap walk is its body) |
| `_aligned_starts` (replaces `_gap_aligned_starts`) | R1 + G1 lattice choice | keep |
| `_eligible_starts` | N2 owner | keep |
| early `return []` | nothing eligible, after validation (A6′) | keep |
| a `SlotPolicy` Protocol, a `Lattice` type, a `Notice` type, a `Buffer` type, new error subtypes | none | **not added** |

---

## 9. Trace

H = 09:00–17:00, d = 30 min unless stated. b = buffer, g = granularity. "Openings" are listed after
`DaySchedule`.

### 9.0 Stage-1 C1–C14 under defaults (S3)

With defaults, `shift_end(0)` returns an equal range. Steps 1, 2 and 4 are stage 1. Step 5 joins only
touching ranges (C3's tiling bookings, C8). Those produced no gap before either, so the gaps are equal.
Each opening is a gap, because there is no shrink when b = 0. `_aligned_starts` yields
`gap.fitting_starts(d, d, gap.start)` = `gap.start + k·d` for `k = 0 … len//d − 1`, which is the R1
postcondition. `eligible` is the whole day, which contains every start. So every row of DESIGN.md §7
and §7.1 holds unchanged:

- C1 → `09:45, 10:15, 12:00 … 16:30`.
- C4 `timedelta.max` → `fitting_starts` compares first → `[]`.
- C9/C12 precedence is unchanged, because the N2 check passes when notice is 0.
- C10: the sort key is unchanged.

### 9.1 Stage-2 cases

| Case | Path | Result |
|---|---|---|
| S1 | b 15, g 15. Occupancy 09:00–10:00, 11:00–12:15 (separated). Openings: gap(09:00,09:00) None; gap 10:00–11:00 closed by a block → `shift_end(−15)` → 10:00–10:45; tail 12:15–17:00. Lattice (09:00, 15): in 10:00–10:45 with length 30 → 10:00, 10:15. In the tail → 12:15 … 16:30 (k gives 18 points). Eligible = whole day. | `10:00, 10:15, 12:15, …, 16:30` ✓ |
| S2 | Same openings, no grid: lattice (opening.start, 30). 10:00–10:45 → 10:00 only (10:30 + 30 > 10:45). Tail → 12:15, 12:45, …, 16:15 (16:45 + 30 > 17:00). | ✓ |
| S3 | §9.0 | ✓ bit-for-bit |
| S4 | No bookings. `_busy = ()`, and the tail opening = H, not shrunk (closed by closing). g 15 → last k with t + 30 ≤ 17:00 → 16:30. | last 16:30 ✓ |
| S5 | 08:00–09:00, b 15 → 08:00–09:15 ∩ H = 09:00–09:15 → tail 09:15–17:00 → 09:15 (both policies). 08:00–08:50 → 08:00–09:05 → 09:00–09:05 → tail 09:05–17:00 → grid: first k ≥ 09:05 → 09:15; no grid: 09:05. 07:00–08:00 → 07:00–08:15 ∩ H = None. | ✓ |
| S6 | 10:00–11:00 and 11:00–12:00: raw touching, so R4 passes. Occupancy 10:00–11:15 and 11:00–12:15 → `joined` → 10:00–12:15. Openings 09:00–09:45 (09:00–10:00 closed by the block, shrunk) and 12:15–17:00. Nothing in [10:00, 12:15). No gap is ever built from a later start and an earlier end, because I3′ holds before the walk. b 60 with 10:00–10:30, 10:45–11:00: 10:00–11:30 and 10:45–12:00 → joined 10:00–12:00. | accepted; ✓ |
| S7 | 10:00–11:00 and 10:30–11:30, b 15: step 2 runs on raw ranges before step 3 → `OverlappingBookingsError(10:00–11:00, 10:30–11:30)`. Touching with b > 0: S6. | ✓ |
| S8 | Occupancy ending 10:00, block at 11:00, b 15: gap 10:00–11:00 → opening 10:00–10:45. d 45: 10:00 + 45 ≤ 10:45 → offered. d 60: 60 > 45 → not offered, although [10:00, 11:00) itself avoids the booking. | ✓ |
| S9 | 17:00–18:00 → 17:00–18:15 ∩ H = None. `_busy = ()` → tail = H → 16:30 offered. | ✓ |
| S10 | g 20: lattice (09:00, 20) → 09:00, 09:20, …, 16:20. g 10 h: k-range computed by floor division → k = 0 only → 09:00 (no overflow). C1 bookings with b 0, g 15: openings 09:45–11:00 and 12:00–17:00 → 09:45, 10:00, 10:15, 10:30, 12:00, …, 16:30. H 09:10–17:00, g 15: origin = hours start → 09:10, 09:25, …. | ✓ |
| S11 | now = day 08:00, notice 2 h: `until_end` is large, so cutoff = day 10:00 → window [10:00, max). 10:00 is contained and 09:45 is not. 90 min → [09:30, …). C1, no grid, now 09:50, notice 0: openings and anchors unchanged (09:45, 10:15, 12:00 …), then the filter drops 09:45 → first 10:15. | ✓ |
| S12 | prev 20:00 + 48 h: notice > `until_end` (27:59:59.999999) → None → `[]` (after validation). prev 16:00 + 16 h → cutoff day 08:00 → [08:00, max) → no effect. now on the next day, notice 0: `until_end` < 0 ≤ notice → None → `[]`. now day 16:40, notice 0 → [16:40, max); the last start is 16:30 → `[]`. | ✓ |
| S13 | notice 2 h with `when=None` → N2 error (step 2). `QueryTime(day, aware)` → `InvalidAvailabilityRequest`. `ResourceRules(buffer=−1 min)`, `(notice=−1 min)`, `(granularity=0)`, `(granularity=−15 min)` → `InvalidAvailabilityRequest` at construction. Precedence is A6′. Example: duration 0 together with notice > 0 and no `when` gives the *duration* error. N2 together with overlapping bookings gives the *N2* error. | ✓ |
| S14 | now = day 10:00, notice 0 → window [10:00, max): 10:00 kept (`contains` is inclusive at start), 09:45 dropped. | ✓ |
| S15 | d = `timedelta.max`: `fitting_starts` compares length > span first → nothing. b = `timedelta.max`: `shift_end(+max)` compares with room-to-midnight → end `time.max`. Openings: `shift_end(−max)` compares −by with the length → None, so the tail alone may offer. notice = `timedelta.max`: notice > `until_end` → None, and `now + notice` is never formed. Booking ending 23:50, b 30 → [.., time.max). No stdlib `OverflowError` anywhere. No loop can hang: `fitting_starts` iterates a finite k-range, and the walk is linear in `_busy`. | ✓ |
| S16 | Sort key (start, end) on raw bookings → identical `ordered` for every permutation. Steps 3–5 are deterministic maps and a fold over it. The reported pair is the first adjacent overlap (unchanged). This holds with S6's buffer-violating input too, because R4 passes and the coalesce input is identical. | ✓ |

### 9.2 X × R re-trace (interactions no S-case lists)

| New axis × existing rule | Outcome |
|---|---|
| buffer × R3, booking straddling close (16:45–17:30, b 15) | occupancy 16:45–17:00. The gap before it is closed by a block, so it is shrunk: a new slot must end by 16:30. Correct under B2 (in-hours occupancy). |
| buffer × R3, booking straddling open (08:30–09:30, b 15) | clip → 09:00–09:45. The first opening starts at 09:45. |
| buffer × A1 (overlap wholly before opening) | still rejected at step 2 on raw bookings. |
| buffer × A2 (duplicates) | still rejected. |
| buffer × hours ending at `time.max` | M1 cut coincides with the hours end. A block reaching `time.max` leaves no tail. |
| buffer larger than a whole gap closed by a block | `shift_end` → None, so no opening and no slot. The next opening is unaffected. |
| grid × opening shorter than d | `fitting_starts` → nothing. |
| grid × second precision (H 09:00:30) | the origin keeps its seconds; integer `timedelta` arithmetic. |
| grid with d not a multiple of g | every fitting grid point is offered (0004 §6). |
| notice × grid | window filter only; the grid origin stays hours.start (0004 §9). |
| notice × gap-aligned | the filter runs after stepping, so anchors are unmoved (S11). |
| notice with `now` microseconds | the window starts at an exact time with µs; `contains` is exact. |
| `QueryTime(date.max, datetime.max)`, notice 0 | `until_end` = 0 ≥ notice → cutoff = now (representable). |
| `now` before `date.min` + notice underflow | the `since_start` comparison gives the whole day, with no subtraction overflow. |
| V1 × defaults | `ResourceRules()` passes, and `when=None` with notice 0 passes N2 → stage 1. |

---

## 10. Design reasoning: H1–H4 and rejected alternatives

**H1 Buffer.** The buffer is occupancy, owned by `DaySchedule` in two halves of one rule:

- *existing* bookings occupy `[s, e+b)` (step 3, before the clip at step 4, so an off-hours booking's
  buffer counts inside hours);
- a *new* booking needs `[t, t+d+b)` clear. That is expressed once, as openings, by shrinking only the
  gaps that a block closes.

The stage-1 invariant that buffers break (busy ranges disjoint) is restored by coalescing into the
union (A10), not weakened. R4 is still checked on raw bookings first, so B3 and S7 both follow from
step order.

Rejected alternatives:
- (a) A trailing filter over candidate starts: a second owner of occupancy, and it would need its own
  closing-edge exception.
- (b) The buffer as a synthetic booking: R4 would reject touching bookings (breaking B3), the buffer
  could be "returned", and it is a concept cram.
- (c) Widening before the R4 check: rejects B3 input.
- (d) No coalescing, relying on "ends are non-decreasing because the buffer is uniform": correct
  today, but the walk's correctness would then rest on an unstated fact of the generator, and a
  nesting occupancy would move the cursor backwards *silently*. Canonical union is cheap and robust.
- (e) Free gaps plus a per-policy "reach = d + b if the gap is block-closed": re-implements B2 in
  every policy (H2's warning).
- (f) Extending blocks backwards by b before clipping: wrong for S9 (a 17:00 booking would block
  16:45–17:00).

**H2 Slot policy.** Two real policies exist now, and they differ only in `(origin, step)`. One
alignment owner (`_aligned_starts`) chooses the lattice, and one total geometric operation
(`fitting_starts`) enumerates the points that fit inside an opening. The fit was already decided
upstream (B2 → openings), so no policy can re-implement it.

Rejected alternatives:
- A Strategy/Protocol with two classes: decorative, since the variation is data.
- A grid as a filter over gap-aligned starts: drops valid grid points, and 0004 §6 rules it out.
- Enumerating the whole day's grid and fit-testing each point with a `DaySchedule.fits(t, d)` query:
  a second fit path beside openings, and work proportional to the grid instead of the output.
- Keeping `leading` and adding an `aligned` operation plus a loop in `slots`: two operations and loop
  arithmetic where one total operation says it.

**H3 Time model.** `QueryTime.eligible_starts(notice)` is the single conversion from (day, now, notice)
to a time-of-day `TimeRange | None`. The core stays in R6's one-day world. Overflow-prone `now + notice`
is formed only after comparisons prove that it lands inside the day.

Rejected alternatives:
- `datetime` in the core: forces dates onto every range and makes midnight crossing representable.
- A time-of-day `now` only: cannot express S12's across-day cases.
- The conversion inside `slots`: feature envy on two loose values.
- The conversion inside `ResourceRules`: mixes the resource's lifetime with the query's.

**H4 Public seam.** The seam is `available_starts(hours, bookings, duration, *, rules=ResourceRules(),
when=None)`. Stage-1 calls are unchanged. The two new values are published, validated, immutable, and
each is one lifetime. V1 has its owners at construction, N2 at the one meeting point. Precedence is A6′.

Rejected alternatives:
- Five loose keyword primitives: a long parameter list with hidden co-requirements.
- One `AvailabilityRequest` bundling everything: breaks stage-1 callers and mixes per-resource with
  per-query data.
- Putting working hours into `ResourceRules`: hours are per day.
- Positional new parameters: positional connascence.
- A CLI: unchanged, because no caller needs one.

---

## 11. Test plan (delta against DESIGN.md §10)

The principle is unchanged: assert contracts at the published seams (`TimeRange`, `ResourceRules`,
`QueryTime`, `available_starts`, the package surface). `DaySchedule` and the policy are covered through
`available_starts`. Order: the refactor step first (the characterization must stay green), then the
stage-2 rows test-first.

### 11.1 Kept, changed, and why

- **Unchanged (characterization, S3):** T1–T7, T9, T10; A1–A21 (their calls use the stage-1 signature,
  which is unchanged); invariants 1–7 and the overlap generator of §10.3, run with default rules; P4, P5.
- **Changed:**
  - **T8** (`leading`) is re-pointed to `fitting_starts` with lattice `(start, length)`. It asserts
    the same decisions: an exact fit ends at `end`; 1 µs too long → nothing; 0 and negative → nothing;
    `timedelta.max` → nothing and no `OverflowError`; 7 min 30 s keeps its seconds. Reason: `leading`
    is cut (§8), and the decision it pinned moved.
  - **P1** gains `ResourceRules` and `QueryTime`.
  - **P2** now pins `{start, end, if_nonempty, intersection, overlaps, fitting_starts, shift_end,
    joined, contains}`.
  - **P3** also resolves the hints of the new parameters to published types only.
  - These are deliberate surface changes, which is exactly what P1/P2 exist to force.

### 11.2 New `TimeRange` tests (`test_time_range.py`)

| # | Decision | Test | Covers |
|---|---|---|---|
| T11 | `fitting_starts` lattice | origin before start: first point ≥ start; origin = start; step > span → at most one point; step ≤ 0 → nothing; `step=timedelta.max` → no overflow; every point satisfies `t + length ≤ end` | G1, S10, S15 |
| T12 | `shift_end` | +b normal; +b crossing midnight → `time.max` (M1); `+timedelta.max` → `time.max`, no overflow; −b partial; −b ≥ length → None; `−timedelta.max` → None; 0 → equal range | B1, B2, M1, S15 |
| T13 | `joined` | overlapping → union; touching → union; apart → None; nested → outer; symmetric | A10, S6 |
| T14 | `contains` | start inside; end outside; before outside | N1 inclusive cutoff, S14 |

### 11.3 New `test_rules.py`

| # | Test | Covers |
|---|---|---|
| R-1 | `ResourceRules()` has defaults (0, 0, None); it is frozen and hashable | V1 defaults |
| R-2 | buffer −1 µs, notice −1 µs, granularity 0, granularity −15 min → `InvalidAvailabilityRequest` with a message naming the setting and value; buffer 0 and notice 0 accepted | V1, S13 |
| R-3 | precedence: negative buffer together with granularity 0 reports the buffer | A6′ |
| R-4 | `QueryTime(day, aware now)` → `InvalidAvailabilityRequest`; `day` as a datetime, and `now` as a date → `TypeError` | V1, A14 |
| R-5 | `eligible_starts`: cutoff on the day → window from the cutoff; earlier day → whole day; later day → None; exact cutoff at `time.max` → None; notice `timedelta.max` → None, no `OverflowError`; `QueryTime(date.max, datetime.max)` with notice 0 → no overflow | N1, S12, S15 |

### 11.4 New rows in `test_available_starts.py` (at the entry seam)

| # | Test | Covers |
|---|---|---|
| B1 | the stage-2 anchor list exactly | S1 |
| B2 | the same without granularity | S2 |
| B3 | defaults passed *explicitly* (`rules=ResourceRules()`, `when=None`) equal A1's list and the no-keyword call | S3, V1 |
| B4 | no bookings, b 15, g 15 → last start 16:30 | S4 |
| B5 | three opening-edge sub-cases, each with and without a grid | S5 |
| B6 | touching 10:00–11:00 and 11:00–12:00 with b 15 → accepted, nothing in [10:00, 12:15); the b 60 pair likewise | S6, B3 |
| B7 | true overlap with b 15 → `OverlappingBookingsError` naming the raw pair | S7 |
| B8 | d 45 → 10:00 offered; d 60 → not offered | S8 |
| B9 | booking 17:00–18:00 with b 15 → 16:30 offered | S9 |
| B10 | g 20; g 10 h; C1 with g 15; hours 09:10 with g 15 | S10, G1 |
| B11 | notice 2 h and 90 min cutoffs; C1 now 09:50 → first 10:15 | S11, N1 anchors |
| B12 | the four across-day cases | S12 |
| B13 | notice > 0 without `when` → error; the A6′ precedence triples (duration vs N2; N2 vs overlap) | S13, N2 |
| B14 | `now` exactly at a start is kept; earlier starts dropped | S14, N2 |
| B15 | `timedelta.max` for d, b, and notice separately; booking ending 23:50 with b 30 in hours 20:00–`time.max` | S15, M1 |
| B16 | permutations of S6's input and of S1's input give identical output | S16 |
| B17 | booking straddling close with b 15 → the preceding slot must end by 16:30 | §9.2 |
| B18 | buffer larger than a block-closed gap → that gap offers nothing; the later gaps are unaffected | §9.2 |
| B19 | granularity with d not a multiple of g → every fitting grid point | G1 |
| B20 | notice + grid: the grid does not shift (the points kept are exactly the no-notice points ≥ cutoff) | N1 |
| B21 | `ResourceRules` passed positionally raises `TypeError` (the keyword-only seam) | H4 |
| B22 | overlapping bookings + a cutoff on a later day → still `OverlappingBookingsError` (validate before `[]`) | A6′ |
| B23 | `now` with notice 0 on a past day → `[]`; the same query without `when` → the full list | A12, N2 |
| B24 | a generator of bookings with b > 0 works | signature contract |

### 11.5 `test_invariants.py` extension (seeded, `random.Random(20260923)`)

The generator is stage 1's, plus:
- buffer ∈ {0, random 0–90 min};
- granularity ∈ {None, random 1–60 min};
- `when` ∈ {None, random `now` from the previous day to the next day, with notice 0–10 h};
- a deliberate share of **buffer-violating** inputs (neighbours closer than b), and bookings just
  before opening and after closing.

The oracle uses its own `datetime.combine(date.min, t)` arithmetic. Let `U` = the union of
`[s, e+b)` (cut at midnight) ∩ H. For result `S`:

1. **Fits (B2):** `[s, s+d) ⊆ H` and `[s, s+d+b)` is disjoint from `U`.
2. **Order:** strictly ascending.
3. **Grid exactness (G1):** with g, `S` equals the brute-force set of `H.start + k·g` satisfying
   property 1 and the N1 predicate (the generator keeps H/g small enough to enumerate).
4. **Gap-aligned soundness and completeness (R1 with buffer):** with no grid and no `when`, the stage-1
   properties 4–5 hold with "gap origin" read as a point of H that is not in `U` and is either `H.start`
   or the end of a `U` component, and with "free" read as property 1.
5. **Notice is a pure filter (N1, "never moves anchors"):**
   `S(when) == [t ∈ S(no when, notice 0) if combine(day, t) ≥ now + notice]`.
6. **Stage-1 reduction (S3):** with b = 0, no grid, and no `when`, `S` equals the stage-1 properties
   verbatim (the existing properties 1–7 run on this subset unchanged).
7. **Metamorphic C10 (S16):** a reshuffle gives an identical `S`, including on buffer-violating input.
8. **Metamorphic R3 with buffer:** adding a booking that overlaps no other booking and whose
   `[s, e+b)` misses H leaves `S` identical.
9. **Buffer monotonicity:** raising b never adds a start (`S(b′) ⊆ S(b)` for b′ > b, grid fixed). This
   is a cheap cross-check on the occupancy owner.

The overlap generator is re-run with a random buffer > 0: the same pair is reported as with b = 0
(R4 is independent of the buffer).

### 11.6 `test_public_surface.py`

P1–P3 are changed as in §11.1. New **P6**: `ResourceRules` and `QueryTime` are frozen, and their public
members are exactly the fields plus `eligible_starts` (on `QueryTime` only).

---

## 12. Records to update (proposed text; not written, per the objective)

- **decisions/0005: stage-2 architecture.**
  - Buffer = occupancy in `DaySchedule` (widen → clip → union; R4 on raw first). B2 = openings
    (only block-closed gaps are shrunk by the buffer).
  - The alignment policy is a lattice choice, `(opening.start, d)` or `(hours.start, g)`, over the one
    total `TimeRange.fitting_starts`. `leading` is cut.
  - Notice is converted once in the published `QueryTime.eligible_starts` into a time-of-day window.
  - The published `ResourceRules` owns V1; the entry gains keyword-only `rules`/`when`.
  - Supersedes 0003 in part: the R1 mechanics (`leading`), `free_gaps` → `openings`, I3 → I3′.
- **architecture.md.**
  - Seams: add `ResourceRules` and `QueryTime`.
  - Invariants: occupancy is the separated union; R4 on raw bookings before buffers; the core sees no
    date or instant.
  - Change axes: "Slot policy → `_aligned_starts` (a lattice)"; "Occupancy → `DaySchedule.__init__`";
    "Instant/calendar → `query_time.py`".

---

## 13. Result

**met.**
- Each new rule has exactly one owner: B1–B3 and M1 in occupancy (`DaySchedule`, with M1's geometry
  in `shift_end`), G1 in the alignment policy, N1 in `QueryTime`, N2 in the entry's `_eligible_starts`,
  and V1 at the construction of `ResourceRules`/`QueryTime` plus N2.
- Every stage-1 rule keeps its owner. R1's owner is the same function, now choosing a lattice.
- Defaults reproduce stage 1 bit-for-bit, by structure rather than by a special case.
- Every element has a concrete stdlib signature.

## 14. New facts and risks

1. **Opening edge vs A1 subtlety (resolved, worth pinning):** the buffer must be applied *before* the
   clip (B1, S5) but *after* the raw R4 check (B3). Only the order 1 → 2 → 3 → 4 satisfies both. Tests
   B5 and B6 pin it.
2. **Extending blocks backwards is wrong** (S9). Anyone "simplifying" B2 into occupancy padded on both
   sides would ship a wrong 16:30. Pinned by B9.
3. **Past-day queries with `now` return `[]`** (A12). This is literal 0004, but a UI that shows past
   days would be surprised. It is a product confirmation, not a design gap.
4. **`day` / ranges coherence is a caller contract** (A13). It cannot be checked without dates on the
   ranges.
5. **Unbounded output (A5′) remains.** With a grid the work is proportional to output. Without a grid,
   a tiny duration still gives about 2.9·10¹⁰ starts. The notice filter iterates the pre-filter starts,
   so a late cutoff on a 1 µs duration still does all the stepping work. This is acceptable under "no
   stated performance requirement". If it ever matters, the window's start could be passed into
   `fitting_starts` as a lower bound, but only on the grid path, because on the gap-aligned path a
   lower bound must not move anchors.
6. **Open product question (not blocking):** should the grid ever be combined with gap-aligned anchors
   (for example "grid, but also offer the first free moment")? This is not decided. If it is ever
   decided, it is the falsifier that would earn a real policy seam (§3.6).
