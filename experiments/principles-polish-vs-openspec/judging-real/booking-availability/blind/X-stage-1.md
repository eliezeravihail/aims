# Design X — stage 1

# Stage 1 — Bookable time slots: architecture (the-method, single arm)

Design objective, **Kind: design**. Run in stepped `plan` + the method's one mandatory
review-and-revise round on the design objective. Deliverable is architecture only — no implementation
code. Durable records filed in the project tree (`goals.md`, `architecture.md`, `base-dependencies.md`,
`decisions/0001–0003`, `.method/state.md`); this file is the frozen consolidated design.

## 1. Objective and the hard decision

Return the start times at which a new booking of a given duration fits in a resource's day: a
contiguous free interval ≥ duration, inside working hours, overlapping no existing booking; offered
back-to-back from the top of each free interval, earliest first.

The judgment a naive "return the free slots" framing would let evaporate: **where does the alignment
rule live, versus where the free/busy rule lives?** Fusing them is what makes a scheduler ossify —
the next rule (a grid, a buffer, a notice window) then has nowhere to attach but the middle of the
loop. So the objective is the *ownership*: one owner for "what is free," one for "how a slot aligns."

## 2. Foundational substrate

Python 3.11+, standard library only (`dataclasses`, `datetime`). A pure compute service — no I/O,
persistence, UI, or network — so the pervasiveness test finds only the language foundational; no core
framework qualifies (`decisions/0001`). Value objects are frozen dataclasses; illegal states are
rejected at construction. (Substrate is normally *asked* of the user; carried as an assumption here.)

## 3. Domain model — value objects (§4)

No primitive stands in for a domain concept, and instant and delta are kept distinct (the common
value-correct cram is one `int` serving both):

| Type | Is | Owns |
|---|---|---|
| `TimeOfDay` | an instant within one day (minutes from midnight, `0..1440`), ordered, immutable | "what a within-day instant is"; validated on construction |
| `Duration` | a positive length (minutes); `TimeOfDay + Duration → TimeOfDay` | the delta concept; rejects non-positive |
| `Interval` | a half-open span `[start, end)`, `start < end` | the geometry **and** half-open semantics (I2) — the single home |
| `Booking` | an existing reservation | its availability projection `occupied_interval() → Interval` |

`Interval` is the sole owner of half-open overlap/intersection (`decisions/0002`), so that rule is
defined once and every consumer inherits it.

## 4. Components and the rule each owns

```
domain/time.py       TimeOfDay, Duration, Interval          (value objects; pure)
domain/booking.py    Booking                                 (entity; occupied_interval projection)
availability/free_windows.py   free_windows(...)             (owner: what time is free)
availability/packing.py        pack(...)                     (owner: how a slot aligns in a window)
availability/service.py        bookable_start_times(...)     (boundary: validate + compose)
```

- **`free_windows(working_hours, busy) -> list[Interval]`** — owns **R2**: subtract the union of
  busy intervals (each clamped to working hours; wholly-outside ones dropped) from working hours,
  giving disjoint free intervals in chronological order. Sole owner of interval-set subtraction, of
  the union of overlapping / adjacent / duplicate bookings, and of clamping (`decisions/0003`).
  Order-independent (sorts internally).
- **`pack(window, slot) -> Iterator[TimeOfDay]`** — owns **I4**: emit `window.start,
  window.start+slot, …` while `start + slot ≤ window.end`. Sole owner of the alignment rule
  (origin = window top, step = slot). *This is deliberately its own owner because alignment is the
  most likely rule to change (A1).*
- **`bookable_start_times(working_hours, bookings, slot) -> list[TimeOfDay]`** — the public seam and
  the functional-core/imperative-shell edge. Validates (fail fast, I5), maps bookings → occupied
  intervals, calls `free_windows`, then `pack` per window in order, concatenates earliest-first. Owns
  **I1** by composition — a start is bookable iff `pack` produced it from a real free window; no rule
  is re-implemented here.

## 5. Seams and crossing types (§0/§5)

- **Public seam:** `bookable_start_times(working_hours: Interval, bookings: Iterable[Booking],
  slot: Duration) -> list[TimeOfDay]`. Every crossing type is a domain value object/entity — never a
  bare `int`/`tuple`. Returns start times (per the spec), not slot objects.
- **Internal seams** speak `Interval`/`Duration`/`TimeOfDay` only. No component references a class
  inside another. `free_windows` and `pack` are pure; only the service is imperative (validation +
  wiring).
- **Errors are boundary vocabulary:** one domain error type `InvalidAvailabilityRequest`; value
  objects reject illegal construction at the edge, the core trusts its inputs.

## 6. Concrete signatures (buildable — a sprint can start here)

