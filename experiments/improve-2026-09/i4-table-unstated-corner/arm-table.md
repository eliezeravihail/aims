# Appointment-slot checker — design (design only, no implementation)

Run as the aims Guide: **one single-pass design**, then **one mandatory review-and-revise round** (`decisions/0011`), graded against `experiments/improve-2026-09/i1-input-space-table/arm-table-design-principles.md`. Deliverable is a **buildable architecture** (concrete types + signatures), no implementation code.

---

## 0. Objective and scope

- **Kind:** design.
- **Objective:** establish the domain types, the single owner of the overlap rule, and the seams that localize the two named change-axes, such that `is_free` is correct across the whole input space — half-open semantics included — and X1/X2 land at a seam rather than a rewrite.
- **Present scope (grounded from the card):** a single resource; bookings and requests are half-open intervals; `is_free` is a pure query returning a boolean.
- **Out of scope today (not built — subtractive discipline):** booking lifecycle (add/cancel/persist), multiple resources (X1), recurrence (X2). X1/X2 are designed *for* (localized), not designed *in*.

### Open product decisions surfaced (not silently guessed)
1. **Substrate/language.** Concrete signatures below are in **Python 3** (dataclasses + type hints) so the design is buildable; this is properly the user-gated foundational-substrate decision (SKILL step 1) and is flagged, not assumed final. Nothing in the design depends on Python specifically.
2. **`Instant` granularity & timezone** — minute vs second vs continuous; tz-aware required? Default below: **tz-aware `datetime`, granularity unconstrained**; the representation is hidden behind `Instant` precisely because this is open.
3. **Zero-length request `[t,t)` policy** — default **reject at the boundary (fail fast)**; alternative "treat as always-free" noted. Reject chosen because a duration-less slot is not a bookable ask.
4. **`is_free` return type** — default **`bool`** per the card ("answers *whether*"); a richer "which bookings conflict" result is a foreseeable but presently unforced extension, so not built.

Intended record homes (co-located, per `references/design-record.md`): `goals.md` (scope + the four decisions), `architecture.md` (types, seams, the X1/X2 landings, invariants), a substrate ADR for decision 1, and companions on the source files once they exist. Files are **not** created here (design-only exercise).

---

## 1. Domain types (concrete representation)

### `Instant` — a point on the timeline (value object)
- **Representation:** wraps one timezone-aware `datetime.datetime`. Immutable, `@dataclass(frozen=True, order=True)`.
- **Exposes only total order** (`<`, `==`). No arithmetic — the card needs no durations.
- **Why it exists (survives the subtractive pass):** it hides the *granularity/timezone* decision (open item 2), which is exactly a "decision likely to change" that §5 says to encapsulate. It is core, not seam machinery. If the user later pins the representation permanently, it can collapse to a type alias.

### `Interval` — a half-open interval `[start, end)` (value object) — **owner of R1 and R2**
```python
@dataclass(frozen=True)
class Interval:
    start: Instant
    end: Instant
    def __post_init__(self) -> None:
        if not (self.start < self.end):
            raise InvalidInterval(self.start, self.end)   # fail fast at construction
    def overlaps(self, other: "Interval") -> bool:
        return self.start < other.end and other.start < self.end
```
- **Class invariant (R1, half-open non-empty):** `start < end`. Rejects empty (`start == end`) and reversed (`start > end`) at construction with a domain error. Because **the request is also an `Interval`**, this one invariant validates bookings and requests through a single owner.
- **`overlaps` is the single owner of R2** (below). Immutable; no other type re-implements overlap.

