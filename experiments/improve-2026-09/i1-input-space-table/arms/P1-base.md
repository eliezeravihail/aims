# Parcel Shipping-Rate Engine — Architecture (design only)

Produced with the aims method as shipped in this repo: a single-designer planning pass, followed by the one mandatory measure → return-findings → revise round (`decisions/0011`, `references/review.md`), graded against `skills/aims-guide/references/design-principles.md`. Findings from that round and the fixes applied are in §7; everything above §7 is the revised final design.

---

## 0. Substrate note (the aims gate, honored explicitly)

Per SKILL.md step 1, the foundational substrate (language/framework) is a **mandatory ask of the user**, never a Guide pick. This is a design-only exercise with no user in the loop, so I pin a concrete, defensible substrate purely to make the architecture *buildable* (the method's bar for a `design` objective) and flag it as the one decision a real run would surface:

- **Language:** Python 3.11+, stdlib only. **Crossing the seams:** `decimal.Decimal` (exact arithmetic — a foundational dependency, fixed before design; the only third-party-style type allowed across a public seam per §0/§5) and the module's own value objects. No framework is needed — this is a pure computation engine (a library), so the pervasiveness test yields language + `decimal` and nothing more.
- **Why Decimal, not float:** two correctness forces demand exact arithmetic (both are §1 traps a float design ships silently): (a) R1's half-up rounding must be correct on half-cent boundaries; IEEE-754 misrepresents e.g. `10.005` and rounds the wrong way. (b) R3's tier boundaries (1, 2, 5 kg) and R2's `/5000` division must compare exactly, or a boundary parcel lands in the wrong tier. `5000 = 2³·5⁴`, so `1/5000 = 0.0002` terminates in Decimal — dimensional weight is exact.

---

## 1. Domain types — concrete representation

Signatures are Python with type hints; bodies are contracts, not implementations. Each value object validates its invariants at construction (fail-fast, §1 "defensive at the edge, trusting inside").

### Money — an amount, as an integer count of cents

```python
@dataclass(frozen=True)
class Money:
    cents: int                                 # invariant: cents >= 0 for this domain
    @classmethod
    def zero(cls) -> "Money": ...              # Money(0)
    def times(self, factor: Decimal) -> "Money":
        # R1 ROUNDING OWNER — half-up to whole cents:
        #   Money(int((Decimal(self.cents) * factor).quantize(Decimal("1"), ROUND_HALF_UP)))
    def plus(self, other: "Money") -> "Money": ...   # exact cent addition (X3 surcharge)
```
Money **is** an integer count of the currency's minor unit — that is the concept, not a cram; a float dollar amount would be the cram. All half-up rounding lives in exactly one place: `Money.times`.

### Weight — a scalar non-negative mass in kg (exact)

```python
@dataclass(frozen=True, order=True)
class Weight:
    kg: Decimal                                # invariant: kg >= 0
    # order=True: comparison + max() for tier containment and R2's max
```

### Dimensions — a box's L/W/H in cm; owns the dimensional-weight rule

```python
@dataclass(frozen=True)
class Dimensions:
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal                         # invariant: each > 0
    DIM_DIVISOR: ClassVar[Decimal] = Decimal(5000)   # the one home of R2's divisor (DRY §7)
    def dimensional_weight(self) -> Weight:    # R2 (dimensional side): (L*W*H)/5000, exact
```

### WeightReading — what the scale reports: an uncertainty interval [low, high] (owns X1)

```python
@dataclass(frozen=True)
class WeightReading:
    low: Weight
    high: Weight                               # invariant: 0 <= low <= high; exact ⇒ low == high
    @classmethod
    def exact(cls, w: Weight) -> "WeightReading": ...     # WeightReading(w, w)
    @classmethod
    def range(cls, low: Weight, high: Weight) -> "WeightReading": ...
    def worst_case(self) -> Weight:            # X1 RULE OWNER — worst case = the maximum:
        return self.high
```
Concept-fit note (verified in the revise round, §7): a scale reading genuinely *is* an uncertainty interval; a precise scale reports a zero-width interval (`low == high`). This is **not** the "degenerate case of a neighbour" cram — `low` is a real, meaningful endpoint, there is no inert always-`None` field, and the interval is the native concept of a measurement. Modelling it uniformly (rather than as an `Exact | Range` sum type) is what lets `worst_case` be a single branch-free owner and confines X1 entirely to this type — the pricing path never learns readings can be ranges.

### Zone — a validated destination-zone identity

```python
@dataclass(frozen=True)
class Zone:
    code: str                                  # invariant: non-blank identifier
```
Kept minimal on purpose (see §7): it owns the identity that R4 reports and that indexes the tariff, guarding against primitive-obsession at the public seam (§4/§8); it is given **no** invented normalization rules the card never stated.

### Bracket + BracketTable — the tier structure (owns R3 and X2)

```python
@dataclass(frozen=True)
class Bracket:
    lower: Weight                              # INCLUSIVE lower bound
    base: Money

class BracketTable:                            # R3 + X2 OWNER
    def __init__(self, breakpoints: Sequence[Bracket]):
        # invariants (fail-fast, InvalidRateTable):
        #   non-empty; strictly increasing by lower;
        #   breakpoints[0].lower == Weight(Decimal(0))   ⇒ TOTAL PARTITION of [0, ∞)
    def base_for(self, w: Weight) -> Money:    # R3 CONTAINMENT: last bracket with lower <= w
```
**Boundary convention (a surfaced product decision):** the shared endpoints 1/2/5 kg are underspecified by the card (the acceptance cases don't touch them). I pin **lower-inclusive, upper-exclusive** — tiers `[0,1) $5, [1,2) $8, [2,5) $12, [5,∞) $20` — because it makes the tiers a **total partition of `[0,∞)` with no gap or overlap**, which is what "make illegal states unrepresentable" (§4) demands of a tier table. The breakpoint representation (only a `lower` per tier; the open last tier is just the last breakpoint, no `+∞` sentinel) makes the convention live in exactly one predicate (`last lower ≤ w`), so flipping it or the invariant is a one-line change. In a real run this endpoint convention is the one question I'd put to the user.

Starter table = `BracketTable([Bracket(0, $5), Bracket(1, $8), Bracket(2, $12), Bracket(5, $20)])`.

### ZoneTariff + ZoneTariffTable — per-zone rate (owns R4 and X3)

```python
@dataclass(frozen=True)
class ZoneTariff:
    multiplier: Decimal                        # invariant: > 0   (R1)
    surcharge: Money = Money.zero()            # X3; default zero = additive identity

class ZoneTariffTable:                         # R4 + X3 OWNER
    def __init__(self, tariffs: Mapping[Zone, ZoneTariff]): ...
    def tariff_for(self, zone: Zone) -> ZoneTariff:   # R4: raises UnknownZone if absent
```
The multiplier and the (X3) surcharge are looked up together, atomically, keyed by zone; an absent zone raises before any surcharge or multiplier logic runs — so R4 "never silently priced" holds even under X3. `surcharge` defaults to `Money.zero()`: a no-surcharge zone genuinely has a zero surcharge (additive identity), not an inert stand-in — including it now is justified by X3 being a **named** change axis (§7 tie-break: the seam serves a named X-item), not speculation.

### ParcelInput — the priced request; owns R2

```python
@dataclass(frozen=True)
class ParcelInput:
    dimensions: Dimensions
    weight: WeightReading
    zone: Zone
    def billable_weight(self) -> Weight:       # R2 OWNER (Tell-Don't-Ask, §4):
        return max(self.weight.worst_case(), self.dimensions.dimensional_weight())
```
R2 is about the parcel's own data (its reading and its box), so the parcel owns it. Note R2 consumes `worst_case()` — this is the single point where X1 meets R2.

### RateEngine — composes the price; owns R1

```python
class RateEngine:                              # R1 OWNER
    def __init__(self, brackets: BracketTable, tariffs: ZoneTariffTable): ...  # injected (§6/§12)
    def price(self, parcel: ParcelInput) -> Money:
        tariff = self.tariffs.tariff_for(parcel.zone)          # R4 first — unknown ⇒ raise
        base   = self.brackets.base_for(parcel.billable_weight())   # R2 → R3
        return base.times(tariff.multiplier).plus(tariff.surcharge) # R1 (round) then X3 (add)
```

### Errors — boundary vocabulary (§5)

```python
class UnknownZone(Exception): ...       # R4 — carries the offending zone code
class InvalidParcel(ValueError): ...    # construction-time value-object validation
class InvalidRateTable(ValueError): ... # bracket/tariff table construction violated an invariant
```

**Error precedence (explicit):** value-object construction validates first (a malformed weight/dimension/zone fails before any pricing). Within `price`, the zone tariff is looked up **before** the bracket, so an unknown zone is reported regardless of the weight's shape or validity of the tier lookup.

---

## 2. Ownership map (one owner per rule/axis, §5)

| Concern | Single owner |
|---|---|
| R1 price formula (base × mult, then + surcharge) | `RateEngine.price` |
| R1 half-up rounding to cents | `Money.times` |
| R2 billable = max(actual, dimensional) | `ParcelInput.billable_weight` |
| R2 dimensional weight `(L·W·H)/5000` | `Dimensions.dimensional_weight` (owns the `5000`) |
| R3 tier containment + boundary convention | `BracketTable.base_for` |
| R4 unknown-zone error | `ZoneTariffTable.tariff_for` |
| X1 range → worst case | `WeightReading.worst_case` |
| X2 insert/re-table tiers | `BracketTable` construction (data) |
| X3 per-zone surcharge | `ZoneTariff.surcharge` + the `.plus` in `RateEngine.price` |

The three change axes land on three **different** owners — `WeightReading` (input boundary), `BracketTable` (config), `ZoneTariffTable` (config) — none of which is the R1 formula. That is the architectural payoff: any combination of X1/X2/X3 composes without reopening `RateEngine.price` (§7 localize change axes, Open/Closed).

---

## 3. R × X input-space handling (the full space, not just the listed cases — §1)

**Base column** = the rule with no axis active. Then each rule crossed with each axis, traced over the whole input space.

### R1 — price = round_half_up(base × multiplier), then + surcharge
- **Base:** `base.times(mult)` rounds the product half-up to whole cents in `Money.times` (Decimal ⇒ half-cent boundaries round up correctly; float would not). Product of two Decimals is exact before quantizing. Input space: any base×mult, incl. exact multiples (`$12×1.5=$18.00`) and half-cent landings (`$10.005→$10.01`).
- **× X1:** X1 changes only *which* bracket base feeds R1 (via billable weight); the formula is untouched. Handled.
- **× X2:** X2 changes the base *value* from the table; the formula/rounding are unchanged. Handled.
- **× X3:** `...plus(tariff.surcharge)` — surcharge (whole cents) is added **after** rounding ("on top of the bracketed price"); no double-rounding, addition exact. Handled.

### R2 — billable = max(actual_worst_case, dimensional)
- **Base:** `max(reading.worst_case(), dims.dimensional_weight())` over exact `Weight`. Input space: actual dominates / dimensional dominates / equal (max returns it); a light item in a bulky box ⇒ dimensional wins. Handled.
- **× X1:** the actual side is `worst_case()` = interval `high`, so billable uses the range's maximum; if `dim ≥ high`, dim still wins — either way the true worst case. `1.9–2.1 kg` with small box ⇒ billable `2.1`. Handled — this is the sole X1×R2 meeting point.
- **× X2:** R2 yields a `Weight`; it then indexes whatever table is in force. Independent of the tier data. Handled.
- **× X3:** independent — R2 is weight-side, X3 is zone-side. No interaction. Handled.

### R3 — tier containment (total partition of [0,∞), lower-inclusive)
- **Base:** `base_for(w)` = last bracket with `lower ≤ w`. Input space incl. `w=0` → `[0,1)`; exact boundaries `1/2/5` → the **upper** neighbour (lower-inclusive) → `$8/$12/$20`; huge `w` → open `[5,∞)`; between → the correct tier. Total partition ⇒ exactly one tier for every `w ≥ 0`. Handled.
- **× X1:** by the time R3 runs, the range is already collapsed to `worst_case` (X1 confined to `WeightReading`), so R3 always sees a single `Weight`. A range straddling a boundary (`1.9–2.1`) bills at the **higher** tier because `worst_case = 2.1` ⇒ `[2,5) $12` (not `[1,2) $8`) — exactly the product's "worst case" intent. Handled.
- **× X2:** X2's home. A re-table or inserted tier is a new `BracketTable`; the containment rule is unchanged, and the construction invariant (starts at `0`, strictly increasing) means a re-table that would create a **gap or overlap is rejected at construction** (`InvalidRateTable`, fail-fast) rather than silently mispricing. Handled.
- **× X3:** independent — tier selection is pre-surcharge; the surcharge is added after and never affects which tier is chosen. Handled.

### R4 — unknown zone → error, never silently priced
- **Base:** `tariff_for(zone)` returns the tariff or raises `UnknownZone`; no default, no fallback price. A blank/malformed code fails earlier at `Zone` construction (`InvalidParcel`). Input space: known → tariff; well-formed-but-unsupported → `UnknownZone`; blank → construction error. Handled.
- **× X1:** independent — weight shape can't make a zone valid/invalid; and `tariff_for` runs before the bracket lookup, so an unknown zone errors even for a range reading. Handled.
- **× X2:** independent — bracket changes don't touch zone validity. Handled.
- **× X3:** multiplier **and** surcharge are one atomic per-zone lookup; an unknown zone raises before either is read, so X3 can never cause an unknown zone to be silently priced. Handled.

**Cross-axis:** X1/X2/X3 are localized to three disjoint owners, so all combinations (e.g. a range reading + a re-tabled tier + a surcharged zone) compose through the unchanged `RateEngine.price`. Traced: nothing forces the formula open.

---

## 4. Acceptance cases (traced)

- **C1** — `0.4 kg` (exact reading; box small enough that dimensional ≤ 0.4, so billable = 0.4) to zone A (mult `1.0`, surcharge 0): `base_for(0.4)` = `[0,1) = $5` = `500¢`; `500.times(1.0)=500¢`; `.plus(0)` = **$5.00**. ✓
- **C2** — `3.0 kg` (billable 3.0) to zone B (mult `1.5`, surcharge 0): `base_for(3.0)` = `[2,5) = $12` = `1200¢`; `1200.times(1.5)=1800¢`; `.plus(0)` = **$18.00**. ✓

(The cases give only actual weight; the design requires `Dimensions`, so each is read as a box whose dimensional weight ≤ the stated actual, making billable = actual — the reading that reproduces the expected numbers.)

---

## 5. Module skeleton (buildable)

`money.py` (Money) · `weight.py` (Weight, Dimensions, WeightReading) · `zone.py` (Zone) · `brackets.py` (Bracket, BracketTable — R3/X2) · `tariffs.py` (ZoneTariff, ZoneTariffTable — R4/X3) · `parcel.py` (ParcelInput — R2) · `engine.py` (RateEngine — R1) · `errors.py`. Dependencies point inward: value objects ← tables/parcel ← engine; the engine depends on the two tables by construction injection (§6 DIP, §12 testability — tables are seams, so R3/R4/X2/X3 are exercised in isolation).

---

## 6. Records to file (were this a live aims run)

`goals.md` (price a parcel from weight+zone; R1–R4; non-goals). `architecture.md` (the ownership map + the three-disjoint-axes seam). `base-dependencies.md` (Python + `decimal`, with the substrate-ask caveat). ADRs: **Money as integer cents + Decimal arithmetic** (rounding/boundary correctness); **tier boundary = lower-inclusive total partition** (the surfaced product decision); **X1 confined to `WeightReading.worst_case`**. Companions anchored on filing via `python3 knowledge/anchor.py <companion>`.

---

## 7. Self-review — the one mandatory revise round (measure → findings → revise)

Filled the assessment against `design-principles.md`, running the **subtractive** and **concept-fit** passes (`review.md`). Findings surfaced and the fixes now folded into the design above:

1. **Subtractive pass (§7 / unpaid seam machinery) — cut three wrappers.** The first pass introduced standalone `ZoneMultiplier`, `Surcharge`, and a `Price` type. None owns a rule the product states today: the multiplier is just a validated `Decimal` field on `ZoneTariff`; a surcharge and a price are both `Money`. Deleting them damages no current ownership → they were ceremony. **Fix:** multiplier is a `> 0`-validated field on `ZoneTariff`; surcharge and the returned price are `Money`. (Kept `Zone`, `Weight`, `Money`, `WeightReading` — each owns a real rule or identity, so each survives the pass.)

2. **Concept-fit pass (§4) — confirmed `WeightReading` is not a cram, and recorded why.** Checked the tempting objection that an exact reading modelled as a zero-width interval is a "degenerate case of a neighbour". It is not: measurement uncertainty is the *native* concept of a scale reading, `low` is meaningful (not an inert always-`None` tell), and the uniform interval is what makes `worst_case` a single-owner, branch-free X1 boundary. **Fix:** kept the interval and recorded the rationale as an ADR, so a later reviewer doesn't "helpfully" refactor it into an `Exact | Range` sum type that re-branches `worst_case` and lets X1 leak into the pricing path.

3. **§1 correctness — pinned the underspecified tier boundary + total-partition invariant.** The shared endpoints 1/2/5 kg were implicit and the acceptance cases never touch them — a classic "clean design ships a wrong number" gap. **Fix:** lower-inclusive convention stated, owned by one predicate in `BracketTable.base_for`, and the `starts-at-0, strictly-increasing` construction invariant added so an X2 re-table cannot silently introduce a gap/overlap (it fails fast as `InvalidRateTable`).

4. **§1/§5 — made error precedence and fail-fast validation explicit.** Value objects validate at construction; `price` looks up the zone tariff **before** the bracket, so R4 fires regardless of weight shape or tier-lookup outcome. Prevents an unknown zone from being masked by an unrelated failure.

5. **§5 — rounding localized and ordered.** All half-up rounding lives in `Money.times` (Decimal, not float); the X3 surcharge is added *after* rounding, in whole cents, so there is no double-rounding and half-cent boundaries stay correct.

Re-measured after the fixes: R1–R4 each have exactly one owner; X1/X2/X3 land on three disjoint owners and compose without reopening the formula; the full R×X space (§3) and both acceptance cases (§4) trace clean; no unpaid seam machinery and no concept cram remain. No substantial finding is left open, so the design reads **met** after the single mandated round.
