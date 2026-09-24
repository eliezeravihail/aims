# Judge report — booking availability (X vs Y)

Disposition: **YAGNI / simplicity.** I scored the designs blind and on structure. I credited only what each design specifies: its types, owners, seams, rules and traced cases. Neither the prose nor the principle vocabulary earned credit.

Instrument: the 17-row assessment form (`rubric/assessment-form.md`) with the mechanics from `rubric/measurement.md`:
- row score = round(10 × passed / applicable), then capped at the ceiling for the worst failed tier (S1→8, S2→7, S3→5, S4→2)
- weight by that same tier (none/S1 ×1, S2 ×2, S3 ×4, S4 ×8)
- grade = Σ(score × weight) / Σweight, with no global cap
- gate: any S4 ⇒ BLOCKED, reported beside the grade

Rows 15 (testability, code-leaning), 16 (performance: no requirement stated) and 17 (security: no trust boundary) are **N/A** for every design. They are left out of every grade, so all arms share the same applicable set.

---

## Step 0 — fixed inventory (from `product/`, not from the designs)

**R — rules**
- R1: the slot `[s, s+d)` lies inside working hours.
- R2: the slot does not overlap an existing booking.
- R3: back-to-back offering ("aligned to the top of the interval"), earliest first.
- R4: a cleanup buffer of N minutes after every booking, set per resource. The buffer is not free time and is not a booking. Buffers may not overlap a neighbour's booking.
- R5: minimum notice, measured from the slot start: `start ≥ now + X`, with X per resource.
- R6: granularity, aligned from the start of working hours, per resource.
- R7: stage-1 behaviour is unchanged where the new rules don't apply.
- R8: the buffer may run to or past closing; only the booking itself must fit inside working hours (oracle).

**X — change axes**
- X1: an occupancy refinement (buffer).
- X2: a candidate cutoff (notice).
- X3: the alignment policy (granularity).
- X4 (plausible, unstated): extra busy-time sources such as breaks, or several resources.

**C — cases**
- Stage 1:
  - C1: a day with bookings.
  - C2: an empty day.
  - C3: a slot ending exactly at close.
  - C4: a slot touching a booking.
  - C5: a duration longer than every gap → `[]`.
  - C6: unsorted input still gives earliest-first output.
- Stage 2:
  - C7: an existing booking's buffer blocks the time after it.
  - C8: a new slot's buffer versus a following in-hours booking.
  - C9: the last slot's buffer may run past closing.
  - C10: a new slot's buffer versus a booking at or after close (R4, "buffers overlap a neighbour's booking").
  - C11: the grid is anchored at the working-hours start.
  - C12: the notice cutoff is inclusive and measured from the slot start.
  - C13: all three rules combined.
  - C14: default rules reproduce stage 1.

### Sub-check catalogue (identical for all four forms)

