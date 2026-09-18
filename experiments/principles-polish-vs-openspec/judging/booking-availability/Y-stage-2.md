# Booking Availability — Stage 2 (the-method)

Design only. No implementation code. A change request has arrived against the **frozen**
Stage-1 baseline. This file bundles, in prose: a **SURVIVAL** map of Stage-1 against the change,
the updated/added capability specs (new requirements + scenarios), and the change bundle
(`a-design-doc`, `a-design-doc`, `a-design-doc`). A **Cost** section closes the file.

The change adds three per-resource rules, applied **together** on top of Stage 1: a cleanup
**BUFFER** after every booking, a **MINIMUM NOTICE** window relative to "now", and a start
**GRANULARITY** grid. Stage-1 behavior is unchanged where a rule does not apply (buffer 0,
notice 0, granularity unset).

---

## SURVIVAL

For each Stage-1 spec element and design component: fate (survived / extended / reopened /
discarded) and whether the Stage-2 treatment is **additive** or a **rewrite**.

| Stage-1 element | Fate | Additive or rewrite | Note |
|---|---|---|---|
| **Capability: `availability`** | survived | additive | Still one pure capability, same question, same output-of-starts contract. |
| Req: *confine to working hours* | survived | additive | Unchanged. The booking body must still fit `[open, close)`. A new booking's trailing **buffer** is explicitly allowed to run past `close` (it only constrains against neighbouring bookings, not the day boundary). |
| Req: *exclude overlap with existing bookings* | extended | additive | Overlap test now runs against each booking **plus its trailing buffer** (occupancy widened), and a candidate must also leave room for **its own** trailing buffer before the next booking. Same half-open semantics. |
| Req: *min-length free interval* | survived | additive | Still "fits in one contiguous free interval"; the free intervals are just computed from buffer-widened occupancy. |
| Req: *alignment = back-to-back from top of each free interval* | **reopened** | **rewrite** | When a resource sets a granularity, offered starts come from a **grid anchored at `open`** (`open + k·G`), each grid point tested for fit — not packed from each free interval's top. When granularity is unset, the Stage-1 rule stands. This is the one genuine rewrite. |
| Req: *earliest-first ordering* | survived | additive | Result is still a single ascending list. |
| Req: *normalize unordered/overlapping/out-of-bounds bookings* | survived | additive | Normalization now also folds each booking's trailing buffer into occupancy before merging. |
| Req: *reject invalid inputs* | extended | additive | New validations: `buffer >= 0`, `notice >= 0`, `granularity > 0` when present, and a valid `now`. |
| Design D1 (half-open intervals) | survived | additive | Reused verbatim for buffers and grid arithmetic. |
| Design D2 (free-interval packing) | **reopened** | **rewrite** | Replaced by grid-from-`open` when granularity is set; retained as the fallback. |
| Design D3 (normalize-then-subtract pipeline) | extended | additive | A buffer-widening step joins Stage 2/normalize; the pipeline shape is unchanged. |
| Design D4 (pure, clock-free) | **reopened** | additive (input, not dependency) | The capability stays pure but now takes **`now` as an explicit input**; it still reads no ambient clock. Purity preserved; the "clock-free" *concept* is narrowed to "no *ambient* clock". |
| Design D5 (errors are a distinct result) | survived | additive | Unchanged; new input errors flow through the same channel. |
| Four-stage pipeline | extended | additive | Grows from four stages to six: **validate → normalize (buffer-widened) → derive free → generate candidate starts → filter (fit + own-buffer + notice) → order**. Enumeration (old stage 4) is the part that is rewritten inside this larger pipeline. |
| Output model (`{ slots: [...] }`) | survived | additive | Identical. Buffers are **never** emitted as slots or bookings. |

**Summary:** the capability, its purpose, its output contract, and five of seven requirements
**survive additively**. Exactly one requirement — **alignment** — is **reopened and rewritten**
(free-interval packing → granularity grid, with the old rule kept as the no-granularity
fallback). One design principle (**clock-free**) is **reopened** but preserved by taking `now`
as data rather than reading a clock. Nothing is discarded.

---

## Updated capability spec: `the-method/the-spec-store/availability/spec.md`

Purpose is extended: the capability now also accepts three per-resource parameters — a cleanup
**buffer** `N` (minutes after every booking), a **minimum-notice** window `X` (hours before which
a slot may not start), and an optional start **granularity** `G` (minutes) — plus the current
instant **`now`**. It still returns start times only, earliest first, and still performs no
booking and no I/O.

New terms:

- **Buffer** — a length `N >= 0`; every booking (existing or newly placed) is followed by `N`
  minutes during which the resource is **not free**. The buffer is **not a booking**: it is never
  returned, has no booker, and never appears in output.
- **Effective occupancy** of a booking `[b.start, b.end)` — the widened blocked span
  `[b.start, b.end + N)`.
- **Notice horizon** — `now + X hours`; a slot may not **start** before it.
- **Granularity grid** — the set `{ open, open + G, open + 2G, … }` within working hours, when
  `G` is set; the anchor is the working-hours **open**, not any free interval's top.

Stage-1 requirements are retained as written **except** the alignment requirement, which is
replaced below. Requirements changed or added in Stage 2:

### The system must treat each booking's trailing buffer as occupied, without ever emitting the buffer.

Existing occupancy for free-interval derivation is the union of each booking's **effective
occupancy** `[start, end + N)`. Buffers widen what is blocked but are never returned as slots and
never described as bookings. `N = 0` reproduces Stage-1 occupancy exactly.

- **Scenario: existing booking blocks its buffer**
  - **Given** working hours `09:00–17:00`, duration 30, buffer `N = 15`, granularity unset
  - **And** an existing booking `10:00–11:00`
  - **When** availability is computed
  - **Then** the first afternoon-side free interval starts at `11:15` (booking end + buffer)
  - **And** no slot starts inside `11:00–11:15`
  - **And** the interval `11:00–11:15` is never labelled or returned as a booking.

### The system must reserve room for a newly placed booking's own trailing buffer before the next booking.

A candidate at `s` occupies `[s, s + duration)` and requires a trailing buffer
`[s + duration, s + duration + N)`. That buffer must not overlap the **next existing booking**.
Because free intervals already begin after a prior booking's buffer, the *leading* side is
handled by occupancy; this requirement handles the *trailing* side. Against the working-hours
**close** (no next booking), the trailing buffer **may** run past `close`; only the booking body
must end by `close`.

- **Scenario: own buffer must clear the next booking**
  - **Given** working hours `09:00–17:00`, duration 30, buffer `N = 15`, granularity unset
  - **And** an existing booking `10:00–11:00`
  - **When** availability is computed
  - **Then** in the morning free interval a candidate ending at `09:45` needs its buffer
    `09:45–10:00` to clear `10:00` — `09:45–10:00` touches but does not overlap `10:00`, so a
    start of `09:15` (body `09:15–09:45`) is admissible
  - **And** a start of `09:30` (body `09:30–10:00`, buffer `10:00–10:15`) is **not** admissible,
    because its buffer overlaps the `10:00` booking.

- **Scenario: last-of-day buffer may spill past close**
  - **Given** working hours `09:00–17:00`, duration 30, buffer `N = 15`, no bookings, granularity unset
  - **When** availability is computed
  - **Then** `16:30` is offered (body ends `17:00`; buffer `17:00–17:15` runs past close, allowed)
  - **And** `16:45` is not offered (body would end `17:15`, past close).

### The system must NOT offer any slot that starts before the notice horizon `now + X hours`.

A candidate start `s` is admissible only if `s >= now + X hours`. `X = 0` imposes no restriction.
This filter is applied to the day being queried; a slot whose start has already passed relative to
`now` is likewise excluded (a special case of `X = 0`).

- **Scenario: minimum notice removes early starts**
  - **Given** working hours `09:00–17:00`, duration 30, `X = 2` hours, granularity unset
  - **And** `now = 10:00` on the queried day, no bookings
  - **When** availability is computed
  - **Then** the notice horizon is `12:00`
  - **And** the earliest offered start is `12:00`
  - **And** no start before `12:00` is offered.

- **Scenario: zero notice changes nothing**
  - **Given** any inputs with `X = 0`
  - **When** availability is computed
  - **Then** no slot is removed on account of notice.

### The system must align offered starts to the per-resource granularity grid anchored at working-hours open, when a granularity is set. (REPLACES the Stage-1 alignment requirement.)

When `G` is set, candidate starts are exactly the grid points `open + k·G` (`k = 0, 1, …`) that
lie within working hours; each grid point is offered iff a booking placed there satisfies every
other requirement (fits a free interval, leaves its own buffer before the next booking, ends by
`close`, and meets the notice horizon). Consecutive offered starts are therefore `G` apart on the
grid, **not** `duration` apart, and the anchor is `open`, **not** each free interval's top. When
`G` is **unset**, the Stage-1 rule stands: back-to-back from the top of each free interval.

