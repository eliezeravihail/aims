---
title: "0008 — Per-market pricing and tax as a post-pass"
date: 2026-09-16
---

## Status
Accepted (stage-3 design, final round). Core rule grounded by cases C1–C6; the three questions are
answered by the owner and folded in (see `design/stage-3.md` §14): (1) keep the deltas adding up, tax
placement our call as long as the customer sees the tax paid — done via the `VAT` ledger entry + the
`net/tax/gross` breakdown; (2) NORTH keeps today's numbers with tax beside them, and **per-line tax is
SOUTH-only** (NORTH `PricedLine.tax is None`); (3) in SOUTH only tax is half-even, discounts stay
half-up. Nothing open.

## Context
The product opens in a second country. A cart is now priced **for a market**, and the two markets' VAT
laws differ structurally, not just by rate:
- **NORTH** (the original behavior): listed prices are tax-**exclusive**; VAT 17% is added to the
  discounted cart net, **half-up, once at the cart level**; lines stay net.
- **SOUTH**: listed prices are tax-**inclusive** (shelf price contains 20% VAT); promotions apply to the
  gross; per-line tax is reported and rounded **half-even, per line**; cart tax = **Σ line tax**, equal
  to the invoice exactly.

The single observation that shapes the design: in *both* markets, promotions apply to the **listed
price as it stands** — the promotion arithmetic is identical, only the meaning of the listed number
(net vs gross) differs, and that meaning is the market's business, not the pipeline's.

## Decision
- **The discount pipeline is tax-agnostic and market-agnostic.** `Money`, the input model, the three
  promotion kinds, the catalog, the pricing engine (order/dedupe/clamp/arbitration), the allocator, and
  the explanation ledger are **unchanged**; they price the listed numbers and yield a final *listed*
  amount per line, a final *listed* total, and the discount ledger.
- **Tax is a post-pass owned by a new `Market` abstraction** (`market.py`). A `Market` owns the rate, the
  inclusive/exclusive meaning of the listed price, the rounding mode and **level** (per line vs per
  cart), and how tax joins the explanation. It is *told* the discount-priced result and returns the
  `net/tax/gross` breakdown for each line and the cart, plus the tax entry that extends each explanation
  to the gross. It holds no discount logic; the engine holds no tax logic (Tell, Don't Ask).
- **`Market` is a genuine polymorphic abstraction, not a flag** (design-principles §2): `NorthMarket`
  and `SouthMarket` differ in structure (additive/exclusive/cart-level-once/half-up vs
  embedded/inclusive/per-line/half-even), and a describable third country makes the seam earn its place.
  The engine reads `Market` the way it reads a promotion's `scope`/`stackable`: it is told the tax
  picture, never inspects a rate to compute tax. Adding a market = one new `Market` class, no engine edit.
- **The market is a pricing context**, passed to `price(cart, catalog, market)`, not stored on the cart;
  the **catalog is shared** across markets (a code means the same discount on the listed price in both).
- **Interface** (`market.py`): `TaxBreakdown(net, tax, gross)`; `Market.line_tax(final_listed) ->
  TaxBreakdown | None` (**None when the market reports no per-line tax — NORTH; a breakdown in SOUTH**),
  `Market.cart_tax(final_listed_total, line_breakdowns) -> TaxBreakdown` (the cart tax is always
  reported), `Market.tax_entry(breakdown) -> Adjustment | None`. `cart_tax` takes both the total and the
  line breakdowns because the cart tax legitimately depends on the total (NORTH) or the summed lines
  (SOUTH); NORTH is passed an empty line-breakdown tuple.
- **Per-line tax is SOUTH-only** (owner): NORTH `PricedLine.tax is None` and its `cost` stays exactly
  today's net line amount; SOUTH lines carry the `net/tax/gross` breakdown their invoices require. The
  **cart-level** `TaxBreakdown` is reported in both markets.
- **Output** gains `PricedCart.market`, a `TaxBreakdown | None` on each `PricedLine` (None in NORTH) and a
  `TaxBreakdown` on the `PricedCart` (`total` becomes the gross), a `TAX` `AdjustmentStatus`, and
  `Adjustment.tax_amount`.

## Consequences
- Change is localized: new `market.py`; a tax tail on `pricing.py`; tax vocabulary in `result.py`; market
  I/O on `cli.py`. `model.py`, `promotions.py`, `catalog.py`, `allocation.py` are untouched.
- New invariants: INV-9 (`net + tax == gross`), INV-10-N / INV-10-S (the two market tax rules), INV-11
  (reported total is gross). INV-3 is restated on **listed** amounts, with tax reconciliation
  market-specific: SOUTH distributes tax to lines (lines sum to gross; taxes sum to cart tax); NORTH
  holds VAT only at the cart (lines sum to net; cart adds VAT to reach the total).

## Alternatives rejected
- **A rate flag / `if market == …` in the engine** — the god-switch the abstraction exists to prevent;
  it cannot express the per-line-vs-cart and inclusive-vs-exclusive structural differences without
  branching the engine on market.
- **Storing the market on the `Cart`** — a cart is priced *for* a market; the same cart may be priced for
  either. The market is context, not cart state.
- **Per-market catalogs** — the cases use `SAVE10` in both markets; a promotion's meaning is
  market-independent. Not built.
- **Distributing NORTH VAT to lines** — contradicts "line amounts stay as they are today; VAT once at the
  cart level" (C1). NORTH lines stay net.
