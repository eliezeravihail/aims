# Checkout pricing service — architecture (stage 3: market-aware, explained prices)

A cart (customer id; lines of {SKU, list unit price, quantity}; entered promotion codes) is priced **for a
market**, returning each line's cost and the cart's cost, each with an ordered **explanation**, plus tax
reporting as the market requires. Promotions are editable data. No persistence.

## Components and the rule each owns

**Money** — value object over an integer count of cents. Sole owner of the money vocabulary and of rounding
*mechanics*: two pure functions, `round_half_up` and `round_half_even`, plus cent arithmetic and
`clamped_at_zero()`. No float or Decimal ever crosses a seam. It owns *how* to round; it does not decide
*which* mode, *where*, or *how often* — that is a market policy (see Market).

**PromotionCatalog** — loads the business-edited data file and acts as a **closed factory keyed by tag**
(exactly `PCT`, `AMT`, `BOGO`). `resolve(code) -> Promotion | Unknown{code, reason}`. It **never throws** —
the halting path is structurally absent, so an unknown/inapplicable code is reported as data while the rest
of the cart prices. Owns: the data format, the closed kind-set, the `non_stackable: bool` flag's value (not
its arbitration), the unknown verdict, and an `N >= 1` guard so BOGO cannot divide by zero. Emits behaviour
objects, never raw rows.

**LineAdjustment (BOGO)** — concrete, behind no interface (a family of one earns none). `apply(lines) ->
line reductions`; free units = `qty // N`, each priced at the line's unit price. Owns BOGO arithmetic and
its applicability. Market-agnostic: it acts on whatever list/shelf price it is handed.

**CartDiscount interface (PCT, AMT)** — `amount_off(base: Money) -> Money`, rounded to the cent. A genuine
two-implementation abstraction; each owns its own arithmetic. The `base` parameter is the structural carrier
of order-independence. Market-agnostic.

**Adjustment{code, delta: Money, applied: bool, superseded_by: code | None}** — a named money movement,
minted **atomically** at the engine's per-promotion call site where the resolved `(code, promotion)` pair is
already jointly in scope (so a code and its delta can never be mis-paired downstream). The same type carries
promotion deltas, the never-negative clamp, and NORTH's VAT — every movement of the payable total is an
Adjustment.

**Explanation{origin: Money, adjustments: [Adjustment]}** — `final() = origin + Σ(a.delta for a where
a.applied)`. **One type at both altitudes** (a line and the cart are the same kind of thing: a priced item
with a named origin and ordered named deltas). `origin` is an absolute anchor field, not a delta-from-zero.
Tell-Don't-Ask: it exposes `final()` and a read-only ordered view; it never hands out raw deltas to be
re-summed elsewhere. **Sole owner of "the deltas sum exactly to (list − final), to the cent, no residue, no
invented rounding line"** — because `final()` *is* that sum; there is no separately stored total to
reconcile, and each rounding lives *inside* a delta. The published amount **is** `final()`, so the
explanation and the amount cannot disagree. Explanation never learns about markets and never folds per kind.

**resolve_non_stackable(ordered_adjustments) -> ordered_adjustments** — pure function, engine-owned. Delta
magnitude is the comparison key (no new comparison type): among qualifying non-stackable codes it keeps the
largest money-off, marks the rest `applied = False, superseded_by = <winner>`, ties broken by entry order.
Runs after deltas are computed against the shared frozen subtotal, so it needs no recomputation and does not
disturb order-independence. A superseded loser stays in the explanation (marked not-applied, naming its
superseder); the `unapplied` channel remains for unknown/inapplicable codes only.

**PricingEngine** — the composer. Routes each resolved promotion to a phase **by type** (no phase tag, no
kind switch). Phase L: apply BOGO → priced lines + a **frozen** post-adjustment subtotal. Phase C: each
CartDiscount computes `amount_off` against the **same frozen subtotal**; the amounts are **summed** (addition
commutes → entry order is unforgeably irrelevant). Then `resolve_non_stackable`, then the single clamp, then
**one terminal call** `market.impose(...)`. Sole owner of pipeline order, order-independence, and the single
clamp seam. It learns no tax formula, no rounding mode, and no market kind.

**Never-negative clamp** — one clamp at the single cart-total-producing seam, **before** tax; when it bites
it appends one clamp Adjustment (offset to zero, reserved code) so `final()` equals the clamped value by
construction. Lines are never clamped.

