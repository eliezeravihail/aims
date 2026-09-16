# Cart Pricing Service — Stage 1 Architecture

Design only. This document is the buildable shape: the components, the rules each owns, the seams
between them, the concrete interfaces in Python, and the reasoning. It contains interface sketches to
make boundaries concrete, not implementations.

Durable design records are filed co-located with the (future) code tree: `goals.md`,
`architecture.md`, `base-dependencies.md`, `dependencies.md`, and `decisions/0001..0005`. This
document is the executive walkthrough of those. All product decisions are now settled by the owner
(final round) — §13 records the resolutions; nothing is left open.

---

## 1. What we are building

A single-process library that, given a **cart** and an operator-maintained **promotions catalog**,
returns the **cost of each line**, the **cost of the whole cart**, and a **report on every code the
customer entered** (applied / unknown / inapplicable-with-reason).

Substrate is fixed by the owner (ADR 0001): **Python 3.11+, standard library only**, `decimal.Decimal`
for money, no UI / network / DB / persistence, single process, single currency. The entry point is a
**library with a thin CLI** (ADR 0004).

---

## 2. The domain vocabulary (what crosses seams)

Only these types + `Decimal` are allowed to cross public boundaries (design-principles §7). No `json`
structure and no concrete promotion class leaks past its module.

```python
# money.py — the one owner of "money is 2dp Decimal, one rounding mode, never float" (INV-2)
class Money:
    """A currency amount, always quantized to 2 places. Immutable. Never negative-checked here —
    non-negativity of the *cart total* is a pricing rule (INV-1), not a money rule."""
    def __init__(self, amount: Decimal | int | str) -> None: ...   # quantizes on construction
    def __add__(self, other: "Money") -> "Money": ...
    def __sub__(self, other: "Money") -> "Money": ...              # may be negative mid-calculation
    def percent(self, pct: Decimal) -> "Money": ...               # pct off? no — returns pct% OF self
    def min(self, other: "Money") -> "Money": ...                 # for clamping a discount to a base
    def is_zero(self) -> bool: ...
    ZERO: "Money"

# model.py — input vocabulary + light structural validation
Sku          = NewType("Sku", str)
PromotionCode = NewType("PromotionCode", str)
CustomerId   = NewType("CustomerId", str)

def normalize_code(code: PromotionCode) -> PromotionCode:
    """The ONE code-identity rule: two entered strings are the same code iff their casefold matches
    (so SAVE10 == save10). Used by both catalog resolution and engine dedupe — one owner of 'same
    code'. The customer's original spelling is preserved for the report; only matching is normalized."""
    return PromotionCode(code.strip().casefold())

@dataclass(frozen=True)
class CartLine:
    sku: Sku
    unit_price: Money
    quantity: int            # validated >= 0 on construction

@dataclass(frozen=True)
class Cart:
    customer_id: CustomerId
    lines: tuple[CartLine, ...]
    codes: tuple[PromotionCode, ...]   # as the customer entered them, original spelling, in order
```

`Sku`/`PromotionCode`/`CustomerId` are `NewType`s — cheap medicine for primitive obsession (§4) that
keeps a SKU from being passed where a code belongs, without ceremony. `normalize_code` is the single
rule for code identity (case-insensitive matching); centralizing it means the catalog and the dedupe
step cannot disagree on whether two spellings are the same code. `Money` is a real type because it
carries real rules (quantization, rounding, arithmetic); a bare `Decimal` would scatter the 2dp rule
across every caller.

---

## 3. The output vocabulary

```python
# result.py
@dataclass(frozen=True)
class PricedLine:
    sku: Sku
    quantity: int
    list_line_total: Money        # unit_price * quantity, before any promotion
    cost: Money                   # what this line costs after all promotions (incl. allocated share)

class CodeOutcome(Enum):
    APPLIED = auto()              # known, produced a discount > 0 on this cart
    UNKNOWN = auto()              # not in the catalog (includes a retired = removed code)
    INAPPLICABLE = auto()         # known, but produced no discount here (with a reason)

@dataclass(frozen=True)
class CodeReport:
    code: PromotionCode           # the customer's original spelling (first occurrence)
    outcome: CodeOutcome
    reason: str | None = None     # human-readable, present for INAPPLICABLE
    times_entered: int = 1        # > 1 means the customer entered this code more than once;
                                  # it is counted ONCE and reported as duplicated (owner)

@dataclass(frozen=True)
class PricedCart:
    lines: tuple[PricedLine, ...]
    total: Money                  # never negative (INV-1); == sum(line.cost) at 2dp (INV-3)
    codes: tuple[CodeReport, ...] # one per DISTINCT code (case-insensitive), first-occurrence order
```

