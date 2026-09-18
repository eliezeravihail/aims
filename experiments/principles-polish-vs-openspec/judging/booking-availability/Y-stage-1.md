# Booking Availability — Stage 1 (the-method)

Design only. No implementation code. This file bundles, in prose, the Stage-1 the-method
artifacts: the affected capability spec, then the change bundle (`a-design-doc`,
`a-design-doc`, `a-design-doc`). At the end of Stage 1 the spec is **FROZEN**; Stage 2 arrives as
a separate change against this frozen baseline.

---

## `the-method/the-spec-store/availability/spec.md`

### Purpose

The **availability** capability answers a single question for one resource on one day:
*at which start times could a new booking of a requested duration be placed?* It takes the
resource's working hours, the bookings that already exist for that day, and a requested slot
duration, and returns the list of admissible start times — earliest first. It performs no
booking, no persistence, and no side effects; it is a pure computation over the day's shape.

Terms used by the requirements:

- **Working hours** — a single interval `[open, close)` on the day, wall-clock, for the
  resource (e.g. `09:00–17:00`).
- **Existing booking** — a half-open interval `[start, end)` on the same day during which the
  resource is occupied.
- **Free interval** — a maximal sub-interval of working hours that overlaps no existing
  booking.
- **Duration** — the length of the booking to be placed (e.g. 30 minutes), strictly positive.
- **Candidate start** / **slot** — a start time `s` such that `[s, s + duration)` lies wholly
  inside one free interval.

All intervals are treated as **half-open** `[start, end)`: a booking that ends exactly when
another begins does not overlap it, and a booking ending at `close` is inside working hours.

### Requirements

#### The system must confine every offered slot to the resource's working hours.

A candidate start `s` is admissible only if `[s, s + duration)` is contained in `[open, close)`.
No slot may begin before `open`, and no slot may end after `close`.

- **Scenario: slot must end by close of day**
  - **Given** working hours `09:00–17:00` and a requested duration of 30 minutes
  - **And** no existing bookings
  - **When** availability is computed
  - **Then** the last offered start is `16:30`
  - **And** no start later than `16:30` is offered (a `16:45` start would end at `17:15`, past close).

- **Scenario: nothing fits before open**
  - **Given** working hours `09:00–17:00`
  - **When** availability is computed
  - **Then** no start earlier than `09:00` is offered.

#### The system must exclude any slot that overlaps an existing booking.

A candidate `[s, s + duration)` must not intersect any existing booking's interval. Because
intervals are half-open, touching at an endpoint is not an overlap.

- **Scenario: no overlap with an existing booking**
  - **Given** working hours `09:00–17:00`, duration 60 minutes
  - **And** an existing booking `10:00–11:00`
  - **When** availability is computed
  - **Then** `09:00` is offered (ends `10:00`, touches but does not overlap)
  - **And** `11:00` is offered (starts where the booking ends)
  - **And** no start in the open range `(09:00, 10:00)` or `(10:00, 11:00)` is offered.

- **Scenario: back-to-back existing bookings leave no gap**
  - **Given** working hours `09:00–17:00`, duration 30 minutes
  - **And** existing bookings `09:00–09:30` and `09:30–10:00`
  - **When** availability is computed
  - **Then** no start before `10:00` is offered.

#### The system must offer a start only where a contiguous free interval of at least the duration exists.

A slot is offered only if it fits inside one free interval whose length is `>= duration`. A
free interval shorter than the duration yields no slots; the duration is never split across two
free intervals.

- **Scenario: a gap too small yields nothing there**
  - **Given** working hours `09:00–17:00`, duration 60 minutes
  - **And** existing bookings `09:00–09:30` and `10:00–17:00`
  - **When** availability is computed
  - **Then** the free interval `09:30–10:00` (30 min) yields no slot
  - **And** the result is empty.

- **Scenario: duration exceeds the whole day**
  - **Given** working hours `09:00–10:00`, duration 90 minutes, no bookings
  - **When** availability is computed
  - **Then** the result is empty.

#### The system must align offered starts back-to-back from the top of each free interval.

Within a free interval, starts are laid down from the interval's start, spaced by exactly the
duration: `f.start, f.start + duration, f.start + 2·duration, …`, continuing while the placed
slot still ends at or before the interval's end. Slots do not overlap one another and leave no
intentional gap between consecutive offered starts inside a free interval. Any remainder shorter
than the duration at the tail of a free interval is not offered.