| row | sub-checks (binary) |
|---|---|
| 1 TDA/LoD | a: no message chains across modules · b: the composer passes values and does not reach into collaborator internals · c: no private access across modules · d: no ask-then-decide on another type's fields for a rule that type owns (if this fails, it is scored in row 5 and only referenced here) |
| 2 Interface / concept fit | a: crossing types are domain or stdlib types · b: no synthetic stand-in (concept cram) · c: peers sit at one altitude · d: the crossing type is complete for its consumer |
| 3 ISP | a: published types expose only members that callers need · b: implementers are not forced into a fat role interface · c: the entry signature carries only what it needs · d: no internal type appears in a published signature |
| 4 Primitive obsession | a: ranges are a named type · b: duration is a typed length · c: output is typed · d (stage 2): rules are grouped and named · e (stage 2): the query-time context is named |
| 5 Anemic model | a: value types enforce their own invariants · b: behaviour sits with the type whose data it reads · c: no data bag plus an external type-switch · d: each rule module owns its rule's logic |
| 6 Cohesion / coupling / OCP | a: each module has one purpose · b: dependencies are acyclic and point downward · c: no feature envy (see row 5) · d: X1–X3 each land at an existing or named seam · e: no shotgun surgery for an X item |
| 7 Leaky abstractions | a: public types do not expose the internal representation · b: one module error type, one per distinct handling · c: messages name the input in caller terms · d: internals are not exported |
| 8 SRP | a: one reason to change per component · b: the composer only composes · c: validation is separated from computation · d: no god module |
| 9 One owner per rule | stage 1: fit-in-hours, no-overlap, alignment, validation, ordering (5). Stage 2 adds buffer, notice, granularity and the "bookable" admission (9 in total) |
| 10 DRY | a: one home per fact · b: no wrong abstraction · c: free time derived once · d: no duplicated validation |
| 11 Naming / least astonishment | a: names reveal intent · b: errors use the consumer's terms · c: no surprising behaviour · d: consistent vocabulary |
| 12 YAGNI / subtractive | a: no seam or protocol without a present variant or an X item · b: every class earns a class (owns something a function could not) · c: no adapter or entry point without a stated consumer · d: no guards or payloads for callers or inputs nobody stated · e: module count proportional to the rules |
| 13 Correctness | stage 1: C1–C6 (6). Stage 2: C7–C14 (8) |
| 14 State / side effects | a: immutable values · b: pure core with no clock or I/O · c: no global mutable state |

---

## 1. D1 — first-round design

### X-stage-1

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA/LoD | Y | 10 | — | 4/4. The composer only passes values: "`gaps = free_gaps(query.working_hours, query.bookings)` then `[to_time(s) for g in gaps for s in back_to_back(g, query.duration)]`". |
| 2 | Interface / concept fit | Y | 10 | — | 4/4. One interval concept is used for hours, bookings and slots: "Every interval (working hours, bookings, and offered slots) SHALL be treated as half-open". |
| 3 | ISP | Y | 10 | — | 4/4. "New public API: one query function plus value types; one CLI entry point." |
| 4 | Primitive obsession | Y | 10 | — | 3/3. `Interval`, `timedelta` duration, `list[datetime.time]` output. |
| 5 | Anemic model | Y | 10 | — | 4/4. "`Interval`… enforces `start < end` at construction and has half-open `overlaps` and `contains` semantics"; "`AvailabilityQuery`… enforces `duration > 0`". |
| 6 | Cohesion / OCP | Y | 10 | — | 5/5. "Dependencies point only downward. `intervals` and `slotting` do not know about each other". X3 lands in one place: "a later change of policy (a fixed grid, a step different from duration, buffers) touches only this module." |
| 7 | Leaky abstractions | Y | **7** | S2 | 3/4 (7a fails). The public query type is built on the internal offset representation (D2): "`Interval(start, end)`: a frozen dataclass over a *day offset*", "`AvailabilityQuery(working_hours: Interval, bookings: Sequence[Interval], duration: timedelta)`". Callers get time-of-day only through the side helper, which "converts `datetime.time` values to day offsets at the boundary". So the public dataclass constructor speaks the internal representation. The leak is local, with one type affected, hence S2. |
| 8 | SRP | Y | 10 | — | 4/4. "`cli`… Owns: the wire format only. It contains no availability logic." |
| 9 | One owner per rule | Y | 10 | — | 5/5. Validation: "Owns: all input-validity rules. Nothing downstream re-validates." Alignment: slotting "is the only code that knows how slots are aligned". Ordering is structural: "No final sort is needed". |
| 10 | DRY | Y | 10 | — | 4/4. "One place for each rule: validation, interval algebra, slot alignment, and I/O formatting each have a single owner." |
| 11 | Naming / astonishment | Y | 10 | — | 4/4. Errors name the field: "`bookings[2]: start 11:00 is not before end 10:00`". |
| 12 | YAGNI / subtractive | Y | **8** | S1 | 4/5 (12c fails). The CLI is an adapter with no stated consumer: "a thin CLI adapter (JSON in, JSON out) for manual use". It brings a wire format, exit codes, a README task and subprocess tests. The substrate permits a CLI, so this is a light cost (S1). Passes: D1 rejects a repository ("would be a speculative seam"), and there is no strategy seam ("Pluggable alignment strategies… stage 1 does not build them"). |
| 13 | Correctness | Y | 10 | — | 6/6. I hand-traced "Alignment restarts…": gaps [09:00,10:00), [11:15,13:00), [14:00,17:00) → 09:00, 09:30, 11:15, 11:45, 12:15, 14:00 … 16:30, which is correct. C3 "Slot ends at close", C4 "Slot abuts a following booking", C5 "Duration longer than working hours… not an error" and C6 "Bookings supplied out of order" are all specified and correct. |
| 14 | State | Y | 10 | — | 3/3. "A pure core: same inputs give the same output, with no clock, I/O, or global state." |
| 15–17 | — | N/A | — | — | code-leaning / no performance requirement / no trust boundary |

