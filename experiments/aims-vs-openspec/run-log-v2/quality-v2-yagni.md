# Quality reading (YAGNI / earned-abstraction) — blind designs P / Q / R

Product: a checkout pricing service, judged only on the final (stage-3) architecture. Disposition:
YAGNI/simplicity — hard on speculative structure, mechanisms where a rule would do, and future-facing
fields that pay no present rent; but per the §2 note a single-implementation interface with a
*describable* second is not itself a fault. Every finding carries a quotation.

---

## Design P — `bundle-P`

### (1) Code smells
The signature blemish is **tax modelled as a zero-delta ledger entry** in the tax-inclusive market. The
market mints a VAT `Adjustment` whose delta is literally zero:

> `# tax_entry(bd): Adjustment(label="VAT", delta=Money.ZERO, status=TAX, tax_amount=bd.tax)  # embedded, delta 0` (P:222)

and the explanation is claimed to "walk LISTED → GROSS," but P's own SOUTH trace shows the row carries no
arithmetic:

> "Deltas sum −1.20 = 10.80 − 12.00 (VAT entry delta 0)." (P:428)

So in SOUTH the ordered ledger gains a row that moves nothing and only re-states a figure already carried
in `PricedLine.tax` (the `TaxBreakdown`). That is padding in an ordered-movement structure — the exact
"synthetic entry" the no-rounding-line principle warns against — and P's self-claim that "the amount is a
projection of its explanation now including tax" (P:351) is **overstated**: it is a real net→gross step
only in NORTH; in SOUTH `gross == final listed` already and the entry is a pure annotation.

`Adjustment` also accretes status-specific optionals (`superseded_by`, `would_be_delta`, `tax_amount`,
P:259–261) — a flat record standing in for a tagged union, now with a tax field bolted on.

### (2) Interfaces & encapsulation
`Market(Protocol)` (P:186) is a genuine abstraction under the §2 note — a describable third country earns
it:

> "A describable third market … is easy to name — the seam earns its place the moment the second country exists." (P:230–232)

But the interface leaks the *output* vocabulary: `tax_entry(self, breakdown) -> Adjustment | None`
(P:201) makes the market a constructor of explanation rows, i.e. the market reaches across into
`result.py`'s `Adjustment`/`AdjustmentStatus`. That is a second responsibility for a type whose stated job
is "the country's VAT law" (P:171–176).

### (3) Genericity calibration (§2 floor/ceiling)
Well-calibrated where it counts. `Money` reopens the rounding mode only under present force:

> "SOUTH breaks that: its per-line tax is rounded half-even … So the single-mode assumption is reopened." (P:125–127)

`fraction(num, den, rounding)` is "the minimal new operation the tax extraction needs" (P:165), though P
then leaves *both* `percent` and `fraction` on `Money` and calls the choice "a mechanism detail" (P:166) —
a small undecided redundancy. No speculative axis-space is built (contrast Q/R): each market is a class.

### (4) Cohesion & coupling (§6)
Discounts and tax are cleanly separated ("the engine holds no tax logic," P:176) and the change is
localized to steps 10–12 (P:336–346). The one coupling wart is the market→`Adjustment` dependency above:
a `NorthMarket`/`SouthMarket` that constructs output rows is mild feature envy toward the result layer.

### (5) Naming (§11)
Clean and consistent. `TaxBreakdown{net, tax, gross}` with `gross` always meaning tax-inclusive (P:180–184)
avoids the stage-2 ambiguity by usage rather than by ceremony. `PricedLine.cost` for the final line price
(P:277) is a slightly off name (it is a price, not a cost) but is carried from earlier stages.

### (6) SRP & size (§8/§12)
Strong. Market owns tax law, Money owns representation+quantization, and §13 deliberately leaves internal
plumbing to the implementer (P:523–533). The leanest **input threading** of the three: one shared catalog
and market as a plain argument —

> "The promotions catalog is shared across markets" (P:92–93); `def price(cart, catalog, market) -> PricedCart` (P:114)

— so P needs no per-market file, no registry, no routing guard. The cost of that leanness: the cart does
not name its market ("the market is a context, not stored on the cart," P:495), so a P `unit_price` is
uninterpretable in isolation. Under the stated spec (retention is not required) that is acceptable.