- **Scenario: back-to-back packing of a free interval**
  - **Given** working hours `09:00–17:00`, duration 30 minutes
  - **And** an existing booking `12:00–13:00`
  - **When** availability is computed
  - **Then** the morning free interval `09:00–12:00` yields `09:00, 09:30, 10:00, 10:30, 11:00, 11:30`
  - **And** the afternoon free interval `13:00–17:00` yields `13:00, 13:30, …, 16:30`
  - **And** no start falls inside `12:00–13:00`.

- **Scenario: tail remainder is dropped**
  - **Given** a single free interval `09:00–09:50`, duration 30 minutes
  - **When** availability is computed
  - **Then** `09:00` is offered
  - **And** `09:30` is not offered (would end `10:00`, past the interval)
  - **And** the leftover `09:30–09:50` is not offered.

#### The system must return start times in ascending (earliest-first) order.

The result is a single flat list of start times, sorted ascending, with earlier free intervals'
starts preceding later ones. Duplicate starts do not occur.

- **Scenario: earliest first across free intervals**
  - **Given** the "back-to-back packing" scenario above
  - **When** availability is computed
  - **Then** the returned list begins `09:00, 09:30, …` and ends `…, 16:00, 16:30`, strictly increasing.

#### The system must be robust to unordered, overlapping, and out-of-bounds inputs.

Existing bookings may arrive in any order, may overlap each other, and may extend partly or
wholly outside working hours. The capability normalizes them (clip to working hours, merge
overlaps) before computing free intervals; the answer is unaffected by input order.

- **Scenario: overlapping and unordered bookings**
  - **Given** working hours `09:00–17:00`, duration 60 minutes
  - **And** existing bookings supplied as `11:00–12:00`, `10:00–11:30` (overlapping, out of order)
  - **When** availability is computed
  - **Then** the occupied span is treated as `10:00–12:00`
  - **And** `09:00` and `12:00`–`16:00` starts are offered accordingly.

- **Scenario: a booking spilling past close is clipped**
  - **Given** working hours `09:00–17:00`, duration 30 minutes
  - **And** an existing booking `16:30–18:00`
  - **When** availability is computed
  - **Then** the last free interval ends at `16:30`
  - **And** the last offered start is `16:00`.

#### The system must reject invalid inputs deterministically.

Non-positive duration, `close <= open`, or malformed intervals (`end <= start`) are input
errors. The capability returns a well-formed error result rather than a slot list; it never
returns a partial list for invalid input.

- **Scenario: non-positive duration is rejected**
  - **Given** working hours `09:00–17:00` and a requested duration of `0`
  - **When** availability is computed
  - **Then** an input error is returned
  - **And** no slot list is produced.

---

## Change bundle: `add-booking-availability`

### `a-design-doc`

**Why.** Callers (a scheduling UI, a booking API) need to show a person the times at which a
resource is actually free for a booking of a chosen length. Today that logic is reinvented ad
hoc per caller, with inconsistent handling of edge cases (day boundaries, adjacent bookings,
gaps too small to use). We want one authoritative, side-effect-free capability that turns
*(working hours, existing bookings, duration)* into a list of admissible start times.

**What.** Introduce the **availability** capability (new spec `the-method/the-spec-store/availability/spec.md`).
Scope for this change:

- Compute free intervals inside working hours by subtracting existing bookings.
- Offer starts packed back-to-back from the top of each free interval, sized to the duration.
- Confine slots to working hours; forbid overlap with existing bookings; drop free intervals
  and tail remainders shorter than the duration.
- Return an ascending, earliest-first list; normalize unordered/overlapping/out-of-bounds
  bookings; reject invalid inputs.

**Out of scope (deliberately deferred).** Cleanup buffers between bookings, minimum-notice
windows relative to "now", per-resource start granularity, multi-day ranges, time-zone math,
concurrent capacity greater than one, and persistence. These are future changes against this
frozen spec.

**Impact.** New capability; no existing capability is modified. Consumers integrate against a
pure function boundary.

### `a-design-doc`

**Shape.** A single pure capability, `computeAvailability(input) -> result`. No I/O, no clock,
no storage — everything it needs is in the input, which makes it fully deterministic and
trivially testable. This purity is a deliberate decision: it keeps Stage-2 additions (buffer,
notice, granularity) expressible as extra input fields and extra filtering stages rather than
as new dependencies.

**Input model (conceptual).**

