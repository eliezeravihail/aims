# Survival Count — Checkout Pricing Service (stage-1 → stage-2 → stage-3)

Judge's count of every named component and named seam in the earlier document, classified against the
later one. Counting scope is **components and seams** (the units the brief names). Invariants (INV-*)
are named responsibilities, but each is owned by a component; to avoid double-counting a single change
(e.g. the rounding-mode change is both "Money" and "INV-2"), invariant restatements are used as
**evidence inside the owning component's row**, not as separate counted rows. Renames with the same
responsibility are marked survived and called out.

Classes: **survived** (present, unchanged, same responsibility) · **extended** (same responsibility &
boundary, given more to do at an existing seam) · **reopened** (responsibility or boundary changed) ·
**discarded** (gone). Every non-survival quotes both versions.

---

## Transition 1: stage-1 → stage-2

| Component / seam | Class | Earlier (stage-1) | Later (stage-2) |
|---|---|---|---|
| `Money` | survived | interface: `__init__(amount)`, `__add__`, `__sub__`, `percent`, `min`, `is_zero`, `ZERO` | same interface; §12 "`money.py` and `model.py` are untouched" (docstring lightly reworded only) |
| `Sku` / `PromotionCode` / `CustomerId` (NewTypes) | survived | — | identical |
| `normalize_code` | survived | "The ONE code-identity rule … casefold" | identical text |
| `CartLine` | survived | — | identical |
| `Cart` | survived | — | identical |
| `Scope` (enum) | survived | `LINE`, `CART` | identical |
| `LineDiscount` / `CartDiscount` / `Inapplicable` | survived | — | identical |
| `DiscountResult` (union) | survived | `LineDiscount \| CartDiscount \| Inapplicable` | identical |
| `CartView` (protocol) + engine↔promotion seam | survived | `line_amounts`, `line_for_sku`, `running_total` | same methods (docstring adds "not the ledger") |
| `PercentPromotion` / `AmountPromotion` / `BogoPromotion` | survived | three kinds | "unchanged in their math" (§5) |
| `PromotionDefinitionError` | survived | "definitions file is malformed" | same type/meaning (now also fires on non-boolean `stackable`, within its existing job) |
| public entry `price(cart, catalog)` | survived | `PricingEngine().price(cart, catalog)` | same signature |
| `PricedLine` | **extended** | `sku; quantity; list_line_total; cost` — "`cost` … after all promotions (incl. allocated share)" | adds `explanation: Explanation  # NEW: this line's list -> adjustments -> cost`; `cost … == explanation.final` — existing fields unchanged |
| `CodeOutcome` (enum) | **extended** | `APPLIED`, `UNKNOWN`, `INAPPLICABLE` | adds `SUPERSEDED = auto()   # NEW`; the three prior members unchanged in name/meaning/value (enum-additive rule) |
| `CodeReport` | **extended** | `code; outcome; reason; times_entered` | adds `superseded_by … # NEW` and `forgone_discount … # NEW`; prior fields unchanged |
| `PricedCart` | **extended** | `lines; total; codes` — `total … == sum(line.cost) at 2dp (INV-3)` | adds `explanation: Explanation  # NEW`; `total … == explanation.final; … == sum(line.cost) (INV-3)` — the sum relation preserved |
| `Promotion` (protocol) + extension-axis seam | **extended** | `class Promotion(Protocol): code; scope; def price(view)` | adds `stackable: bool  # NEW`; "the second such attribute (after `scope`) … still never branches on *kind*" |
| `PromotionCatalog` + catalog file seam | **extended** | JSON `{kind, percent/amount/…}`; no stackability | "The **only new field** is an optional `"stackable"` (default `true` …)"; same `load`/`resolve` signatures |
| kind registry | **extended** | "maps … to a parser that builds the matching `Promotion`" | "… builds the matching `Promotion` **and attaches `stackable`**" |
| `PricingEngine` | **extended** | "owns order, dedupe, and the clamp"; "Its one reason to change: the ordering / stacking / dedupe rules" | "order, dedupe, clamp, **non-stackable arbitration, and the ledger**"; "Its reasons to change: the ordering/stacking/dedupe rules, **or the non-stackable selection rule**" — steps 1–3/6 preserved, signature unchanged, arbitration+ledger added |
| `cli.py` | **extended** | "JSON stdin -> Cart -> price() -> PricedCart -> JSON stdout — thin adapter" | "… -> JSON stdout **(now incl. explanations)** — thin adapter" |
| `Allocator` + engine↔allocator seam | **reopened** | `def allocate(self, line_amounts, cart_discount: Money) -> tuple[Money, ...]` — "spreading `cart_discount` … sum(result) == sum(line_amounts) - cart_discount" | `def allocate(self, line_amounts, cart_adjustments: tuple[CartAdjustment, ...]) -> tuple[tuple[Share, ...], ...]` — "**New in stage 2:** the allocator attributes **each cart-stage adjustment** to lines (not just the lump total)". Input type and return type both changed; new types `CartAdjustment`, `Share` introduced. |

