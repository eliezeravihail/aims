# Cart Pricing Service — Stage 3 Architecture

Design only. This is the complete, self-contained buildable shape of the product **as it now stands**:
the components, the rule each owns, the seams between them, the concrete Python interfaces, and the
reasoning. It contains interface sketches to make boundaries concrete, not implementations. It is not a
diff against stage 2 — it stands on its own. (`design/stage-1.md` and `design/stage-2.md` are left
untouched as prior snapshots.)

Durable records are filed co-located in the code tree: `goals.md`, `architecture.md`,
`base-dependencies.md`, `dependencies.md`, `decisions/0001..0009`. This document is the executive
walkthrough of those.

One capability is new in this stage, on top of the stage-2 pricing-with-explanations service:

**A cart is now priced *for a market*, and each market has its own VAT law.** Two markets exist today:

- **NORTH** (what the product has always done): listed prices are **tax-exclusive**. VAT of **17%** is
  applied to the discounted cart amount **after every promotion**, rounded **half-up**, **once at the
  cart level**. Line amounts stay exactly as they are today.
- **SOUTH** (new): listed unit prices are **tax-inclusive** (the shelf price already contains **20%**
  VAT). Promotions apply to the **gross** (tax-inclusive) amount, as a customer expects. Each line must
  report how much of its final amount is tax; **per-line tax is rounded half-even, per line**; the cart
  tax is the **sum of the line tax figures** and must equal the invoice exactly.

Everything the stage-1 and stage-2 product did still holds exactly for NORTH (§11, case C6), and the
explanation still accounts for every price — now including the tax.

---

## 1. The one load-bearing idea: the discount pipeline is tax-agnostic; the market is a tax pass

The whole design turns on a single observation about the two markets:

> In **both** markets, promotions apply to the **listed price as it stands**. NORTH's listed price is a
> net (tax-exclusive) number; SOUTH's listed price is a gross (tax-inclusive) number. But the *promotion
> arithmetic is identical* — 10% off, 10.00 off, buy-3-get-1 — it just runs on whatever the listed
> number means. The pipeline never needs to know which.

So the entire stage-1/stage-2 machine — `Money`, the input model, the three promotion kinds, the
catalog, the pricing engine (order, dedupe, clamp, non-stackable arbitration), the allocator, and the
explanation **ledger** — is **unchanged and market-agnostic**. It prices the listed numbers and produces
a *final listed amount* per line, a *final listed total*, and the ordered discount explanation, exactly
as before.

**Tax is a post-pass.** A new **`Market`** abstraction takes that discount-priced result and produces the
tax-aware result: the `net / tax / gross` breakdown for each line and the cart, and the tax entry that
extends each explanation to the gross the customer pays. The market owns *everything* about tax — the
rate, whether the listed price is inclusive or exclusive, where and how tax is rounded, and how tax
appears in the explanation — and *nothing* about discounts.

This is why the change is localized (ADR 0008): the pipeline that computes discounts does not move.

```
                       ┌───────────────────  unchanged, market-agnostic  ───────────────────┐
  definitions file ─▶ Catalog ─▶ [Promotion]                                                 │
          Cart ───────────────▶ PricingEngine ─(discounts: line stage, arbitrate, cart stage,│
                                   │             clamp, ledger, allocate)─▶ discount-priced   │
                                   │                                         (final LISTED    │
                                   │                                          amounts + ledger)│
                                   └────────────────────────────────────────────────┬────────┘
         Market (NORTH | SOUTH) ──────────────── tax pass ────────────────────────▶  ▼
                                   (net/tax/gross per line & cart; append the tax entry
                                    to each explanation so it walks LISTED → GROSS)      ─▶ PricedCart ─▶ CLI (JSON)
```

---

## 2. What we will be judged on (the point of the stage)

The stage-2 invariants stand, and the tax feature adds its own. All hold **by construction**.

- **The explanation still accounts for every price — now including tax.** For every line and the cart,
  the explanation is the ordered walk `list_total → (discount adjustments) → (tax entry) → gross`, and
  `list_total + sum(every delta) == gross`, to the cent, no residue, **no synthetic rounding line**
  (INV-7, extended to include the tax entry). Ordered provenance (INV-8) now ends with the tax step.
- **NORTH tax is exact and cart-level-once.** `cart.tax == round_half_up(discounted_net · 17%)`, computed
  a single time on the discounted cart net; no line carries a tax share (INV-10-N). The reported total is
  `net + tax` (C1).