**Market (interface; NorthMarket, SouthMarket — a closed set)** — sole owner of a market's **tax model**
(exclusive-added vs inclusive-extracted), its **rate** (17 / 20), and its **rounding policy** (which Money
mechanic, at what granularity, at what point). `impose(line_explanations, cart_explanation) -> Taxed`. The
engine holds one Market and never branches on kind (Tell-Don't-Ask).
- **NorthMarket** — appends **one** VAT Adjustment = `Money.round_half_up(0.17 × clamped cart final())` to
  the cart explanation, as a real (moving) delta; line explanations untouched (NORTH lines show no tax).
  "Half-up once at cart, after every promotion" is structural: one figure, one rounding call.
- **SouthMarket** — gross is already payable, so it adds **no** delta; it produces per-line `LineTax{net,
  tax}` with `tax = Money.round_half_even(line_final × 20 / 120)` and `net + tax = line_final`; `cart_tax =
  Σ line tax` (exact). "Half-even per line" and "cart tax = sum of the line figures" are structural — it is
  impossible to round at cart level or return a cart tax that is not the sum.

**Taxed{line_explanations, cart_explanation, cart_tax: Money, per_line_tax: [LineTax] | None}** — the only
tax vocabulary crossing back to the engine; no float; the concrete Market type never leaks. `per_line_tax`
is `None` for a market that does not itemize (NORTH) — an honest absence, not a fabricated zero.

**LineTax{net, tax}** — SOUTH-only decomposition of a line's `final()`, joined to the movement chain at the
single shared number `final() == gross == payable`.

**Market registry** — a minimal closed `name -> Market`, resolved once at the facade. No unknown-verdict
machinery: a market is trusted system selection, not untrusted cart data.

**CheckoutPricer (facade) → PricedCart{ lines:[{sku, line_cost, explanation}], cart_total, cart_explanation,
cart_tax, per_line_tax | None, unapplied:[{code, reason}] }** — resolves the Market once and drives catalog
→ engine → market. `unapplied` is unknown/inapplicable only.

## Where each rule lives (one owner each)

- deltas sum exactly / amount == explanation → **Explanation** (unchanged from stage 2, both markets).
- order-independence, pipeline order, single clamp seam → **PricingEngine**.
- never-negative (cart total only) → the **clamp**.
- rounding *mechanics* → **Money**; rounding *policy* (mode, granularity, point) → **each Market**.
- NORTH tax model + "half-up once at cart, after promotions" → **NorthMarket**.
- SOUTH tax model + "half-even per line, cart tax = Σ line figures" → **SouthMarket**.

## How the invariant holds in both markets, without a per-kind fold

- **NORTH** tax is a *movement* of the payable total, so it is a live Adjustment delta entering through the
  one existing minting path: `final() = frozen subtotal + Σ discount deltas + clamp + VAT`. Explanation just
  sums applied deltas, as always. (C1: taxable 22.50, VAT delta 3.83, final 26.33.)
- **SOUTH** tax is a *decomposition* of the gross, so the market adds no delta; every `final()` is exactly
  the discount composition (= gross), and the invariant holds trivially. Tax lives in the segregated
  `LineTax` stratum with its own invariant (`net + tax = final()` per line; `cart_tax = Σ line tax`),
  joined to the movement chain at the shared `final()`. (C2 gross 10.80, line tax 1.80; C4 cart tax 0.06 =
  Σ per-line, not 0.08.)

The two tax models are unified at the **Market seam** (a higher altitude), never in a shared delta or a
shared field — NORTH's added-on movement and SOUTH's extracted-from decomposition are each modelled as what
they are.

## The stated structural questions

- **Adding a fourth promotion kind** touches the PromotionCatalog's closed kind-set and adds one behaviour
  implementation at the existing LineAdjustment/CartDiscount altitude; the component that computes the total
  (Explanation.final via the engine) does **not** change — a new kind just contributes an Adjustment.
- **Rounding places:** mechanics in one module (Money, two functions); policy in one module (Market, two
  instances). Call sites: NORTH one (cart VAT); SOUTH one per line; both only from `market.impose`.
- **Explanation vs amount:** the amount *is* `Explanation.final()`; there is no second computation to
  diverge.
- **Adding a third market:** one new Market implementation in the closed set (rate + rounding policy + tax
  model). A genuinely new *report* shape would add one tax-report type at that time; today only SOUTH
  itemizes, so no report supertype is built speculatively.
- **Order of adjustments** is stated in one place: the PricingEngine pipeline (L → C → non-stackable →
  clamp → tax), and it is the same order the explanation lists.
- **"The deltas sum exactly"** is owned by Explanation, by construction.