---

## Design Q — `bundle-Q`

### (1) Code smells
Q's core is clean, but it carries the most **unpaid fields**. `MarketProfile.minor_units` pays no present
rent — both markets are 2, and Q concedes the field does not actually make a different-quantum market free:

> `minor_units: int   # 2 for both markets today` (Q:209); "This is not a claim that a 0- or 3-decimal market is free." (Q:1174)

`TaxView` stores seven fields including `net`, `tax`, `payable` *and* `taxable_amount` — Q's own heading is
"**Why four money fields when two would do**" (Q:321), and the answer leans partly on a non-goal:

> "A stored quote must explain itself a year later, after a rate change …" (Q:329–330)

against a substrate where "There is no persistence" (Q:154) and retention is explicitly out. `TaxDerivation`
is a two-value enum (`COMPUTED` | `SUM_OF_LINES`, Q:298–300) — the "boolean with a label" the subtractive
pass names, defended as answering the C4 support question on the value itself.

Q's marquee claim is also **overstated**: "an entire second tax regime landed as one data row and one new
pure function" (Q:1620–1621). The actual stage-3 diff is a whole-payload rename (§2.1/§2.7), a new error
category, `Cart.market`, `Quote.market/payable/tax`, `LineQuote.tax`, `TaxView`, and I21–I32 — far more
than a row and a function; the phrase describes only the *next* market.

### (2) Interfaces & encapsulation
Excellent boundary discipline — this is Q's real strength. `explain` is the only constructor of `Quote`,
`tax` the only constructor of `TaxView`, checkable by imports (I14, Q:554; §4.9 Q:933–935). The market is
data, not a Protocol; the one branch that varies lives in `cart_tax` (Q:873–878).

