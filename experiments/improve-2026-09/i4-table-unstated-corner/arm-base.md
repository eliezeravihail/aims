# Appointment-Slot Checker — Architecture (design only)

Produced by a single aims planning pass followed by the one mandatory review-and-revise round (`decisions/0011`). Graded against `references/design-principles.md`. No implementation code.

Kind: **design** objective — deliverable is a buildable shape (types with concrete representation, the precise predicate, contracts, and full-input-space handling), not shipped feature code.

---

## 0. Substrate note and surfaced product decisions

**Substrate.** In a real aims run the foundational substrate (language/framework) is a *gate* asked of the user (SKILL §1). As a subagent with no user, I pin **Python 3, stdlib only, frozen dataclasses** as the *illustrative* substrate so the representation is concrete — the design's shape is substrate-independent (any language with immutable value objects works). This is the one substrate choice a real run would confirm with the user.

**Product decisions I surface rather than silently assume** ("no silent product decisions"):

- **D1 — Degenerate/empty interval rejected at the boundary.** `[s, e)` with `s ≥ e` occupies no instant and creates a real pathology (a zero-length request `[t, t)` would otherwise test as "inside" a booking under a naïve predicate). Resolution-by-design: **the `Interval` invariant is `start < end`, enforced at construction (fail-fast)**; `is_free(s, e)` with `s ≥ e` raises `InvalidInterval` at the edge. Alternative (allow empty intervals, special-case the predicate) rejected — it pushes a degenerate case into the core. This is observable behavior, so I flag it explicitly; a real run confirms it with the user.
- **D2 — Whether booking a slot enforces `is_free` is OPEN.** The card asks for a *checker* (`is_free`). Whether the complementary command `add`/`book` rejects a conflicting booking (no double-booking) is a distinct product rule and is left open, not silently decided. The checker (`is_free`) is the deliverable.

---

## 1. Domain types (concrete representation)

Four value objects/entities. Dependencies point toward the most stable, most-depended-on type (the predicate owner). Acyclic: `Schedule → Booking → Interval → Instant`.

### Instant — a point on the resource's timeline
The lightest type; its single job is an **exact total order** and hiding time-resolution (§5 information hiding). Backed by an exact integer tick (minutes from a fixed epoch) so the boundary-touch comparisons are exact — floating time would risk error precisely at the abutting cases where correctness is subtlest.
```python
@dataclass(frozen=True, order=True)
class Instant:
    _tick: int          # exact, monotonic; total order via the int. Resolution hidden.
    # constructors are the Worker's detail, e.g. Instant.from_hm(h, m)
```
Honest scope note: if the chosen substrate's own time type already gives an exact total order and the domain needs no added behavior, `Instant` collapses to an alias of it. Kept as the named domain type + representation owner.

### Interval — a half-open span `[start, end)` — **owner of the conflict predicate**
```python
@dataclass(frozen=True)
class Interval:
    start: Instant
    end: Instant
    def __post_init__(self):
        if not (self.start < self.end):          # D1: fail fast, illegal state unrepresentable
            raise InvalidInterval(self.start, self.end)
    def overlaps(self, other: "Interval") -> bool:
        return self.start < other.end and other.start < self.end   # THE predicate (R2) — one owner
```
This is the **single home of R2** (§5 one-owner-per-rule, a precondition). Everything that means "conflict" calls `Interval.overlaps`; nothing anywhere re-derives the `<` comparisons.

### Booking — a commitment occupying a span (a domain entity)
A booking is **not** the same concept as a request: both carry an interval, but a booking is a persisted entity and a request is a transient query — so a request is *not* modeled as a `Booking` (that would be the "distinct concept as a synthetic instance of an entity" cram the concept-fit pass warns against). Today a booking holds one interval; identity/resource/recurrence are the fields X1/persistence/X2 add later — **not built now**.
```python
@dataclass(frozen=True)
class Booking:
    interval: Interval
    def conflicts_with(self, request: Interval) -> bool:
        return self.interval.overlaps(request)     # Tell-Don't-Ask; the X2 extension point
```
`conflicts_with` owns a *different* rule from `overlaps` — namely **which time a booking occupies** — so it is not a second owner of the predicate (it delegates to it). It earns its place doubly: (a) **present force** — Tell-Don't-Ask / Law of Demeter: the schedule asks the booking "do you conflict?" instead of pulling `b.interval` and deciding outside it (§4/§5); (b) it is the seam where X2 lands (§2 below).

