# YAGNI / simplicity judgment — three checkout pricing designs

Judged only on the final stage-3 architecture texts. Disposition: is each abstraction paying for
itself, or anticipating a future nobody asked for? Where has a team built a mechanism where a rule
would have done? Which could a competent engineer hold whole in their head?

---

## Design X

**S1 — fourth promotion kind; does the total-computer change?**
No. The rules module and the catalogue schema change; the engine (the fold that computes the total)
does not. *"Adding a fourth promotion kind is a new rule class plus a catalogue schema entry. The
engine does not learn about it, and it inherits stackability, explanation and tax for free."* The
fold is literally kind-blind: *"the engine's loop never mentions PCT, AMT or BOGO."*

**S2 — how many places round money?**
One module, reached from three kinds of site. *"a `money` module owns three operations — quantize to
two places under a named rounding mode ... and nothing else in the codebase calls `.quantize()`"*, and
*"`quantize` is reached from exactly three kinds of site — where a rate becomes an amount, where a
proportional share becomes cents, and where a tax portion becomes an amount."* Catalogue parsing does
not round — it *"rejects a bare float in a money field rather than coercing it."*

**S3 — explanation same structure as the amount, or separate?**
Same structure for price; a separate but joined account for tax. *"`current` is a projection, not a
field. There is no second copy of the amount to drift, so 'the explanation and the amount disagree' is
not a bug we test for — it is a state the type cannot hold."* Tax is a second account joined at one
number: *"`basis_amount` is the ledger's `current`, not a copy computed alongside it, so the two
accounts join at one number that exists once."* A boundary guard re-derives every relation before
return.

**S4 — third market with a third tax model; which components change?**
The `markets` table — a data row — provided the model fits the four declared facts; otherwise the
`tax` stage too. *"A tax law is four declared facts ... A third country that fits those four is a table
entry, not a release of the engine."* The tax producer is one function branching on a data field
(`assess`, basis branch) with the level selecting one of two constructors — not new classes.

**S5 — where is the order of adjustments stated?**
One place, as data. *"Ordering is a business rule, so it should be data. The `Scope` ordinal *is* the
ordering policy, stated once."* The secondary sort on code is stated in the same key.

**S6 — who owns "the deltas sum exactly to the difference"?**
The `ledger`. *"`ledger` owns *the chain links, and the deltas sum to the difference*."* The invariant
is definitional (`final` is read off the chain, no residue possible), and the boundary guard checks it
again before returning.

**Self-assessment check:** X's claims ("engine never mentions the kinds", "one module rounds", "a
third country is a table entry") hold against its own structure. The one soft spot is shared by all
three: a market needing *per-product* rates exceeds the four-fact model, which X concedes in
Decision 13.

---

## Design Y

**S1 — fourth promotion kind; does the total-computer change?**
`promotions.py` gains the rule and `catalog.py` learns the kind; `engine.py` also carries the kind's
rank in the ordering. *"`pricing/promotions.py` | a promotion **kind**'s own rule is added or
changed"*, while ordering *"sort by (stage, kind rank, code)"* lives in `canonical_order` inside the
engine, so a new kind needs a rank there. The money-moving fold itself is otherwise untouched.

**S2 — how many places round money?**
One. *"There is still exactly one *place* that rounds — the rule that changed is that the caller now
names the mode."* That place is `Money.portion`: *"THE rounding point, now with the mode named by the
caller ... rounded ONCE to the cent."*

**S3 — explanation same structure, or separate?**
Same structure — Y makes tax an actual entry in the explanation. *"The final amount is COMPUTED from
the entries. There is no stored total to disagree with them."* Tax is *"one more thing that happens,
recorded the same way"* as a `TAX` adjustment. The cost of that choice is a corrective mechanism:
*"Stage-2's `deltas_for(scope)` ... is not safe now ... So the discount folds are explicitly
`kind == PROMOTION` folds"* — putting tax in the chain forced kind-filtered folds to keep the
delta-sum rule true.

**S4 — third market; which components change?**
`market.py`, and it changes by gaining a *class*, not a data row. *"A country with tax-exclusive shelf
prices that taxes **per line** ... is a `LineTaxRule` whose assessment returns a non-zero delta ... no
other module changes,"* and a genuinely new combination *"is a third small class, which is one honest
sentence in `market.py`."*

**S5 — where is the order of adjustments stated?**
One place. *"`canonical_order` ... THE ordering rule (I5): sort by (stage, kind rank, code). Never by
submission order."*