```python
# domain/time.py
@dataclass(frozen=True, order=True)
class TimeOfDay:
    minutes: int                      # 0..1440; validated in __post_init__
    def __add__(self, d: "Duration") -> "TimeOfDay": ...

@dataclass(frozen=True, order=True)
class Duration:
    minutes: int                      # > 0; validated

@dataclass(frozen=True)
class Interval:
    start: TimeOfDay
    end: TimeOfDay                    # start < end; validated
    @property
    def length(self) -> Duration: ...
    def overlaps(self, other: "Interval") -> bool: ...      # half-open
    def intersect(self, other: "Interval") -> "Interval | None": ...

# domain/booking.py
@dataclass(frozen=True)
class Booking:
    interval: Interval
    def occupied_interval(self) -> Interval: return self.interval

# availability/free_windows.py
def free_windows(working_hours: Interval, busy: Iterable[Interval]) -> list[Interval]: ...

# availability/packing.py
def pack(window: Interval, slot: Duration) -> Iterator[TimeOfDay]: ...

# availability/service.py
class InvalidAvailabilityRequest(ValueError): ...
def bookable_start_times(working_hours: Interval,
                         bookings: Iterable[Booking],
                         slot: Duration) -> list[TimeOfDay]: ...
```

## 7. Invariants (structural)

I1 fit · I2 half-open (only in `Interval`) · I3 strictly-increasing earliest-first output ·
I4 per-window alignment (only in `pack`) · I5 fail-fast at the boundary. I1/I3 follow for free
because `free_windows` returns disjoint ordered windows and `pack` is monotonic within each.

## 8. Exit-criteria trace (how the shape satisfies each)

| # | Case | Where satisfied |
|---|---|---|
| C1 | empty bookings | `free_windows` returns `[working_hours]`; `pack` from its top |
| C2 | fully booked | union covers working hours → no free window → `[]` |
| C3 | duration > every window | `pack` yields nothing when `start+slot > window.end` |
| C4 | duration == window length | `pack` yields exactly the top |
| C5 | overlapping bookings | `free_windows` unions before subtracting — no phantom gap |
| C6 | touching bookings | half-open union emits no zero-length free window |
| C7 | straddling booking | clamped to working hours before subtraction |
| C8 | wholly-outside booking | `intersect` with working hours is `None` → dropped |
| C9 | gap < duration | `pack` yields nothing in that window |
| C10 | unsorted input | `free_windows` sorts internally |
| C11 | duplicate bookings | union is idempotent |
| C12 | non-positive duration | `Duration` construction rejects → boundary error |
| C13 | empty/inverted hours | `Interval` construction rejects → boundary error |
| C14 | start == prior end | half-open `overlaps` is false at the shared endpoint |
| C15 | ordering + fit | disjoint ordered windows × monotonic `pack` |
| C16 | zero-length booking | no valid `Interval` builds → blocks nothing |

## 9. Mandatory review-and-revise round (design objective — one round)

A `design` objective is never read as met on its first pass. Measured with the assessment form;
building projection (fix-list, most-severe-first, no aggregate). The first-pass design carried three
pieces of seam ceremony that the **subtractive pass** removed:

- **`Resource(working_hours)` wrapper** — held only working hours, owned no rule. *Deleting it
  damages no current ownership* (working hours is an `Interval`). **Cut** → the boundary takes
  `working_hours` directly. Recorded as candidate axis A2-adjacent, not built (§7 falsifier: no
  present X-item forces it).
- **`Slot(start, duration, interval)` value object** — the spec asks for start times; the caller
  already knows the duration. A `Slot` owns no rule the output needs. **Cut** → return
  `list[TimeOfDay]`.
- **`SlotPacker` class** — wrapped a pure function with no state. **Cut** → a module-level `pack`.

The **concept-fit pass** (run on the design, before code) found the model sound: `pack` is a
*movement* (a cursor advanced by the delta `slot`) with no inert member; `free_windows` is a
*decomposition* (working hours partitioned into free/busy) modeled honestly as set subtraction;
instant (`TimeOfDay`) and delta (`Duration`) are distinct types, so neither crams into the other.

Post-revision fix-list: empty at S2+ — §0 seams speak domain types, §5 one-owner-per-rule holds for
R2/I4/I1, §1 covers C1–C16, §4/§7 clean after the three cuts. The one mandated round was taken and
converged; the design reads **met**. **Frozen here.**

## Cost (stage 1)
- Plan passes: 1 (single-pass `plan`, not the opening panel — stepped `/the-method-plan`).
- Design review rounds: 1 (mandatory), 3 subtractions applied, 0 further rounds needed.
- Open product decisions surfaced: 4 (carried as assumptions, no live user).
- Approx word count (this deliverable): ~1,350.
