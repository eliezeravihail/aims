# Checkout Pricing Service — Architecture (stage 1)

## Domain types (the shared vocabulary)
- **`Money`** — a value type wrapping an integer cent count in the single currency. It owns *all* arithmetic
  and the round-to-the-cent rule, so rounding lives in exactly one place and is deterministic. Surface:
  `zero()`, `+`, `-`, `*factor` (with defined rounding), `clamped_at_zero()`. No other component ever touches
  a float.
- **`CartLine {sku: SKU, unit_price: Money, qty: int}`** with `gross() -> Money` (= unit_price × qty). `SKU`
  is a small typed identifier, not a bare string.
- **`Cart {customer: CustomerId, lines: [CartLine], codes: [Code]}`** — the input.

## PromotionCatalog — the data boundary (the editable-data seam)
Loads the business-edited file and is the *only* component that knows its format. Contract:
`resolve(code: Code) -> Known(Promotion) | Unknown(code)`. Adding or retiring a code is a file edit; no other
component changes. It translates rows into typed `Promotion` objects and never leaks the file's shape
outward.

## Promotion — behavior behind an interface
The three kinds compute differently, so each is its own implementation, addressed through two sub-abstractions
distinguished by *scope*:
- **`LinePromotion`** — targets one SKU; `discount(line) -> Money`, `target() -> SKU`. `Bogo(sku, n)` returns
  `(qty // n) * unit_price`.
- **`CartPromotion`** — contributes a *typed* reduction to the cart stage: `Proportional(factor)` (Pct) or
  `Fixed(amount)` (Amt). It declares *what kind* of reduction it is rather than a pre-sequenced number, so the
  engine can order deterministically.

Every promotion also answers `applies_to(cart) -> bool` (a Bogo whose SKU is absent does not apply).

## PricingEngine — orchestrator and invariant owner
`price(cart, catalog) -> PricingResult`. One fixed canonical pipeline, independent of the order codes were
entered:
1. Resolve every code through the catalog; record unknowns.
2. Compute each line's gross.
3. Apply each applicable `LinePromotion` to its target line → per-line net; record any resolved-but-
   inapplicable code.
4. Cart base = Σ line nets.
5. Apply all `Proportional` factors (a product — commutative), then all `Fixed` amounts (a sum —
   commutative). Fixed-after-proportional is the fixed rule.
6. `clamped_at_zero()` on the cart total.

The engine is the single owner of order-independence (fixed stages + within-stage commutative combination),
of the never-negative cart invariant (one clamp, one place), and of producing both per-line and cart figures.

## PricingResult
`{ lines: [{sku, cost: Money}], total: Money, codes: [{code, status: Applied|Unknown|Inapplicable}] }`.
Assembling every code's status here is the single owner of "report it, don't silently ignore it, don't stop
the rest."

## Why these seams
The editable file is quarantined in one component, so a new *code* is pure data. The three kinds sit behind
scope-typed interfaces, so a fourth kind of an existing shape (another line / proportional / fixed rule) is a
new implementation, not a rewrite. Each declared rule has exactly one home: rounding and currency in `Money`;
order-independence and never-negative in the engine; existence-of-code in the catalog; reporting in the
result. Core computation is pure over immutable inputs — the same cart yields the same answer.

## Self-check — which component produces each result
- **A1**: engine step 2 — 12.50×2 = 25.00 line and total.
- **A2**: `Proportional(0.9)` → 25.00×0.9 = 22.50.
- **A3**: `Fixed(10.00)` → 25.00−10.00 = 15.00.
- **A4**: `Bogo(COFFEE,3)` → 4//3 = 1 free → 16.00−4.00 = 12.00 line/total.
- **A5**: Bogo sets COFFEE line to 12.00; base 12.00+12.50 = 24.50; `Proportional(0.9)` → 22.05.
- **A6**: catalog returns `Unknown(NOPE)`; line 12.50, total 12.50; result marks NOPE Unknown.
- **A7**: `Fixed(10.00)` → 1.00−10.00 = −9.00; engine `clamped_at_zero()` → 0.00.