- **SOUTH tax is per-line and the invoice reconciles exactly.** Each `line.tax == round_half_even(
  line_gross · rate/(1+rate))`, rounded **per line**; `cart.tax == sum(line.tax)` **exactly** — never a
  cart-level re-rounding (this is precisely case C4: three 0.15 lines give 0.06, not 0.08) (INV-10-S,
  INV-11).
- **The breakdown is internally exact.** Every tax breakdown produced — each SOUTH line and both carts —
  has `net + tax == gross`, exactly (INV-9). (NORTH lines produce no breakdown: no per-line tax there.)

---

## 3. The input vocabulary (unchanged) + the market as a pricing context

The input model is **unchanged from stage 1/2**. The market is **not** a property of the cart — the same
cart can be priced for either market — so it is a *context passed to pricing*, alongside the catalog. The
promotions catalog is **shared** across markets: `SAVE10` means "10% off the listed price" in both (C1
and C2 both use it); a promotion's meaning is market-independent because it operates on the listed
number.

```python
# model.py — UNCHANGED
Sku = NewType("Sku", str); PromotionCode = NewType("PromotionCode", str); CustomerId = NewType("CustomerId", str)
def normalize_code(code: PromotionCode) -> PromotionCode: ...   # the one code-identity rule (casefold)

@dataclass(frozen=True)
class CartLine:
    sku: Sku
    unit_price: Money           # the LISTED unit price — net in NORTH, gross in SOUTH; the pipeline does not care
    quantity: int               # validated >= 0

@dataclass(frozen=True)
class Cart:
    customer_id: CustomerId
    lines: tuple[CartLine, ...]
    codes: tuple[PromotionCode, ...]

# The public entry point gains a market:
def price(cart: Cart, catalog: PromotionCatalog, market: Market) -> PricedCart: ...
```

Only domain types + `Decimal` cross public seams (design-principles §7). `Market` is a domain
abstraction, not an implementation type, so it may cross.

---

## 4. `money.py` — the reopened invariant: Money still owns money, but the rounding *mode* is now a parameter

Stage 1/2 fixed a single global rounding mode (ROUND_HALF_UP). SOUTH breaks that: its **per-line tax**
is rounded **half-even**, while discounts and NORTH's VAT stay half-up. So the single-mode assumption is
reopened (ADR 0009).

The honest split: **`Money` remains the one and only owner of "money is a 2-decimal `Decimal`, exact to
the cent, never `float`," and of quantization — but quantization takes a rounding mode, defaulting to
half-up.** The *policy* (which mode, and whether per line or per cart) is **not** Money's; it belongs to
the market. Money provides the mechanism; the market chooses the mode.

```python
# money.py
CENT = Decimal("0.01")

class Money:
    """A currency amount, always quantized to 2 places. Immutable. Non-negativity of the *cart total*
    is a pricing rule (INV-1), not a money rule."""
    def __init__(self, amount: Decimal | int | str,
                 rounding: str = ROUND_HALF_UP) -> None: ...   # quantizes on construction, mode-parameterized
    def __add__(self, other: "Money") -> "Money": ...
    def __sub__(self, other: "Money") -> "Money": ...
    def percent(self, pct: Decimal, rounding: str = ROUND_HALF_UP) -> "Money": ...   # pct% OF self
    def fraction(self, num: Decimal, den: Decimal, rounding: str = ROUND_HALF_UP) -> "Money": ...  # (num/den) OF self
    def min(self, other: "Money") -> "Money": ...
    def is_zero(self) -> bool: ...
    ZERO: "Money"
```

Consequences and why this stays safe:
- **Every existing caller is unchanged** because the default is half-up: the discount pipeline, the
  allocator's residual reconciliation, and NORTH's VAT (`net.percent(Decimal(17))`) all use the default,
  so every stage-1/2 number is byte-identical (C6).
- **SOUTH tax uses the explicit mode**: `gross.fraction(rate.numerator, rate.denominator,
  ROUND_HALF_EVEN)` — e.g. at 20%, `tax = gross · (1/6)` half-even (0.025 → 0.02, 0.075 → 0.08). Because
  a value handed to `Money(...)` that is *already* at 2dp quantizes to itself under any mode, there is no
  double-rounding: the market rounds once, at its chosen mode, and the result is a clean `Money`.
- INV-2 restated: **Money owns the representation and the quantization mechanism; the rounding *mode* is
  an argument, half-up by default. No component other than Money quantizes; no component other than a
  `Market` chooses a non-default mode.** `float` remains forbidden near money.

