# Checkout pricing service — architecture (stage 2: explained prices, non-stackable promotions)

Extends stage 1. Every price (each line and the cart) now carries an **explanation**; some promotions are
**non-stackable**. All stage-1 behaviour is preserved.

## Changes to stage-1 components

- **Money** — unchanged.
- **PromotionCatalog** — unchanged except one new data field per definition, `non_stackable: bool`, loaded
  at the existing factory seam. Owns the flag's value, not its arbitration.
- **LineAdjustment (BOGO)** — arithmetic unchanged; its result is recorded as an Adjustment (the engine
  stamps the code).
- **CartDiscount interface** — unchanged: `amount_off(base: Money) -> Money` stays bare Money; identity is
  paired in at the engine.
- **PricingEngine** — same routing / Phase L / Phase C / order-independence / single clamp seam. Now also
  (1) assembles Explanations and (2) owns non-stackable arbitration (it is the only thing that sees all
  resolved promotions and entry order). `line_cost` / `cart_total` become the respective `.final()`.
- **Never-negative clamp** — same single seam; when it bites it now appends one clamp Adjustment (offset to
  zero, reserved code) to the cart explanation so `final()` equals the clamped value by construction.
- **CheckoutPricer / PricedCart** — each line and the cart gain an `explanation`; costs are `.final()`.
  `unapplied` keeps its stage-1 meaning (unknown/inapplicable only).

## New types and the rule each owns

- **Adjustment{code, delta: Money, applied: bool, superseded_by: code | None}** — a named money movement,
  minted **atomically** at the engine's per-promotion call site (code and delta born together, never
  mis-paired).
- **Explanation{origin: Money, adjustments: [Adjustment]}** — `final() = origin + Σ(a.delta where
  a.applied)`. One type for both line and cart; `origin` is an absolute anchor field, not a delta-from-zero.
  Tell-Don't-Ask (exposes `final()` and a read-only ordered view; never hands out raw deltas). **Sole owner
  of "the deltas sum exactly to (list − final), no residue, no invented rounding line"** — `final()` *is*
  that sum, there is no separate stored total, and each rounding lives inside a delta. The published amount
  **is** `final()`, so the explanation and the amount cannot disagree.
- **resolve_non_stackable(ordered_adjustments) -> ordered_adjustments** — pure, engine-owned; delta
  magnitude is the comparison key; among qualifying non-stackable codes keeps the largest money-off, marks
  the rest `applied = False, superseded_by = <winner>`, ties → entry order. Runs after deltas are computed on
  the shared frozen subtotal (no recomputation). Superseded losers stay in the explanation, marked
  not-applied; the `unapplied` channel is not reused for them.

## Ownership map (additions)

deltas sum exactly / amount == explanation → Explanation; non-stackable arbitration → PricingEngine (via
resolve_non_stackable); non_stackable flag value → PromotionCatalog.
