# Merged design — O1, opening panel round (merge agent, in Guide context)

## Strengths harvest (what each axis contributed)

- **Clean code** — (a) all wall-clock arithmetic in *one* file, on the range type, so the time model
  (the one R6-dependent trick: pinning `time` to a reference date) is never spread across modules
  (named the feature-envy / shotgun-surgery risk of a free stepping function); (b) the R1 *policy*
  ("tile each free gap from its own start") separated from the *mechanics* (left-aligned tiling of any
  span); (c) zero dependencies including tests (`unittest`); (d) duplicate bookings rejected as overlap;
  (e) duration ≤ 0 rejected even when no gap exists.
- **Correct encapsulation** — (a) a two-class error split by *handling* (the requester's duration vs the
  resource's calendar data) — harmonized below; (b) a seeded, stdlib-random **invariant test** over the
  whole input space (every start fits, overlaps nothing, sorted, gap-start-or-previous+d, no leftover ≥ d);
  (c) a public-surface test pinning `__all__`; (d) deterministic validation precedence; (e) surfaced the
  unbounded-output risk for microscopic durations.
- **Correct genericity** — (a) the floor/ceiling table: `Iterable[TimeRange]` in, `list[time]` out,
  `timedelta` duration, `time` not `datetime` (a date would be invented data); (b) `DaySchedule` whose
  *type* is the evidence that R4 was checked and R3 applied (field named `busy`, not `bookings`, because
  clipped spans are no longer the caller's bookings); (c) count-based stepping (`length // duration`) that
  cannot loop forever; (d) the proof that an adjacent-pair check after sorting finds every overlap and
  always names a *true* offending pair.

All three surfaced the same two open points (overlap wholly outside hours; closing at 24:00) and the same
resolution; filed as stated assumptions.

## Axis splits

1. **Public input type** — encapsulation: stdlib `(time, time)` tuples at the seam, `TimeRange` private,
   so callers never couple to internals; genericity + clean: publish `TimeRange`.
   **Decided: publish `TimeRange`** — it is a foundational value type *defined up front as part of the
   interface* (principles §0), and publishing it makes an empty/reversed/aware range unconstructible on
   the caller's side (§4 illegal states unrepresentable). A tuple alias is a data clump whose rule owner is
   invisible to the caller. Encapsulation's real concern — publishing internal *mechanics* — is honored by
   keeping the published surface of `TimeRange` to construction, fields, `length`, `overlaps`, `__str__`;
   clipping and tiling are module-private functions beside it (see §2 below).
2. **Owner of R1** — genericity: a `_stepping` module; encapsulation: `_FreeGap.slot_starts`; clean:
   `Interval.tile_starts` + one policy line. **Harmonized:** mechanics beside the range type (one file owns
   time arithmetic), policy stated once in the entry's composition line. `_FreeGap` cut: a wrapper whose
   only content is one method over a range (lightest element in its own pass).
3. **Duration** — encapsulation: `SlotDuration`; the other two: `timedelta`. **Decided `timedelta`**: its
   only rule has one owner (the one entry that accepts a duration); a wrapper moves one comparison.
   Count-based tiling means a bypassed precondition fails loudly (`ZeroDivisionError`), never hangs.
4. **Occupancy aggregate** — clean: `Bookings` (clips lazily in `free_within(window)`); others:
   `DaySchedule(hours, busy)`. **Decided `DaySchedule`**: the concept is the day's occupancy, not the
   caller's bookings; clean itself noted `Bookings` would need renaming to `Occupancy` the moment a break
   exists.
5. **Errors** — clean: one type; genericity: base + overlap subtype; encapsulation: five.
   **Harmonized to two**: `InvalidAvailabilityRequest(ValueError)` and
   `OverlappingBookingsError(InvalidAvailabilityRequest)` carrying `.first/.second` (C9's pair as data).
   The duration/schedule split is not a handling difference any stated caller has.

## The composed design

```
availability/
  __init__.py      # __all__ = TimeRange, available_starts, InvalidAvailabilityRequest, OverlappingBookingsError
  errors.py
  time_range.py    # TimeRange (published) + module-private clip/tile/arithmetic
  _day.py          # DaySchedule: validated occupancy of one day; free gaps
  slots.py         # available_starts: entry; R5-duration; R1 policy line
tests/ test_time_range.py, test_available_starts.py, test_invariants.py
```

```python
# time_range.py
@dataclass(frozen=True, slots=True)
class TimeRange:
    start: time
    end: time
    def __post_init__(self) -> None: ...   # start < end; both naive  → InvalidAvailabilityRequest
    @property
    def length(self) -> timedelta: ...
    def overlaps(self, other: "TimeRange") -> bool: ...    # self.start < other.end and other.start < self.end
    def __str__(self) -> str: ...          # "09:00–09:45" (seconds shown only when non-zero)

def _range_if_nonempty(start: time, end: time) -> TimeRange | None: ...
def clip(r: TimeRange, window: TimeRange) -> TimeRange | None: ...
def tile_starts(span: TimeRange, size: timedelta) -> Iterator[time]: ...  # count = span.length // size

# _day.py
@dataclass(frozen=True, slots=True)
class DaySchedule:
    hours: TimeRange
    busy: tuple[TimeRange, ...]
    @classmethod
    def build(cls, hours: TimeRange, bookings: Iterable[TimeRange]) -> "DaySchedule": ...
    def free_gaps(self) -> Iterator[TimeRange]: ...

# slots.py
def available_starts(working_hours: TimeRange, bookings: Iterable[TimeRange],
                     duration: timedelta) -> list[time]:
    # if duration <= 0: raise InvalidAvailabilityRequest
    # day = DaySchedule.build(working_hours, bookings)
    # return [t for gap in day.free_gaps() for t in tile_starts(gap, duration)]
```

Gap note for the Guide (present in all three, not patched): none beyond the stated assumptions.