### Schedule — one resource's occupancy; owner of `is_free`
```python
class Schedule:                                   # exactly one resource's timeline
    def __init__(self, bookings: Iterable[Booking] = ()): ...
    def is_free(self, request: Interval) -> bool:
        return not any(b.conflicts_with(request) for b in self._bookings)   # R2 quantified
    def add(self, booking: Booking) -> None: ...  # command (CQS-separate); D2 enforcement is OPEN
```
`Schedule.is_free` owns the **quantification** ("no booking conflicts"). It is per-resource by concept, which is exactly the X1 seam (§2).

### The request is an Interval (no `Request` type today)
A request carries nothing beyond `[s, e)`, so it *is* a half-open `Interval`. A separate `Request` type would be inert ceremony now (subtractive pass would cut it). It earns its place only when X1 adds a resource dimension → `(resource, interval)`. Recorded, not built.

### Boundary facade — the card's literal `is_free(s, e)`
```python
def is_free(schedule: Schedule, s: Instant, e: Instant) -> bool:
    return schedule.is_free(Interval(s, e))       # build+validate the request once, at the edge
```
Defensive-at-the-edge, trusting-inside (§1): primitives are validated into an `Interval` (raising per D1) at the boundary; the core assumes valid inputs.

---

## 2. The overlap / conflict predicate — stated precisely

For a request `[s, e)` and a booking `[c, d)`, both half-open and non-empty:

> **overlap(request, booking)  ≡  s < d  ∧  c < e**

Equivalently on the type: `request.overlaps(booking) = request.start < booking.end ∧ booking.start < request.end`.

**Why this is exactly "share ≥ 1 instant."** Two non-empty half-open intervals `[a,b)`, `[c,d)` share an instant iff `max(a,c) < min(b,d)`. Given `a<b` and `c<d`, that reduces exactly to `a<d ∧ c<b`. So the predicate is *precisely* the real-overlap requirement of R2 — no more (it excludes mere touching), no less.

**Properties:** symmetric; reflexive on any valid interval; and **abutting intervals do not conflict** — `[x, y)` and `[y, z)` give `c<e ⇒ y<y ⇒ false`. This is the half-open payoff: back-to-back bookings leave the seam free.

`is_free` at the resource level:
> **is_free(request) = ¬ ∃ booking b : b.conflicts_with(request)**, and today `b.conflicts_with(request) = b.interval.overlaps(request)`.

---

## 3. Operations and contracts

All queries are pure (CQS §2): `overlaps`, `conflicts_with`, `is_free` never mutate. `add` is the sole command.

| Operation | Pre | Post / meaning | Notes |
|---|---|---|---|
| `Interval(start, end)` | `Instant`s | immutable interval, invariant `start < end` held for life | raises `InvalidInterval` if `start ≥ end` (fail-fast, D1) |
| `Interval.overlaps(other)` | both valid intervals | returns `start<other.end ∧ other.start<end`; True ⟺ share an instant | pure, symmetric; **sole owner of R2** |
| `Booking.conflicts_with(request)` | valid request interval | True ⟺ this booking occupies some instant in `request`; today `= interval.overlaps(request)` | pure; **X2 override point** |
| `Schedule.is_free(request)` | valid request interval | True ⟺ `¬∃ b: b.conflicts_with(request)` | pure query; **X1 sits above it** |
| `Schedule.add(booking)` | valid booking | booking added to this resource's occupancy | command (CQS); conflict-enforcement = D2 (open) |
| `is_free(schedule, s, e)` | `Instant`s | `= schedule.is_free(Interval(s,e))` | validates at the edge (D1) |

Invariant threaded through the whole design: **`start < end` on every `Interval`** — which is what lets the core trust its inputs and eliminates the empty-interval edge case before it can reach the predicate.

