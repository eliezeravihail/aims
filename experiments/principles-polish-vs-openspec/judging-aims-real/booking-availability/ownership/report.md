# Judge report: booking-availability, designs X and Y

Judge disposition: **invariant ownership**. The questions I asked most were: does every rule have exactly one owner that cannot be bypassed? Do the types make illegal states unrepresentable? When a new requirement arrives, does it land at a seam, or does it reopen an owner?

Instrument: `rubric/assessment-form.md` (17 rows), with severity, ceilings and weights taken from `rubric/measurement.md`.
- Row score = `min(round(10 × passed/applicable), ceiling)`.
- Rows 15 (testability, code-leaning), 16 (performance: no requirement stated) and 17 (security: no trust boundary) are **N/A** for every design, so all four forms share the same applicable set, rows 1–14.
- Each profile is reported as: grade, worst chapter, (#S3, #S4), gate.

---

## Step 0: fixed inventory (from `product/`, not from the designs)

**R (rules)**
- R1: a slot `[s, s+d)` lies inside working hours.
- R2: the slot overlaps no existing booking (half-open intervals).
- R3: starts are laid back-to-back, earliest first.
- R4 (stage 2): a buffer of N minutes follows every booking.
  - The buffer is not free time.
  - It is never a booking and has no booker.
  - No booking's buffer may overlap a neighbour's booking.
  - The buffer may run to or past closing; only the booking must fit inside the hours (oracle).
- R5 (stage 2): minimum notice. Start `s` is offered only if `s ≥ now + X`, measured from the slot start (oracle).
- R6 (stage 2): granularity. Starts lie on `hours.start + k·g` (oracle: aligned from the working-hours start).
- R7: stage-1 behaviour is unchanged wherever the new rules don't apply.

**X (change axes)**
- X1: buffer.
- X2: minimum notice.
- X3: granularity.
- X4 (plausible, unstated): a different buffer shape, e.g. per-booking or before-booking buffers.

**C (acceptance and capability checks)**
- C1: worked day, 09:00–17:00 with a 30-minute duration.
- C2: empty day.
- C3: a slot that ends exactly at closing.
- C4: duration longer than every gap → `[]`.
- C5: the new slot's buffer runs past closing.
- C6: an on-grid candidate that sits inside a buffer is excluded.
- C7: the notice cutoff is inclusive and measured from the slot start.
- C8: the grid is anchored at the hours start.
- C9: the new slot's buffer must not overlap a neighbouring booking, including one after closing.
- C10: all three rules combined.
- C11: zero, negative and overflow inputs (the §1 edge item).

---

## 1. D1: first-round design (stage 1)

### X-stage-1

| § | principle | applies | score | sev | finding and citation |
|---|---|---|---|---|---|
| 1 | Tell-Don't-Ask / LoD | Y | 10 | — | 3/3. Validity and half-open semantics sit on the type: "`Interval(start, end)` … enforces `start < end` at construction and has half-open `overlaps` and `contains` semantics". There are no message chains. |
| 2 | Interface / concept-fit | Y | 10 | — | 3/3. The query is a named type (`AvailabilityQuery`). The output is calibrated (`list[datetime.time]`, D6). Free gaps are `Interval`s, not synthetic bookings. |
| 3 | Interface Segregation | Y | 10 | — | 2/2. "`intervals` and `slotting` do not know about each other, about bookings as a concept, or about the CLI." |
| 4 | Primitive obsession / illegal states | Y | **7** | S2 | 3/4 (8), capped at 7. **Fail:** the published value type holds raw offsets with no day bound: "`Interval(start, end)`: a frozen dataclass over a *day offset*", and "New public API: one query function plus value types". Only the helper "converts `datetime.time` values to day offsets at the boundary". A direct `Interval(timedelta(hours=-1), timedelta(hours=26))` can therefore be built, and the R-level fact "All times are wall-clock times of day on the same single day" has no owner on that path. **Passes:** `start < end` is enforced; `duration > 0` is enforced at construction; `timedelta` is used rather than integer minutes (D2). |
| 5 | Anemic domain model | Y | 10 | — | 3/3. `Interval` owns overlap and contains. `AvailabilityQuery` validates itself. No manager holds a type's rules. |
| 6 | Cohesion / coupling / OCP | Y | 10 | — | 4/4. Dependencies are acyclic ("Dependencies point only downward"). Alignment is isolated for X3: "a later change of policy (a fixed grid, a step different from duration, buffers) touches only this module". The occupancy seam `free_gaps(window, busy)` is where X1 can land. |
| 7 | Leaky abstractions / errors | Y | 10 | — | 3/3. "`InvalidQuery(ValueError)`: the only error type the core raises". The CLI "Owns: the wire format only". (The offset exposure is scored under §4, not deducted again here.) |
| 8 | SRP / God object | Y | 10 | — | Each of the five modules has one "Owns:" line. |
| 9 | One unforgeable owner | Y | 10 | — | 5/5. Half-open ("single owner of rule A2"). Validity ("Nothing downstream re-validates"). Tolerance: A3 is owned by `intervals`. Alignment: A1 is owned by `slotting`. Ordering is structural in `availability`. |
| 10 | DRY | Y | 10 | — | Each fact has one home (D4 "parse, don't validate"). |
| 11 | Naming and failure | Y | 10 | — | Errors name the field, e.g. "`bookings[2]: start 11:00 is not before end 10:00`". |
| 12 | YAGNI / subtractive | Y | 10 | — | The repository seam was rejected (D1). A small CLI is explicitly permitted by `substrate.md`. |
| 13 | Functional correctness | Y | **2** | **S4** | 5/6 (8), capped at 2. **Fail (C11, overflow):** "`back_to_back(gap, duration)`: yields `gap.start + k*duration` while `start + duration <= gap.end`". The addition happens before any comparison. Reproduction and the correct output are in §3. **Passes:** C1–C4 are all traced in the spec scenarios; half-open edges; ordering without a sort; invalid input rejected. |
| 14 | State and side effects | Y | 10 | — | "A pure core: same inputs give the same output, with no clock, I/O, or global state." Types are frozen. |
| 15–17 | Testability / performance / security | N/A | — | — | Code-leaning / no stated requirement / no trust boundary. |

**Profile X-1:** grade = (12×10 + 7×2 + 2×8) / 22 = **6.82**, worst = 2, (#S3,#S4) = (0,1), gate = **BLOCKED**.
If the one removable overflow blemish is taken out, the grade is 9.60 and the gate is CLEAR.

### Y-stage-1

| § | principle | applies | score | sev | finding and citation |
|---|---|---|---|---|---|
| 1 | Tell-Don't-Ask / LoD | Y | 10 | — | The stepping loop "*tells* the range what to do (`leading`, `if_nonempty`) and never reads `start`/`end` to do its own arithmetic". |
| 2 | Interface / concept-fit | Y | 10 | — | "Free time is emitted explicitly as its own value. It is never a synthetic booking". Busy time is renamed `busy` once clipped. |
| 3 | Interface Segregation | Y | 10 | — | `DaySchedule` and `_gap_aligned_starts` "are not exported and appear in no public signature". |
| 4 | Primitive obsession / illegal states | Y | 10 | — | 4/4. `TimeRange` has `time` fields, so an out-of-day value cannot be represented. The invariant is "start < end", naive, with a type guard. Empty ranges are `None` ("an empty range cannot be represented anywhere"). Duration is a `timedelta` whose one rule has one owner. |
| 5 | Anemic domain model | Y | 10 | — | `DaySchedule` validates at construction and owns `free_gaps`. `TimeRange` owns all time arithmetic. |
| 6 | Cohesion / coupling / OCP | Y | 10 | — | Acyclic ("`slots ──► _day ──► time_range ──► errors`"). X-items have named landing points: buffers go to "`DaySchedule.__init__`: widen occupancy there, the one owner"; a grid goes to "`slots._gap_aligned_starts`". |
| 7 | Leaky abstractions / errors | Y | 10 | — | The published surface is pinned (P1–P4). There are two error types; the subtype is justified by its payload (`.first`, `.second`). |
| 8 | SRP / God object | Y | 10 | — | Four small modules, one responsibility each (§2). |
| 9 | One unforgeable owner | Y | 10 | — | The §5 rule-to-owner table checks against the signatures. `DaySchedule` has "one construction path … An unvalidated `DaySchedule` therefore cannot be built through any intended path". |
| 10 | DRY | Y | 10 | — | "This is the only strict bound comparison in the package." |
| 11 | Naming and failure | Y | 10 | — | Messages use wall-clock terms, e.g. "`invalid time range 17:00–09:00: end must be after start`". |
| 12 | YAGNI / subtractive | Y | 10 | — | No CLI, no Strategy seam; each type has a present force (§8.5). |
| 13 | Functional correctness | Y | 10 | — | 6/6. C1–C4 are traced. Overflow is handled: "length is compared with (end - start) BEFORE any addition, so a huge length cannot overflow". The duration is rejected first. I found no failing input. |
| 14 | State and side effects | Y | 10 | — | Frozen `TimeRange`; `DaySchedule` uses `__slots__`, private attributes and "no method assigns to them". |
| 15–17 | — | N/A | — | — | as for X |

**Profile Y-1:** grade = **10.00**, worst = 10, (#S3,#S4) = (0,0), gate = **CLEAR**.

Considered and deducted from neither design: both publish geometry on their value type that no caller needs.
- X: `Interval` exposes `overlaps` and `contains`.
- Y: "No stated caller needs `if_nonempty`, `intersection`, `overlaps` or `leading`".

These are the type's own total operations, so they do not breach a rule. I treated both the same.

**D1 winner: Y.** The result is robust:
- Literal scores: 10.00 vs 6.82.
- With X's removable overflow blemish removed: 10.00 vs 9.60.

The structural difference that remains is §4. Y's range type cannot represent an out-of-day time; X's public `Interval` over offsets can.

---

## 2. D2: change absorption

### Survival classification

**X (stage 1 → stage 2)**

| component / seam | class | evidence |
|---|---|---|
| `model` | extended | "gains the rule and context types (still the single owner of validity)" |
| `Interval` | survived | Unchanged. |
| `InvalidQuery` | survived | Unchanged. |
| `AvailabilityQuery` (and `.of`) | extended | "gains `rules: ResourceRules = ResourceRules()` and `as_of: AsOf \| None = None`"; `.of` "gains keyword arguments". |
| `intervals` (`merge`, `free_gaps(window, busy)`) | survived | "`intervals` is unchanged". The buffer arrives through widened inputs. |
| `slotting` (module) | extended | It stays the alignment owner; `Grid` and `policy_for` are added. |
| **`slotting.back_to_back(gap, duration)`** | **reopened** | "The interface changes from `back_to_back(gap, duration)` to a small protocol"; "Refactor `back_to_back` into the `SlotPolicy` protocol with `BackToBack` (step = footprint)". Both the boundary and the stepping semantics change. |
| `availability.find_slots` | extended | Same signature and the same composer role ("composes the rules; owns no rule"). New steps are added. |
| `cli` | extended | "New optional fields". |

**X reopened + discarded = 1**: `back_to_back`.

**Y (stage 1 → stage 2)**

| component / seam | class | evidence |
|---|---|---|
| `errors` (both types) | survived | "unchanged types" |
| `TimeRange` | extended | `whole_day`, `extended`, `trimmed`, `fitting_starts` and `__contains__` are added. |
| `if_nonempty`, `intersection`, `overlaps`, `__str__` | survived | — |
| **`TimeRange.leading`** | **discarded** | "Stage-1 `leading` is **removed**". |
| `DaySchedule` (class, `__init__`) | extended | It stays the occupancy owner and gains a `buffer` parameter. **Borderline:** its stated invariant was weakened ("Stage-1 I2 'strictly ascending' and I3 'pairwise disjoint' no longer hold"). |
| **`DaySchedule.free_gaps`** | **reopened** | "`free_gaps` → `bookable_spans`"; "the yielded ranges are no longer free gaps". The meaning of the output changed. |
| **`slots._gap_aligned_starts(gap, duration)`** | **reopened** | It becomes `_aligned_starts(span, duration, grid_origin, granularity)`: "replace the R1 loop with `_aligned_starts`". The signature, the body and the scope (R1 → R1 + G1) all change. |
| `available_starts` | extended | Keyword-only `rules=` and `as_of=` with stage-1 defaults. |
| `__init__` | extended | Six exported names instead of four. |

**Y reopened + discarded = 3**: `leading`, `free_gaps`, `_gap_aligned_starts`. The count would be 4 if the weakening of `DaySchedule`'s invariant were counted as a reopen.

Both designs meet the hidden survival oracle's "extends" condition: stage 1 already had an occupancy step and an enumeration step, and the buffer widens occupancy. All of Y's reopens are package-private or within the owner. X's reopen is a module-internal interface.

**D2 winner on survival: X** (1 vs 3). Per `measurement.md` this is corroboration only and does not outrank the form.

### X-stage-2

| § | principle | applies | score | sev | finding and citation |
|---|---|---|---|---|---|
| 1 | Tell-Don't-Ask / LoD | Y | **8** | S1 | 3/4. **Fail:** the notice rule pulls both fields of a pure data bag and decides outside it. "`AsOf(date, now)`: a frozen dataclass holding the query-time facts"; "`earliest_start(as_of, min_notice)` … returns `(as_of.now + min_notice) - datetime.combine(as_of.date, time.min)`". **Passes:** validity on types; no message chains; half-open semantics on `Interval`. |
| 2 | Interface / concept-fit | Y | 10 | — | "D7. The buffer is modeled as a widening of occupancy, not as pseudo-booking intervals"; "D10. Minimum notice is a filter on candidates, not busy time". |
| 3 | Interface Segregation | Y | 10 | — | "The policy sees a gap and a length. It does not know that the length includes a buffer, and it does not know about notice." |
| 4 | Primitive obsession / illegal states | Y | **7** | S2 | 3/4 (8), capped at 7. **Fail (carried from stage 1, now explicit):** "offsets are unbounded `timedelta`s" on the published `Interval`. **Passes:** "Pairing them in one type makes 'only one of date/now' impossible to represent"; `ResourceRules` rejects negative values; `start < end`. |
| 5 | Anemic domain model | Y | 10 | — | `ResourceRules` validates itself. (`AsOf` as a bag is scored under §1, not deducted again.) |
| 6 | Cohesion / coupling / OCP | Y | **8** | S1 | 3/4. **Fail (connascence of meaning outside the owner):** the buffer rule is correct only if the composer pairs two `occupancy` outputs: "The window end `wh.end + buffer` turns `s + d <= wh.end` into `s + fp <= window.end`". The pairing is done in `find_slots` ("working hours --search_window-->" … "fp = footprint(duration, buffer)"). Using `footprint` without `search_window` would silently drop valid last slots. **Passes:** acyclic ("None of the four rule modules imports another"); X1 was absorbed at the unchanged `free_gaps` seam; X3 landed in the alignment owner. |
| 7 | Leaky abstractions / errors | Y | 10 | — | One `InvalidQuery`; new errors name the field ("an error naming the buffer"). |
| 8 | SRP / God object | Y | 10 | — | `availability` is "composition only". |
| 9 | One unforgeable owner | Y | 10 | — | "buffer: `occupancy` / notice: `notice` / granularity: `slotting.Grid`". The cross-field rule is on the query. `policy_for` is "the only place that turns 'granularity is set' into behavior". |
| 10 | DRY | Y | **7** | S2 | 3/4 (8), capped at 7. **Fail:** the fit bound is restated by every policy. The protocol contract reads "ascending, `gap.start <= s`, and `s + footprint <= gap.end`", and it is implemented separately by `BackToBack` ("`gap.start + k*footprint`") and `Grid` ("then every `step` while it fits"). Two classes own the same fit comparison. **Passes:** single validation; single buffer arithmetic; single notice cutoff. |
| 11 | Naming and failure | Y | 10 | — | "Minimum notice without now → rejected with an error naming now". |
| 12 | YAGNI / subtractive | Y | 10 | — | `SlotPolicy` has two present implementations, so it is not speculative. |
| 13 | Functional correctness | Y | **2** | **S4** | 6/7 (9), capped at 2. **Fail (C11, overflow):** `footprint(duration, buffer)` returns "`duration + buffer`", and `earliest_start` computes `as_of.now + min_notice`, both before any comparison (§3). **Passes:** C3, C5 ("New slot's buffer may run past closing → 09:00"), C6, C7 (inclusive cutoff), C8 ("Grid anchored at the start of working hours"), C9 ("New slot's buffer may not overlap a booking after closing → the result is empty"), C10. I recomputed the "All three rules combined" scenario and got the stated `10:30 … 11:30`. |
| 14 | State and side effects | Y | 10 | — | "D12. Neither the core nor the CLI reads a clock." |
| 15–17 | — | N/A | — | — | — |

**Profile X-2:** grade = (9×10 + 8 + 7×2 + 8 + 7×2 + 2×8) / 23 = **6.52**, worst = 2, (#S3,#S4) = (0,1), gate = **BLOCKED**.
With the overflow blemish removed: 9.00, CLEAR.

### Y-stage-2

| § | principle | applies | score | sev | finding and citation |
|---|---|---|---|---|---|
| 1 | Tell-Don't-Ask / LoD | Y | 10 | — | The notice cutoff is on the type that owns `day` and `now`: "`AsOf.eligible_starts` … N1, the one owner". |
| 2 | Interface / concept-fit | Y | 10 | — | The buffer's "*effect* is occupancy"; the new booking's buffer is "a reservation at the end of the room — not fake busy time". "Bookable span" is a named concept. |
| 3 | Interface Segregation | Y | 10 | — | "`_day` imports `time_range` and `errors` — **not** `rules`: it receives the buffer as a `timedelta`". |
| 4 | Primitive obsession / illegal states | Y | 10 | — | `AsOf` makes "a day without a now" unrepresentable and guards `day` against `datetime` (A10). `TimeRange` is unchanged. `ResourceRules` is validated. |
| 5 | Anemic domain model | Y | 10 | — | `DaySchedule` owns occupancy and spans. `ResourceRules` validates itself. |
| 6 | Cohesion / coupling / OCP | Y | **8** | S1 | 3/4. **Fail (load-bearing invariant resting on another module's property):** "bookable_spans() is correct ONLY while I2′ holds … I2′ is not checked at run time". One of its premises lives in `time_range.py`: "`TimeRange.extended` (a monotone cap at `whole_day().end` — load-bearing for I2′)". The design chose this fragility over a union step: "A merge would add a public `joined` member". **Passes:** acyclic; the buffer's two halves have one owner ("`DaySchedule`, already the occupancy owner, owns both halves"); the lattice is chosen at one site. |
| 7 | Leaky abstractions / errors | Y | 10 | — | "`DaySchedule`, spans, the lattice choice and the eligibility helper appear in no public signature". Every new rejection is `InvalidAvailabilityRequest`. |
| 8 | SRP / God object | Y | 10 | — | `rules` / `as_of` / `_day` / `slots` each have one reason to change (§2 "Why the time model is two files"). |
| 9 | One unforgeable owner | Y | 10 | — | The fit test: "`TimeRange.fitting_starts` (`t + length <= end`) … the only fit test". B2 is owned by `bookable_spans`. N1 is owned by `AsOf.eligible_starts` and applied once. N2 is owned by `_eligible_starts`. There are two tz checks ("Two naive-time facts, one owner each"); I accept them as two different subjects, not one rule enforced twice. |
| 10 | DRY | Y | 10 | — | "Neither branch contains a comparison, so neither can re-implement the fit." |
| 11 | Naming and failure | Y | 10 | — | "`minimum notice is 2:00:00, so the query needs as_of=AsOf(day, now)`". |
| 12 | YAGNI / subtractive | Y | 10 | — | Every new member has a force (§8.4). The Protocol, the per-rule types and the error subtypes were not added. |
| 13 | Functional correctness | Y | **2** | **S4** | 6/7 (9), capped at 2. **Fail (C9, R4 "buffers overlap a neighbour's booking" × R3):** occupancy is clipped to the hours before the new slot's buffer is checked. "`[t, t + d + buffer)` must not overlap **in-hours** occupancy", and the S9 trace reads "17:00–18:00+15 ∩ H = None; tail = H. \| 16:30 ✓". Reproduction is in §3. **Passes:** C5 (untrimmed tail), C6, C7, C8, C10, C11 (every operation is total, e.g. "`timedelta.max` … no `OverflowError`"). |
| 14 | State and side effects | Y | 10 | — | Frozen values, pure, `now` passed as data. |
| 15–17 | — | N/A | — | — | — |

**Profile Y-2:** grade = (12×10 + 8 + 2×8) / 21 = **6.86**, worst = 2, (#S3,#S4) = (0,1), gate = **BLOCKED**.
With the after-hours blemish removed: 9.86, CLEAR.

### D2 verdicts

- **On survival: X**, with 1 reopen or discard against Y's 3.
- **On the stage-2 form: Y, narrowly.**
  - Literal scores: 6.86 vs 6.52, and both are BLOCKED.
  - With both removable S4 blemishes taken out: 9.86 vs 9.00.
  - The structural gap comes from ownership of the fit rule and the buffer:
    - X restates the fit bound in each policy (§10).
    - X has the notice rule outside `AsOf` (§1).
    - X's public `Interval` can hold out-of-day values (§4).
    - Y's only structural deduction is the load-bearing I2′ (§6).
  - **Caveat, stated plainly:** Y's S4 is a card-rule miss on a plausible input, while X's S4 needs an absurd duration. If only Y's defect were counted and X's dismissed, X would lead (9.00 vs 6.86). I apply the rule that a removable local blemish must not flip a verdict, treat both as removable, and rest the verdict on structure. That gives Y.

---

## 3. Correctness traps (`spec-and-oracle.md`)

| trap | X | Y |
|---|---|---|
| **1. Buffer-as-booking cram** | **Avoided.** "D7. The buffer is modeled as a widening of occupancy, not as pseudo-booking intervals … creates buffer objects that could leak into output or be confused with bookings … Rejected." Busy time is `[b.start, b.end + buffer)`, a booking's footprint. | **Avoided.** "Buffer as a synthetic booking — the concept cram 0004 rules out; it would trip R4 on S6". Buffer: "a `timedelta` on `ResourceRules`; its *effect* is occupancy". |
| **2. Scattered "bookable" rule** | **Avoided, with one partial breach.** One place computes the footprint (`occupancy`), one place selects the enumeration (`policy_for`), and notice is one filter (`notice`). Nothing re-derives free intervals: "`intervals` is unchanged". Partial: the admission bound `s + footprint <= gap.end` is implemented in both `BackToBack` and `Grid` (see the §10 finding). | **Avoided.** Occupancy has one owner: "`DaySchedule`, already the occupancy owner, owns both halves". Enumeration happens at one site (`_aligned_starts`). The fit is one test ("the ONLY fit test in the package"). Notice is one window applied by one `if start in eligible`. |
| **3. Interaction coverage** | **Avoided.** The last slot needs room for the booking, not the buffer: "`search_window(working_hours, buffer)` … `[wh.start, wh.end + buffer)`", with scenario "New slot's buffer may run past closing → 09:00". An on-grid candidate inside a buffer is excluded ("Granularity with buffer → 09:00, 09:15"). A neighbour after closing is honoured: "New slot's buffer may not overlap a booking after closing → the result is empty". | **Partly failed.** The last slot needs room for the booking only: "the tail … closed by closing: buffer may run past it" (S4 → 16:30). ✓ The grid × buffer interaction is handled. ✓ **But the buffer × out-of-hours-neighbour interaction fails**, because occupancy is clipped to the hours before the buffer check (reproduction below). |

Both designs also follow the oracle answers:
- Granularity is anchored at the hours start. X: "`Grid(working_hours.start, g)`". Y: "anchor is the hours' start".
- Notice is measured from the slot start, with an inclusive cutoff. X: "A start exactly at that cutoff SHALL be offered". Y: "exactly at the cutoff is offered".

### Reported failures, with reproductions

**F-Y1: Y-stage-2, row 13. The new slot's buffer overlaps an after-hours booking.**
- Input: `available_starts(TimeRange(09:00, 17:00), [TimeRange(17:00, 18:00)], timedelta(minutes=30), rules=ResourceRules(buffer=timedelta(minutes=15)))`, with no grid and no `as_of`.
- What the design does:
  - R4 passes.
  - Occupancy `[17:00, 18:15) ∩ [09:00, 17:00)` is `None` because the ranges only touch, so `_busy = ()`.
  - The tail span is `[09:00, 17:00)`, untrimmed.
  - R1 then steps from 09:00 in 30-minute steps.
- Y returns `09:00, 09:30, …, 16:30` (16 starts). This matches Y's own trace row S9 ("16:30 ✓").
- Correct output: `09:00 … 16:00` (15 starts). Slot 16:30–17:00 has its buffer at 17:00–17:15, which overlaps the 17:00 booking. The card says "two bookings may not be scheduled such that their buffers overlap a neighbour's booking".
- Fix: local, inside `DaySchedule`. The tail span must also be trimmed when the first booking after closing starts before `hours.end + buffer`.

**F-X1: X-stage-1 and X-stage-2, row 13. An oversized duration overflows instead of returning `[]`.**
- Input: `find_slots(AvailabilityQuery.of(working=(time(9), time(17)), bookings=[], duration=timedelta.max))`.
- What the design does: stage 1 evaluates `gap.start + duration`, i.e. `timedelta(hours=9) + timedelta.max`, in `back_to_back` before comparing it with `gap.end`. Stage 2 evaluates `footprint = duration + buffer`, then `gap.start + footprint`.
- X raises Python's `OverflowError` ("days=1000000000; must have magnitude <= 999999999"). This is not `InvalidQuery`, so the CLI's error mapping does not catch it either.
- Correct output: `[]`, by X's own scenario "Duration longer than working hours → the result is empty, and this is not an error".
- Same class in stage 2: `min_notice=timedelta.max` with `now=2026-10-01T08:00` makes `as_of.now + min_notice` raise `OverflowError` ("date value out of range"). The correct output is `[]`, by "Notice reaches beyond the queried day → the result is empty".
- Fix: local. Compare before adding.

**Divergences I did not score as failures:**
- **No-grid stepping with a buffer.** X steps by `duration + buffer` (B5); Y steps by `duration` (A14). Both are stated assumptions, the card does not decide it, and the oracle is silent. Example: hours 09:00–11:00, no bookings, buffer 15, duration 30. X gives `09:00, 09:45, 10:30`; Y gives `09:00, 09:30, 10:00, 10:30`. Both fit the card; a product owner would decide.
- **Overlapping bookings.** Y rejects them (R4); X tolerates them. The oracle says to assume non-overlapping bookings, so neither choice is wrong.
- **Past-day queries.** Y returns `[]` for a past day when `as_of` is supplied (A12). This is literal, disclosed and consistent with N1.

---

## 4. Residual tells and how I controlled for them

- **Method guess.** In `GUESS.md` I guessed X = OpenSpec and Y = aims at 97%. The rubric is aims' own document, so Y's prose recites its vocabulary: "subtractive pass", "concept-fit", "§5", "feature envy", "Result: met". Controls:
  - I gave no credit for self-assessment. Y's §5 rule-to-owner table, §8.4 keep/cut table and "Result: met" were each checked against the actual signatures.
  - I deducted from Y where the structure warranted it: §6 for the load-bearing I2′, and §13 for the after-hours miss. The §13 miss is exactly a case Y's own trace marks "✓".
  - I did not deduct from X for its spec/tasks format, and the stripped proposal and tasks were not scored.
- **Length and trace volume.** Y is two to four times longer and has far more traces. I scored correctness only by recomputing outputs myself:
  - X's "All three rules combined", "Granularity with buffer" and "CLI with rules" scenarios, and its buffer-before-hours scenario.
  - Y's S1, S5 and S9 rows.

  A trace table earned nothing by itself, and Y's S9 trace is precisely where it is wrong.
- **Disposition bias.** My disposition favours Y's style: geometry on a value type, `time` fields, private helpers. Controls:
  - Every deduction names a failing structural fact, not a missing style.
  - I applied the same check to both designs where they share a pattern. Publishing unused geometry on the value type was deducted from neither. `ResourceRules` as a validated settings bag was deducted from neither.
  - I gave X credit where it is structurally better: survival count (1 vs 3), and the correct after-hours buffer rule.
- **The S4 gate is sensitive to how edge-trivial a defect is.** X's S4 needs a duration of about 2.7 million years; Y's needs a booking just after closing. I reported the literal rubric profile and a blemish-removed profile side by side. I rested each verdict on the reading that holds when removable local blemishes are set aside. D1 is Y in every combination. The stage-2 form verdict is Y in both symmetric combinations but not in the asymmetric one, and I stated that openly rather than hiding it.