`CodeReport` makes "reported, never silently ignored" (INV-4) a value in the output, not an exception
or a log line the caller can miss. A duplicate code yields a single report with `times_entered > 1`
(owner: count once, tell the customer it was entered more than once).

---

## 4. Promotions — the extension axis (ADR 0002)

A promotion is a small object that owns its own discount math and its own applicability rule. The
engine *tells* it to price against a read-only view and is *told* the result (Tell, Don't Ask §1); it
never reaches into a promotion's parameters to compute the discount itself.

```python
# promotions.py
class Scope(Enum):
    LINE = auto()     # discounts specific lines (BOGO)
    CART = auto()     # discounts the whole order (PCT, AMT)

@dataclass(frozen=True)
class LineDiscount:
    line_index: int
    amount: Money

@dataclass(frozen=True)
class CartDiscount:
    amount: Money     # engine clamps the running total to >= 0 as it folds this in

@dataclass(frozen=True)
class Inapplicable:
    reason: str       # why this known code did nothing here (SKU absent, qty < N, subtotal 0)

# A promotion returns a positive discount, or Inapplicable when it would be zero. Applicability is
# decided by EFFECT, uniformly: discount > 0 -> APPLIED; Inapplicable -> INAPPLICABLE.
DiscountResult = LineDiscount | CartDiscount | Inapplicable

class Promotion(Protocol):
    code: PromotionCode
    scope: Scope
    def price(self, view: "CartView") -> DiscountResult: ...

class CartView(Protocol):
    """Read-only projection the engine passes to a promotion. Exposes exactly what a promotion needs
    to compute its discount — not the mutable pricing state, not other promotions."""
    def line_amounts(self) -> tuple[Money, ...]: ...         # current per-line amounts (post line-stage)
    def line_for_sku(self, sku: Sku) -> tuple[int, CartLine] | None: ...
    def running_total(self) -> Money: ...                    # for cart-stage promotions
```

The three concrete kinds:

```python
class PercentPromotion:      # PCT   scope = CART
    # price(): d = view.running_total().percent(self.pct)   # off the RUNNING (folded) total, so
    #          two 10% codes compound to 19% off, not 20% (INV-6). Inapplicable if d == 0 (empty cart).
class AmountPromotion:       # AMT   scope = CART
    # price(): d = self.amount.min(view.running_total())    # capped so the total can't go < 0
    #          -> CartDiscount(d), or Inapplicable if d == 0 (nothing left to discount)
class BogoPromotion:         # BOGO  scope = LINE
    # price(): find the SKU line; absent -> Inapplicable("no COFFEE in cart")
    #          free_units = qty // self.n           # owner-confirmed: 3 in cart -> 1 free
    #          free_units == 0 -> Inapplicable("need 3 COFFEE for one free; cart has 2")
    #          else -> LineDiscount(index, unit_price * free_units)
```

**Why one interface with a `scope`, not a `kind` switch or two interfaces:** the engine orders by
`scope` and never asks "what kind are you", so a fourth kind (say a "spend X, get Y off" cart promo,
or a "second unit half price" line promo) is a new class here + one catalog registry line, with **no
engine edit** — this is the localized-extension the design is built to absorb. Two segregated
interfaces were considered and rejected for three kinds (ADR 0002).

---

## 5. The catalog — the operator-editable seam (ADR 0001, dependencies.md)

The catalog is the *only* component that knows the definitions file exists or what format it is in. It
resolves a `PromotionCode` to a `Promotion`, or reports it unknown.

```python
# catalog.py
class PromotionCatalog:
    @classmethod
    def load(cls, path: Path) -> "PromotionCatalog": ...   # parse+validate the file (fail-fast on bad data)
    def resolve(self, code: PromotionCode) -> Promotion | None: ...   # matches via normalize_code;
                                                                      # None -> unknown code

class PromotionDefinitionError(Exception):
    """The definitions file is malformed (operator error, surfaced at load, not at pricing)."""
```

Definitions file (JSON, stdlib `json`) — the shape the operator edits by hand:

```json
{
  "SAVE10":  { "kind": "percent", "percent": "10" },
  "TENOFF":  { "kind": "amount",  "amount": "10.00" },
  "COFFEE3": { "kind": "bogo",    "sku": "COFFEE", "n": 3 }
}
```

A **kind registry** inside the catalog maps `"percent"|"amount"|"bogo"` to a parser that builds the
matching `Promotion`. Adding a kind = register one parser. An unknown `kind`, or missing/ill-typed
params, raises `PromotionDefinitionError` at load — a bad *catalog* is the operator's mistake and
should fail loudly; a bad *code on a cart* is a shopper's and is reported, never raised (§7 error
boundary: the two failures have two different, deliberate handlings).

