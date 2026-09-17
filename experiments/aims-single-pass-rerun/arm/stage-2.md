# Checkout Pricing Service — Stage 2 (explanations + non-stackable)

**Extension overview.** The single structural change: a price is no longer a bare number with a status list
beside it — it *is* the running total of an ordered ledger of adjustments. Everything else stays or gains an
attribute at a seam it already owns. All stage-1 finals are preserved.

**Money — stays.** Its integer-cent representation is *why* deltas can sum with no residue: every delta is a
whole number of cents, so `list − final` is an exact integer sum, never an approximation needing a fudge
line. No new surface.

**Cart / CartLine / SKU — stay unchanged** (inputs).

**PromotionCatalog — gains at its existing seam.** A definition may now carry a `non_stackable` flag; the
catalog reads it into the typed `Promotion` (`stackable: bool`). `resolve(code) -> Known | Unknown` is
unchanged — richer data, no code change elsewhere.

**Promotion family — gains one uniform query.** Each promotion answers `delta_on(base) -> Money`: the
effective money it removes (Bogo against its line; Proportional/Fixed against the cart base; floored by what
is available). This one query serves both *ranking* non-stackables and *applying* them, so the "larger
discount" comparison and the applied amount can never diverge.

**PricingEngine — same seams and invariants, new internals.** Still owns the canonical order, the
never-negative cart floor, and producing per-line and cart figures. It now (a) delegates non-stackable
conflicts to a Selector, then (b) *folds* surviving adjustments through a ledger instead of computing a bare
number. Canonical order: line promos → resolve non-stackable cart promos → apply all proportional then all
fixed (survivors + stackables) → floor at zero. Same cart → same answer; entry order is consulted only to
break exact ties, which the spec requires.

**New — `PriceLedger` (the explanation, and the price).** A value type holding `list_price: Money` and an
ordered `[Adjustment]`, deriving `final() = list_price + Σ(applied deltas)`. It stores no independently-
computed total. **This is the single mechanism making "the explanation can never disagree with the amount"
true by construction: the amount *is* the fold of the explanation — one value, one source, nothing to
drift.** It is also the **single owner of "deltas sum exactly":** because deltas are whole cents summed by
integer arithmetic, `list − final ≡ Σ deltas` identically — no residue, no invented rounding entry (a
percentage's rounding is baked into that adjustment's own recorded delta). When the floor truncates the last
delta, the ledger records the *effective* movement (delta = −running_total), so it still sums exactly to a
zero final.

**New — `Adjustment {label: ListPrice | Code, delta: Money, status: Applied | NotApplied(reason)}`**, reason
∈ {Unknown, Inapplicable, SupersededBy(code)}. Stage-1's unknown/inapplicable statuses become not-applied
entries here, unifying all reporting in one place.

**New — `ConflictResolver` (Selector), sole owner of non-stackability.** `select(qualifying, base) ->
(applied_in_order, superseded)`. Ranks non-stackables by `delta_on(base)`, keeps the largest, breaks ties by
entry order, emits each loser as `SupersededBy(winner)`; stackables always pass through (non-stackable
excludes only other non-stackable). Line and cart each carry a ledger; a cart-level discount lives in the
cart ledger (starting from Σ line list prices), never redistributed onto lines — so stage-1 line costs are
unchanged.

**Self-check.** B1: cart ledger [25.00, SAVE10 −2.50] → 22.50, Σ −2.50. B2: COFFEE line [16.00, COFFEE3
−4.00]→12.00, WIDGET [12.50]; cart [28.50, COFFEE3 −4.00, SAVE10 −2.45]→22.05, Σ −6.45. B3: base 50.00,
TENOFF −10 > SAVE10 −5 → cart [50.00, TENOFF −10.00, SAVE10 NotApplied SupersededBy TENOFF]→40.00. B4: base
150.00, SAVE10 −15 > TENOFF −10 → 135.00, TENOFF superseded. B5: base 100.00, tie −10 each → SAVE10 (entered
first) → 90.00, TENOFF superseded. B6: every stage-1 final unchanged — the ledger is additive metadata; A7
still floors to 0.00 (TENOFF's effective delta −1.00, Σ = list−final).

> Note (stage-3 foresight): the stage-2 choice that a cart-level discount is **not** redistributed onto lines
> is correct while there is no per-line figure that depends on it. Stage 3's SOUTH market introduces exactly
> such a figure (per-line tax on the discounted amount), and the stage-3 design adds the allocation then —
> discovered by the §13 correctness trace over the full input space, not by a stated case.
