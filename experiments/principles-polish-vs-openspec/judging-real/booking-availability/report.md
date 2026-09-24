# Booking availability: blind design judgement (X vs Y)

Instrument: `rubric/assessment-form.md` (the 17 rows), scored with the rules in `rubric/measurement.md`: sub-check-derived row scores, a severity ceiling and weight per row, and a weighted average with an S-gate. Principle content comes from `rubric/design-principles.md`. The ground truth is `product/*`.

**Scoring conventions I followed (applied identically to all four forms):**

- **Row numbering.** The form's rows are numbered 1–17. The principles document is organised as chapters §0–§14. I used the form's rows and took each row's sub-checks from the matching principle items. The §0 seam items are folded into rows 2 and 7.
- **Capping.** `measurement.md` is canonical, and it says *"there is no global cap that overrides [the grade]"*. The form's older caps say *"S2 ≤ 8.5 · S3 ≤ 7.5 · S4 ≤ 5.0"*. I report the canonical grade and gate first, then the form-capped figure for reference.
- **What counts as the stage-2 design.** A stage-2 design is its stage-1 design plus its delta. A stage-1 finding that stage 2 does not fix is carried forward.
- **What gets no credit.** I gave no credit for self-assessment sections. That covers X's "Mandatory review-and-revise round" and "Cost" sections, and Y's "Open Questions" and "Migration Plan" prose. They count only where they specify a type, an owner, a seam, a rule or a case.

---

## Step 0: fixed inventory (from `product/`, not from the designs)

**Rules (R)**

| ID | Rule |
|----|------|
| R1 | **Fit.** A start `s` is bookable iff `[s, s+d)` lies within working hours and overlaps no booking. |
| R2 | **Alignment.** Starts run back-to-back from the top of each free interval. |
| R3 | **Order.** Earliest first, no duplicates. |
| R4 | **Half-open intervals.** Intervals that only touch do not conflict (implied). |
| R5 | **Invalid input.** Non-positive duration and empty or inverted intervals are rejected (implied). |
| R6 | **Buffer (stage 2).** N minutes after every booking. The buffer is not free time and is not a booking (never returned, no booker). A new booking's buffer may not overlap a neighbour's booking. Per the oracle, the buffer may run to or past closing; only the booking must fit within working hours. |
| R7 | **Minimum notice (stage 2).** Starts earlier than `now + X` are not offered. Measured from the slot's start (oracle). |
| R8 | **Granularity (stage 2).** Offered starts are `open + k·G`, with the grid anchored at the start of working hours (oracle). |
| R9 | **Composition (stage 2).** The three rules apply together, and stage-1 behaviour is unchanged where they don't apply. |

**Change axes (X)**

| ID | Axis |
|----|------|
| X1 | New constraints that refine what counts as free time (the buffer). |
| X2 | The alignment policy (grid versus back-to-back). |
| X3 | A rule that depends on the wall clock (minimum notice). |
| X4 | Plausible unstated variant: per-resource or per-booking variation of those parameters, such as a different buffer per booking. |

**Acceptance cases (C)**

Stage 1:
- C1: a day with no bookings.
- C2: a fully booked day.
- C3: a gap shorter than the duration.
- C4: a gap equal to the duration, or a slot ending exactly at close.
- C5: overlapping, touching or duplicate bookings.
- C6: a booking partly or wholly outside working hours.
- C7: bookings supplied unsorted.
- C8: invalid inputs.
- C9: realignment after a booking that ends off-grid.

Stage 2:
- C10: a buffer blocks the time after a booking.
- C11: a new slot's buffer runs into the next booking.
- C12: a buffer runs past closing.
- C13: the notice cutoff: inclusive, before opening, inside the day, past closing.
- C14: the grid is anchored at opening, and free time starting off-grid waits for the next grid point.
- C15: grid combined with buffer.
- C16: all three rules together.
- C17: neutral defaults reproduce stage 1.

