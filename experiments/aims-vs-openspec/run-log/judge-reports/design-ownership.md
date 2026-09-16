> **SUPERSEDED — do not read as the Q1 result.** This invariant-ownership judge answered six operator-written seam questions, not aims' `design-principles.md`, so it did not assess code smells, interface use, encapsulation or genericity, and it over-weighted the one axis (tax placement) where aims was weakest. The Q1 reading was re-run against the full rubric; see `quality-ownership.md`. Kept for audit only.

# Design judgment — invariant ownership

Three final architectures for a checkout pricing service. I judge by one question: is each stated
rule owned and enforced in exactly one place, made true by structure rather than by a promise someone
must remember to keep? Below, the six questions for each of X, Y, Z, each with a quotation, then one
verdict.

---

## Design X

**S1 — Fourth promotion kind: which components change? Does the total-computer change?**
Changes: `rules` (a new class) and `catalogue` (a schema entry). The engine — which computes the
total — does **not** change.
> "Adding a fourth promotion kind is a new rule class plus a catalogue schema entry. The engine does
> not learn about it, and it inherits stackability, explanation and tax for free."

and, structurally:
> "Here the engine's loop never mentions PCT, AMT or BOGO."

This holds up: order is a `Scope` ordinal carried on the rule, so a new kind declares its own scope
and the fold is untouched. The self-claim is not overstated.

**S2 — How many places round money?**
One module, reached from three kinds of call site.
> "Exactly one module rounds, and exactly one place can violate the sum invariant."
> "`quantize` is reached from exactly three kinds of site — where a *rate* becomes an *amount*, where
> a *proportional share* becomes *cents*, and where a *tax portion* becomes an amount."

Named: rate→amount (in rules-via-money), share→cents (allocation), tax-portion→amount (tax). One
module, `money`, is the only caller of `.quantize()`.

**S3 — Explanation from the same structure as the amount, or separate?**
Same structure; there is no second copy to drift.
> "`current` is a projection, not a field. There is no second copy of the amount to drift, so 'the
> explanation and the amount disagree' is not a bug we test for — it is a state the type cannot hold."

Tax is the one thing held *outside* that structure, joined at exactly one number:
> "`basis_amount` is the ledger's `current`, not a copy computed alongside it, so the two accounts
> join at one number that exists once."

**S4 — Third market with a third tax model: which components change?**
The `markets` table (a declared entry), and `tax` only if the arithmetic is genuinely new.
> "A tax law is four declared facts ... A third country that fits those four is a table entry, not a
> release of the engine."

The two arms (add / extract) are data-parameterised by basis/level/rounding, so a *new combination*
of the four facts is free; only a genuinely novel arithmetic touches `tax`.

**S5 — Where is the order of adjustments stated?**
One place — as data, the scope ordinal.
> "Ordering is a business rule, so it should be data. The `Scope` ordinal *is* the ordering policy,
> stated once."

**S6 — Who owns "the deltas sum exactly to the difference"?**
`ledger`, and it holds only price movements (tax is not in the chain).
> "`ledger` owns *the chain links, and the deltas sum to the difference*."
> "The invariant is not 'we corrected the residue' but 'there is no residue'."

---

## Design Y

**S1 — Fourth promotion kind: which components change? Does the total-computer change?**
Changes: `promotions.py` (the new kind) and `catalog.py` (schema).
> "`pricing/promotions.py` | a promotion **kind**'s own rule is added or changed"

The total is read off the explanation, but the fold that feeds it orders codes through the engine:
> "THE ordering rule (I5): sort by (stage, kind rank, code)."

So a fourth kind also needs a **kind rank** inside the engine's `canonical_order` — the ordering half
of the total-computer is touched, unlike in X where the ordinal rides on the rule.

**S2 — How many places round money?**
One place.
> "There is still exactly one *place* that rounds — the rule that changed is that the caller now names
> the mode".

Named: `Money.portion` (`percentage` is defined through it; allocation truncates exactly, so it is
not a rounding site).

**S3 — Explanation from the same structure as the amount, or separate?**
Same structure — and tax is folded *into* that same structure as a `TAX` entry.
> "The final amount is COMPUTED from the entries. There is no stored total to disagree with them."
> "Tax becomes one more thing that happens, recorded the same way".

This is the load-bearing difference. Because tax is a delta in the chain, the stage-2 discount fold
broke and had to be patched:
> "Stage-2's `deltas_for(scope)` summed every delta of a scope, which was safe while every non-opening
> entry was a promotion. It is not safe now ... a fold that only filtered by scope would report the
> cart's discount total as 1.33 ... instead of 2.50."

The remedy — "the discount folds are explicitly `kind == PROMOTION` folds" — restores correctness, but
"the sum of the deltas" no longer denotes the discount; every future fold must remember the kind
filter. Ownership shifts from the structure's contents to a filtering convention applied at each read.

**S4 — Third market with a third tax model: which components change?**
`market.py` only — a third small class.
> "A country with tax-exclusive shelf prices that taxes **per line** ... is a `LineTaxRule` whose
> assessment returns a non-zero delta; the line ledger applies it, the cart's aggregate sums the
> deltas as well as the taxes, and no other module changes."

Note Y deliberately makes rounding+level part of the *class identity*, not data, so a new combination
is a new class rather than a table row — one module either way, marginally more code than X/Z.

**S5 — Where is the order of adjustments stated?**
One place — the `canonical_order` function.
> "THE ordering rule (I5): sort by (stage, kind rank, code). Never by submission order."