- **Scenario: 15-minute grid, 30-minute bookings**
  - **Given** working hours `09:00–17:00`, duration 30, `G = 15`, buffer 0, notice 0, no bookings
  - **When** availability is computed
  - **Then** starts are `09:00, 09:15, 09:30, …, 16:30` (every 15 min, overlapping candidate
    bodies are fine — only one will be booked)
  - **And** `16:45` is not offered (body would end past `17:00`).

- **Scenario: grid anchored at open, not at the free-interval top**
  - **Given** working hours `09:00–17:00`, duration 30, `G = 20`, buffer 0, notice 0
  - **And** an existing booking `09:00–09:50`
  - **When** availability is computed
  - **Then** the free interval `09:50–17:00` still draws starts from the `open`-anchored grid:
    the first admissible grid point is `10:00` (`09:00 + 3·20`), since `09:40` precedes the free
    interval — the top `09:50` is **not** itself a start unless it is a grid point.

- **Scenario: granularity unset falls back to Stage-1 packing**
  - **Given** working hours `09:00–17:00`, duration 30, `G` unset, buffer 0, notice 0
  - **And** an existing booking `12:00–13:00`
  - **When** availability is computed
  - **Then** the result equals the Stage-1 back-to-back result (`09:00…11:30`, `13:00…16:30`).

### The system must apply buffer, notice, and granularity together, and reproduce Stage-1 output when none applies.

The three rules compose: occupancy is buffer-widened, candidate starts come from the grid (or the
Stage-1 packing when `G` is unset), and each candidate is filtered by fit, own-buffer, and notice.
With `N = 0`, `X = 0`, and `G` unset, the output is byte-for-byte the Stage-1 output.

- **Scenario: all three at once**
  - **Given** working hours `09:00–17:00`, duration 30, `N = 10`, `X = 1` hour, `G = 15`
  - **And** `now = 09:20`, existing booking `11:00–11:30`
  - **When** availability is computed
  - **Then** the notice horizon is `10:20`, so the earliest grid start considered is `10:30`
  - **And** the booking's effective occupancy is `11:00–11:40`, so grid starts whose body or own
    buffer would touch that span are dropped: a `10:30` body ends `11:00` with buffer `11:00–11:10`
    overlapping the booking, so `10:30` is **not** offered; `10:15` precedes the horizon; the
    afternoon resumes at the first admissible grid point at/after `11:40`
  - **And** buffers appear nowhere in the output.

- **Scenario: neutral configuration reproduces Stage 1**
  - **Given** `N = 0`, `X = 0`, `G` unset, and any Stage-1 scenario's other inputs
  - **When** availability is computed
  - **Then** the result equals that Stage-1 scenario's result exactly.

### The system must validate the new parameters.

`N >= 0`; `X >= 0`; `G > 0` when present; `now` is a valid instant. Violations produce the same
distinct error result as Stage 1, never a partial slot list.

- **Scenario: negative buffer rejected**
  - **Given** `N = -5`
  - **When** availability is computed
  - **Then** an input error is returned and no slot list is produced.

---

## Change bundle: `add-buffer-notice-granularity`

### `a-design-doc`

**Why.** Real resources are not free the instant a booking ends (they need cleanup), cannot be
booked "right now" (staff need lead time), and expose tidy start times rather than arbitrary
offsets. Callers currently bolt these on downstream, inconsistently and after the fact —
producing slots that get rejected at booking time. Folding the three rules into the availability
capability makes the returned list actually bookable.

**What.** Extend the frozen `availability` spec with three composable, per-resource rules:

1. **Buffer `N`** — every booking is trailed by `N` minutes of not-free time that is never itself
   a booking; existing bookings widen occupancy, and a new booking must leave its own trailing
   buffer clear of the next booking (the day's close does not constrain the trailing buffer).
2. **Minimum notice `X`** — no slot may start before `now + X hours`; `now` becomes an explicit
   input.
3. **Granularity `G`** — offered starts snap to `open + k·G`; unset `G` keeps Stage-1 free-interval
   packing.

Applied together, with `N=0, X=0, G unset` reproducing Stage 1 exactly.

**Out of scope (still deferred).** Buffers *before* a booking (setup, as opposed to cleanup),
notice measured in business hours, multi-day/time-zone handling, capacity > 1, and persistence.

**Impact.** Amends one capability spec; reopens exactly one requirement (alignment) and preserves
its old behavior as a fallback; adds `now`, `N`, `X`, `G` to the input. No new dependency: the
capability stays pure by taking `now` as data.

### `a-design-doc`

**Pipeline (six stages; Stage-1's four extended).**

1. **Validate** — Stage-1 checks plus `N >= 0`, `X >= 0`, `G > 0` if present, `now` valid.
2. **Normalize (buffer-widened)** — clip bookings to working hours; replace each with its
   **effective occupancy** `[start, min(end + N, close)?]`… no: widen to `[start, end + N)` **before**
   clipping the *leading* boundary, keeping `end + N` even past `close` for occupancy purposes only,
   then merge overlaps. (Buffer past `close` only matters when another booking follows; between
   real bookings the widening is what enforces "a buffer may not overlap a neighbour".)
3. **Derive free intervals** — subtract merged effective occupancy from `[open, close)`.
4. **Generate candidate starts** —
   - if `G` set: the grid `open + k·G` within `[open, close)`;
   - if `G` unset: Stage-1 packing, `f.start + k·duration` per free interval.
5. **Filter each candidate** — keep `s` iff: body `[s, s+duration)` fits inside one free interval;
   trailing buffer `[s+duration, s+duration+N)` does not overlap the **next existing booking**
   (unbounded by `close`); and `s >= now + X hours`.
6. **Order** — concatenate/sort ascending; emit starts only. Buffers are never emitted.

**Key decisions.**

- **D6 — Buffer is occupancy, never an entity.** Modeled purely as interval widening in
  normalization plus a trailing-room filter on candidates. It has no identity, no booker, and no
  output representation — satisfying "not a booking, never returned". Chosen over modeling buffers
  as synthetic bookings, which would risk leaking them into output.
- **D7 — Trailing buffer is unbounded by `close`, bounded by neighbours.** Directly encodes the
  card: "two bookings may not be placed so a buffer overlaps a neighbour's booking" — the only
  constraint on a buffer is a neighbouring booking, not the day boundary. Keeps end-of-day slots
  bookable.
- **D8 — `now` is explicit input, not an ambient clock.** Preserves Stage-1 purity/determinism
  (Stage-1 D4) while enabling notice. Reopens "clock-free" only in the narrow sense of "no *ambient*
  clock"; testability is retained since `now` is passed in.
- **D9 — Granularity grid anchored at `open`, replacing free-interval packing.** The one rewrite.
  The card says "from the top of working hours"; a global grid, not per-interval packing. The
  Stage-1 packing is retained as the `G`-unset fallback so neutral config reproduces Stage 1.
- **D10 — Rules compose as independent stages.** Buffer lives in normalization + trailing filter,
  notice and fit live in the candidate filter, granularity lives in candidate generation. Because
  they touch different stages, "applied together" needs no special combination logic, and each
  reduces to a no-op at its neutral value.

**Interaction worked through.** With granularity on, candidate bodies may overlap one another
(grid step `G` < `duration`); this is intended — the list is *offers*, and only one is booked.
The filter still guarantees each individual offer is placeable given current occupancy (existing
buffers) and would itself leave a clean trailing buffer before the next booking.

### `a-design-doc`

Ordered, no code.

1. [ ] Confirm the SURVIVAL map: mark the alignment requirement reopened/rewrite; all others
   survived/extended/additive; nothing discarded.
2. [ ] Amend `the-method/the-spec-store/availability/spec.md` Purpose and terms to add `N`, `X`, `G`, `now`,
   buffer, effective occupancy, notice horizon, granularity grid.
3. [ ] Add the buffer-occupancy requirement (+ "buffer is never emitted" clause) with scenarios.
4. [ ] Add the own-trailing-buffer requirement, including the "spills past close is allowed" scenario.
5. [ ] Add the minimum-notice requirement with `now + X` scenarios (including `X = 0` no-op).
6. [ ] **Replace** the Stage-1 alignment requirement with the granularity-grid requirement; keep
   the Stage-1 packing as the explicit `G`-unset fallback; add anchor-at-`open` scenario.
7. [ ] Add the composition requirement (all three together; neutral config reproduces Stage 1).
8. [ ] Extend input validation (`N>=0`, `X>=0`, `G>0` if set, valid `now`) with a rejection scenario.
9. [ ] Update `a-design-doc` to the six-stage pipeline and record decisions D6–D10.
10. [ ] Verify every retained Stage-1 scenario still passes under neutral config (regression intent).
11. [ ] Cross-check: each new requirement has a scenario; each rule reduces to a no-op at its
    neutral value; buffers appear in no output scenario.

---

## Cost

- **Stage 1:** 1 design pass (spec + proposal/design/tasks, single freeze). Approx **1,500 words**.
- **Stage 2:** 1 design pass (SURVIVAL map + amended spec + change bundle). Approx **2,050 words**.
- **Total:** 2 passes, approx **3,550 words** across both stage files. No implementation code in
  either stage; one Stage-1 requirement reopened and rewritten (alignment), the rest additive.