`fraction(num, den, rounding)` is the minimal new operation the tax extraction needs (a rational fraction
of an amount at a stated mode); `percent` is retained and used by NORTH. Whether the Worker expresses
SOUTH's extraction via `fraction` or a small `percent`-with-mode is a mechanism detail; the *owner of the
mode* is the market, and the *owner of quantization* is Money.

---

## 5. `market.py` — the new abstraction (ADR 0008)

A `Market` is the country's VAT law as an object. It owns the rate, the inclusive/exclusive meaning of
the listed price, the rounding mode and *level* (per line vs per cart), and how tax joins the
explanation. It is handed the discount-priced result (final **listed** amounts) and returns the tax
picture. It holds **no** discount logic and the engine holds **no** tax logic.

```python
# market.py
@dataclass(frozen=True)
class TaxBreakdown:
    """How a final amount decomposes. INV-9: net + tax == gross, exactly, at 2dp."""
    net: Money
    tax: Money
    gross: Money

class Market(Protocol):
    name: str                                    # "NORTH" | "SOUTH" — echoed in output, never a switch key

    def line_tax(self, final_listed: Money) -> TaxBreakdown | None:
        """The tax decomposition of ONE final (post-all-discounts) listed line amount, or None when the
        market does not report per-line tax. Per-line tax is a SOUTH requirement only (owner): NORTH
        returns None — its lines stay exactly today's net amount, with no per-line tax figure."""

    def cart_tax(self, final_listed_total: Money,
                 line_breakdowns: tuple[TaxBreakdown, ...]) -> TaxBreakdown:
        """The tax decomposition of the whole cart (always reported, in both markets). A market uses
        whichever inputs its law needs: NORTH computes from the total; SOUTH sums the per-line taxes (so
        the cart equals the invoice). `line_breakdowns` is the tuple of per-line breakdowns that exist —
        empty for NORTH (no per-line tax), all lines for SOUTH."""

    def tax_entry(self, breakdown: TaxBreakdown) -> Adjustment | None:
        """The provenance entry that carries this breakdown's final from the discount ledger's end to
        `gross`. None when the market records no tax step here."""
```

Two concrete implementations:

```python
class NorthMarket:      # tax-EXCLUSIVE, 17%, added once at cart, half-up
    name = "NORTH"
    # line_tax(x):   None                                                  # NORTH reports no per-line tax
    # cart_tax(total, _):  net=total; tax=total.percent(Decimal(17))       # half-up (default), ONCE
    #                      gross=net + tax
    # tax_entry(bd): None if bd.tax.is_zero()                              # a fully-zero cart -> no VAT line
    #                else Adjustment(label="VAT", delta=+bd.tax, status=TAX, tax_amount=bd.tax)  # net -> gross

class SouthMarket:      # tax-INCLUSIVE, 20%, per line, half-even
    name = "SOUTH"
    RATE = Fraction(20, 100)                                              # extraction factor rate/(1+rate) = 1/6
    # line_tax(x):   gross=x; tax = x.fraction(1, 6, ROUND_HALF_EVEN); net = x - tax     # PER LINE, half-even
    # cart_tax(total, line_bds):  gross=total; tax = sum(b.tax for b in line_bds); net = total - tax   # SUM, exact
    # tax_entry(bd): Adjustment(label="VAT", delta=Money.ZERO, status=TAX, tax_amount=bd.tax)  # embedded, delta 0
```

