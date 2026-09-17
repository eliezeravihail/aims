# Checkout pricing service — architecture (stage 1: price a cart)

A cart (customer id; lines of {SKU, list unit price, quantity}; entered promotion codes) is priced,
returning each line's cost and the cart's cost. Promotions are editable data. No persistence.

## Components and the rule each owns

- **Money** — value object over integer cents; sole owner of the money vocabulary and one half-up rounding
  function; cent arithmetic; `clamped_at_zero()`. No float/Decimal crosses any seam. Does not own
  non-negativity.
- **PromotionCatalog** — loads the business-edited data file; a **closed factory keyed by tag** (PCT / AMT /
  BOGO); `resolve(code) -> Promotion | Unknown{code, reason}`; **never throws** (halting path structurally
  absent); owns the data format, the closed kind-set, the unknown verdict, and an `N >= 1` guard. Emits
  behaviour objects, not raw rows.
- **LineAdjustment (BOGO)** — concrete, no interface (a family of one earns none). `apply(lines) -> line
  reductions`; free = `qty // N` at the line's unit price. Owns BOGO arithmetic and applicability.
- **CartDiscount interface (PCT, AMT)** — `amount_off(base: Money) -> Money`, rounded to the cent; two real
  implementations; the `base` parameter is the structural carrier of order-independence.
- **PricingEngine** — routes each resolved promotion to a phase **by type** (no kind switch). Phase L: apply
  BOGO → priced lines + a **frozen** post-adjustment subtotal. Phase C: each CartDiscount computes
  `amount_off` against the **same frozen subtotal**; the amounts are **summed** (addition commutes → entry
  order is unforgeably irrelevant). Sole owner of order-independence and pipeline order.
- **Never-negative** — exactly one clamp: `cart_total = Money.clamped_at_zero(frozen_subtotal − Σ
  discounts)`, at the single cart-total-producing seam; lines are never clamped.
- **CheckoutPricer (facade) → PricedCart{ lines:[{sku, line_cost}], cart_total, unapplied:[{code, reason}] }**
  — unknown/inapplicable codes are data in the result, never exceptions; no explanation objects; no per-line
  allocation.

## Ownership map

order-independence + pipeline order → PricingEngine; cents + rounding → Money; never-negative → the single
clamp; unknown-code verdict (without halting) → PromotionCatalog; BOGO → LineAdjustment; PCT/AMT →
CartDiscount.