**Applicability** (identical for all four forms, so the grades are comparable):
- Row 15, testability: N/A. The principles classify it as *"Code-leaning (N/A on a pure design document)"*.
- Row 16, performance: N/A. No requirement is stated.
- Row 17, security: N/A. The service is a single-process library or local CLI with no trust boundary.
- 14 rows are scored.

### Sub-checks per row (same set for every form)

A score is `round(10 × passed / applicable)` (7.5 rounds to 8), then `min(score, severity ceiling)`.

| Row | Sub-checks |
|---|---|
| 1 Tell-Don't-Ask / LoD | a) interval behaviour lives on the interval type · b) no reach-through chains between components · c) the composer delegates rules rather than pulling state and deciding |
| 2 Interface / concept fit | a) the public seam's types are stated and complete · b) internal seams take the most generic sufficient type · c) every domain element is modelled as the kind of thing it is · d) peers share one altitude |
| 3 ISP | a) each component seam takes only what it uses · b) no fat interface or protocol · c) callers aren't forced to supply unused data |
| 4 Primitive obsession | a) domain concepts have types · b) an instant and a delta are distinct types · c) no bare tuple or pair at a seam · d) policy values are typed (stage 2 only) |
| 5 Anemic model | a) value objects enforce their own invariants · b) rule logic sits with its owner, not in a manager over data bags |
| 6 Cohesion / OCP | a) each module has one purpose · b) dependencies are acyclic and point downward · c) the alignment axis (X2) is isolated · d) the free-time axis (X1) has a seam · e) new rules extend owners without editing unrelated ones (stage 2 only) |
| 7 Boundary vocabulary / errors | a) seams speak domain or published types · b) one error type per distinct handling at the public seam · c) the path from where an error is raised to that type is specified coherently |
| 8 SRP | a) no god object · b) each component has one reason to change |
| 9 One owner per rule | Each rule has one home: half-open · free/busy · alignment · validation · ordering. Stage 2 adds: buffer · notice · grid anchor · fit admission. |
| 10 DRY | a) each fact has one home · b) no wrong abstraction · c) no duplicated computation path |
| 11 Naming / failure | a) names reveal intention · b) failures speak the consumer's concepts · c) the stated cases and claims match the mechanism · d) least astonishment: the result has one meaning in every mode |
| 12 YAGNI / subtractive | a) every type or method has a present force, or a named X-item (the §7 tie-break) · b) no speculative generality or pattern without a force · c) no pass-through layer |
| 13 Correctness (precondition) | a) every stated or required case is correct · b) contracts and invariants are consistent · c) edges are covered · d) failure is fast at the boundary · e) every rule is traced against every other rule and axis it interacts with |
| 14 State / effects | a) values are immutable · b) the core is pure, with a functional core and imperative shell · c) there is no global state and no clock read inside the core |

---

## 1. D1: first-round design (stage 1)

### X-stage-1