Two owner rulings (final round) land here:
- **Retiring a code = removing its entry** from the file. A removed code that a customer types simply
  resolves to `None` → `UNKNOWN`. There is no `active`/`expired` flag — the catalog holds only live
  codes.
- **Case-insensitive matching.** `resolve` keys off `normalize_code`, so `SAVE10` and `save10` hit the
  same definition. The catalog is built with normalized keys at load; the definitions file may be
  written in any case.

Format is JSON (owner deferred the choice; stdlib `json`), and stays confined here.

---

## 6. The pricing engine — owns order, dedupe, and the clamp (INV-1, INV-4, INV-5, INV-6)

```python
# pricing.py
class PricingEngine:
    def price(self, cart: Cart, catalog: PromotionCatalog) -> PricedCart: ...   # pure: same cart, same result
```

Algorithm (each numbered step is a decision with its own test):

1. **Dedupe by identity, preserve order.** Fold the entered codes on `normalize_code`, keeping the
   first-occurrence spelling and counting occurrences → an ordered list of `(code, times_entered)`.
   A code entered twice is now one entry with `times_entered == 2` (owner: count once, report as
   duplicated).
2. **Resolve** each distinct code via the catalog, in first-occurrence order. `None` → a pending
   `UNKNOWN` report; otherwise a resolved `Promotion` carried with its report slot.
3. **Line stage.** For every resolved `LINE`-scope promotion, call `price(view)`; a `LineDiscount`
   reduces that line's working amount.
4. **Post-line subtotal** = sum of working line amounts.
5. **Cart stage.** For every resolved `CART`-scope promotion, in **first-occurrence order** (a fixed,
   deterministic order — owner: same cart, same answer), call `price(view)`; fold its `CartDiscount`
   onto the running total, **clamping to `≥ 0` after each fold (INV-1)**. Because a PCT reads the
   *running* total, percentages compound (two 10% ⇒ 19% off, INV-6).
6. **Classify each code by effect (INV-4).** discount > 0 → `APPLIED`; `Inapplicable` →
   `INAPPLICABLE(reason)`; unresolved → `UNKNOWN` — each carrying its `times_entered`. Nothing is
   dropped; nothing raises.
7. **Allocate** the total cart-stage discount back over the lines via the `Allocator` (§7) so the lines
   sum exactly to the final total (INV-3).
8. **Assemble** `PricedCart`: the `PricedLine`s (with allocated `cost`), the clamped `total`, and the
   `CodeReport`s in first-occurrence order.

The engine holds *no* per-kind math and *no* money-rounding — it sequences, dedupes, clamps, and
classifies. Its one reason to change: the ordering / stacking / dedupe rules. Determinism is structural:
the function reads only the cart and the catalog, and every order it uses is fixed.

---

## 7. The allocator — owns lines-sum-to-total (INV-3, ADR 0003)

The owner confirmed a line's cost is what the customer pays for that line — the invoice line — and the
line prices add up to the total. So cart-level discounts are allocated back to lines, and one component
owns the rounding:

```python
# allocation.py
class Allocator:
    def allocate(self, line_amounts: tuple[Money, ...], cart_discount: Money) -> tuple[Money, ...]:
        """Return the per-line costs after spreading `cart_discount` across `line_amounts`, such that
        sum(result) == sum(line_amounts) - cart_discount, exactly, at 2dp."""
```