New in stage-2 (not survival items): `Adjustment`, `AdjustmentStatus`, `Explanation`, `CartAdjustment`,
`Share`, INV-7, INV-8.

**Transition 1: reopened = 1 (`Allocator`/engine↔allocator seam) · discarded = 0.**

---

## Transition 2: stage-2 → stage-3

| Component / seam | Class | Earlier (stage-2) | Later (stage-3) |
|---|---|---|---|
| `Sku` / `PromotionCode` / `CustomerId`, `normalize_code`, `CartLine`, `Cart` | survived | input vocabulary | "`# model.py — UNCHANGED`" (CartLine `unit_price` comment notes net/gross, type unchanged) |
| `Scope`, `LineDiscount`, `CartDiscount`, `Inapplicable`, `DiscountResult` | survived | promotions vocabulary | `promotions.py … [UNCHANGED]` |
| `Promotion` (protocol, +stackable) + extension-axis seam | survived | `code; scope; stackable; price` | `promotions.py … [UNCHANGED]` |
| `CartView` (protocol) | survived | 3 methods | unchanged |
| `PercentPromotion` / `AmountPromotion` / `BogoPromotion` | survived | three kinds | unchanged |
| `PromotionCatalog`, kind registry, `PromotionDefinitionError` + catalog file seam | survived | `load`/`resolve`, stackable field | `catalog.py … [UNCHANGED]` |
| `Allocator` (+`CartAdjustment`, `Share`) + engine↔allocator seam | survived | `allocate(line_amounts, cart_adjustments) -> Shares` | "`allocation.py` is **unchanged from stage 2**" (§8) |
| `CodeOutcome` (enum) | survived | `APPLIED; UNKNOWN; INAPPLICABLE; SUPERSEDED` | "`# unchanged`" |
| `CodeReport` | survived | 6 fields | "`# unchanged from stage 2`" |
| `PricedLine` | **extended** | `sku; quantity; list_line_total; cost; explanation` | adds `tax: TaxBreakdown \| None  # NEW … SOUTH only; None in NORTH`; prior fields unchanged (`cost` = final listed line amount) |
| `AdjustmentStatus` (enum) | **extended** | `APPLIED`, `SUPERSEDED` | adds `TAX = auto()   # NEW`; the two prior members unchanged (enum-additive rule) |
| `Explanation` | **extended** | "walk from list price to final price. INV-7: list_total + sum(a.delta) == final" | same three fields; "walk from listed price to the **GROSS** … INV-7 … == final(== gross)"; adjustments may now include the tax entry — boundary (fields) unchanged, walk extended through tax |
| `cli.py` | **extended** | JSON in/out incl. explanations | "JSON stdin **(now incl. "market")** … -> JSON stdout `[CHANGED]`"; role (adapter) unchanged, gains market I/O |
| `Money` | **reopened** | `def __init__(self, amount) …  # quantizes on construction`; INV-2 "one rounding mode" (global ROUND_HALF_UP) | `def __init__(self, amount, rounding: str = ROUND_HALF_UP) …`; new `fraction(num, den, rounding)`; §4 "**the reopened invariant** … the rounding *mode* is now a parameter"; §12 "`Money` (rounding-mode parameter …) — INV-2 **(reopened)** `[CHANGED]`". The sole-quantizer boundary/responsibility over rounding mode changed. |
| `Adjustment` | **reopened** | `code: PromotionCode` (field name+type) | `label: PromotionCode \| str   # a promotion code … or "VAT" (tax)`; adds `tax_amount: Money \| None`. Field renamed **and** type widened, now hosts tax steps — boundary changed. |
| `PricedCart` + public entry seam `price(...)` | **reopened** | `total: Money  # == explanation.final; … == sum(line.cost) (INV-3)`; `def price(self, cart, catalog) -> PricedCart` | `total: Money  # == tax.gross — the tax-INCLUSIVE amount …`; adds `market: str`, `tax: TaxBreakdown`; `def price(self, cart, catalog, market) -> PricedCart`. Existing `total` field's contract changed (no longer `sum(line.cost)` — §9: "`sum(line.cost)` equals the cart **net**, not the cart total, in NORTH"); entry signature gained required `market`. |
| `PricingEngine` | **reopened** | `def price(self, cart, catalog) -> PricedCart`; owns order/dedupe/clamp/arbitration/ledger | `def price(self, cart, catalog, market) -> PricedCart`; steps 1–9 "**exactly stage 2**" but a required `market` param added and a tax pass (steps 10–12) appended. Signature/boundary changed. |