### `Booking` — a reservation (entity) — **owner of "a booking conflicts with a request"**
```python
@dataclass(frozen=True)
class Booking:
    interval: Interval
    # X1 later: resource: ResourceId
    # X2 later: recurrence: Recurrence
    def conflicts_with(self, request: Interval) -> bool:
        return self.interval.overlaps(request)
```
- **Concept fit:** a booking *has* an interval; it is **not** an interval. Modeling it as a bare `Interval` would be the value-correct cram — and would leave X1 (resource) and X2 (recurrence) with no home. Today it holds one field; it earns its place as the home of two named axes.
- **`conflicts_with` earns its place** by the §7 tie-break falsifier: name the X-item the seam serves → **X2**. It also keeps the Law of Demeter (the schedule never reaches through to `booking.interval`). It is the exact site X2 expands (occurrences), leaving `Interval.overlaps` and `Schedule.is_free` untouched.

### `Schedule` — the bookings on the single resource — **owner of "free ⇔ no conflict"**
```python
@dataclass(frozen=True)
class Schedule:
    bookings: tuple[Booking, ...] = ()
    def is_free(self, s: Instant, e: Instant) -> bool:
        request = Interval(s, e)                                  # validate at the edge
        return not any(b.conflicts_with(request) for b in self.bookings)
```
- Public operation matches the card's `is_free(s, e)`. The boundary constructs `Interval(s, e)` (defensive at the edge, trusting inside — §1); the core works on validated `Interval`s.
- Empty schedule ⇒ `not any(∅)` ⇒ `True` (vacuously free — **not** via a sentinel "always-free" booking).

### `InvalidInterval` — domain error (boundary vocabulary)
- Raised at `Interval` construction when `start ≮ end`. **One** error type for the one distinct handling (an invalid request/booking); no dead subtype hierarchy. The checker raises its own domain error rather than leaking a raw `ValueError` (§5).

---

## 2. The overlap / conflict predicate (stated precisely)

For two **non-empty half-open** intervals `A = [a₁, a₂)` and `B = [b₁, b₂)` (so `a₁ < a₂`, `b₁ < b₂` by the class invariant):

> **`A.overlaps(B) ≡ (a₁ < b₂) ∧ (b₁ < a₂)`**  — true iff `A` and `B` share at least one instant.

Properties (contract):
- **Symmetric:** `A.overlaps(B) == B.overlaps(A)`.
- **Reflexive on any valid interval:** `A.overlaps(A)` is true (`a₁ < a₂` both conjuncts).
- **Touching does not overlap:** if `a₂ == b₁` then `b₁ < a₂` is `a₂ < a₂` = false ⇒ no overlap. This is the half-open semantics — the excluded endpoint is the whole point of R1.
- **Both conjuncts use strict `<`.** Using `≤` would wrongly report touching intervals as overlapping.

**Conflict / freeness:**
> **`is_free(request) ≡ ∀ b ∈ bookings: ¬ request.overlaps(b.interval)`**
> equivalently **`is_free(request) = False ⟺ ∃ b ∈ bookings: request.overlaps(b.interval)`** — exactly R2.

`is_free` contract: **pure query** (CQS — returns a value, changes no state), **deterministic**, **order-independent** over `bookings`, **duplicate-insensitive** (an existential is unchanged by repeats), empty schedule ⇒ `True`.

Acceptance checks against the predicate:
- **C1** req `[13:00,14:00)`, bk `[13:30,14:30)`: `13:00<14:30 ∧ 13:30<14:00` → overlap → **not free**. ✓
- **C2** req `[09:00,10:00)`, bk `[15:00,16:00)`: `09:00<16:00 ∧ 15:00<10:00`(false) → disjoint → **free**. ✓

---

## 3. One-owner-per-rule (§5) and change-axis localization (§7)

| Rule | Single owner | When a change adds a case |
|---|---|---|
| Interval validity (R1 non-empty half-open) | `Interval.__post_init__` | — |
| Overlap (R2) | `Interval.overlaps` | absorbed here; never a second overlap path |
| "a booking conflicts with a request" | `Booking.conflicts_with` | **X2** expands occurrences *inside here* |
| "free ⇔ no conflict with any booking" | `Schedule.is_free` | **X1** keys schedules by resource *around here* |