- `workingHours`: `{ open, close }` — wall-clock times on the day, `open < close`.
- `bookings`: list of `{ start, end }`, `start < end`; any order; may overlap; may exceed
  working hours.
- `duration`: positive length.

Times are represented as minutes-from-midnight (or equivalent monotonic scalar) so the whole
computation is integer interval arithmetic; the caller owns date and time-zone concerns.

**Output model.** `{ slots: [start, …] }` on success (ascending, may be empty), or
`{ error: <reason> }` on invalid input. Slots are start times only; the caller reconstructs
`[start, start+duration)`.

**Component structure (four stages, one direction of data flow).**

1. **Validate** — check `duration > 0`, `open < close`, every booking `start < end`. On failure,
   short-circuit to an error result.
2. **Normalize occupancy** — clip each booking to `[open, close)`, drop empties, sort by start,
   and merge overlapping/adjacent-into-overlap intervals into a minimal set of disjoint occupied
   intervals. This makes input order, duplicates, and overlaps irrelevant downstream.
3. **Derive free intervals** — subtract the merged occupied set from `[open, close)`, yielding a
   sorted list of disjoint free intervals. This is the single source of "where could anything go".
4. **Enumerate slots** — for each free interval in order, emit starts `f.start + k·duration`
   for `k = 0, 1, …` while `f.start + (k+1)·duration <= f.end`; concatenate across intervals to
   get the ascending result.

**Key decisions.**

- **D1 — Half-open intervals `[start, end)`.** Removes all endpoint ambiguity: a booking ending
  at `10:00` and one starting at `10:00` do not overlap, and a slot may start exactly at close of
  a prior booking. Chosen over inclusive intervals to avoid off-by-one and double-counting.
- **D2 — Alignment = back-to-back from the top of each free interval.** The card fixes this. It is
  packing per free interval, *not* a global grid; the anchor is each free interval's own start.
  (Stage 2 will reopen this in favor of a per-resource granularity grid; isolating it as its own
  requirement now makes that a clean, contained replacement later.)
- **D3 — Normalize before deriving free intervals.** Merging occupancy first means the free-interval
  derivation never sees overlaps and is a simple linear subtraction; robustness (unordered /
  overlapping / out-of-bounds bookings) falls out of Stage 2, not the enumeration stage.
- **D4 — Pure, clock-free capability.** No reading of "now" and no persistence keeps the function
  referentially transparent and keeps the Stage-1 spec free of any time-of-day-of-execution
  concept — deliberately, since minimum-notice (which needs "now") is out of scope here.
- **D5 — Errors are a distinct result, never a partial list.** Prevents a caller from mistaking a
  truncated list for a valid empty-or-short answer.

**Alternatives considered.** (a) Emitting `[start, end)` pairs instead of starts — rejected as
redundant since `end = start + duration` is known to the caller; starts keep the contract minimal.
(b) A global grid from `open` even in Stage 1 — rejected because the card specifies free-interval
packing; deferring the grid keeps Stage 1 faithful and the later change explicit.

### `a-design-doc`

Ordered, no code.

1. [ ] Write `the-method/the-spec-store/availability/spec.md` (Purpose + the seven requirements above with
   their scenarios).
2. [ ] Fix the interval convention (half-open `[start, end)`) and the scalar time representation
   in the spec's Purpose/terms.
3. [ ] Specify the input and output models and the invalid-input result shape.
4. [ ] Specify the four-stage pipeline (validate → normalize → derive free → enumerate) as the
   design of record.
5. [ ] Enumerate the acceptance scenarios: day-boundary, adjacency (touch-not-overlap), gap-too-
   small, tail-remainder dropped, unordered/overlapping/clipped bookings, invalid duration.
6. [ ] Cross-check every requirement has at least one scenario and every scenario names Given/When/Then.
7. [ ] Record decisions D1–D5 and the two rejected alternatives in `a-design-doc`.
8. [ ] Confirm the deferred list (buffer, notice, granularity, multi-day, TZ, capacity, persistence)
   is stated in `a-design-doc` so Stage 2 has an explicit baseline.
9. [ ] **FREEZE** the spec: tag this as the Stage-1 baseline; no further edits except via a new
   change bundle.

---

## Stage-1 status: FROZEN

The `availability` capability spec above is the frozen baseline. Its requirements (working-hours
confinement, no-overlap, min-length-free-interval, back-to-back-from-free-interval-top alignment,
earliest-first ordering, input normalization, invalid-input rejection) are the contract Stage 2
must either preserve, extend additively, or explicitly reopen.