| § | principle | applies | score | severity | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 10 | — | 3/3. `Interval` "overlaps … intersect". The service "calls `free_windows`, then `pack` … no rule is re-implemented here". |
| 2 | Interface / concept fit | Y | 10 | — | 4/4. `bookable_start_times(working_hours: Interval, bookings: Iterable[Booking], slot: Duration) -> list[TimeOfDay]`. Internal seams speak "`Interval`/`Duration`/`TimeOfDay` only". |
| 3 | ISP | Y | 10 | — | 3/3. `free_windows(working_hours, busy: Iterable[Interval])` and `pack(window, slot)` each take only what they use. |
| 4 | Primitive obsession | Y | 10 | — | 3/3 (d is N/A). "instant and delta are kept distinct": `TimeOfDay` versus `Duration`. Every crossing type is "never a bare `int`/`tuple`". |
| 5 | Anemic | Y | 10 | — | 2/2. Value objects are "validated in `__post_init__`", and `Interval` owns the geometry and the half-open semantics. |
| 6 | Cohesion / OCP | Y | 10 | — | 4/4 (e is N/A). `pack` is the "Sole owner of the alignment rule" (X2). `Booking.occupied_interval()` is the footprint seam for X1. The layout is downward. |
| 7 | Boundary errors | Y | **7** | S1 | 2/3; c fails. The error type is placed in the service (`availability/service.py: class InvalidAvailabilityRequest(ValueError)`), but the rejection happens in the domain: "value objects reject illegal construction at the edge". The path from, for example, `Duration.__post_init__` (in `domain/time.py`) to that type is unspecified, and raising it from the domain would import the service upward. The service also "Validates (fail fast, I5)" without saying what it validates beyond the value objects. Local; the type subclasses `ValueError`. |
| 8 | SRP | Y | 10 | — | 2/2. Five units, one rule each (§4 list). |
| 9 | One owner | Y | 10 | — | 5/5. "`Interval` is the sole owner of half-open overlap"; `free_windows` is the "Sole owner of interval-set subtraction … union … clamping"; `pack` is the "Sole owner of the alignment rule". I3 follows from composition. |
| 10 | DRY | Y | 10 | — | 3/3. Each rule is defined once (I2 "only in `Interval`", I4 "only in `pack`"). |
| 11 | Naming / failure | Y | **8** | S1 | 3/4; c fails. The case table contradicts the types. "C16 zero-length booking: no valid `Interval` builds → blocks nothing". But `Interval` is "start < end; validated" and C13 says "`Interval` construction rejects → boundary error". So a zero-length booking is described as ignored, yet the types make it an error. The spec doesn't fix this edge case, so I classed it as a documentation-truth issue rather than §13. |
| 12 | YAGNI | Y | 10 | — | 3/3. Three wrappers were cut ("`Resource(working_hours)`", "`Slot`", "`SlotPacker`"). `occupied_interval()` passes through for now but names its X-item (X1, the buffer), so the §7 tie-break makes it acceptable. |
| 13 | Correctness | Y | 10 | — | 5/5. Every C1–C9 case is traced (C1–C16 table), and all check out. Fail-fast: "`Duration` construction rejects". |
| 14 | State | Y | 10 | — | 3/3. "Value objects are frozen dataclasses". "`free_windows` and `pack` are pure". |
| 15–17 | — | N/A | — | — | Code-leaning, or no stated requirement or boundary. |