Policy: each line's share = `cart_discount * amount_i / subtotal`, quantized to 2dp; the leftover
residual pennies (discount minus the sum of quantized shares) are handed out one at a time by largest
fractional remainder, ties broken by line order — a deterministic distribution, not a drift. Guards:
`subtotal == 0` → nothing to allocate; a share never exceeds its line (so no line < 0); a discount
clamped to the whole subtotal → every line resolves to `0`.

This concern was kept as its own owner precisely so the "invoice line vs pre-discount line" choice
moved one component and nothing else; the owner chose the invoice line, and the `Allocator` is where
that lives.

---

## 8. The invariants and where each is enforced (single points)

| # | Invariant | Enforced in |
|---|---|---|
| INV-1 | Cart total is never negative | `PricingEngine` (clamp `≥ 0` per cart-stage fold) |
| INV-2 | Every money amount is 2dp, exact to the cent, one rounding mode, never float | `Money` (quantize on construction) |
| INV-3 | `sum(line.cost) == total` exactly (invoice lines add up) | `Allocator` (residual reconciliation) |
| INV-4 | Every entered code reported; pricing never aborts | `PricingEngine` (outcomes are data, not exceptions) |
| INV-5 | Pure/deterministic: same cart → same answer; line stage before cart stage; cart stage in first-occurrence order | `PricingEngine` |
| INV-6 | Percentages compound, not add (two 10% ⇒ 19% off) | `PercentPromotion` (reads the running, folded total) |

The code-identity rule (case-insensitive matching) has its own single owner, `normalize_code` in
`model.py`, used by both the catalog and the engine's dedupe.

A malformed *catalog file* is the one deliberate hard failure (`PromotionDefinitionError` at load) —
it is an operator error, distinct from a shopper's bad code, and has a different handling (§7 of the
principles: number of error types = number of distinct handlings).

---

## 9. The stage-1 cases traced through the design

All under the settled rules: BOGO free = `qty // N`; cart discounts fold on the running subtotal;
percentages compound; ROUND_HALF_UP; lines allocated to sum to the total; case-insensitive codes.

| # | Trace | Total |
|---|---|---|
| A1 | line 12.50×2 = 25.00; no promos | **25.00** (line 25.00) |
| A2 | subtotal 25.00; PCT 10% → 2.50 | **22.50** |
| A3 | subtotal 25.00; AMT 10.00 (≤25) | **15.00** |
| A4 | COFFEE 16.00; BOGO free 4//3=1 → −4.00 → 12.00; no cart promo | **12.00** |
| A5 | COFFEE 16.00 → BOGO −4.00 → 12.00; +WIDGET 12.50 = 24.50; PCT 10% → −2.45 | **22.05** (coffee 10.80, widget 11.25, sum 22.05) |
| A6 | WIDGET 12.50; NOPE unresolved → `CodeReport(UNKNOWN)`; no effect | **12.50** |
| A7 | WIDGET 1.00; AMT 10.00 → clamp to min(10, 1.00)=1.00 → total 0.00 | **0.00** (not negative) |

Owner-supplied facts, traced:

| # | Trace | Result |
|---|---|---|
| F1 | subtotal 25.00; two 10% codes (e.g. `SAVE10`, `TENPCT`): 25.00 → 22.50 → 20.25 | **20.25** = **19% off**, not 20% (compounding) |
| F2 | `["SAVE10","save10"]` on subtotal 25.00: normalized identical → **one** application of 10% | **22.50**; one `CodeReport(APPLIED, times_entered=2)` |

A5 is the load-bearing case: it pins that BOGO (line stage) runs before PCT (cart stage), that PCT
computes on the post-BOGO 24.50 (not the list 28.50), and it exercises allocation (2.45 split 1.20 /
1.25 across the two lines). F1 pins compounding (INV-6); F2 pins case-insensitive dedupe with a count.

---

## 10. Edge and adversarial cases the build must cover (beyond A1–A7)

Named now so the implementation objective's exit criteria can be derived adversarially:

- **Empty cart** (no lines): total 0.00; cart promos produce 0 → `INAPPLICABLE`; a BOGO is `INAPPLICABLE`.
- **Quantity 0 line**: line cost 0.00; BOGO on it yields 0 free → `INAPPLICABLE`.
- **Quantity < 0**: rejected at `CartLine` construction (structural validation) — not a pricing path.
- **BOGO SKU absent**: `INAPPLICABLE("no X in cart")`, other lines still price.
- **BOGO qty < N** (e.g. 2 coffees, `COFFEE3`): 0 free → `INAPPLICABLE("need 3 COFFEE for one free")`
  — the uniform "no effect ⇒ inapplicable, with a reason" rule (settled, no longer open).