- **X1 (multiple resources).** Lands by adding `resource: ResourceId` to `Booking`, keying schedules by resource, and extending the conflict owner with a **same-resource guard** (`booking.resource == request.resource ∧ interval overlap`) — the new case absorbed in the existing owner, **not** bolted on as a trailing filter (a second owner). `Interval.overlaps` is untouched.
- **X2 (recurrence).** Lands *inside* `Booking.conflicts_with`, which becomes `any(occ.overlaps(request) for occ in self.occurrences(request.window))`. A recurring booking is modeled as a **set of occurrence `Interval`s** (a compound), never as one mutant interval with a sentinel field. `Interval.overlaps` and `Schedule.is_free` are untouched.

Both axes are **localized, not built** (YAGNI + the §7 tie-break: each seam names the X-item it serves, so it is neither over-built nor under-provided).

---

## 4. How correctness is handled across the whole input space

The input-space table below is the mechanical trace required by arm-table §1: one row per corner the (X × R) crossing implies, column 4 answered against the concrete type chosen. **Current-scope rows** carry a required output today; **change-axis rows (16–17)** certify the *seam* the future value shape lands at (their "represent?" answer is localization, and per the note below they are §7 extension rows, not current-scope S4s).

| corner (X × R) | concrete extreme value | required output | chosen type represents this value? |
|---|---|---|---|
| 1. R2 edge — touch at end | req `[14:00,15:00)`, bk `[13:00,14:00)` | **free** | yes — `overlaps` strict `<`: `b₁(13:00)<a₂` true but `a₁(14:00)<b₂(14:00)` false → no overlap |
| 2. R2 edge — touch at start | req `[12:00,13:00)`, bk `[13:00,14:00)` | **free** | yes — `b₁(13:00)<a₂(13:00)` false → no overlap |
| 3. R2 minimal real overlap (1 unit) | req `[13:00,14:00)`, bk `[13:59,15:00)` | **not free** | yes — `13:00<15:00 ∧ 13:59<14:00` → overlap |
| 4. R2 request contained in booking | req `[13:30,13:45)`, bk `[13:00,14:00)` | **not free** | yes |
| 5. R2 booking contained in request | req `[13:00,15:00)`, bk `[13:30,13:45)` | **not free** | yes |
| 6. R2 identical intervals | req = bk = `[13:00,14:00)` | **not free** | yes — both conjuncts true |
| 7. R1 empty schedule (**empty**) | req `[09:00,10:00)`, no bookings | **free** | yes — `not any(∅)` = True (vacuous, no sentinel) |
| 8. R1 one booking — C1 | req `[13:00,14:00)`, bk `[13:30,14:30)` | **not free** | yes — overlap |
| 8b. R1 one booking — C2 | req `[09:00,10:00)`, bk `[15:00,16:00)` | **free** | yes — `15:00<10:00` false → disjoint |
| 9. R1 **many** bookings, overlaps k-th | req overlaps 3rd of N | **not free** | yes — existential over all N |
| 10. R1 many bookings, in the gap | req between two, touching neither | **free** | yes — no conjunct pair true |
| 11. zero-length request `[t,t)` | req `[13:00,13:00)` | **invalid → rejected** at boundary | yes — `Interval` invariant `start<end` rejects (`InvalidInterval`); open decision, default reject |
| 12. reversed request `start>end` | req `[14:00,13:00)` | **invalid → rejected** | yes — same invariant rejects (negative case) |
| 13. **overflow** — extreme instants | req at max representable instant vs bk near it | predicate still correct, no wraparound | yes — `Instant` over aware `datetime` (or 64-bit epoch); range ≫ appointment domain, total order, no overflow |
| 14. **absent optional** | (no nullable domain field exists) | n/a | yes — by construction no optional/nullable field exists; the "absence" case is the empty schedule (row 7) |
| 15. ordering / duplicates | duplicate bookings; any insertion order | **same result** | yes — `is_free` is an order-independent, duplicate-insensitive existential |
| 16. **X1** × R2 — second resource (compound where one implicit resource was assumed) | req `[13:00,14:00)` on resource **B**, bk `[13:00,14:00)` on resource **A** | **free** (different resource ⇒ no conflict though intervals overlap) | **localized (not built today):** add `ResourceId` to `Booking`, key `Schedule` by resource, add a same-resource guard to the conflict owner; `Interval.overlaps` unchanged. §7 extension row — see note |
| 17. **X2** × R2 — recurring booking (set of occurrences where one interval was assumed) | weekly bk `[Mon 13:00,14:00)`; req `[Mon(next) 13:30,14:30)` | **not free** (overlaps an occurrence) | **localized (not built today):** expand occurrences inside `Booking.conflicts_with` over the request window; `Interval.overlaps` and `Schedule.is_free` unchanged. Seam already present, which is why `conflicts_with` exists today |