**Profile.** Weighted average = (12×10 + 7 + 8) / 14 = **9.64**. Worst = 7. (#S3, #S4) = (0, 0). Gate **CLEAR**. The form cap does not apply, so the reported grade is **9.64**.

### Y-stage-1

| § | principle | applies | score | severity | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 10 | — | 3/3. `Interval` has "half-open `overlaps` and `contains`". `find_slots` only composes `free_gaps` and `back_to_back`. |
| 2 | Interface / concept fit | Y | 10 | — | 4/4. `find_slots(query: AvailabilityQuery) -> list[datetime.time]`, where `AvailabilityQuery(working_hours: Interval, bookings: Sequence[Interval], duration: timedelta)`. Treating a booking as its interval is a faithful projection for stage 1, not a synthetic stand-in. |
| 3 | ISP | Y | 10 | — | 3/3. `free_gaps(window, busy)` and `back_to_back(gap, duration)`. |
| 4 | Primitive obsession | Y | **7** | S1 | 2/3 (d is N/A); b fails. Instants and deltas share one type. `Interval(start, end)` is "a frozen dataclass over a *day offset*", with "Internal time is a `timedelta` offset from midnight" (D2), and the duration is also a `timedelta`. So a duration can be passed where a time of day is expected. The choice is deliberate and argued (D2), and conversion happens "only at the API edge", so it is local. |
| 5 | Anemic | Y | 10 | — | 2/2. "It enforces `start < end` at construction". `AvailabilityQuery` "enforces `duration > 0`". |
| 6 | Cohesion / OCP | Y | 10 | — | 4/4. "Dependencies point only downward. `intervals` and `slotting` do not know about each other". `slotting` "is the only code that knows how slots are aligned" (X2). `free_gaps(window, busy)` takes busy intervals (X1). |
| 7 | Boundary errors | Y | 10 | — | 3/3. "`InvalidQuery(ValueError)`: the only error type the core raises". It "wraps construction errors so the message names the failing field". The CLI maps it to "stderr and exit code 2". |
| 8 | SRP | Y | 10 | — | 2/2. `cli` "Owns: the wire format only". `availability` owns composition. |
| 9 | One owner | Y | 10 | — | 5/5. The model "Owns: all input-validity rules. Nothing downstream re-validates". `Interval` is the "single owner of rule A2". `intervals` owns A3 and gap ordering. `slotting` owns A1. |
| 10 | DRY | Y | 10 | — | 3/3. No fact is repeated. |
| 11 | Naming / failure | Y | 10 | — | 4/4. The error names the field (e.g. "`bookings[2]: start 11:00 is not before end 10:00`"). |
| 12 | YAGNI | Y | 10 | — | 3/3. "Pluggable alignment strategies, buffers … stage 1 does not build them". D1 rejects a repository. A CLI is allowed by the substrate: "a library with a small CLI … the design's call". |
| 13 | Correctness | Y | 10 | — | 5/5. I re-computed every scenario and all are correct: off-grid realignment "09:00, 09:30, 11:15, 11:45, 12:15, 14:00 … 16:30"; overlapping bookings "09:00, 11:00, 11:30"; a booking before hours "09:30, 10:00, 10:30". Fail-fast holds by construction (D4). |
| 14 | State | Y | 10 | — | 3/3. "A pure core: … no clock, I/O, or global state". |
| 15–17 | — | N/A | — | — | As for X. |

**Profile.** Weighted average = (13×10 + 7) / 14 = **9.79**. Worst = 7. (#S3, #S4) = (0, 0). Gate **CLEAR**. The reported grade is **9.79**.

**D1 winner: no clear advantage.** The two stage-1 designs have almost the same structure: a pure core, interval subtraction owned in one place, alignment isolated in its own owner, and validation at construction. The 0.15 gap comes entirely from S1 nits on each side: X's error path and its contradictory C16 note, against Y's shared `timedelta` for instants and deltas. Either nit could be removed locally.

---

## 2. D2: change absorption

**Classification rule (applied identically to both designs):**
- **Survived:** unchanged.
- **Extended:** a compatible, additive change, with the stage-1 contract intact.
- **Reopened:** the stage-1 responsibility or boundary was altered. That means an incompatible signature, a new rule added to an existing owner's contract, or the owner's core rule rewritten.
- **Discarded:** the component is gone.

A component and the seam that calls it count as one instance.

### X: survival

| Stage-1 element | Fate | Evidence |
|---|---|---|
| `TimeOfDay` | survived | "within-day model held; notice's `datetime` stayed at the boundary" |
| `Duration` | survived *as claimed*, but see the flag below | "reused verbatim as the type of N, X, and G" |
| `Interval` | extended | "one new op `expanded_by(Duration)`" |
| `Booking` / `occupied_interval()` | survived | "buffer is *not* a booking, so no change to the entity" |
| **`free_windows`** (and the service→`free_windows` seam) | **reopened** | Stage 1: `free_windows(working_hours: Interval, busy: Iterable[Interval])`, owner of interval-set subtraction. Stage 2: `windows = free_windows(effective, buffer=N, bookings)`, and "Buffer → one owner, `free_windows`". Its signature changed from busy intervals to bookings plus a buffer, and it gained a domain rule. X's own table labels this "extended", but by the definition above it is reopened. |
| **`pack`** (and the service→`pack` seam) | **reopened** | "`pack` (alignment owner) \| **reopened** \| its core rule (origin+step) generalized to a grid"; "`pack` gains the global anchor as an input when G is set" |
| `bookable_start_times` (public seam) | extended | "notice narrowing + passes new policy". The new signature is never given, and the fact that `now` must be passed conflicts with the backward-compatibility claim; this is scored in the stage-2 form. |
| `InvalidAvailabilityRequest` | survived | not touched |
| *(new)* `Resource` | new | Stage 1 deliberately cut it; stage 2 introduces it: "`Resource` now earns its place" |

**X reopened + discarded = 2:** `free_windows` and `pack`. Nothing was discarded.

**Flag on `Duration`.** X says it survived "verbatim", but stage 1 fixes `Duration.minutes: int  # > 0; validated` ("rejects non-positive"). Stage 2 sets the defaults "N=0, X=0" (D5, D12). A `Duration` cannot hold 0. Making that true requires either reopening `Duration`'s invariant or adding a new type. Counting that, the tally would be 3. I scored the contradiction in the stage-2 form below.

### Y: survival

| Stage-1 element | Fate | Evidence |
|---|---|---|
| `model.Interval` | survived | not changed |
| `model.AvailabilityQuery` (and `.of`) | extended | "gains `rules: ResourceRules = ResourceRules()` and `as_of: AsOf \| None = None`"; `of(...)` "gains keyword arguments". Defaults are neutral, so the change is compatible. |
| `model.InvalidQuery` | survived | the same single error type, with new validation messages |
| `intervals` (`merge`, `free_gaps`) | survived | "`intervals` is unchanged" |
| **`slotting`** (and the availability→slotting seam) | **reopened** | "The interface changes from `back_to_back(gap, duration)` to a small protocol … `SlotPolicy.starts(gap, footprint)`". The back-to-back algorithm itself is unchanged, now as the `BackToBack` class, and `Grid` and `policy_for` are added beside it. The boundary changed. |
| `availability.find_slots` | extended | the signature `find_slots(query)` is unchanged; it is "Rewire[d] … occupancy, then free_gaps, then policy, then notice filter" |
| `cli` | extended | "New optional fields: `buffer_minutes`, `min_notice_minutes`, …" |
| *(new)* | new | `occupancy` (buffer), `notice` (cutoff), `ResourceRules`, `AsOf`, `SlotPolicy` / `Grid` / `policy_for` |

Y also revised two assumptions; these are assumptions, not components, so they are not counted. A7 now reads "Before this change, 'resource' was only the carrier … Now it also carries this policy", and A1 now "applies only when the resource has no granularity".

**Y reopened + discarded = 1:** `slotting`. Nothing was discarded.

**Sensitivity.** Under a lenient rule where an additive keyword argument counts as an extension, X's `free_windows` becomes "extended", and the counts tie at 1 vs 1. Measured against the hidden survival oracle, **both extend**. Neither design tears open an inline "bookable" function, and neither models the buffer as a booking. Both widen the booking footprint, trim with notice, and give enumeration a parameter.

**D2 survival winner: Y, narrowly (1 vs 2).** The margin rests on one borderline call: Y kept its interval algebra untouched and put the buffer rule in a new module, while X put the buffer into `free_windows`. The result is not robust to the lenient reading.

### X-stage-2 form

Stage-1 findings that stage 2 does not fix are carried forward.

| § | principle | applies | score | severity | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 10 | — | 3/3. Composition stays at the boundary; `Interval.expanded_by`. |
| 2 | Interface / concept fit | Y | **5** | S2 | 2/4; a and c fail. **(a)** The stage-2 public seam is never specified. The only statement is "`bookable_start_times` (boundary) \| extended \| notice narrowing + passes new policy", and `now` is only "an absolute instant injected at the boundary". No signature carries `Resource` or `now`, although stage 1 had a "Concrete signatures (buildable)" section. **(c)** Concept fit: the product's trailing buffer ("buffer … *after* every booking") is modelled as a symmetric pad on existing bookings: "expanding each existing booking's blocked interval to `[start − N, end + N)`". The concept is then renamed to fit ("name the owned rule **'minimum inter-booking separation N'**"). The leading pad is really the *new* booking's buffer attached to its neighbour. It gives correct values for a single per-resource N, but it cannot express X4 (a buffer per booking) without reopening. The design's stated dilemma ("(b) … splits one rule across two owners") is false: a footprint of duration + N on the candidate keeps the buffer trailing with one owner. |
| 3 | ISP | Y | 10 | — | 3/3. |
| 4 | Primitive obsession | Y | **8** | S1 | 3/4; c fails. The grid crosses the `pack` seam as an untyped pair: "Generalize the alignment owner to a `(origin, step)` grid"; "`grid = (open,G) if G else (window.top,D)`". No grid type is named. N, X and G are typed as `Duration` (d passes). |
| 5 | Anemic | Y | 10 | — | 2/2. "`Resource` holds policy and computes nothing" is fine here: it is configuration, and the rules live in their owners. |
| 6 | Cohesion / OCP | Y | 10 | — | 5/5. The buffer lands in the free-time owner, the grid in the alignment owner, and notice at the boundary. |
| 7 | Boundary errors | Y | **7** | S1 | 2/3. Carried from stage 1: the path from domain construction errors to `InvalidAvailabilityRequest` is unspecified. Stage 2 adds validation of N, X and G without saying where it is raised. |
| 8 | SRP | Y | 10 | — | 2/2. |
| 9 | One owner | Y | 10 | — | 9/9. Buffer in `free_windows`; grid in `pack` ("still **one owner**"); notice at the boundary. The two notice mechanisms (window narrowing and a filter) are both in the one boundary owner; the redundancy is covered in §13. |
| 10 | DRY | Y | 10 | — | 3/3. The redundant notice filter is the same defect as §13(e) and is referenced there, not deducted twice. |
| 11 | Naming / failure | Y | **8** | S1 | 3/4. Carried from stage 1: the C16 contradiction. The overclaims in D12 and D6 are consequences of the §13 defects and are referenced there, not deducted again. |
| 12 | YAGNI | Y | **7** | S1 | 2/3; a fails. `Booking.occupied_interval()` ("`return self.interval`") was justified in stage 1 by X1. When X1 (the buffer) arrived, it went elsewhere ("buffer folded into [`free_windows`'] input transform"), so the hook now serves nothing. |
| 13 | Correctness (precondition) | Y | **2** | S4 | 3/5; b and e fail. **(b) The contract contradicts the design's defaults.** `Duration` is "a positive length … rejects non-positive" and is "reused verbatim as the type of N, X, and G", yet the defaults are "D5 buffer N = 0" and "D12 … a `Resource` with N=0, X=0, G=None". The design's own default configuration cannot be built. **(e) One interaction is untraced (notice × back-to-back).** Notice narrows the free window (`effective = [max(open, now + X), close)`), and with no granularity `pack` starts at `window.top`. So a cutoff of 10:37 re-anchors every later slot to 10:37, 11:37 and so on. This contradicts X's own "D6 … starts `< now+X` dropped" and "D9 G `None` → stage-1 back-to-back … preserved". It also makes D12's claim false, because a same-day `now` narrows the window even with X=0. The card says slots before the cutoff "are not offered", not that later slots move. X traced notice × granularity ("Re-anchoring would silently offer off-grid starts") but not this path. Passing checks: (a) buffer maths ("D2 gap exactly `2N` → no start"; D4 buffer past close is allowed, matching the oracle); (c) edges D1–D12; (d) fail fast. |
| 14 | State | Y | 10 | — | 3/3. "`now` … injected at the boundary (not read from a wall clock)". |
| 15–17 | — | N/A | — | — | |

**Profile.**
- Weighted average = (5×2 + 8 + 7 + 8 + 7 + 2×8 + 8×10) / 22 = 136 / 22 = **6.18**.
- Worst = 2. (#S3, #S4) = (0, 2). Gate **BLOCKED**.
- The form-capped grade (S4 ≤ 5.0) would be 5.0.
- **Sensitivity:** with both S4 items fixed, which is local work, row 13 scores 10 and the average is 130/15 = **8.67**. The form cap (S2 ≤ 8.5) would make that 8.5.

### Y-stage-2 form

| § | principle | applies | score | severity | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 10 | — | 3/3. `find_slots` "composes the rules; owns no rule". |
| 2 | Interface / concept fit | Y | 10 | — | 4/4. The public seam is fully specified: `ResourceRules(buffer, min_notice, granularity: timedelta \| None)` and `AsOf(date, now)`. On concept fit, the buffer is a trailing footprint: "Each booking … occupies `[start, end + buffer)`", and "`footprint(duration, buffer)` … the span a new slot claims". D7 rejects pseudo-booking intervals. `AsOf` "makes 'only one of date/now' impossible to represent". |
| 3 | ISP | Y | 10 | — | 3/3. `SlotPolicy` has one method. Every new field has a default. |
| 4 | Primitive obsession | Y | **8** | S1 | 3/4; b fails. Carried from stage 1: offsets and durations are both `timedelta`, and `earliest_start` returns a "`timedelta` … day offset". The new policy values are typed (d passes). |
| 5 | Anemic | Y | 10 | — | 2/2. `ResourceRules` and `AvailabilityQuery` enforce their own invariants (D13). |
| 6 | Cohesion / OCP | Y | 10 | — | 5/5. "None of the four rule modules imports another". "`intervals` is unchanged". The policy is selected through a protocol. |
| 7 | Boundary errors | Y | 10 | — | 3/3. The same `InvalidQuery` is used, with field-named messages ("an error naming the buffer"). |
| 8 | SRP | Y | 10 | — | 2/2. |
| 9 | One owner | Y | 10 | — | 9/9. Buffer: `occupancy` ("single owner of B1 and B2"). Notice: `notice`. Grid: `slotting.Grid`, selected only in `policy_for` ("the only place that turns 'granularity is set' into behavior"). Fit admission: `[s, s+fp)` inside one gap, plus the one cutoff filter. |
| 10 | DRY | Y | 10 | — | 3/3. |
| 11 | Naming / failure | Y | **8** | S1 | 3/4; d fails. The result list means different things in the two modes. In grid mode, "offered slots MAY overlap each other" (B4), so the list is alternatives. In back-to-back mode, "step `duration + buffer`, so consecutive offers are each bookable in turn" (B5), so the list is compatible offers. Each choice is stated, but a caller switching modes gets a list with different semantics. |
| 12 | YAGNI | Y | 10 | — | 3/3. The small pieces carry load. `footprint`, a one-line sum, is the single home of "a candidate claims duration + buffer". `search_window` holds B1, "a single line here". |
| 13 | Correctness (precondition) | Y | 10 | — | 5/5. I re-computed all the new scenarios and every one is correct. That covers the buffer cases ("09:20, 10:10"; the slot buffer past closing; the slot buffer into a booking after closing), the notice cases (inclusive cutoff, previous day, beyond the day, "Zero notice still excludes the past"), the grid cases (anchored at 09:10; off-grid free time "10:15 … 11:30"), grid with buffer ("09:00, 09:15"), all three together ("10:30 … 11:30") and the CLI ("09:30", "10:00"). The equivalence argument in `occupancy` holds. D10 traces notice × back-to-back and avoids re-anchoring. "Default rules reproduce stage-1 results" holds, because `as_of` is optional. |
| 14 | State | Y | 10 | — | 3/3. "Neither the core nor the CLI reads a clock" (D12). |
| 15–17 | — | N/A | — | — | |

**Profile.** Weighted average = (12×10 + 8 + 8) / 14 = **9.71**. Worst = 8. (#S3, #S4) = (0, 0). Gate **CLEAR**. The reported grade is **9.71**.

### D2 winners

- **On survival: Y, narrowly.** The reopened-plus-discarded count is 1 against 2, and the result depends on one borderline call (see the sensitivity note). By `measurement.md`, this is weak corroboration only.
- **On the stage-2 form: Y, clearly.** Y scores 9.71 and CLEAR; X scores 6.18 and BLOCKED. The verdict does **not** depend on X's two local S4 items: with both forgiven, X is 8.67. The gap then comes from structure: X's concept substitution in the buffer model and its unspecified stage-2 public seam (§2, S2), against Y's footprint model and a fully typed seam.

---

## 3. Correctness traps (`spec-and-oracle.md`)

| Trap | X | Y |
|---|---|---|
| **1. The buffer as a booking** | **Avoided.** "it is never instantiated as a `Booking` and never emitted — satisfying 'not a booking.'" (A milder issue remains: the trailing buffer is recast as a symmetric "separation"; see §2 above. It is not the trap.) | **Avoided.** "D7. The buffer is modeled as a widening of occupancy, not as pseudo-booking intervals … It also creates buffer objects that could leak into output … Rejected." |
| **2. A scattered "bookable" rule** | **Avoided.** One composer: "Composition order at the boundary". The buffer is applied once in `free_windows`, candidates are enumerated once in `pack`, and free intervals are never re-derived. Minor: notice is encoded twice in the same owner ("notice narrows the window" and "filtered to t >= notice_floor"). The two agree on the grid path but diverge on the back-to-back path (§13e). | **Avoided.** "Rules combine by **composition** … `slotting` does not know that buffers or notice exist". One pipeline: occupancy → `free_gaps` → policy → one cutoff filter. "The order in which the rules are checked SHALL NOT affect the result." |
| **3. Interaction coverage** | **Mostly avoided.** Buffer × granularity: "grid points are enumerated inside buffer-shrunk windows". The last slot needs room only for the booking: "D4 booking's trailing buffer runs past close → allowed … the new booking need not carry a trailing buffer before close (SD1)", which matches the oracle. **Missed:** notice × back-to-back re-anchors the slots (§13e). | **Avoided.** "Granularity with buffer" gives "09:00, 09:15". "New slot's buffer may run past closing" gives "09:00", while the slot's buffer may not overlap a booking after closing. D10 covers notice × back-to-back ("would then re-anchor there and shift every slot"). "All three rules combined" gives "10:30, 10:45, 11:00, 11:15, 11:30". The oracle points hold: notice is measured "from slot start", and the grid anchors at "`working_hours.start + k*g`". |

---

## 4. Residual tells and how I controlled for them

- **My method guess (X = aims, Y = OpenSpec) and the rubric's origin.** The rubric files are plainly aims material: `aims-guide` and `/aims-review` appear by name. Its guided design (by my guess, X) speaks the rubric's own vocabulary: "§4 cram", "subtractive pass", "concept-fit pass", "§7 falsifier". That creates a real risk of **vocabulary capture in X's favour**.
  - **Control:** I gave no credit for self-described passes or self-classifications. For example, X labels `free_windows` "extended", and I reclassified it by the rule.
  - X's review round *claimed* it fixed concept fit, yet I scored the buffer model's actual shape as a §4 substitution.
  - In the other direction, I credited X's structural facts even where they arrive in rubric vocabulary: the distinct instant and delta types, the three cuts, and the one-owner layout.
- **Length.** Y is roughly 3.5 times longer, mostly spec scenarios and a CLI wire format.
  - **Control:** I credited the scenarios only after re-computing each one, since correct and checkable cases are legitimate §13 evidence.
  - I gave no credit for the extra prose, tasks, migration notes or the CLI.
  - X's brevity was penalised only where a seam is genuinely unspecified: the stage-2 public signature and the grid type.
- **Checkability asymmetry.** Y's concrete WHEN/THEN examples let me verify its behaviour directly. X's D-criteria are qualitative, so I had to derive X's behaviour from its mechanism. That is how I found §13(b) and §13(e).
  - **Control:** I ran the same derivation on Y's mechanism: the `search_window` clipping, buffer-to-buffer overlap, and whether defaults reproduce stage 1. It held up.
  - I also applied the least-astonishment check (§11d) to both designs. It found an S1 in Y that X does not have.
- **The severity mechanics would amplify a local fix.** Both of X's S4 items can be fixed locally: allow a non-negative length for N and X, and filter instead of narrowing on the back-to-back path.
  - **Control:** I followed `measurement.md`'s no-global-cap rule and reported the gate separately.
  - I recomputed without them (8.67) and confirmed that the D2 form verdict holds either way. No verdict here rests on a single removable blemish.
- **Borderline survival call.** The `free_windows` classification decides whether survival is 2 vs 1 or a 1 vs 1 tie. I stated my rule, applied it to Y's `slotting` in the same way, and reported the sensitivity. That is why I call the survival win narrow.
- **Rubric inconsistencies.** The form's rows (1–17) and the principles' chapters (§0–§14) are numbered differently, and the form's caps conflict with `measurement.md`. I resolved both the same way for every design, as stated in the header.