**Why this is a genuine abstraction, not a decorative flag (design-principles §2).** The two markets are
not two values of a rate; they differ in *structure* — additive vs embedded, cart-level-once vs
per-line-summed, half-up vs half-even, and where tax lands in the explanation. A describable third market
(another country: a different rate, tax-exclusive but rounded per line, or a second compounded tax) is
easy to name — the seam earns its place the moment the second country exists. The engine reads `Market`
the way it reads `Scope`/`stackable` on a promotion: it is *told* the tax picture and never inspects a
rate or a mode to compute tax itself (Tell, Don't Ask §1). Adding a market = one new `Market` class, no
engine edit.

**`cart_tax` takes both the total and the line breakdowns** because "the cart's tax" legitimately depends
on different inputs in the two laws (NORTH: a function of the total; SOUTH: the sum of the lines). Each
implementation uses what its law needs; neither input is foreign to the concept "how much tax does this
cart bear" (§3). This is the honest floor for a cart-tax abstraction over these two markets, not a
bundle.

---

## 6. The output vocabulary — the tax breakdown and the tax entry are new

```python
# result.py

class AdjustmentStatus(Enum):
    APPLIED    = auto()   # a discount that moved the price by its delta
    SUPERSEDED = auto()   # a non-stackable code that lost; delta ZERO, carries would_be_delta
    TAX        = auto()   # NEW: a tax step; delta is its effect on the running amount
                          #   +VAT when tax is ADDED on top (NORTH, exclusive); ZERO when tax is
                          #   EMBEDDED in the listed price (SOUTH, inclusive) — tax_amount always shown

@dataclass(frozen=True)
class Adjustment:
    label: PromotionCode | str                   # a promotion code (discount/superseded) or "VAT" (tax)
    delta: Money                                 # exact signed effect on the running amount
    status: AdjustmentStatus
    superseded_by: PromotionCode | None = None   # SUPERSEDED only
    would_be_delta: Money | None = None          # SUPERSEDED only: what it would have saved
    tax_amount: Money | None = None              # TAX only: the tax portion shown, even when delta == ZERO

@dataclass(frozen=True)
class Explanation:
    """The ordered walk from listed price to the GROSS the customer pays. INV-7: list_total +
    sum(a.delta) == final(== gross), exactly, no residue, no rounding line. INV-8: entries in
    application order — the discount adjustments first, then the tax entry (if any)."""
    list_total: Money
    adjustments: tuple[Adjustment, ...]
    final: Money                                 # == gross of this line/cart

@dataclass(frozen=True)
class PricedLine:
    sku: Sku
    quantity: int
    list_line_total: Money        # unit_price * quantity, before any promotion (in the listed meaning)
    cost: Money                   # final listed line amount, all promotions in — the line's own amount
                                  #   (net in NORTH — exactly today's number; gross in SOUTH)
    tax: TaxBreakdown | None      # NEW: net / tax / gross of this line — SOUTH only; None in NORTH
                                  #   (owner: only SOUTH invoices show per-line tax)
    explanation: Explanation

class CodeOutcome(Enum):
    APPLIED = auto(); UNKNOWN = auto(); INAPPLICABLE = auto(); SUPERSEDED = auto()   # unchanged

@dataclass(frozen=True)
class CodeReport:                 # unchanged from stage 2
    code: PromotionCode
    outcome: CodeOutcome
    reason: str | None = None
    superseded_by: PromotionCode | None = None
    forgone_discount: Money | None = None
    times_entered: int = 1

@dataclass(frozen=True)
class PricedCart:
    market: str                   # NEW: which market this was priced for ("NORTH" | "SOUTH")
    lines: tuple[PricedLine, ...]
    total: Money                  # == tax.gross — the tax-INCLUSIVE amount the customer pays (INV-11)
    tax: TaxBreakdown             # NEW: net / tax / gross of the whole cart
    explanation: Explanation      # NEW final entry: the cart's tax step
    codes: tuple[CodeReport, ...]
```

**What appears where.**
- **NORTH line:** `tax = None` — NORTH reports no per-line tax (owner); the line carries just its
  amount (`cost`, net) and its discount explanation, with **no** tax entry. Exactly today's line.
- **NORTH cart:** `tax = (net = discounted subtotal, tax = VAT, gross = net + VAT)` — the cart-level VAT
  and the amount paid sit beside the numbers; the explanation ends with `VAT +tax` carrying net → gross.
- **SOUTH line:** `tax = (gross = final listed, tax = per-line half-even, net = gross − tax)`; the
  explanation ends with a `VAT` entry, delta 0, `tax_amount = line tax` ("of this final, X is tax").
- **SOUTH cart:** `tax = (gross = final listed total, tax = sum(line tax), net = gross − tax)`; same
  embedded `VAT` entry, delta 0, `tax_amount = cart tax`.

`CodeReport` (fate of each entered code) and `Explanation` (the delta ledger) remain two projections of
one engine pass, and are unchanged in that relationship — the tax entry is produced in the same assembly.

---

## 7. The pricing engine — discounts unchanged; a tax pass and a tax-aware ledger tail

```python
# pricing.py
class PricingEngine:
    def price(self, cart: Cart, catalog: PromotionCatalog, market: Market) -> PricedCart: ...  # pure
```

Steps 1–9 are **exactly stage 2** (dedupe, resolve, stackable line stage, non-stackable arbitration,
apply winner, cart stage with clamp + compounding, per-adjustment allocation, classify, and the discount
ledger). They run **without any knowledge of the market**, on the listed amounts, producing per line a
`final_listed` amount + its discount ledger, and for the cart a `final_listed_total` + its discount
ledger — the stage-2 output, byte-for-byte.

Then the **tax pass** (new, steps 10–12), which is where — and the only where — the market is consulted:

10. **Line tax.** For each line, `bd = market.line_tax(final_listed)`; set `line.tax = bd` (a breakdown in
    SOUTH, `None` in NORTH) and `line.cost = final_listed` (= `bd.gross` when `bd` exists). If `bd` is not
    `None` and `market.tax_entry(bd)` is not `None`, append it to that line's explanation and set
    `line.explanation.final = bd.gross`. (NORTH: `bd` is `None` — no line tax, no line entry, final stays
    the net line amount. SOUTH: delta-0 VAT entry, final stays gross.)
11. **Cart tax.** `cbd = market.cart_tax(final_listed_total, tuple(b for b in line_breakdowns if b))`;
    set `cart.tax = cbd` and `cart.total = cbd.gross`. Append `market.tax_entry(cbd)` (if any) to the cart
    explanation; set `cart.explanation.final = cbd.gross`. (NORTH: the line-breakdown tuple is empty; `VAT
    +tax` is net → gross, computed once here. SOUTH: delta-0 VAT entry; `cbd.tax` is the *sum* of the line
    taxes, so the cart equals the invoice, C4.)
12. **Assemble** `PricedCart(market=market.name, …)`.

The engine still holds the ledger (INV-7/INV-8) — it *appends* the market-supplied tax entry and reads
the reported amount from the ledger; the **content** of the tax entry (its delta and tax amount) is the
market's. So "the amount is a projection of its explanation" now spans the tax step too: the reported
`gross` equals `list_total + sum(delta)` including the tax delta, by construction.

The engine's reasons to change are unchanged (ordering / stacking / dedupe / arbitration); tax is not
among them — that is the market's. Determinism (INV-5) extends cleanly: the tax pass is a pure function
of the discount-priced result and the market.

---

## 8. The allocator — unchanged; and how SOUTH per-line tax rides on it

`allocation.py` is **unchanged from stage 2** (it distributes each cart-stage adjustment across lines so
the per-line **listed** costs sum exactly to the listed subtotal — the stage-2 INV-3 on listed amounts).

SOUTH's per-line tax needs no change to the allocator: it is computed **on each line's already-allocated
final listed (gross) amount**. So a SOUTH cart with a cart-level discount across several lines allocates
the gross discount to lines exactly as today, and then each line's tax is `half_even(line_gross · 1/6)`,
and the cart tax is their sum. The allocator owns "lines sum to the listed total"; the market owns "each
line's tax."

---

## 9. Invariants and where each is enforced (single points)

| # | Invariant | Enforced in |
|---|---|---|
| INV-1 | Cart total never negative (gross ≥ net ≥ 0) | `PricingEngine` (clamp on listed folds) |
| INV-2 | Money is 2dp `Decimal`, never float; Money is the sole quantizer — **rounding *mode* is a parameter, default half-up** | `Money` |
| INV-3 | Per-line **listed** costs sum exactly to the cart's listed subtotal | `Allocator` (per-adjustment residual reconciliation) |
| INV-4 | Every entered code reported; pricing never aborts | `PricingEngine` (outcomes are data) |
| INV-5 | Pure/deterministic; line stage before cart stage; tax pass a pure function of the priced result + market | `PricingEngine` |
| INV-6 | Percentages compound, not add | `PercentPromotion` (reads the running listed total) |
| INV-7 | Deltas sum exactly to `gross − list`, no residue, no rounding line; amount is a projection of its ledger — **now including the tax entry** | `PricingEngine` ledger + `Allocator` + market tax entry |
| INV-8 | Entries in application order — discounts, then the tax entry last | `PricingEngine` |
| **INV-9** | **`net + tax == gross`, exactly, for every tax breakdown produced (each SOUTH line, both carts)** | **`Market`** (breakdown construction) |
| **INV-10-N** | **NORTH: `cart.tax == round_half_up(net · 17%)`, computed once at cart; lines carry no per-line tax (`line.tax is None`)** | **`NorthMarket`** |
| **INV-10-S** | **SOUTH: each `line.tax == round_half_even(line_gross · rate/(1+rate))`, per line; `cart.tax == sum(line.tax)` exactly** | **`SouthMarket`** |
| **INV-11** | **The reported cart `total` is the gross (tax-inclusive) amount the customer pays** | **`PricingEngine` / `Market`** |

**INV-3 is deliberately stated on *listed* amounts, and tax reconciliation is market-specific** — the
one honest consequence of "tax once at cart in NORTH, per line in SOUTH":

- **SOUTH** distributes tax to lines (each line carries its own tax), and gross = listed for both line and
  cart, so line grosses sum to the cart gross *and* line taxes sum to the cart tax (INV-10-S). The SOUTH
  invoice is the standard tax-inclusive shape: line grosses (with per-line tax) summing to the gross
  total.
- **NORTH** holds VAT only at the cart; lines stay net (gross = net per line). So line costs sum to the
  cart **net** (the subtotal), and the cart adds VAT once to reach the gross total. The NORTH invoice is
  the standard tax-exclusive shape: net line amounts → net subtotal → + VAT → gross total. This is *why*
  `sum(line.cost)` equals the cart net, not the cart total, in NORTH — and it is exactly what "line
  amounts stay as they are today; VAT once at cart level" requires (C1).

The code-identity rule (`normalize_code`) and the malformed-catalog hard failure
(`PromotionDefinitionError` at load) are unchanged.

---

## 10. The cases traced through the design

Rules in force: the stage-1/2 discount rules (BOGO `qty // N`; cart discounts fold on the running listed
subtotal; percentages compound; discounts round half-up; per-adjustment allocation; case-insensitive
codes; non-stackable arbitration by largest discount, ties by first entry) — **all on the listed
amount** — plus the market tax pass.

### New market cases

**C1 — NORTH, WIDGET 12.50×2, `SAVE10`.** Listed (net) 25.00. `SAVE10` → −2.50 → net 22.50. Tax pass:
`cart.tax = round_half_up(22.50 · 17%) = round_half_up(3.825) = 3.83`; gross = 22.50 + 3.83 = **26.33**.
- Cart explanation: `list 25.00 → SAVE10 −2.50 → 22.50 → VAT +3.83 → 26.33`. Deltas sum −2.50 + 3.83 =
  +1.33 = 26.33 − 25.00. ✓
- Line: cost 22.50 (net, exactly today's number), `tax = None` — NORTH reports no per-line tax; no VAT
  entry on the line. ✓
- `cart.tax = (net 22.50, tax 3.83, gross 26.33)`; total = 26.33. ✓

**C2 — SOUTH, WIDGET 12.00×1, `SAVE10`.** Listed (gross) 12.00. `SAVE10` → −1.20 → gross 10.80. Line tax:
`round_half_even(10.80 · 1/6) = round_half_even(1.80) = 1.80`; net 9.00.
- final gross **10.80**; line tax **1.80**. ✓
- Line explanation: `list 12.00 → SAVE10 −1.20 → 10.80 (VAT incl. 1.80)`. Deltas sum −1.20 = 10.80 −
  12.00 (VAT entry delta 0). ✓
- Cart tax = sum(line tax) = 1.80; total 10.80. ✓

**C3 — SOUTH, SACHET 0.15×1, CLIP 0.45×1, no codes.** No discounts; grosses 0.15 and 0.45.
- SACHET tax = `half_even(0.15 · 1/6) = half_even(0.025) = 0.02` (2 is even). ✓
- CLIP tax = `half_even(0.45 · 1/6) = half_even(0.075) = 0.08` (round 7→8, to even). ✓
- Cart tax = 0.02 + 0.08 = **0.10**; total 0.60. ✓

**C4 — SOUTH, SACHET 0.15×1, CLIP2 0.15×1, PIN 0.15×1, no codes.** Each line tax =
`half_even(0.025) = 0.02`. Cart tax = 0.02 + 0.02 + 0.02 = **0.06** — because tax is summed from the
per-line figures, **never** re-derived at cart level (a cart-level `half_even(0.45 · 1/6) = 0.08` would be
wrong). This case is the whole reason INV-10-S rounds per line and INV-11 sums the lines. ✓

**C5 — SOUTH, COFFEE 4.00×4, `COFFEE3`.** Listed (gross) 16.00. BOGO free = 4 // 3 = 1 → −4.00 → gross
12.00 (the promotion applies to the gross shelf prices, C5's point). Cart tax =
`half_even(12.00 · 1/6) = 2.00`. gross **12.00**, tax **2.00**, net 10.00. ✓

**C6 — NORTH, every earlier acceptance case, unchanged to the cent.** The discount pipeline is
byte-for-byte stage 1/2 (all discount rounding is the half-up default; no market touches it), and NORTH's
tax pass adds VAT once at the cart and leaves lines net. Each earlier cart now additionally reports a
cart `VAT` line and a gross total; every pre-tax number (line costs, subtotal, explanations of the
discount steps) is identical. ✓

### Stage-1/2 discount cases (the pre-tax numbers, still exact — the body of C6)

| # | Trace (listed / net) | Pre-tax total |
|---|---|---|
| A1–A7 | as `design/stage-1.md` §9 | 25.00 / 22.50 / 15.00 / 12.00 / 22.05 / 12.50 / 0.00 |
| F1 | two 10% codes compound → 19% off 25.00 | 20.25 |
| F2 | `["SAVE10","save10"]` deduped | 22.50, one report `times_entered=2` |
| B1–B5 | explanation + non-stackable arbitration (`design/stage-2.md` §10) | 22.50 / 22.05 / 40.00 / 135.00 / 90.00 |

Under NORTH each gains `VAT = half_up(net · 17%)` and a gross total; under SOUTH the same listed numbers
would instead be read as gross and decomposed per line. The discount arithmetic does not move.

---

## 11. Edge and adversarial cases the build must cover (beyond the table)

Named now so the implementation objective's exit criteria can be derived adversarially. The stage-2 edge
list still applies (superseded Δ0 exactness, cross-scope non-stackable, two cart discounts on a multi-line
cart, subtotal-0 allocation, malformed catalog, determinism); the tax pass adds:

- **NORTH rounding boundary** — a discounted net whose VAT is a half-cent (`x · 17%` ending in …5):
  half-up applies once at cart (C1 is one: 3.825 → 3.83). A test must pin the mode and the single
  cart-level application.
- **SOUTH per-line vs cart-level rounding (C4 generalized)** — several small lines whose per-line taxes
  each round one way but whose *summed gross* would round the other: the cart tax must be the **sum of the
  per-line figures**, never a re-rounding of the total. This is the SOUTH invariant's falsifier.
- **SOUTH half-even both directions** — a line landing on `…0.025` (→ down, even) and one on `…0.075`
  (→ up, even): C3 covers both; a test must assert half-even, not half-up (half-up would give 0.03 / 0.08).
- **NORTH lines carry no per-line tax and sum to net; cart adds VAT** — a multi-line NORTH cart: assert
  every `line.tax is None`, `sum(line.cost) == cart.net`, and `cart.total == cart.net + cart.tax`, i.e.
  lines do **not** each carry a VAT share, and no per-line tax figure is reported (the INV-3 / SOUTH-only
  falsifier).
- **SOUTH lines sum to gross and taxes sum to cart tax** — a multi-line SOUTH cart with a cart discount:
  assert every `line.tax is not None`, `sum(line.tax.gross) == cart.tax.gross` and `sum(line.tax.tax) ==
  cart.tax.tax`, both exact.
- **`net + tax == gross` on every breakdown** (INV-9) — each SOUTH line and both carts, including SOUTH
  where `net` is the residual `gross − tax` (so the rounding residue lives in `net`, never a rounding
  line).
- **Everything free, then tax** — a cart discounted to 0 (NORTH: net 0 → VAT 0 → gross 0, no VAT entry;
  SOUTH: gross 0 → tax 0 → net 0): no division issues, explanations end at 0.00 exactly.
- **Explanation exactness with a tax entry present** — for every case, `list_total + sum(delta) == gross`
  including the tax entry (NORTH `VAT` delta > 0; SOUTH `VAT` delta 0), and with superseded Δ0 entries
  also present (B3–B5 under a market).
- **Same cart, two markets** — pricing one cart for NORTH and for SOUTH yields the two correct, different
  answers with no shared mutable state (the market is a context, not stored on the cart).

---

## 12. Module map (the buildable skeleton)

```
money.py        Money (rounding-mode parameter, default half-up), CENT       — INV-2 (reopened)  [CHANGED]
model.py        Sku, PromotionCode, CustomerId, normalize_code, CartLine, Cart                   [UNCHANGED]
promotions.py   Scope, Promotion(+stackable), Percent/Amount/BogoPromotion, DiscountResult, CartView  [UNCHANGED]
catalog.py      PromotionCatalog, kind registry, stackable flag, PromotionDefinitionError        [UNCHANGED]
allocation.py   Allocator.allocate(line_amounts, cart_adjustments) -> per-line Shares            [UNCHANGED]
market.py       Market(Protocol), NorthMarket, SouthMarket, TaxBreakdown     — tax law, ADR 0008/0009  [NEW]
pricing.py      price(cart, catalog, market) -> PricedCart
                — discounts (unchanged) + tax pass + tax-aware ledger tail, INV-1/4/5/7/8/11     [CHANGED]
result.py       PricedLine(+tax: TaxBreakdown|None, SOUTH-only), PricedCart(+market,+tax),
                Explanation(final==gross), Adjustment(+TAX status,+tax_amount), CodeReport       [CHANGED]
cli.py          JSON stdin (now incl. "market") -> Cart -> price(...,market) -> PricedCart -> JSON stdout  [CHANGED]
```

Public entry point: `price(cart, catalog, market) -> PricedCart` (plus `PromotionCatalog.load(path)` and
the two market objects `NorthMarket()` / `SouthMarket()`). The change from stage 2 is concentrated in the
new `market.py`, a tax tail on `pricing.py`, the tax vocabulary in `result.py`, a rounding-mode parameter
on `money.py`, and market I/O on `cli.py`. `model.py`, `promotions.py`, `catalog.py`, and `allocation.py`
are untouched — evidence the discount seams were drawn in the right places.

---

## 13. What is deliberately left to the implementer (not pre-made here)

Per the method, the internal design is the Worker's: whether the discount-priced intermediate is a named
type or engine-internal state; how the market threads its tax entry (a returned `Adjustment` vs an
engine-owned append is fixed, but the object plumbing is open); whether `TaxBreakdown` lives in
`market.py` or `result.py`; how the rate is represented (`Fraction`, a `(num, den)` pair) and whether
SOUTH extraction is `fraction` or a mode-carrying `percent`; the exact typing of an `Adjustment`'s
`label` (reuse of `code` vs a small union); the tax label wording; the JSON shape of a serialized
breakdown and the market field. This document fixes the **seams, owners, invariants, the tax-as-post-pass
decision, the market abstraction, and the reopened rounding-mode ownership** — the shape a build must
conform to — and no more.

---

## 14. Product decisions — all settled (owner, final round)

### Settled and carried forward (stages 1–2, still in force)

Per-line cost = the invoice line; BOGO = one free per N; cart codes stack in first-occurrence order and
percentages compound; duplicates counted once; retiring = removal (→ UNKNOWN); codes case-insensitive;
definitions file JSON; explanation is the source of truth (amount = list + sum(deltas), one fold, no
rounding line); non-stackable arbitration (largest wins, kind- & scope-agnostic, ties by first entry,
loser SUPERSEDED with forgone discount). (ADRs 0001–0007.)

### Settled this stage (grounded by C1–C6 + the request)

- **The discount pipeline is tax-agnostic and runs on listed prices in both markets; tax is a market
  post-pass** (ADR 0008). Promotions apply to the listed number as-is (NORTH net, SOUTH gross), which is
  why C2/C5/C6 need no pipeline change.
- **The market is a pricing context** (`price(cart, catalog, market)`), not a property of the cart; the
  **catalog is shared** across markets.
- **NORTH:** exclusive; VAT 17% on discounted net, half-up, **once at cart**; lines stay net (INV-10-N,
  INV-11). **SOUTH:** inclusive; per-line tax half-even; **cart tax = Σ line tax** (INV-10-S, INV-11).
- **The reported cart total is the gross the customer pays** (INV-11); `net + tax == gross` on every
  breakdown produced (INV-9).
- **Rounding mode is reopened** (ADR 0009): Money stays the sole quantizer but takes a mode (default
  half-up); the tax mode/level is the market's. Discounts and NORTH VAT stay half-up; SOUTH tax is
  half-even.

### The three questions, answered by the owner (final round)

1. **How tax sits in the output — owner: "keep the working adding up; where the tax sits is your call,
   as long as the customer can see what tax they paid."** Resolved: the deltas-sum-exactly property is
   preserved (INV-7 now spans the tax entry), and tax is shown two ways — the ordered `VAT` entry in each
   explanation (NORTH `+tax` net → gross; SOUTH a delta-0 `VAT (incl.)` annotation) **and** the
   `net/tax/gross` breakdown — so the customer can always see the tax paid. Placement was left to us; this
   is the chosen placement.
2. **NORTH invoice shape — owner: "the numbers you had stay the numbers you had; the tax and the amount
   they pay sit beside them. Only SOUTH invoices show per-line tax."** Resolved: NORTH lines are exactly
   today's numbers (net `cost`, no per-line tax — `PricedLine.tax is None`); the cart-level VAT and the
   gross total sit beside them. `sum(line.cost) == cart.net`, and `cart.total == cart.net + cart.tax`.
   **Per-line tax is a SOUTH-only feature** — this refined the earlier draft, which had carried a trivial
   `tax=0` breakdown on NORTH lines; it is now `None`, removing a field NORTH does not report.
3. **SOUTH discount rounding — owner: "tax only."** Resolved: in SOUTH only the tax is half-even;
   discounts keep the existing half-up rounding (ADR 0009).