**Note on the change-axis rows (16–17) and the S4 rule.** arm-table §1 says any `no`/blank in column 4 is an unrepresentable *required case* = an S4 to fix before shipping. The S4 test applies to **current-scope required cases** — rows 1–15, every one of which is representable (no `no`, no blank). Rows 16–17 are the **stated future axes** ("Later…"): they have no *required output today*, so they are not current S4s. Their column-4 job is the §7 check — that the design absorbs the future value shape at a seam without reopening the R2 owner — which both pass. Building the resource/recurrence machinery now would instead be over-build (YAGNI). This distinction is the honest reading; it is not hand-waving a missing case.

---

## 5. Review-and-revise round (the one mandatory round; `decisions/0011`)

Pass-1 design was measured (exit criteria + subtractive pass + concept-fit pass + input-space table). Findings returned and folded into the final design above:

- **Subtractive pass.** Only two elements were candidates for cutting: `Instant` (a wrapper that only re-exposes ordering) and `Booking` (one field today). Both **kept with explicit present-force justification** — `Instant` encapsulates the genuinely-open granularity/timezone decision (§5, a decision likely to change); `Booking` is the home of two *named* axes (tie-break falsifier passes). `conflicts_with` justified by X2 + Demeter. **No unpaid seam machinery** (no Resource/Recurrence types, no booking-lifecycle) — correctly absent.
- **Concept-fit pass.** Corrected/hardened: booking modeled as *has-an-interval*, not *is-an-interval* (avoids the value-correct cram); freeness modeled as `not any(overlap)`, **not** a score/penalty or an allow/deny sentinel; empty schedule free by vacuous existential, **not** a sentinel booking; recurrence pre-specified as a *set of occurrences* (compound), not a mutant interval — so X2 cannot later be crammed.
- **Input-space / correctness.** Added the strict-`<` justification for the touching boundary (rows 1–2) as the load-bearing half-open case; unified request and booking validation under the single `Interval` invariant (rows 11–12); pinned overflow to a range far exceeding the domain (row 13); added the explicit S4-vs-§7 note so rows 16–17 are not mistaken for missing current cases.
- **Residual (carried as ordinary loop items, not blockers):** the four open product decisions in §0 — substrate/language, `Instant` granularity+tz, zero-length policy, `is_free` return shape — are surfaced for the user, not silently resolved.

Re-measure after revision: the current-scope input-space table is complete with no `no`/blank (no S4); R1/R2 each have one owner; C1/C2 verified against the predicate; both change-axes localized at a named seam. **Design reads met** after the one revise round.

---

## 6. Buildability summary

A capable engineer could start the first sprint from this: types `Instant`, `Interval`, `Booking`, `Schedule`, error `InvalidInterval`, with concrete Python signatures; the exact overlap predicate `a₁<b₂ ∧ b₁<a₂`; `is_free` as a pure order-independent existential validating at the boundary; and the two extension points (per-resource keying around `Schedule.is_free`; occurrence expansion inside `Booking.conflicts_with`) that leave `Interval.overlaps` untouched. The only items to confirm with the user before coding are the four flagged open decisions in §0.