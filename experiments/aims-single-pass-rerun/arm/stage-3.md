# Checkout pricing service — architecture (stage 3: markets + tax)

A cart (customer id; lines of {SKU, list unit price, quantity}; entered promotion codes; a market) is priced
for its market, returning each line's cost and the cart's cost, each with an ordered explanation, plus tax
reporting as the market requires. Promotions are editable data. No persistence.

## Domain types and the rule each owns

- **Money** — value type over an integer cent count in the single currency. Owns **all** arithmetic and the
  round-to-the-cent rule; the rounding **mode** (half-up vs half-even) is a parameter the caller supplies,
  since markets round differently — the mechanics stay in Money, the mode choice belongs to the market model.
  No float crosses any seam. Surface: `zero()`, `+`, `-`, `*factor(mode)`, `clamped_at_zero()`.
- **SKU** — a small typed identifier (not a bare string). **CartLine{sku, unit_price: Money, qty}** with
  `gross() -> Money`. **Cart{customer, lines, codes, market: Market}** (`Market` a small typed value).

- **PromotionCatalog** — the data boundary; the only component that knows the editable file's format.
  `resolve(code) -> Known(Promotion) | Unknown(code)`; each `Promotion` carries `stackable: bool`. Adding or
  retiring a code is a file edit; nothing else changes. It discounts *listed* prices — whether those are
  tax-exclusive (NORTH) or tax-inclusive (SOUTH) is the market's interpretation, not the promotion's concern.

- **Promotion family** — three kinds behind scope-typed sub-interfaces: **LinePromotion** (`Bogo(sku,n)` →
  `(qty//n) * unit_price`, `target() -> SKU`) and **CartPromotion** (`Proportional(factor)` = Pct,
  `Fixed(amount)` = Amt). Each answers `delta_on(base) -> Money` (the effective money it removes, floored by
  what's available) and `applies_to(cart) -> bool`. The one `delta_on` query serves **both** ranking
  non-stackables and applying them, so "larger discount" and the applied amount can never diverge.

- **ConflictResolver (Selector)** — sole owner of non-stackability. `select(qualifying, base) ->
  (applied_in_order, superseded)`: ranks non-stackables by `delta_on(base)`, keeps the largest, breaks ties
  by entry order, emits each loser as `SupersededBy(winner)`; stackables always pass through.

- **PricingEngine** — orchestrator and invariant owner. Canonical pipeline, independent of entry order:
  line promotions → resolve non-stackable cart promotions → apply all `Proportional` (a commutative product)
  then all `Fixed` (a commutative sum) → `clamped_at_zero()` on the cart total. It owns order-independence,
  the never-negative floor (one clamp, one place), and producing per-line + cart figures. It then delegates
  one final stage: `cart.market.finalize(priced_cart) -> TaxedResult`. Tax is delegated, never inlined.

- **PriceLedger** — value type `{list_price: Money, adjustments: [Adjustment]}` with
  `final() = list_price + Σ(applied deltas)`. It stores **no** independently-computed total, so the reported
  amount *is* the fold of the explanation — one source, nothing to drift. **Sole owner of "deltas sum
  exactly to (list − final), no residue, no invented rounding line"**: deltas are whole cents summed by
  integer arithmetic; a percentage's rounding is baked into that adjustment's own delta; when the clamp
  truncates, the ledger records the *effective* movement so it still sums to the final. A ledger may also
  carry a read-only **tax decomposition** of its final (SOUTH).

- **Adjustment** `{label: ListPrice | Code | Tax, delta: Money, status: Applied | NotApplied(reason)}`,
  `reason ∈ {Unknown, Inapplicable, SupersededBy(code)}`. All reporting (unknown/inapplicable/superseded)
  is unified as not-applied entries here.

- **MarketTaxModel (seam)** with **NorthTaxModel** and **SouthTaxModel** — each the single owner of its
  market's tax model and rounding rule:
  - **NorthTaxModel** — prices tax-exclusive; VAT = `round(net × 0.17, half_up)` applied once to the
    discounted cart net, at cart level; **appends one Tax `Adjustment`** to the cart ledger → total = net +
    VAT; lines pass through untouched (no line tax). Every stage-1&2 figure and explanation is preserved
    exactly — VAT is a separable added entry.
  - **SouthTaxModel** — prices tax-inclusive (20% inside); tax reported per line, rounded half-even per line,
    cart tax = Σ line taxes. Because tax is per-line, it **first allocates the cart-level discount across the
    lines** — spread in proportion to each line's gross, leftover pennies assigned by largest fractional
    remainder, so line finals sum *exactly* to the cart net. Each line's tax = `round(line_final × 20/120,
    half_even)`, recorded as a **decomposition** of that final (never a delta). Cart tax = Σ line taxes =
    the tax embedded in the invoice.

- **TaxedResult** — the taxed invoice: per line {cost, optional tax}; cart {total, tax}.

## Ownership map

rounding mechanics → Money; rounding mode + tax model per market → each MarketTaxModel; order-independence,
pipeline order, never-negative floor → PricingEngine; non-stackable arbitration → ConflictResolver;
"deltas sum exactly / amount == explanation" → PriceLedger; editable-data / unknown-code → PromotionCatalog.

## Invariant preserved in both markets, undissolved

A priced amount equals the running total of its ledger, and its deltas sum exactly to (list − final).
**NORTH** keeps it by reusing the same append/fold — VAT is one more real adjustment, so amount = fold.
**SOUTH** keeps it because tax is **not** a delta — it is a read-only decomposition derived from the
already-final inclusive amount (a function of the amount, which cannot disagree); the promotion deltas still
fold exactly, and the per-line allocation only *splits* the cart-level delta into per-line deltas reconciled
to the penny, so each line ledger folds exactly and the cart is their exact sum.

## Correctness trace (all cases + the full input space)

- C1 NORTH: net 25.00 − 2.50 = 22.50; VAT half-up(3.825)=3.83 appended; total 26.33; no line tax.
- C2 SOUTH (1 line): gross 12.00 − 1.20 = 10.80; tax half-even(1.80)=1.80.
- C3 SOUTH: tax half-even(0.025)=0.02, half-even(0.075)=0.08; cart 0.10.
- C4 SOUTH: three 0.15 lines; each half-even(0.025)=0.02; cart 0.06 (Σ per line), not 0.08.
- C5 SOUTH: BOGO net 12.00; tax half-even(2.00)=2.00.
- C6 NORTH: neutral pipeline untouched → every stage-1&2 figure and explanation identical.
- **Multi-line SOUTH + cart-level discount:** the cart PCT/AMT is allocated across lines (proportional to
  gross, pennies by largest remainder, line finals summing exactly to the discounted cart total); per-line
  tax = half-even(discounted_line / 6), so it falls on the **discounted** amount and Σ line tax = the
  reported cart tax. Every branch — one line or many, with or without a cart-level discount, either market —
  produces a per-line and cart figure with an explanation the amount cannot contradict.