**Profile X-stage-1:** grade = (12×10 + 7×2 + 8×1) / 15 = **9.47** · worst **7** · (#S3,#S4) = **(0,0)** · gate **CLEAR**

### Y-stage-1

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA/LoD | Y | 10 | — | 4/4. `_gap_aligned_starts` "*tells* the range what to do (`leading`, `if_nonempty`) and never reads `start`/`end` to do its own arithmetic". |
| 2 | Interface / concept fit | Y | 10 | — | 4/4. `available_starts(working_hours: TimeRange, bookings: Iterable[TimeRange], duration: timedelta) -> list[time]`. Free time is its own value: "Free gap… a `TimeRange` **produced by** `DaySchedule.free_gaps()`". |
| 3 | ISP | Y | **8** | S1 | 3/4 (3a fails). The design says itself: "No stated caller needs `if_nonempty`, `intersection`, `overlaps` or `leading`. These four are still public methods." A published type carries internal-only members. |
| 4 | Primitive obsession | Y | 10 | — | 3/3. `TimeRange`, `timedelta`, `list[time]`. |
| 5 | Anemic model | Y | 10 | — | 4/4. `TimeRange` invariants are set in `__post_init__`, and the geometry sits on the type. |
| 6 | Cohesion / OCP | Y | 10 | — | 5/5. The acyclic graph is "slots ──► _day ──► time_range ──► errors". §9 names the landing points: buffers → "`DaySchedule.__init__`", grid → "`slots._gap_aligned_starts`". |
| 7 | Leaky abstractions | Y | 10 | — | 4/4. The representation stays private ("`_offset`/`_at`"), and "`DaySchedule` and `_gap_aligned_starts` are not exported and appear in no public signature." |
| 8 | SRP | Y | 10 | — | 4/4. "The body is three statements at one level of abstraction". |
| 9 | One owner per rule | Y | 10 | — | 5/5. The "§5 Rule → owner" table maps each rule to one mechanism. For example, R1 → "`slots._gap_aligned_starts`" and R4 → "`DaySchedule.__init__` steps 1–2". |
| 10 | DRY | Y | 10 | — | 4/4. "`_nonempty`… `start < end`: the ONE strict comparison". |
| 11 | Naming / astonishment | Y | 10 | — | 4/4. "bookings 10:00–11:00 and 10:30–11:30 overlap; bookings must not overlap (touching… is fine)". |
| 12 | YAGNI / subtractive | Y | **6** | S2 | 3/5. **12b fails:** `DaySchedule` is a private class, built once and consumed immediately by one caller: "`_day.py` is a package-private module whose one class, `DaySchedule`, is imported by exactly one sibling". Its only consumer of the type-as-evidence is its own method: "Its type is the evidence that R4 was checked… and `free_gaps` trusts that". Two private functions would keep the same ownership. **12d fails:** guards and payloads serve callers nobody stated. "**Time-zone-aware `time` values are rejected**"; "`TimeRange` guards its field types… otherwise it raises `TypeError`"; and an error subtype with a `.first/.second` payload exists because "A caller that wants to highlight two calendar entries catches this subtype". No stated caller wants that. These items spread across three of the four components, hence S2 rather than S1. Passes: no strategy seam ("A `SlotPolicy` Protocol… is over-build") and no CLI. |
| 13 | Correctness | Y | 10 | — | 6/6. The C1 trace yields "`09:45, 10:15, 12:00, 12:30, …, 16:30`". Close is inclusive ("C14… offered"), touching bookings pass ("C8"), and an oversize duration returns `[]` ("C4"). Rejecting overlapping bookings is compatible with the oracle ("Assume valid, non-overlapping bookings"), so it is not scored as wrong. |
| 14 | State | Y | 10 | — | 3/3. "`@dataclass(frozen=True, slots=True)`"; "Pure: no state, no I/O". |
| 15–17 | — | N/A | — | — | as above |

**Profile Y-stage-1:** grade = (12×10 + 8×1 + 6×2) / 15 = **9.33** · worst **6** · (#S3,#S4) = **(0,0)** · gate **CLEAR**

**D1 winner: no clear advantage.** The grades are 9.47 against 9.33, both CLEAR, and each design has one moderate defect:
- **X** exposes offset representation in its public query type.
- **Y** carries extra machinery at its edges: guards, a payload error subtype and a class where functions would do.

Under my YAGNI weighting X is slightly leaner. The one thing X adds without a present force is a CLI, and the substrate permits one. But the gap is inside what one sub-check can move. The core decomposition is essentially the same in both: free gaps, then per-gap slicing, then a pure core.

---

## 2. D2 — change absorption

### Survival classification (stage 1 → stage 2)

**X**

| stage-1 component / seam | class | evidence |
|---|---|---|
| `model.Interval` | survived | unchanged; still the day-offset interval |
| `model.InvalidQuery` | survived | still "the only error type" |
| `model.AvailabilityQuery` (+ `of`) | extended | "`AvailabilityQuery` gains `rules: ResourceRules = ResourceRules()` and `as_of: AsOf \| None = None`" |
| `intervals.merge` / `free_gaps(window, busy)` | survived | "`intervals` is unchanged"; it now receives a widened window and busy set |
| `slotting.back_to_back(gap, duration)` | **reopened** | "The interface changes from `back_to_back(gap, duration)` to a small protocol". The step semantics also change: "with step `duration + buffer`" |
| `availability.find_slots(query)` | extended | its public signature is unchanged and it still does composition only; its body is rewired ("Rewire `availability.find_slots` to follow the design's data flow") |
| `cli` | extended | "new optional JSON fields `buffer_minutes`…" |
| new | — | `occupancy`, `notice`, `ResourceRules`, `AsOf`, `SlotPolicy`/`BackToBack`/`Grid`/`policy_for` |

**X reopened + discarded = 1:** `slotting.back_to_back` becomes `SlotPolicy.starts(gap, footprint)`. Stage 1 had named this exact module as the landing point for a grid, so the reopen fell where the design predicted.

**Y**

| stage-1 component / seam | class | evidence |
|---|---|---|
| `errors` (both types) | survived | "`errors.py` — unchanged types" |
| `TimeRange` (`if_nonempty`, `intersection`, `overlaps`, `__str__`) | extended | it gains "`whole_day`, `extended`, `trimmed`, `fitting_starts`, `__contains__`" |
| `TimeRange.leading` | **discarded** | "Stage-1 `leading` is **removed**" |
| `DaySchedule` (constructor + invariant) | **reopened** | its signature gains `buffer`, and the invariant is replaced: "Stage-1 I2 'strictly ascending' and I3 'pairwise disjoint' no longer hold"; "`DaySchedule` I2 (strict) and I3 (disjoint) → I2′" |
| `DaySchedule.free_gaps` | **reopened** | "`DaySchedule.free_gaps` → `bookable_spans`", with a changed contract: "the yielded ranges are no longer free gaps" |
| `slots._gap_aligned_starts` | **reopened** | replaced by `_aligned_starts (R1 + G1)`: "replace the R1 loop with `_aligned_starts`… remove `leading`" |
| `available_starts` | extended | keyword-only additions; "a three-argument call has the same meaning, result, errors and precedence" |
| `__init__` surface / public-surface tests | extended | "`__all__` = the six names"; P1/P2 changed |

**Y reopened + discarded = 4:**
1. `leading` (discarded).
2. `DaySchedule`'s constructor and invariant (reopened).
3. `free_gaps` → `bookable_spans` (reopened).
4. `_gap_aligned_starts` → `_aligned_starts` (reopened).

All four are private or internal, and Y lists them itself as supersessions (§8.3).

**Structural note on Y (a corroborating observation, not a deduction).** Y deliberately avoided a merge step and made the gap walk rely on an ordering invariant. Its own docstring carries a "LOAD-BEARING" warning: "bookable_spans() is correct ONLY while I2′ holds". X's `free_gaps` merges and is robust to overlapping busy runs by construction. So X absorbed the buffer without touching its interval algebra, while Y had to rewrite its occupancy invariant.

**D2 winner on survival: X** (1 reopen against 4). This is weak corroboration only, per `measurement.md`, and it points the same way as the stage-2 form.

### X-stage-2

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA/LoD | Y | 10 | — | 4/4 (the 1d failure is scored in row 5). The composer passes values: "`policy.starts(gap, fp)`", "`free_gaps(window, busy)`". |
| 2 | Interface / concept fit | Y | 10 | — | 4/4. The buffer is a footprint widening, not a booking: "Existing bookings become `[start, end + buffer)`, and a candidate claims `duration + buffer`". `AsOf` pairs date and now. |
| 3 | ISP | Y | 10 | — | 4/4. The one-method protocol is "`def starts(self, gap: Interval, footprint: timedelta) -> Iterator[timedelta]`". |
| 4 | Primitive obsession | Y | 10 | — | 5/5. `ResourceRules(buffer, min_notice, granularity)` and `AsOf(date, now)`. |
| 5 | Anemic model | Y | **8** | S1 | 3/4 (5b fails). `AsOf` is a bare data bag, and its only behaviour is computed in another module from both of its fields. "`AsOf(date: datetime.date, now: datetime.datetime)`: a frozen dataclass holding the query-time facts" versus "`earliest_start(as_of: AsOf \| None, min_notice)`: returns `(as_of.now + min_notice) - datetime.combine(as_of.date, time.min)`". It is a two-line function, so S1. |
| 6 | Cohesion / OCP | Y | 10 | — | 5/5. "None of the four rule modules imports another". X4 (breaks) would add to busy time in the composer, and `intervals` would stay untouched. |
| 7 | Leaky abstractions | Y | **7** | S2 | 3/4 (7a fails; the stage-1 leak persists and widens). "Time inside the system is a `timedelta` offset from midnight of the queried day (D2)." The public `AvailabilityQuery` built on offset-`Interval` now also carries `rules` and `as_of`. |
| 8 | SRP | Y | 10 | — | 4/4. "`availability`: composition only". |
| 9 | One owner per rule | Y | 10 | — | 9/9. "buffer: `occupancy` · notice: `notice` · granularity: `slotting.Grid`". "`policy_for`… This is the only place that turns 'granularity is set' into behavior". The fit is "`[s, s + fp)` lies inside one free gap". |
| 10 | DRY | Y | **8** | S1 | 3/4 (10a fails). The fit bound is one contract with two implementations: "The contract is: ascending, `gap.start <= s`, and `s + footprint <= gap.end`", implemented in both "`BackToBack()`: `gap.start + k*footprint`" and "`Grid(anchor, step)`… then every `step` while it fits". Both live in one module under one contract, so S1. |
| 11 | Naming / astonishment | Y | **8** | S1 | 3/4 (11c fails). What the offer list means depends on the mode. Without a grid, offers are spaced "with step `duration + buffer`, so consecutive offers are each bookable in turn". With a grid, "offered slots may overlap". A caller cannot tell from the result which meaning applies. |
| 12 | YAGNI / subtractive | Y | **8** | S1 | 4/5 (12c fails). The CLI, which has no consumer, grows date and datetime parsing: "CLI: new optional JSON fields `buffer_minutes`, `min_notice_minutes`, `granularity_minutes`, `date` and `now`." 12a passes on the §7 tie-break: `SlotPolicy` serves two present variants ("returns `Grid(working_hours.start, g)` if a granularity is set, otherwise `BackToBack()`"). It is heavier than the two-value lattice it encodes, but it is forced. `occupancy` and `notice` each own exactly one rule. |
| 13 | Correctness | Y | 10 | — | 8/8, each hand-traced. C7: "Existing booking's buffer blocks the time after it" → empty. C8: "Slot plus buffer does not fit before the next booking" → empty. C9: "New slot's buffer may run past closing" → 09:00. C10: "New slot's buffer may not overlap a booking after closing" → empty. C11: "Grid anchored at the start of working hours" → 09:10, 09:40, 10:10. C12: "Start exactly at the cutoff is offered". C13: "All three rules combined" (window [09:00,12:15), busy [09:30,10:15), footprint 45, grid from 10:15 to 11:30, cutoff 10:30 → 10:30, 10:45, 11:00, 11:15, 11:30, as specified). C14: "Default rules reproduce stage-1 results". |
| 14 | State | Y | 10 | — | 3/3. "The core stays pure. `now` is data. Nothing reads a clock." |
| 15–17 | — | N/A | — | — | as above |

**Profile X-stage-2:** grade = (9×10 + 8 + 7×2 + 8 + 8 + 8) / 15 = **9.07** · worst **7** · (#S3,#S4) = **(0,0)** · gate **CLEAR**

### Y-stage-2

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA/LoD | Y | 10 | — | 4/4. The notice decision is told to `AsOf` ("`as_of.eligible_starts(notice)`") and applied with one `start in eligible`. |
| 2 | Interface / concept fit | Y | 10 | — | 4/4. "Buffer… its *effect* is occupancy… never a booking". The bookable span is its own concept. |
| 3 | ISP | Y | **8** | S1 | 3/4 (3a fails; it widens from stage 1). "Public members: `{start, end, if_nonempty, whole_day, intersection, overlaps, extended, trimmed, fitting_starts}` plus `__contains__`". Most of these serve only the package internals. |
| 4 | Primitive obsession | Y | 10 | — | 5/5. `ResourceRules`, `AsOf`, `TimeRange`, `timedelta`. |
| 5 | Anemic model | Y | 10 | — | 4/4. `AsOf` owns its conversion: "`eligible_starts(self, notice: timedelta) -> TimeRange \| None`". `ResourceRules` is a validated configuration value whose meanings are owned by the modules that apply them (the same shape as X's, and not failed there either). |
| 6 | Cohesion / OCP | Y | 10 | — | 5/5. `_day` does not import `rules` ("it receives the buffer as a `timedelta`"). The lattice is one call site. |
| 7 | Leaky abstractions | Y | 10 | — | 4/4. "`DaySchedule`, spans, the lattice choice and the eligibility helper appear in no public signature." |
| 8 | SRP | Y | 10 | — | 4/4. The entry validates, builds the day and composes. |
| 9 | One owner per rule | Y | 10 | — | 9/9. Buffer → "`DaySchedule`… owns both halves". Fit → "`fitting_starts`… the ONLY fit test in the package". Notice → "`AsOf.eligible_starts`… applied by the one `if start in eligible`". Grid → "`slots._aligned_starts`". |
| 10 | DRY | Y | 10 | — | 4/4. "Gap-aligned and grid differ only in two values — the lattice origin and the step". The two tz checks cover two separate inputs (a `time` and a `datetime`) and give two different messages, so they are not one fact stored twice. |
| 11 | Naming / astonishment | Y | 10 | — | 4/4. Offers mean the same thing in both modes: "They are alternatives for **one** new booking". The rename matches the changed contract: "the yielded ranges are no longer free gaps". |
| 12 | YAGNI / subtractive | Y | **6** | S2 | 3/5. **12b fails**, carried from stage 1: `DaySchedule` is still a single-use private class. **12d fails and widens:** new guards for input nobody stated, such as "`AsOf(day=<datetime>)` raises `TypeError`" and an aware-`now` rejection, on top of the stage-1 tz and type guards and the `.first/.second` payload. S2 because these span `TimeRange`, `AsOf` and `errors`. Passes: "`SlotPolicy` Protocol, policy classes, `Lattice`/`Grid`/`Notice`/`Buffer` types, error subtypes | none | **not added**". |
| 13 | Correctness | Y | **2** | **S4** | 7/8 (C10 fails; a precondition item, so S4). Y narrows the buffer rule to in-hours occupancy: "`[t, t + d + buffer)` must not overlap in-hours occupancy. Its buffer may run to or past closing." It then clips out any booking that starts at or after close: "S9 \| 17:00–18:00+15 ∩ H = None; tail = H. \| 16:30 ✓". The card forbids this: "two bookings may not be scheduled such that their buffers overlap a neighbour's booking". The reproducing input is in §3, trap 3. The other seven pass: C7 is "B1 Buffer is occupancy"; C8 is the S8 trace ("d 60 → not offered"); C9 is the S4 trace ("Its buffer to 17:15 is never looked at"); C11 is "G1… `hours.start + k·g`"; C12 is "exactly at the cutoff is offered"; C13 is the S1 trace (checked by hand); C14 is "Default rules and no as_of → exactly the stage-1 result". |
| 14 | State | Y | 10 | — | 3/3. Frozen values, and "Pure; `bookings` consumed once". |
| 15–17 | — | N/A | — | — | as above |

**Profile Y-stage-2:** grade = (11×10 + 8 + 6×2 + 2×8) / 22 = **6.64** · worst **2** · (#S3,#S4) = **(0,1)** · gate **BLOCKED**

**D2 winner on survival: X** (1 against 4 reopened or discarded).

**D2 winner on the stage-2 form: X**, at 9.07 CLEAR against 6.64 BLOCKED.

The form result depends entirely on the one correctness item in §13. Leave that row out and Y's structure scores **9.33** against X's **9.07**. Y's stage-2 structure is slightly cleaner: it has a single fit test and treats policy as data, where X has two policy classes each implementing the fit bound. X, in turn, has more small blemishes than Y (the anemic `AsOf`, the duplicated fit bound, mode-dependent offer semantics).

I still name X because the S4 is not a stylistic blemish. It is a wrong answer on an explicit stage-2 card rule, and Y chose it deliberately by carrying its stage-1 rule "only what lies inside working hours matters" into the buffer rule. It is locally fixable in one owner (`DaySchedule`). If fixed, the form comparison would become **no clear advantage**, with Y marginally ahead.

---

## 3. Correctness traps (`spec-and-oracle.md`)

**Trap 1: buffer-as-booking cram.**
- **X avoided it.** "D7. The buffer is modeled as a widening of occupancy, not as pseudo-booking intervals… It also creates buffer objects that could leak into output or be confused with bookings… Rejected."
- **Y avoided it.** "Buffer as a synthetic booking — the concept cram 0004 rules out"; "Buffer | a `timedelta` on `ResourceRules`; its *effect* is occupancy | never a booking".

**Trap 2: scattered "bookable" rule.**
- **X avoided it.** One footprint owner ("`occupancy`… the single owner of B1 and B2"), one enumeration seam (`SlotPolicy`), and notice applied as a filter in one place ("keep s >= cutoff"). Free time is derived once, by the unchanged `free_gaps`. The residual is that the fit bound `s + footprint <= gap.end` is implemented in each of the two policy classes (row 10, S1). The two copies cannot disagree on today's inputs, because both obey one stated contract.
- **Y avoided it.** Occupancy has one owner (`DaySchedule`). There is one enumeration and one fit test: "`fitting_starts`… the ONLY fit test in the package". Notice is applied by one filter: "`if start in eligible`".

**Trap 3: interaction coverage.**
- **X avoided it.**
  - Last slot before close, with the buffer past close: "New slot's buffer may run past closing" → 09:00.
  - Grid × buffer: "Granularity with buffer" → 09:00, 09:15.
  - All three combined: traced correct (row 13).
  - A buffer from a booking before opening: "Buffer of a booking before working hours" → 09:20, 10:10.
- **Y partly failed.** Y gets the last-slot-before-close case right ("S4… grid last point 16:30… Its buffer to 17:15 is never looked at"), and grid × buffer (S1) and notice × buffer (B25) are right too. It misses the interaction between a new slot's buffer and a booking at or after close:
  - **Input:** `available_starts(TimeRange(09:00, 17:00), [TimeRange(17:00, 18:00)], timedelta(minutes=30), rules=ResourceRules(buffer=timedelta(minutes=15)))`, with no grid and no `as_of`.
  - **Y as written:** occupancy `[17:00,18:15) ∩ [09:00,17:00)` → `None`, so the tail span is `[09:00,17:00)` untrimmed. The result is `09:00, 09:30, …, 16:00, 16:30` (16 starts). Y's own trace confirms this: "S9 … 16:30 ✓".
  - **Correct:** `09:00, 09:30, …, 16:00` (15 starts). A 16:30 slot's buffer `[17:00,17:15)` overlaps the 17:00 booking, which violates "buffers overlap a neighbour's booking".
  - **With `granularity=15 min`:** Y offers up to 16:30, but the correct last start is 16:15 (its buffer ends exactly at 17:00, which is touching and allowed).
  - For comparison, X's spec pins exactly this case: "New slot's buffer may not overlap a booking after closing… the result is empty".

**Other §13 findings.** I found no failure in X at either stage, and no failure in Y at stage 1.
- I probed X's claimed equivalence, where the window is extended by the buffer, for a gap opening after close. Any gap inside `(wh.end, wh.end + b]` is shorter than `d + b`, so no out-of-hours slot can be emitted, and the claim holds.
- Both designs keep an optional no-granularity mode even though the card says starts "must align to a per-resource granularity". Both state this as an assumption, and it is symmetric, so it is not scored.
- X's step of `duration + buffer` in back-to-back mode is a stated assumption (B5), not a wrong answer against any oracle item.

---

## 4. Residual tells and bias controls

- **Method guess.** Before scoring I guessed X = OpenSpec and Y = aims (GUESS.md). The rubric *is* the aims principle set, and Y cites its vocabulary throughout ("subtractive pass", "concept-fit", "falsifier", "feature envy (§8)"). That is the capture risk `measurement.md` warns about. **Control:** I credited no self-declared verdicts. Y's own "Subtractive pass… keep" table was ignored, and I failed 12b and 12d on items that table kept. Every pass or fail cites a type, signature, owner or traced output.
- **Length and documentation style.** Y is 3–4× longer, with proofs, precedence tables and microsecond-overflow analysis. X arrives as proposal, spec and tasks with SHALL/WHEN/THEN scenarios. **Control:** I counted neither prose volume nor proofs as structure, and I did not penalise them as components. X's concrete scenarios made it easier to verify, so I hand-traced Y's cases to the same depth (S1, S4, S9, C1).
- **Disposition pull.** My YAGNI weighting pushes against Y's edge machinery. The rubric itself says "the graver risk is too little structure". **Control:** I applied the §7 tie-break mechanically. X's `SlotPolicy` passes because two variants exist today. Y's `DaySchedule` fails 12b only because a function would keep identical ownership. The resulting D1 verdict is a tie, not an X win.
- **Y's internal product decisions.** Y cites records I cannot see ("decisions/0002", "decisions/0004 §3", goals.md) and treats R3 as decided ("not open to re-decision"). Its C10 failure may be sanctioned by a product answer it received. I scored against the product cards and the oracle, the only shared Step 0, and I flag this as the one place where Y's context might excuse the defect.
- **Verdict sensitivity.** The D2 stage-2 form verdict (X) rests on the single S4. I stated the structural-only comparison (Y 9.33, X 9.07) so a reader can weigh that directly. The D1 verdict and the D2 survival verdict do not depend on it.