**S6 — who owns "the deltas sum exactly to the difference"?**
`Explanation`, by construction. *"`final == list_price.after(net_delta)` and `net_delta ==
MoneyDelta.between(list_price, final)` — the deltas sum exactly to the difference, to the cent,
**including the tax delta**."*

**Self-assessment check:** Y repeatedly asserts "promotions.py is not touched at all" — true for
stage 3, and a real strength. But its claim that two tax protocols are necessary — *"two structurally
identical protocols are not distinguishable by `isinstance`"* — is a symptom, not a justification:
needing distinct method names to tell two classes apart is evidence the two classes are one rule
wearing two coats.

---

## Design Z

**S1 — fourth promotion kind; does the total-computer change?**
No; the journal (the total-computer) is untouched. *"'Buy X get Y free' (cross-SKU) | New rule class +
catalog schema fragment + a phase-10 entry. Engine untouched; it journals, explains and taxes itself
for free."* (Mild tension: the phase table is *"owned by the engine"* — but a BOGO-shaped kind reuses
existing phase 10, so no engine edit is actually required.)

**S2 — how many places round money?**
Four, each named. *"Where rounding happens — exactly four places, each with a named mode"*: catalog
load (percent→4dp, amount→quantum), proposal (HALF_UP), allocation (largest-remainder), and tax
(profile's mode). This is the largest rounding surface of the three — Z rounds the *rate* to 4dp at
load and republishes it, where X and Y keep the rate an exact fraction and never round it.

**S3 — explanation same structure, or separate?**
Promotion amounts come from the journal; tax is produced separately in the `tax` component and joined
by invariant. *"the explanation is not derived from the amounts; the amounts are derived from the
explanation."* Tax is deliberately *not* an entry — *"Stage 3's tax figures are a function of the
column totals ... They are not a row"* — and disagreement is blocked by *"**I22: a `TaxView`'s
`taxable_amount` is the `final` of the explanation it accompanies**"* plus I14 (tax computed only in
`tax`, from a journal fold).

**S4 — third market; which components change?**
The profile table — a data row — if the axes are existing enum members; otherwise a new enum member
and a branch in `tax`. *"**A third market** | One row in the profile table (§2.2) + one acceptance row
per case. If its four axes are among the existing enum members, that is the whole change."*

**S5 — where is the order of adjustments stated?**
One place, keyed by kind. *"Order is not a property of a code and not of the order the customer typed
things. It is a property of the **kind**, in a table owned by the engine."* Within a phase, submission
order; the pair `(phase, submission_index)` is the single walk order.

**S6 — who owns "the deltas sum exactly to the difference"?**
`explain`. *"`sum(a.delta) == final - basis`, exactly, for every line explanation and the cart
explanation | Owned by ... `explain`."* It rests on I13 (every journal row sums), owned by `journal`.

**Self-assessment check:** Z's computation model is clean, but it publishes more than it earns. Its
`TaxView` carries seven fields — the doc itself asks *"Why four money fields when two would do"* — and
carries `rate`, `treatment` and a `derivation` enum on every value *"so a stored quote explains itself
a year later ... without needing today's market profile table."* Yet Z states *"There is no
persistence in the substrate, and none is added."* Structure sized for an audit-a-year-later that the
stateless calculator never provides is exactly anticipation of a future nobody asked for. Removable in
isolation, but it is woven through I21–I29.

---

## Verdict: **X**

**The single structural fact that decides it:** stage 3's whole novelty is the market's tax law, and
the split between the three is *how a tax law is expressed*. Y builds it as **two polymorphic protocol
classes** (`LineTaxRule` / `CartTaxRule`, `VatAddedToCart` / `VatIncludedInLine`) dispatched by type —
a mechanism where a rule would have done, and one that additionally forces a "third small class" for
every new market and forces kind-filtered folds because Y also made tax an entry in the chain. X and Z
both express it instead as **one function branching on a data profile**, so a third market is a table
row. Between those two, X is the smaller and more decided realization: its tax value derives `net` and
`payable` as projections over a single joined number (`basis_amount == ledger.current`) and it adds no
wire-level `derivation`/audit surface, where Z stores the same figures plus a published `derivation`
enum and self-explaining `rate`/`treatment` fields justified by an audit the substrate cannot back. X
is the one design whose tax mechanism a competent engineer holds whole: a four-field policy record, one
`assess` with one branch, and the level selecting one of two constructors — nothing anticipating a
future that was not asked for.