---

## 4. Correctness across the whole input space

The single general statement, valid across all three axes:

> A request `[s,e)` is **FREE on resource r** ⟺ for **every** booking `b` on `r`, for **every** interval `iv` that `b` occupies within the request's span, `¬(s < iv.end ∧ iv.start < e)`.
>
> **Today** `r` is fixed (single resource) and each booking occupies exactly `{b.interval}`, so this collapses to `is_free = ¬∃ b : s < b.interval.end ∧ b.interval.start < e`. X1 and X2 are additional *quantifiers* (over resources, over occurrences); neither changes the atom.

### Relative-position coverage (all Allen relations, half-open) — verified against `s<d ∧ c<e`
| Request vs booking | Condition | `s<d` | `c<e` | Result | Correct? |
|---|---|---|---|---|---|
| before (gap) | `e<c` | T | F | free | ✓ disjoint |
| **meets (abut)** | `e=c` | T | F | free | ✓ half-open touch |
| overlaps-front | `s<c<e<d` | T | T | conflict | ✓ (this is **C1**) |
| starts | `s=c, e<d` | T | T | conflict | ✓ |
| during (inside) | `c<s, e<d` | T | T | conflict | ✓ |
| finishes | `c<s, e=d` | T | T | conflict | ✓ |
| equal | `s=c, e=d` | T | T | conflict | ✓ |
| contains | `s<c, d<e` | T | T | conflict | ✓ |
| overlaps-back | `c<s<d<e` | T | T | conflict | ✓ |
| **met-by (abut)** | `s=d` | F | — | free | ✓ half-open touch |
| after (gap) | `d<s` | F | — | free | ✓ disjoint |

Every genuine sharing → conflict; both abutting cases and both gap cases → free. The predicate is exactly correct over the entire relative-position space.

### Acceptance cases
- **C1:** request `[13:00,14:00)`, booking `[13:30,14:30)` → `s<d`: `13:00<14:30` ✓; `c<e`: `13:30<14:00` ✓ → conflict → **not free**. ✓
- **C2:** request `[09:00,10:00)`, booking `[15:00,16:00)` → `c<e`: `15:00<10:00` ✗ → **free**. ✓

### Edge / boundary cases (§1)
- **Empty schedule** → `is_free` is vacuously True for any valid request (`any` over ∅ is False). ✓
- **Abutting** request/booking on either side → free (half-open). ✓
- **Identical / containing / contained** intervals → not free. ✓
- **Request exactly in a gap** between two bookings (e.g. bookings `[9,11),[12,14)`, request `[11,12)`) → free — abuts both, overlaps neither. ✓
- **Request spanning a gap** (overlaps ≥1 booking) → not free via any-overlap. ✓
- **Degenerate `s ≥ e`** → rejected at construction (D1); never reaches the predicate. ✓
- **Booking order** in the collection → irrelevant; `is_free` is order-independent.
- **Time exactness** → integer-tick `Instant` makes the `=`/`<` at touch points exact (no float boundary error) — the property the meets/met-by correctness depends on.

---

## 5. How the two change axes land at seams (each has a home; none reopens the predicate)

This is the §7 structure-vs-YAGNI tie-break applied with named X-items: the seams below are the ones a *foreseeable, named* change would otherwise force open (so providing them is right, not speculative), while the **machinery of the changes themselves is deliberately NOT built** (YAGNI).

- **X1 (multiple resources) → lands at `Schedule` / a future `Calendar`.** `Schedule` is *one resource's* occupancy by concept. Multi-resource is a containing map `resource → Schedule` (a `Calendar`), with `Calendar.is_free(resource, request)` selecting the schedule and delegating. `Schedule.is_free` and `Interval.overlaps` are **untouched**; the conflict relation simply becomes `(same resource) ∧ (intervals overlap)`, and "same resource" is universally true today. The public entry signature gains a `resource` argument — an inherent new dimension on a *new* method of a *new* type, not a reopen of any owner. **Not built now** (single resource has no present force for `Calendar`).

