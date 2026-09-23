# Design: Parcel Shipping-Rate Engine

Design-only (no implementation). One planning pass followed by the mandatory review-and-revise round (`decisions/0011`), graded against `experiments/improve-2026-09/i1-input-space-table/arm-table-design-principles.md`. The final revised design is the body below; the review round that produced it (with the S4 it caught) is in §8.

Objective (Kind: `design`): *Establish the domain types and the single-owner pricing pipeline for a parcel rate engine such that each of R1–R4 has exactly one home and each change-axis X1–X3 lands at a seam without reopening an owner — with every (R × X) corner of the input space shown representable by the chosen types.* Behavior (R1–R4, C1–C2) is the constraint the design must satisfy.

---

## 1. Product intent & scope (→ `goals.md`)

A pure pricing function: given a parcel (a scale reading, physical dimensions, a destination zone) and a rate table, return the price in whole cents, or a typed error for an unknown zone. No persistence, no I/O, no concurrency, no ordering/time — it is a deterministic total function over validated inputs (functional core, §11). Out of scope: how the table is loaded, how the scale/API is read (that is the boundary shell's job).

## 2. Foundational substrate

Substrate choice (language/framework) is normally an *ask* of the user (SKILL step 1); for this design-only arm I fix only what correctness forces and leave the rest open: the implementation language must provide **arbitrary-precision integers and exact decimals** (no binary float anywhere in the money or weight path). Types are given below as concrete representations + signatures in a language-neutral notation; they are buildable as-is in Python (`Decimal`/`int`), Java (`BigDecimal`/`long`), TS (`bigint` + a decimal lib), etc. `Result<T,E>` denotes an explicit success/error sum (exceptions at the boundary are acceptable if translated to the same vocabulary, §5).

## 3. Domain types — concrete representation (→ `architecture.md`, value-object module)

Every concept with a rule gets its own type; illegal states are rejected at construction so the core trusts its inputs (§1 fail-fast / defensive-at-edge, §4 value objects, make-illegal-states-unrepresentable).

**`Money`** — a discrete quantity of currency.
- Representation: `cents: int` (arbitrary precision), invariant `cents ≥ 0`. **Never a float.**
- `Money.of_dollars(d)` accepts only an exact 2-dp decimal (rejects `$5.001`).
- `times(m: Multiplier) -> Money` = `round_half_up(cents × m.value)` as cents (see §4).
- `plus(other: Money) -> Money`.
- Concept: money is countable cents, so half-up rounding is exact and total, never a float artifact.

**`Multiplier`** — a non-negative exact scalar applied to a base price.
- Representation: `value: ExactDecimal`, invariant `value ≥ 0`. (`1.0`, `1.5`, `1.15` are all exact.)

**`Weight`** — a non-negative mass in kilograms.
- Representation: `kg: ExactDecimal`, invariant `kg ≥ 0`. Exact decimal so tier boundaries (`1`, `2`, `5`) and `x/5000` are exact (5000 = 2³·5⁴ ⇒ terminates); no float boundary drift.
- `max(a, b) -> Weight`; total order.

**`Length`** — one box edge in cm. Representation: `cm: ExactDecimal`, invariant `cm > 0`.

**`Dimensions`** — a physical box.
- Representation: `(l, w, h: Length)`.
- `dimensional_weight() -> Weight` = `Weight(l·w·h / VOLUMETRIC_DIVISOR)`, where `VOLUMETRIC_DIVISOR = 5000` is a **named domain constant with one home** (not an inline literal, not a config knob — see §8 review, subtractive pass).

**`ScaleReading`** — what the warehouse scale reported. **Sum type** (this is the load-bearing type; see §8):
- `Exact(kg: Weight)` — a precise single reading.
- `Range(lo: Weight, hi: Weight)` — an imprecise reading; invariant `lo < hi` (a genuine range; `lo == hi` is constructed as `Exact` by the smart constructor `ScaleReading.from_scale(lo, hi)`, so one value has one representation).
- `worst_case() -> Weight` — total function: `Exact(k)→k`, `Range(lo,hi)→hi`. This is R2/X1's single rule for collapsing a reading to a billable scalar, owned here.

**`ZoneId`** — a destination-zone identity.
- Representation: `code: string` in canonical form (canonicalization owned here at the boundary; see §8 open decision on case/whitespace). Identity only — the multiplier/surcharge do **not** live on the id (that data changes; X3).

**`BracketUpperBound`** — a tier's top. **Sum type** (concept-fit, avoids a sentinel):
- `Bounded(Weight)` | `Unbounded` (the `5kg+` top tier; not a huge number).

**`Bracket`** — one weight tier. Representation: `{ upper: BracketUpperBound, base: Money }`. Its lower bound is implicit (the previous bracket's upper, or 0 for the first).

**`ZoneRate`** — per-zone rate data. Representation: `{ multiplier: Multiplier, surcharge: Money = Money.zero }`. Surcharge defaults to `$0.00`, present from day one so X3 is a *data* change, not a code change.

## 4. `round_half_up`

`round_half_up(x: ExactDecimal) -> int` for `x ≥ 0` = `floor(x + 0.5)` computed on the exact decimal. Because the operand `base.cents × multiplier.value` is an exact product, ties (`…​.5`) are real, not float noise, and round up deterministically. Rounding happens **once**, only at the money boundary in `Money.times`.

## 5. Rate table — the configuration owner (→ `rate_table` module; §7 schema/representation evolution has one owner)

**`BracketTable`** — the tier schedule (owns R3, absorbs X2).
- Representation: an ordered `list[Bracket]`, ascending by upper bound.
- **Construction invariant (fail-fast, illegal-states-unrepresentable):** non-empty; strictly ascending bounds; contiguous coverage of `[0, ∞)` with no gap and no overlap; exactly one `Unbounded`, and it is last. An ill-formed table cannot exist past the constructor, so no downstream code can hit an uncovered weight.
- `bracket_for(w: Weight) -> Bracket` — **total** over `w ≥ 0` (coverage invariant guarantees a hit). Tier membership is **upper-inclusive**: bracket *n* covers `(prev_upper, upper]`, the first covers `[0, upper]`. So `1.0kg→$5`, `2.0kg→$8`, `5.0kg→$12` (see §8 open decision + boundary rows in §7 table).

**`ZoneTariff`** — the zone schedule (owns R4, absorbs X3).
- Representation: `map[ZoneId → ZoneRate]`.
- `lookup(zone: ZoneId) -> Result<ZoneRate, UnknownZone>` — an unknown zone returns the **`Unknown` error variant**, never a default rate (R4). The absence of a zone is a first-class error, not a silent multiplier.

`RateTable = { brackets: BracketTable, zones: ZoneTariff }` is the single home the X2/X3 schema changes edit.

## 6. The pricing operation — one pipeline, one owner per rule (→ `pricing` module)

```
price(parcel: Parcel, table: RateTable) -> Result<Money, PricingError>

  Parcel        = { reading: ScaleReading, dimensions: Dimensions, zone: ZoneId }
  PricingError  = UnknownZone(ZoneId)          # boundary vocabulary, §5

  1. billable = Weight.max( parcel.reading.worst_case(),           # R2 + X1
                            parcel.dimensions.dimensional_weight() )
  2. bracket  = table.brackets.bracket_for(billable)               # R3 + X2  → bracket.base
  3. rate     = table.zones.lookup(parcel.zone)?                   # R4 + X3  (Err ⇒ return UnknownZone)
  4. total    = bracket.base.times(rate.multiplier)               # R1
                            .plus(rate.surcharge)                 # X3
     return Ok(total)
```

**Contracts.**
- *Pre:* all value objects are already validated (weights ≥ 0, lengths > 0, `Range` has `lo<hi`, `Multiplier`/`Money` ≥ 0, `BracketTable` well-formed). The core trusts them (§1 defensive-at-edge/trusting-inside).
- *Post:* returns `Ok(Money ≥ 0)` for a known zone, `Err(UnknownZone)` for an unknown one — never a silent price (R4).
- *Invariant:* `billable = max(worst_case(actual), dimensional)` always (R2); rounding is applied exactly once (R1); each of R1–R4 has exactly one home (`Money.times`+`.plus` / `bracket_for` / `worst_case`+`max` / `lookup`).

**One owner per rule (§5):**

| Rule | Single home |
|---|---|
| R1 price = base × mult, half-up, +surcharge | `Money.times` (round-once) then `Money.plus` |
| R2 billable = max(worst_case(actual), dim) | `ScaleReading.worst_case` + `Dimensions.dimensional_weight` + `Weight.max` (composed once in `price` step 1) |
| R3 tier selection | `BracketTable.bracket_for` |
| R4 unknown-zone error | `ZoneTariff.lookup` returning `Unknown` |

## 7. Input-space table — the required artifact (§1 addition)

Every (R × X) corner, each rule's boundary taken *exactly on the edge*, empty/one/many, zero/negative/overflow, the absent optional, and each change-axis's value shape. Column 4 is answered against the concrete type chosen above. **No `no` rows and no blanks remain** (the one `no` the first pass had is §8's fixed S4).

| corner (which X × R) | concrete extreme value | required output | chosen type represents it? |
|---|---|---|---|
| C1 baseline | 0.4kg, zone A ×1.0 | $5.00 | yes — `bracket_for(0.4)=(0,1]→$5`; `500¢×1.0=$5.00` |
| C2 baseline | 3.0kg, zone B ×1.5 | $18.00 | yes — `(2,5]→$12`; `1200¢×1.5=1800¢=$18.00` |
| R3 edge, exactly on 1kg | 1.0kg ×1.0 | $5.00 (upper-inclusive → tier (0,1]) | yes — exact `Weight`, deterministic `bracket_for` |
| R3 edge, exactly on 2kg | 2.0kg ×1.0 | $8.00 (tier (1,2]) | yes |
| R3 edge, exactly on 5kg | 5.0kg ×1.0 | $12.00 (tier (2,5]) | yes |
| R3 just over top edge | 5.0001kg ×1.0 | $20.00 (tier (5,∞)) | yes — `Unbounded` variant |
| R3 many / overflow weight | 10 000kg ×1.0 | $20.00 (unbounded top) | yes — arbitrary-precision `Weight`, `Unbounded` |
| R3 zero weight (degenerate) | 0kg | $5 tier (first bracket covers [0,1]) — `bracket_for` total | yes — coverage invariant, no gap |
| R1 half-cent tie (half-up) | base $5=500¢ ×1.001 | $5.01 (`500.5 → floor(501.0)`) | yes — exact product, half-up defined |
| R1 non-tie rounding | 500¢ ×1.0009 = 500.45 | $5.00 (`floor(500.95)`) | yes — exact decimal, round-once |
| R2 dim > actual | actual 0.4kg, box 30×20×15=9000cm³/5000=1.8kg | billable 1.8 → $8 | yes — `dimensional_weight`, `Weight.max` |
| R2 actual > dim | actual 3.0kg, dim 0.5kg | billable 3.0 → $12 | yes |
| R2 huge dimensions (overflow) | 1000×1000×1000 cm | no overflow, exact `l·w·h/5000` | yes — arbitrary precision |
| R4 unknown zone | zone "Z" ∉ tariff | `Err(UnknownZone("Z"))`, never priced | yes — `lookup` returns `Unknown` sum, not a default |
| R4 empty tariff (empty) | tariff = {} | every zone → `Err(UnknownZone)` | yes |
| Zones one / many | 1 zone / N zones | correct lookup either way | yes — map |
| Negative weight | −0.5kg | rejected at `Weight` construction | yes — precondition, unrepresentable |
| Negative dimension | −10cm | rejected at `Length` construction | yes — precondition |
| Negative multiplier / surcharge | ×−1 / −$2 | rejected at construction | yes — precondition |
| Zero multiplier | ×0, base $12 | $0.00 (+surcharge) | yes — `Money(0)` |
| **X1 × R2** — range where a point was assumed | reading `Range(1.9,2.1)`, dim 0.5 | billable = **2.1** (worst case) → then max with dim | **yes — `ScaleReading.Range.worst_case()=hi`; a bare scalar `Weight` (or a float) could NOT hold this** |
| **X1 × R3** — range straddling a tier edge | `Range(1.9,2.1)` crosses boundary 2.0 | bill on **2.1** ⇒ tier (2,5]=$12, NOT 1.9's tier (1,2]=$8 | yes — `worst_case` runs before `bracket_for` in step 1 |
| X1 × R2 — range max still below dim | `Range(0.3,0.5)`, dim 1.8 | billable 1.8 (dim wins) | yes — `Weight.max` |
| X1 — invalid / degenerate range | `Range(2.1,1.9)` / `Range(2,2)` | `lo>hi` rejected; `lo==hi` → `Exact` | yes — smart constructor, one repr per value |
| X1 × R1 | `Range(1.9,2.1)` ×1.5 | price on worst case 2.1 as normal | yes |
| **X2 × R3** — re-table a price | change tier (2,5] $12→$13; 3.0kg | $13 × mult, **no code change** | yes — `BracketTable` is validated data; `bracket_for` unchanged |
| **X2 × R3** — insert a tier | add (5,10]→$16, top→(10,∞); 7kg | $16 × mult | yes — data change; new boundary at 10 classified deterministically |
| X2 — ill-formed table | `[0,1],[2,5],(5,∞)` (gap (1,2]) | rejected at `BracketTable` construction | yes — coverage invariant, unrepresentable |
| X2 × R1 | re-tabled base | flows through same `times`+`plus` | yes |
| **X3 × R1** — per-zone surcharge | zone ×1.5, surcharge $2.00, 3.0kg base $12 | `1800¢ + 200¢ = $20.00` | yes — `ZoneRate.surcharge`, combined once at step 4 |
| X3 — default (absent optional) | zone with no surcharge | surcharge `$0.00`, price unchanged vs R1 | yes — default `Money.zero` is identity |
| X3 × R4 | unknown zone, surcharges configured | still `Err(UnknownZone)` (surcharge only for known zones) | yes |
| X3 — pre- vs post-multiplier order | `(base+sur)×mult` vs `base×mult+sur` | **open product decision (§8)** — both land at step 4 seam | yes — seam absorbs either; not silently guessed |
| Ordering / time / duplicates | — | N/A — pure total function, no state/sequence | N/A (recorded, not skipped) |

## 8. Mandatory review-and-revise round (self-review against the principles)

The first planning pass was measured with the subtractive pass, the concept-fit pass, and the input-space table. Findings and the revisions applied (the body above is post-revision):

**Finding 1 — S4, §1 / §4 (the input-space table's one `no`).** Planning-pass v1 modelled the actual weight as a single scalar `Weight` and computed `billable = max(actual, dim)`. The **X1 × R2** row's column 4 came back **"no — a scalar `Weight` cannot hold a range"**: the "1.9–2.1 kg" reading was *unrepresentable*, so worst-case billing could not be expressed at all (the design would silently price on whatever single number the boundary happened to pass). This is exactly the §1-addition failure ("a range where a point was assumed"). **Fix:** introduced the `ScaleReading = Exact | Range` sum type with `worst_case()`, and made `price` step 1 call `worst_case()` before `max`/`bracket_for`. The row now reads **yes**. (This is the round's headline catch — an S4 that a first, clean-looking pass shipped.)

**Finding 2 — concept-fit (§4).** v1 expressed the `5kg+` top tier as `Bounded(5_000_000 kg)` and a point reading, when needed, as `Range(x, x)`. Both are value-correct crams (an inert sentinel; a range that is really a point). **Fix:** `BracketUpperBound = Bounded | Unbounded`, and `Range` requires `lo < hi` with the smart constructor returning `Exact` for `lo==hi`. The tell (the sentinel, the degenerate range) disappears.

**Finding 3 — subtractive (§7 tie-break).** v1 made `VOLUMETRIC_DIVISOR` a configurable field on the rate table "for symmetry with X2/X3." No listed change-axis varies the 5000 divisor; the falsifier names no X-item ⇒ over-build, §7 finding at S1. **Fix:** collapsed to a single named domain constant. (Kept it *named*, not inlined — §3/§7 DRY.)

**Finding 4 — subtractive (§7).** v1 had both a `Bracket.contains(w)` method and a separate `TierSelector` strategy object. Removing `TierSelector` damages no current ownership (there is one selection rule, not a family of them). **Fix:** removed it; `BracketTable.bracket_for` is the sole owner.

**Finding 5 — §5 one-owner confirm.** Checked that surcharge is combined in exactly one place. It is (step 4 `.plus`), not also folded into the multiplier — so X3 cannot create a second pricing path. Rounding likewise applied once (`Money.times`). Confirmed, no change.

**Open product decisions surfaced (flagged, not guessed — SKILL "No silent product decisions"):**
- **Bracket boundary inclusivity:** no acceptance case pins a boundary weight; the design commits to **upper-inclusive** tiers (`1.0kg→$5`) as the single documented rule, but this is a product decision to confirm.
- **Surcharge pre- or post-multiplier** (X3): `base×mult+surcharge` assumed; both compositions land at the same step-4 seam, so the type design is decision-independent, but the *value* differs and the user should choose.
- **`ZoneId` canonicalization:** whether "a" == "A"/whitespace-trimmed; owned in one place (`ZoneId` construction) so the answer is a one-line change.
- **Dimensions required:** a parcel is assumed always to carry dimensions (dim weight needs them); "dimensions unknown" is out of scope, not silently defaulted.

**Exit-criteria re-measure after revision:** every (R × X) cell handled (§6 matrix + §7 table); every table row representable (no `no`, no blank); each of R1–R4 has one owner (§5); each of X1–X3 lands at a seam without reopening an owner (X1 → `ScaleReading` variant; X2 → `BracketTable` data + revalidation; X3 → `ZoneRate.surcharge` default-zero + step-4 combine); C1 and C2 reproduce ($5.00, $18.00). Design reads **met** after the one mandatory round.

## 9. Where this would be filed (record mapping)

`goals.md` (§1); `architecture.md` (the three modules, seams, the one-owner table, invariants); `base-dependencies.md` (exact-decimal/arbitrary-int substrate requirement); a `decisions/` ADR for **upper-inclusive bracket boundaries** and for **`ScaleReading` as a sum type driving worst-case billing** (with the rejected `Range(x,x)`/scalar alternatives). No source files exist yet, so no companions/anchors — this is a design deliverable.

**Key files I read:** `skills/aims-guide/SKILL.md`, `skills/aims-guide/references/{objective-selection,design-record,review}.md`, and the substituted principles `experiments/improve-2026-09/i1-input-space-table/arm-table-design-principles.md` (its §1 input-space-table requirement is the artifact in §7 above).