### (3) Genericity calibration (§2 floor/ceiling)
The four-axis profile looks speculative but is honestly calibrated: every binary axis has *both* values
realized across the two shipped markets — `NORTH=(EXCLUSIVE, CART, HALF_UP)`, `SOUTH=(INCLUSIVE, LINE,
HALF_EVEN)` (Q:217–222) — so no axis models an absent value. The generality is bounded ("a closed table of
named markets … Nobody can construct a market at runtime," Q:242–243). The over-reach is not the axes but
the *fields copied onto every TaxView* (rate/treatment/derivation) for a self-description use the spec does
not ask for.

### (4) Cohesion & coupling (§6)
The best of the three. I26 makes the market-blind pipeline a *checkable* invariant, verified two ways —
imports and a both-markets-equal-journal test:

> "the journal is identical in every market" (Q:566); "price the same cart under both profiles and asserts the journals are equal (case F7)" (Q:588)

Each component has one owner capable of violating each invariant (Q:536). This is genuinely stronger than
R's prose statement of the same property.

### (5) Naming (§11)
Disciplined but verbose. The five-word vocabulary (list/amount/tax/net/payable, Q:172–178) and the outright
retirement of `gross`/`net` (Q:184–188) are real naming hygiene, but they are a section of apparatus where
R simply chose good names.

### (6) SRP & size (§8/§12)
Component SRP is crisp and finer-grained than R (engine/journal/explain/tax split). The cost is the heaviest
apparatus of the three: the `Cart.market` + catalog-market + `MarketMismatchError` + I30 routing guard
(Q:275–283, 570) — a mechanism whose need is *created* by Q's own one-file-per-market choice, and partly
justified by replay/retention (a non-goal). Length here is not "less decided"; it is *over*-decided —
I24/I25 are "the same fact said twice on purpose" (Q:601).

---

## Design R — `bundle-R`

### (1) Code smells
Fewest and mildest. The tax value object is the leanest of the three: `net` and `payable` are **projections
over a single stored amount**, not stored-and-asserted fields —

> `basis_amount: Decimal   # the amount this was figured from - the chain's own end` … `@property def net(...)` … `@property def payable(...)` (R:915–924)
> "net and payable are projections, so `net + tax == payable` is arithmetic the type performs rather than an invariant the code maintains." (R:928–929)

So R stores three where P and Q store the whole decomposition, and the identity cannot drift by construction.
`TaxSource` (`FIGURED`|`SUMMED`, R:920) is the same two-value enum as Q's derivation. `TaxPolicy.name`
("VAT", R:819) is constant across present markets — a minor unpaid field, cheaper than Q's `minor_units`.

### (2) Interfaces & encapsulation
Market is data (`TaxPolicy`, four facts, R:817–827) resolved through a `markets` registry; tax is one pure
function `assess(policy, amount)` with a single basis branch (R:831–842). `TaxLevel` selects *which
constructor* builds the cart figure, which makes the wrong C4 answer unreachable rather than merely
forbidden:

> "the cart figure a *different constructor* — one that takes line figures and cannot take an amount — means the wrong number is … unreachable" (R:886–888)

Same clean tax-as-separate-account seam as Q, joined "at exactly one number" (Decision 15, R:909; `basis_amount`
is the ledger's own `current`, R:927–928).

### (3) Genericity calibration (§2 floor/ceiling)
Best YAGNI discipline: R names seams and **declines to build them**. Per-line tax in a cart-level market
is explicitly not built —

> "Not built, because nobody has asked and a fabricated line tax on a legal document is not a default worth guessing." (R:900–901)

and the `allocation.apportion` helper is reused for discounts, with its only future use flagged and unbuilt
(R:282–283). No axis-space and no fields carried for a hypothetical reader.

### (4) Cohesion & coupling (§6)
Strong. Leaves (`money`, `allocation`, `ledger`, `tax`, `markets`) each own exactly one invariant-critical
property (R:192–197), and the fold completes before tax is touched: "The fold's code contains the word
'market' exactly nowhere" (R:426). This is the same market-blind property as Q's I26 but stated as prose +
acceptance cases (C1/C6) rather than an import-checkable invariant — slightly weaker enforcement than Q.

### (5) Naming (§11)
Economical. R uses `net`/`payable`/`basis_amount` consistently and never needs Q's gross/net retirement
section — good names instead of a vocabulary apparatus. `assess`, `CartTax.summed`, `PriceBasis`,
`TaxLevel` all read cleanly.

### (6) SRP & size (§8/§12)
Mostly good, with one concentration: the engine owns a long list —

> "Order, arbitration, the floor, apportionment, posting steps, market resolution, refusing a catalogue of another market, tax assembly, the boundary guard, rendering" (R:189)

— broader than Q's separated engine/explain, though each item is thin orchestration and the leaves hold the
real logic. R shares Q's routing-guard apparatus (Decision 12, R:796–802; third `markets` argument, R:766),
so it is not simpler than Q on input threading.

---

## Verdict — **R**, narrowly, over Q, with P close behind

The deciding property is **the amount of *unpaid* structure spent at the new tax seam — the one surface
stage 3 exists to add.**

- **P** keeps its input threading leanest (shared catalog, market as an argument, no routing guard) but
  pays for it at the tax seam: tax is injected into the promotion ledger as a **zero-delta `Adjustment`
  minted by the market** (P:222, P:201), which pads the ordered ledger in SOUTH and couples the VAT law to
  the output vocabulary. That is architectural, not a removable local blemish, and it makes P's
  "explanation is a projection including tax" claim true only in NORTH.
- **Q** models tax cleanly as a separate account and has the strongest *checkable* boundary (I26), but
  carries the most future-facing weight: `minor_units` that admits it buys nothing (Q:1174), a `TaxView`
  that stores four money fields plus rate/treatment/derivation for a "year later" the spec disowns
  (Q:329–330 vs Q:154), and the heaviest routing apparatus.
- **R** reaches the same clean tax-as-separate-account seam as Q **without** the over-storing: `net` and
  `payable` are projections over one stored amount, so the `net+tax==payable` identity is performed by the
  type rather than stored-and-asserted (R:928–929), and R alone *names-but-declines-to-build* the seams
  with no present force (R:900–901). It neither pads the ledger like P nor carries unpaid fields like Q.

R does not win on everything — Q's import-checkable market-blindness (I26) is the single strongest
individual abstraction in the set, and P's shared-catalog threading is the leanest plumbing. But on the
YAGNI axis I am asked to weigh, R spends the least structure that pays no present rent while still getting
the stage's hard properties (cart tax = sum, `net+tax==payable`) *by construction*. That is the
best-calibrated earned abstraction here.