- **AMT / PCT that would drive the cart below 0** (A7 generalized to many lines): clamp to 0; allocator
  zeroes every line; `sum == total == 0`.
- **Two cart promos together** (PCT + AMT): folded in first-occurrence order with clamp per fold —
  deterministic; two PCTs compound (F1).
- **Duplicate / mixed-case code** (`["SAVE10","save10"]`): normalized to one code, applied once,
  reported once with `times_entered = 2` (F2).
- **All lines free after BOGO** (subtotal 0) then a cart promo: no division by zero in the allocator;
  the cart promo is `INAPPLICABLE` (0 effect).
- **Rounding-sensitive PCT** (e.g. 10% of 12.33 = 1.233): quantized once in `Money`, ROUND_HALF_UP.
- **Malformed definitions file**: `PromotionDefinitionError` at load, never a half-loaded catalog.
- **Determinism**: pricing the same cart twice yields byte-identical output (pure function).

---

## 11. Module map (the buildable skeleton)

```
money.py        Money                                    — INV-2
model.py        Sku, PromotionCode, CustomerId, normalize_code, CartLine, Cart  — code identity (case)
promotions.py   Scope, Promotion, Percent/Amount/BogoPromotion, DiscountResult, CartView  — extension axis, ADR 0002; INV-6
catalog.py      PromotionCatalog, kind registry, PromotionDefinitionError  — file seam, ADR 0001
pricing.py      PricingEngine.price(cart, catalog) -> PricedCart  — order + dedupe + clamp + classify, INV-1/4/5
allocation.py   Allocator.allocate(...)                  — INV-3, ADR 0003
result.py       PricedLine, CodeOutcome, CodeReport, PricedCart
cli.py          JSON stdin -> Cart -> price() -> PricedCart -> JSON stdout   — thin adapter, ADR 0004
```

Public entry point: `pricing.PricingEngine().price(cart, catalog)` (equivalently a module-level
`price(cart, catalog)`), plus `PromotionCatalog.load(path)`.

---

## 12. What is deliberately left to the implementer (not pre-made here)

Per the method, the internal design is the Worker's: exact class internals, whether `CartView` is a
concrete adapter or a small dataclass, how the kind registry is spelled, the precise residual-tiebreak
data structure, error-message wording, and CLI argument shape. This document fixes the **seams,
owners, invariants, ordering, and the extension axis** — the shape a build must conform to — and no
more.

---

## 13. Resolved product decisions (owner, final round — nothing open)

Every decision below was surfaced to the owner, not guessed; each is isolated so its answer edits one
component, not the architecture. The design absorbed all seven answers plus the two volunteered facts
without a structural change — evidence the seams were drawn in the right places.

| # | Decision | Owner answer | Lives in |
|---|---|---|---|
| 1 | Per-line cost | The invoice line; lines sum to the total | `Allocator` (INV-3) |
| 2 | BOGO N | One free for every N present (`qty // N`); 3 in cart → 1 free | `BogoPromotion` |
| 3 | Cart-code stacking | Any fixed order (we use first-occurrence); percentages **compound** — two 10% ⇒ 19% off | `PricingEngine` (INV-5) + `PercentPromotion` (INV-6) |
| 4 | Duplicate codes | Count once; report it was entered more than once | `PricingEngine` dedupe + `CodeReport.times_entered` |
| 5a | Retiring a code | Remove from file → reported `UNKNOWN` | `PromotionCatalog` |
| 5b | File format | Deferred to us → JSON (stdlib `json`) | `PromotionCatalog` |
| 6 | Rounding | Fixed, exact to the cent, repeatable → ROUND_HALF_UP | `Money` (INV-2) |
| 7 | Case | `SAVE10` == `save10` (case-insensitive) | `normalize_code` (`model.py`) |

Determinism (INV-5) is the through-line of answers 3 and 6: pricing is a pure function of the cart, and
every order and rounding it depends on is fixed — the same cart always prices the same.

With all decisions settled, the next objective (a later stage; **not** this design-only round) is the
`implementation` of this architecture: a vertical slice conforming to it, test-first, covering A1–A7,
F1–F2, and every §10 edge.