**S6 — Who owns "the deltas sum exactly to the difference"?**
`explanation.py`, but the invariant now spans the tax delta.
> "`final == list_price.after(net_delta)` ... the deltas sum exactly to the difference, to the cent,
> **including the tax delta** (I8)."

Owned in one place, but the "difference" it sums to is now list→payable, not list→discounted; the
discount is recovered only by the kind-filtered fold above.

---

## Design Z

**S1 — Fourth promotion kind: which components change? Does the total-computer change?**
Changes: a new `rules` class + a `catalog` schema fragment + a phase entry.
> "'Buy X get Y free' (cross-SKU) | New rule class + catalog schema fragment + a phase-10 entry.
> Engine untouched; it journals, explains and taxes itself for free."

The "Engine untouched" self-assessment is **mildly overstated**: order is "a property of the **kind**,
in a table owned by the engine" (§6.1), so the kind→phase table the engine owns gains a row for the
new kind. The journal that computes amounts is untouched; the engine's phase table is not quite.

**S2 — How many places round money?**
Four call sites, one module.
> "Where rounding happens — exactly four places, each with a named mode"

Named: (1) catalog load (exact), (2) proposal `HALF_UP`, (3) allocation (largest-remainder),
(4) tax (profile's mode). "Nowhere else" — all four are calls into `money`. The most explicit and the
most honest enumeration of the three.

**S3 — Explanation from the same structure as the amount, or separate?**
The price comes from the journal (same structure); tax is produced *separately* in `tax`, joined by
invariant.
> "the amounts are derived from the explanation."
> "'The explanation and the amount disagree' and 'the invoice and the tax figure disagree' are both
> unrepresentable for the same reason: there is one source for each, and the second one is a pure
> function of the first."

The join is an asserted equality:
> "**I22: a `TaxView`'s `taxable_amount` is the `final` of the explanation it accompanies.**"

(`tax_for` is handed `explanation.final` as its argument, so it is the same number; I22 guards the
call.) Like X, tax is kept out of the delta chain — but joined by a checked invariant rather than by
X's shared field identity.

**S4 — Third market with a third tax model: which components change?**
One row in the `market` profile table (and `tax` only for genuinely novel arithmetic).
> "**A third market** | One row in the profile table (§2.2) + one acceptance row per case. If its four
> axes are among the existing enum members, that is the whole change."

New *combinations* compose for free: "`EXCLUSIVE` × `LINE` already composes ... Nothing." A truly new
model (per-product rates) is flagged honestly as the one thing that "moves a seam."

**S5 — Where is the order of adjustments stated?**
One place — the engine's phase table.
> "Order is not a property of a code and not of the order the customer typed things. It is a property
> of the **kind**, in a table owned by the engine".

**S6 — Who owns "the deltas sum exactly to the difference"?**
`explain`, and tax is explicitly excluded from the deltas.
> "I11 | `sum(a.delta) == final - basis`, exactly, for every line explanation and the cart
> explanation | `explain`"
> "**There is deliberately no `RESIDUAL` / `ROUNDING` kind, and no `TAX` kind.** The enum has three
> members."

Clean single owner over a structure that holds only price movements.

---

## Verdict: **X**

**The single structural fact that decides it: whether tax lives inside or outside the structure that
owns "the deltas sum exactly to the difference," and whether the component that computes the total
names any promotion kind, market, or tax.**

On the first half, Y is eliminated. Y makes tax a `TAX` delta *inside* the explanation, so the one
invariant the whole product is built on — deltas sum to the difference between list and final — now
spans the tax, and "the sum of the deltas" stops meaning "the discount." Y documents the consequence
itself: the stage-2 discount fold became unsafe and had to be re-cut as a `kind == PROMOTION` fold.
That converts a property once guaranteed by the *contents* of the structure into a filtering
convention that every future read must remember. X and Z both keep tax out of the delta chain — a
separate account (X) / a `TaxView` (Z) joined to the explanation at exactly one number — so a fold
over the chain means exactly one thing and cannot silently pick up tax.

Between the two survivors, X edges Z on the second half. In X the fold that computes the total names
no promotion kind ("the engine's loop never mentions PCT, AMT or BOGO"), no market ("the fold's code
contains the word 'market' exactly nowhere"), and no tax (assessed after the fold completes); order is
a `Scope` ordinal carried on the rule, so a fourth kind, a third market, and the entire tax feature
each land without editing the thing that computes the total. Z reaches the same tax isolation, but
locates the kind→phase ordering in a table the engine owns — so a fourth kind edits the total-computer
by one row, and its "Engine untouched" claim is correspondingly overstated. X also leans harder on
making the bad state unrepresentable rather than checked: the amount is a projection of the chain
(no second copy to drift), `net + tax == payable` is "arithmetic the type performs rather than an
invariant the code maintains," and the wrong per-line-market cart tax is barred by a constructor that
"takes line figures and cannot take an amount." Z achieves equivalent safety but carries more of it as
invariants (I21–I31) verified before return — checks that must run, where X has states that cannot be
built.

Z is the more thoroughly specified document and is not behind on any single question; under a stricter
reading its import-checkable single-constructor boundary is a genuine strength. But on the disposition
that governs here — each rule made true by structure, and the total-computer closed to new kinds,
markets, and tax alike — X owns the most with the least, and it is not close enough to Y to be in
doubt, nor far enough from Z to be luck.