- **X2 (recurrence) → lands entirely inside `Booking.conflicts_with`.** A recurring booking occupies a *set* of occurrence-intervals; it conflicts iff the request overlaps **any** occurrence within the request's own span (the request is the natural bound — no leaked `window` parameter). Because `Schedule.is_free` already asks each booking `conflicts_with(request)`, the recurring case is absorbed **inside the booking** with `Schedule.is_free` unchanged and `Interval.overlaps` still the atom — no parallel special-case path, so no second owner (§5).
  - **Concept-fit guardrail recorded for X2:** when it lands, a recurring booking must be modeled as an **occurrence-generator** (a recurrence rule that *produces* `Interval`s), **not** as a `Booking` with a single `interval` field plus a "repeats" flag. The latter is the value-correct/concept-wrong cram (§4) — it would pass today's tests and break the moment expansion is needed. Recording this now is the cheap place to buy it (the concept-fit pass's whole point: catch it in the design, not after a rewrite).

---

## 6. Architecture (buildable skeleton)

Pure domain, no I/O or framework (functional core, §11; ports & adapters left for later, §10 — persistence/UI arrive with X1, reached *through* the domain, not the reverse).

```
scheduling/
  instant.py    # Instant           (exact totally-ordered time point)
  interval.py   # Interval, overlaps (HALF-OPEN span; SOLE owner of R2), InvalidInterval
  booking.py    # Booking, conflicts_with (occupancy; X2 extension point)
  schedule.py   # Schedule, is_free, add (one resource; X1 seam)
  # public entry is_free(s, e) — on Schedule or a thin facade
```
Dependency direction points at the most stable type: `Schedule → Booking → Interval → Instant`, acyclic; `Interval` (the predicate) is the most depended-on and most stable (§6 stable-dependencies).

---

## 7. The mandatory review-and-revise round (what it surfaced; how the final absorbs it)

The single required round (measure → return findings → revise) ran even though the first pass looked sound; it sharpened rather than overturned (a legitimate confirming-plus-sharpening outcome per `decisions/0011`):

1. **Concept-fit (forward, X2):** recorded that a recurring booking is an occurrence-generator, not a single-interval booking with a flag — §5 above. *(Sharpens the X2 seam so it is used concept-correctly.)*
2. **Subtractive / honesty:** `Instant` named as the lightest type with a single justification (exact total order + resolution hiding) that collapses to the substrate time type if that already suffices — no over-selling. *(§1 above.)*
3. **Input-space:** made the *general quantified* conflict statement explicit and showed today's `is_free` is its single-resource, single-occurrence instance — this is what proves X1/X2 don't touch the atom. *(§4 above.)*
4. **No silent product decisions:** surfaced D1 (reject `s≥e`) and D2 (`add` enforcement OPEN) with rationale rather than burying them as defaults. *(§0.)*
5. **YAGNI / performance (§13, note not build):** `is_free` is an O(n) linear scan — fine for stated needs; an interval-tree is a *future* seam only if booking counts ever demand it, explicitly **not built** now.

Subtractive pass verdict: every element earns its place against a present force — `Interval.overlaps` (R2 owner), `Booking.conflicts_with` (Tell-Don't-Ask now + X2 home), `Schedule` (the `is_free` quantifier + X1 seam), the `is_free(s,e)` facade (card's operation + edge validation). `Instant` is the one light type, kept as the representation owner and honestly labeled as collapsible.

## 8. Deliberately NOT built (YAGNI)
`Calendar`/multi-resource map (X1), recurrence expansion and a `RecurrenceRule` (X2), a `Request` type, an interval-tree index, and any persistence/UI adapter. Each has a named seam it will land at without reopening `Interval.overlaps` or `Schedule.is_free`; none has a present product force.

---

**The heart of the design in one line:** the conflict predicate `s < d ∧ c < e` lives in exactly one place (`Interval.overlaps`), it is provably "share ≥ 1 instant" for half-open intervals (so abutting is free, real overlap is not), and the two future axes are absorbed as extra quantifiers at two named seams (`Schedule` for resources, `Booking.conflicts_with` for recurrence) that never touch that predicate.