(Note: `PricedCart` public-seam signature and `PricingEngine` share the same `price` signature change; they are listed separately because `PricedCart` also reopens its own `total` field contract. In the count below they are folded into **two** distinct underlying reopenings — the `price(...)` signature, and the `total`/INV-3 contract — not three.)

New in stage-3 (not survival items): `Market`/`NorthMarket`/`SouthMarket`, `TaxBreakdown`, engine↔market
seam, `CENT`, `fraction`, INV-9/10-N/10-S/11.

**Transition 2 distinct reopenings:**
1. `Money` — rounding-mode reopened (INV-2).
2. `total` contract / `PricedCart` — `== sum(line.cost)` → `== tax.gross`; INV-3 restated to listed subtotal.
3. `Adjustment` — `code: PromotionCode` → `label: PromotionCode | str`, tax step added.
4. `price(...)` entry / `PricingEngine` — required `market` parameter added.

**Transition 2: reopened = 4 · discarded = 0.**

---

## 2. Reopened + discarded count

- **Transition 1 (stage-1→2): 1** (Allocator interface; 0 discarded)
- **Transition 2 (stage-2→3): 4** (Money, total/INV-3, Adjustment, `price(...)` signature; 0 discarded)
- **Across both transitions: 5.**

(No component or seam was discarded in either transition — every stage-1 name survives into stage-2, and
every stage-2 name into stage-3.)

---

## 3. The single most expensive reopening

**The `total` / INV-3 contract (stage-2 → stage-3).** A headline invariant that held unchanged across
stages 1 **and** 2 — the cart total equals the sum of the line costs — is revoked and made
market-specific.

- Stage-2, `PricedCart.total`: `# == explanation.final; never negative (INV-1); == sum(line.cost) (INV-3)`
  and INV-3 table row: "`sum(line.cost) == total` exactly (invoice lines add up)".
- Stage-3, `PricedCart.total`: `# == tax.gross — the tax-INCLUSIVE amount the customer pays (INV-11)`;
  INV-3 restated to "Per-line **listed** costs sum exactly to the cart's listed **subtotal**"; §9 spells
  out the break: "This is *why* `sum(line.cost)` equals the cart **net**, not the cart total, in NORTH".

It is the most expensive because it does not merely add a field or a parameter — it retracts a guarantee
that every earlier trace, invoice mental-model, and test relied on (`lines add up to the total`), and
replaces it with a per-market rule. The largest *concrete interface* reopening is a runner-up: the
stage-1→2 `Allocator`, whose input type (`cart_discount: Money` → `cart_adjustments: tuple[CartAdjustment,
...]`) **and** return type (`tuple[Money, ...]` → `tuple[tuple[Share, ...], ...]`) both changed and which
introduced two new types.

---

## 4. Self-assessments the text contradicts

**Stage-3 §1 lists `Money` as unchanged; §4 and §12 reopen it.**

- §1: "the entire stage-1/stage-2 machine — **`Money`**, the input model, the three promotion kinds, the
  catalog, the pricing engine …, the allocator, and the explanation ledger — is **unchanged** and
  market-agnostic."
- §4 (heading): "`money.py` — **the reopened invariant**: Money still owns money, but the rounding *mode*
  is now a parameter"; §12: "`money.py  Money (rounding-mode parameter, default half-up), CENT — INV-2
  **(reopened)**  `[CHANGED]``".

`Money`'s constructor gained a `rounding` parameter and a new `fraction(...)` method; it is flatly listed
as "unchanged" in §1 and simultaneously marked `[CHANGED]`/reopened in §4 and §12. The "unchanged"
claim is wrong for `Money`.

**Related overstatement (same §1 sentence, disclosed elsewhere):** the same list calls "the explanation
ledger … unchanged," yet `result.py` is `[CHANGED]` — `Adjustment` is reopened (`code` → `label:
PromotionCode | str`, `+tax_amount`) and `AdjustmentStatus` gains `TAX`. And the stage-1/stage-2 intro
line "Everything … still holds exactly for NORTH" is true only of the **pre-tax** numbers; the reported
cart `total` now grosses up by VAT and the INV-3 equality is redefined — the stage-3 body does disclose
this (§9, C6), so it is an overstated headline rather than a hidden one.

**Not contradicted (checked):** stage-2 "`money.py` and `model.py` are untouched" holds (interfaces
identical). Stage-2 "Everything the stage-1 product did still holds exactly (B6)" holds at the output
level — the `Allocator` interface changed, but the doc acknowledges that in §8/§12 and proves
per-adjustment allocation equals lump allocation for ≤1 cart discount. Stage-3 "`model.py`,
`promotions.py`, `catalog.py`, and `allocation.py` are untouched" holds — all four are byte-for-byte
stage-2.
