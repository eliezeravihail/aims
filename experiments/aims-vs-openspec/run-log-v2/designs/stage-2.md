# Cart Pricing Service — Stage 2 Architecture

Design only. This is the complete, self-contained buildable shape of the product **as it now stands**:
the components, the rule each owns, the seams between them, the concrete Python interfaces, and the
reasoning. It contains interface sketches to make boundaries concrete, not implementations. It is not a
diff against stage 1 — it stands on its own. (`design/stage-1.md` is left untouched as the prior
snapshot.)

Durable records are filed co-located in the code tree: `goals.md`, `architecture.md`,
`base-dependencies.md`, `dependencies.md`, `decisions/0001..0007`. This document is the executive
walkthrough of those.

Two capabilities are new in this stage, on top of the stage-1 pricing service:

1. **Explanations.** Every price — each line, and the cart as a whole — now ships with its
   **explanation**: the ordered list of adjustments that took it from list price to final price, each
   naming what it was (a promotion code, or the list price itself) and the **exact money delta** it
   contributed.
2. **Non-stackable promotions.** A promotion definition may be marked non-stackable. When two
   non-stackable promotions both qualify on one cart, the larger discount is applied and the other is
   not — but the loser still appears, marked not applied, naming the code that superseded it.

Everything the stage-1 product did still holds exactly (§10, case B6).

---

## 1. What we are building

A single-process library that, given a **cart** and an operator-maintained **promotions catalog**,
returns:

- the **cost of each line** and the **cost of the whole cart**;
- for each line and for the cart, an **explanation** — the ordered ledger of adjustments from list
  price to final price;
- a **report on every code the customer entered** (applied / unknown / inapplicable-with-reason /
  superseded-by-another-code).

Substrate is fixed by the owner (ADR 0001): **Python 3.11+, standard library only**, `decimal.Decimal`
for money, no UI / network / DB / persistence, single process, single currency. The entry point is a
**library with a thin CLI** (ADR 0004).

---

## 2. The two things we will be judged on (the point of the feature)

These are the hard invariants of the new capability. The architecture is arranged so both hold **by
construction**, not by a check bolted on afterward — that is the load-bearing design decision (ADR 0006).

- **Deltas sum exactly.** In any explanation, `list_total + sum(delta of every adjustment) == final`,
  to the cent, every time — no residue, and **no synthetic "rounding" adjustment** that exists only to
  make the arithmetic close. (INV-7.)
- **The explanation is what actually happened, in the order it happened.** The amount and its
  explanation can never disagree, because the amount is *produced by folding the explanation* — it is
  not computed on one path and described on another. Adjustments are recorded in application order
  (line stage before cart stage; cart stage in first-occurrence order). (INV-7, INV-8.)

The mechanism that delivers both: a single **pricing accumulator** (a "ledger") that co-produces the
running amount and its ordered adjustments in one operation — see §6 and §8. The reported amount is
*read from the ledger*; there is no second code path that computes an amount without recording why.

---

## 3. The input vocabulary (unchanged from stage 1)

Only these types + `Decimal` cross public boundaries (design-principles §7). No `json` structure and no
concrete promotion class leaks past its module.

```python
# money.py — the one owner of "money is 2dp Decimal, one rounding mode, never float" (INV-2)
class Money:
    """A currency amount, always quantized to 2 places. Immutable. Non-negativity of the *cart total*
    is a pricing rule (INV-1), not a money rule; a Money may be negative mid-calculation."""
    def __init__(self, amount: Decimal | int | str) -> None: ...   # quantizes on construction
    def __add__(self, other: "Money") -> "Money": ...
    def __sub__(self, other: "Money") -> "Money": ...
    def percent(self, pct: Decimal) -> "Money": ...                # returns pct% OF self
    def min(self, other: "Money") -> "Money": ...                  # clamp a discount to a base
    def is_zero(self) -> bool: ...
    ZERO: "Money"

# model.py — input vocabulary + light structural validation + the one code-identity rule
Sku           = NewType("Sku", str)
PromotionCode = NewType("PromotionCode", str)
CustomerId    = NewType("CustomerId", str)

def normalize_code(code: PromotionCode) -> PromotionCode:
    """The ONE code-identity rule: two entered strings are the same code iff their casefold matches
    (SAVE10 == save10). Used by both catalog resolution and engine dedupe. Original spelling is
    preserved for the report; only matching is normalized."""
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

---

## 4. The output vocabulary (explanations are new)

```python
# result.py

# ---- the explanation ledger (NEW) -----------------------------------------------------------------

class AdjustmentStatus(Enum):
    APPLIED    = auto()   # contributed its delta to the price
    SUPERSEDED = auto()   # a non-stackable code that lost to a rival; its delta is ZERO

@dataclass(frozen=True)
class Adjustment:
    """One step in an explanation: a promotion code and the exact money it moved. The list price is not
    an Adjustment — it is the Explanation's anchor (`list_total`)."""
    code: PromotionCode
    delta: Money                                 # exact signed contribution; ZERO iff SUPERSEDED
    status: AdjustmentStatus
    superseded_by: PromotionCode | None = None   # set iff SUPERSEDED — names the winning code
    would_be_delta: Money | None = None          # SUPERSEDED only: what it would have saved (support)

@dataclass(frozen=True)
class Explanation:
    """The ordered walk from list price to final price. INV-7: list_total + sum(a.delta) == final,
    exactly, no residue, no rounding line. INV-8: adjustments are in application order."""
    list_total: Money                            # the anchor — price before any promotion
    adjustments: tuple[Adjustment, ...]          # in application order
    final: Money                                 # == list_total + sum(a.delta for a in adjustments)

# ---- priced results -------------------------------------------------------------------------------

@dataclass(frozen=True)
class PricedLine:
    sku: Sku
    quantity: int
    list_line_total: Money        # unit_price * quantity, before any promotion
    cost: Money                   # == explanation.final  (what this line costs, all promotions in)
    explanation: Explanation      # NEW: this line's list -> adjustments -> cost

class CodeOutcome(Enum):
    APPLIED      = auto()   # known, produced a discount > 0 on this cart
    UNKNOWN      = auto()   # not in the catalog (a retired = removed code lands here)
    INAPPLICABLE = auto()   # known, but produced no discount here (with a reason)
    SUPERSEDED   = auto()   # NEW: known and would have discounted, but a non-stackable rival won

@dataclass(frozen=True)
class CodeReport:
    code: PromotionCode                       # the customer's original spelling (first occurrence)
    outcome: CodeOutcome
    reason: str | None = None                 # human-readable, present for INAPPLICABLE
    superseded_by: PromotionCode | None = None  # NEW: present for SUPERSEDED — the winning code
    forgone_discount: Money | None = None     # NEW: present for SUPERSEDED — what this code would have
                                              # saved (the sentence support reads to the customer)
    times_entered: int = 1                    # > 1 => entered more than once; counted ONCE

@dataclass(frozen=True)
class PricedCart:
    lines: tuple[PricedLine, ...]
    total: Money                  # == explanation.final; never negative (INV-1); == sum(line.cost) (INV-3)
    explanation: Explanation      # NEW: cart-wide list -> adjustments -> total
    codes: tuple[CodeReport, ...] # one per DISTINCT code (case-insensitive), first-occurrence order
```

**Two projections of one computation, never two computations.** `CodeReport` answers *"what happened
to the code I typed?"* (fate of every entered code, including unknown/inapplicable ones that never
touched a price). `Explanation` answers *"why is it this price?"* (the delta ledger). They overlap for
applied and superseded codes and are built from the **same** classification/fold pass in the engine, so
they cannot disagree. They are kept as distinct types because they have genuinely different shapes and
different consumers (support vs. audit) — not duplication in the §10 sense.

**What appears where.** A line's explanation lists only what moved *that* line's price: its list anchor,
its own line-stage discount (BOGO) if it was a target, and its share of each applied cart-stage
discount. A superseded code touched no line, so it does **not** appear in line explanations; it appears
in the **cart** explanation (delta ZERO, `SUPERSEDED`, naming the winner) and in its `CodeReport`.
Unknown and inapplicable codes appear only in `CodeReport` (they never entered the ledger).

---

## 5. Promotions — the extension axis, now carrying a stackability flag (ADR 0002, ADR 0007)

A promotion owns its own discount math and its own applicability rule. The engine *tells* it to price
against a read-only view and is *told* the result (Tell, Don't Ask §1); it never reaches into a
promotion's parameters to compute a discount.

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

DiscountResult = LineDiscount | CartDiscount | Inapplicable

class Promotion(Protocol):
    code: PromotionCode
    scope: Scope
    stackable: bool                       # NEW: False => conflicts with other non-stackable promotions
    def price(self, view: "CartView") -> DiscountResult: ...

class CartView(Protocol):
    """Read-only projection the engine passes to a promotion. Exposes exactly what a promotion needs to
    compute its discount — not the mutable pricing state, not other promotions, not the ledger."""
    def line_amounts(self) -> tuple[Money, ...]: ...          # current per-line amounts (post line-stage)
    def line_for_sku(self, sku: Sku) -> tuple[int, CartLine] | None: ...
    def running_total(self) -> Money: ...                     # for cart-stage promotions
```

The three concrete kinds are unchanged in their math:

```python
class PercentPromotion:      # PCT   scope = CART
    # price(): d = view.running_total().percent(self.pct)   # off the RUNNING (folded) total, so
    #          two 10% codes compound to 19% off, not 20% (INV-6). Inapplicable if d == 0.
class AmountPromotion:       # AMT   scope = CART
    # price(): d = self.amount.min(view.running_total())     # capped so the total can't go < 0
    #          -> CartDiscount(d), or Inapplicable if d == 0.
class BogoPromotion:         # BOGO  scope = LINE
    # price(): find the SKU line; absent -> Inapplicable; free = qty // self.n; 0 -> Inapplicable;
    #          else -> LineDiscount(index, unit_price * free)
```

**`stackable` is a declarative classification attribute, exactly like `scope`.** The engine reads it to
*select*, never to compute — per-kind math stays inside the promotion. It is the second such attribute
(after `scope`); the engine orders by `scope` and arbitrates by `stackable`, and still never branches on
*kind*. A fourth kind remains one new class here + one catalog registry line, with no engine edit.

**Arbitration is kind- and scope-agnostic (owner, final round).** Non-stackable means only *"cannot sit
next to another non-stackable"* — one flat rule, not named groups. When two non-stackable promotions
both qualify, **the bigger discount wins, whatever kind or scope they are** — a non-stackable BOGO (LINE
scope) and a non-stackable PCT (CART scope) compete on the raw discount amount just as two cart codes do.
So the engine compares each candidate's discount amount (from the `DiscountResult` each promotion already
returns) — it needs neither the kind nor the scope to arbitrate, only the amount.

---

## 6. The catalog — the operator-editable seam (ADR 0001, dependencies.md)

The only component that knows the definitions file exists or what format it is in. It resolves a
`PromotionCode` to a `Promotion`, or reports it unknown.

```python
# catalog.py
class PromotionCatalog:
    @classmethod
    def load(cls, path: Path) -> "PromotionCatalog": ...   # parse + validate (fail-fast on bad data)
    def resolve(self, code: PromotionCode) -> Promotion | None: ...   # matches via normalize_code;
                                                                      # None -> unknown code

class PromotionDefinitionError(Exception):
    """The definitions file is malformed (operator error, surfaced at load, not at pricing)."""
```

Definitions file (JSON, stdlib `json`) — the shape the operator edits by hand. The **only new field** is
an optional `"stackable"` (default `true` — omit it and a code stacks as before):

```json
{
  "SAVE10":  { "kind": "percent", "percent": "10", "stackable": false },
  "TENOFF":  { "kind": "amount",  "amount": "10.00", "stackable": false },
  "COFFEE3": { "kind": "bogo",    "sku": "COFFEE", "n": 3 }
}
```

A **kind registry** inside the catalog maps `"percent"|"amount"|"bogo"` to a parser that builds the
matching `Promotion` and attaches `stackable`. Adding a kind = register one parser. An unknown `kind`,
missing/ill-typed params, or a non-boolean `stackable` raises `PromotionDefinitionError` at load — a bad
*catalog* is the operator's mistake and fails loudly; a bad *code on a cart* is a shopper's and is
reported, never raised (two distinct handlings, §7 of the principles). Owner rulings from stage 1 still
hold: retiring a code = removing its entry (→ `UNKNOWN`); matching is case-insensitive.

---

## 7. The pricing engine — order, dedupe, clamp, non-stackable arbitration, and the ledger

```python
# pricing.py
class PricingEngine:
    def price(self, cart: Cart, catalog: PromotionCatalog) -> PricedCart: ...  # pure: same cart, same result
```

Algorithm (each numbered step is a decision with its own test). The dedupe, resolve, stage ordering, and
clamp are stage 1; **the arbitration (steps 4–5) and the ledger threading are new**. Because
non-stackable is now kind- **and scope-agnostic** (owner: "the bigger one wins, whatever kind"),
arbitration happens once, over *all* non-stackable candidates, before the winner is committed to its
stage — so it is a step of its own rather than a filter inside the cart stage:

1. **Dedupe by identity, preserve order.** Fold the entered codes on `normalize_code`, keeping the
   first-occurrence spelling and counting occurrences → an ordered list of `(code, times_entered)`.
2. **Resolve** each distinct code via the catalog, first-occurrence order. `None` → a pending `UNKNOWN`;
   else a resolved `Promotion` carried with its report slot. Partition the resolved promotions into
   **stackable** and **non-stackable**.
3. **Apply stackable line-stage promotions.** For every resolved *stackable* `LINE`-scope promotion, call
   `price(view)`; a `LineDiscount` reduces that line's working amount and appends a line-stage adjustment
   to the ledger. Stackable codes always apply; this is the fixed backdrop the non-stackable ones compete
   on. The resulting line amounts (and their sum, the subtotal) are the **common arbitration base**.
4. **Non-stackable arbitration (NEW) — kind- and scope-agnostic.** Probe each *non-stackable* candidate's
   discount on the common base (a `LINE` candidate against the current line amounts, a `CART` candidate
   against the subtotal — each via its own `price(view)`, so the engine reads only the amount, never the
   kind). Among the **qualifying** ones (discount > 0), keep the **single largest discount**; ties broken
   by **first-occurrence entry order**. The winner joins the apply set at its own scope; every other
   qualifying non-stackable becomes **`SUPERSEDED`**, naming the winner and carrying its **forgone
   discount** (what it would have saved — the sentence support reads). A non-stackable candidate that does
   not qualify (discount 0) is `INAPPLICABLE`, not superseded — it lost to nothing.
5. **Apply the non-stackable winner at its stage.** If it is `LINE`-scope, reduce its target line now (a
   line-stage adjustment) — this further lowers the subtotal that cart-stage promotions will see; if it is
   `CART`-scope, add it to the cart-stage apply set. (At most one non-stackable winner exists per cart.)
6. **Cart stage.** Apply the cart-stage apply set (all qualifying stackable `CART` promotions + the
   non-stackable winner if it is cart-scope) in **first-occurrence order**, folding each `CartDiscount`
   onto the running total, **clamping to `≥ 0` after each fold (INV-1)**, appending a cart-stage
   adjustment per fold. A PCT reads the *running* total, so percentages compound (two 10% ⇒ 19%, INV-6).
7. **Allocate** each cart-stage adjustment back over the lines via the `Allocator` (§8), yielding each
   line its share of each cart adjustment — the material for the line explanations and INV-3.
8. **Classify each entered code (INV-4):** applied-with-positive-delta → `APPLIED`; non-stackable loser →
   `SUPERSEDED(by=winner, forgone=…)`; `Inapplicable` → `INAPPLICABLE(reason)`; unresolved → `UNKNOWN` —
   each carrying `times_entered`. Nothing is dropped; nothing raises.
9. **Assemble** `PricedCart`: each `PricedLine` (with its `Explanation` and `cost = explanation.final`),
   the cart `Explanation` (list anchor → every applied adjustment in order → superseded entries), the
   `total = cart_explanation.final`, and the `CodeReport`s.

The engine holds **no** per-kind math and **no** money-rounding — it sequences, arbitrates, dedupes,
clamps, classifies, and threads the ledger. Its reasons to change: the ordering/stacking/dedupe rules,
or the non-stackable selection rule. Determinism is structural: it reads only the cart and catalog, and
every order and comparison base it uses is fixed (INV-5). The arbitration compares would-be discounts on
the common (stackable-only) base; the winner's *recorded* delta is what it actually removes at its stage
— the two coincide whenever the winner is the only discount at its stage, which is every acceptance case.

**The ledger (the heart of INV-7/INV-8).** As the engine folds a discount it appends the matching
`Adjustment` in the *same operation* that moves the amount — there is no way to change a price without
recording why, and no way to record an adjustment without moving the price. The reported `total`/`cost`
are then *read from* the ledger (`list_total + sum(delta)`), not computed on a parallel path. That is
what makes "the amount and the explanation cannot disagree" a property of the shape rather than a test.
Whether the ledger is a small dedicated accumulator object or the engine's own internal state is the
Worker's mechanism choice; the **invariant** — one write moves amount and provenance together, and the
amount is a projection of the provenance — is fixed here.

---

## 8. The allocator — lines-sum-to-total, now per adjustment (INV-3, ADR 0003, ADR 0006)

A line's cost is the invoice line, and the lines add up to the total (owner, stage 1). Cart-level
discounts are attributed back to lines. **New in stage 2:** the allocator attributes **each cart-stage
adjustment** to lines (not just the lump total), because each line's explanation must name each
cart-stage code with the exact share it took from *that* line.

```python
# allocation.py
@dataclass(frozen=True)
class CartAdjustment:
    code: PromotionCode
    amount: Money                 # the exact money this cart-stage discount removed (a fold delta)

@dataclass(frozen=True)
class Share:
    code: PromotionCode
    amount: Money                 # this line's exact share of that cart adjustment

class Allocator:
    def allocate(
        self,
        line_amounts: tuple[Money, ...],               # post-line-stage per-line amounts
        cart_adjustments: tuple[CartAdjustment, ...],  # each cart-stage discount, application order
    ) -> tuple[tuple[Share, ...], ...]:                # per line: one Share per cart adjustment, in order
        """For every cart adjustment: sum of its Shares across lines == its amount, exactly, at 2dp.
        Consequently each line's cost = list_line - line_stage_discount - sum(its Shares), and the line
        costs sum to the cart total (INV-3). Residual pennies are folded INTO real Shares (never a
        separate 'rounding' entry) — the honest home for the rounding residue is a real adjustment."""
```

**Policy (per adjustment).** For a cart adjustment of amount `D` over post-line line amounts `a_i`
(subtotal `S`): each line's share = `quantize(D * a_i / S)`; the leftover residual pennies (`D` minus the
sum of quantized shares) are handed out one at a time by largest fractional remainder, ties by line
order — deterministic, and folded into the real shares. Guards: `S == 0` → nothing to allocate (all
lines already 0); a line's total share never exceeds its own amount (no line < 0); a discount clamped to
the whole subtotal → every line resolves to 0.

**Why per adjustment, and why it changes no earlier number.** Allocating each adjustment separately is
what lets a line explanation read `WIDGET 12.50 → SAVE10 −1.25 → 11.25` with an exact per-code delta.
On any cart with **at most one** cart-stage discount — which is every stage-1 acceptance case (A1–A7)
and every stage-2 case (B1–B5) — per-adjustment allocation is arithmetically identical to allocating the
lump total, so all earlier line costs and totals are unchanged (case B6). It differs from lump allocation
only when two or more cart discounts land on a multi-line cart, and there it produces the exact
per-code, per-line breakdown the explanation requires — with the residue always living in a real code's
share, satisfying "no rounding line" (INV-7).

---

## 9. Invariants and where each is enforced (single points)

| # | Invariant | Enforced in |
|---|---|---|
| INV-1 | Cart total is never negative | `PricingEngine` (clamp `≥ 0` per cart-stage fold) |
| INV-2 | Every money amount is 2dp, exact to the cent, one rounding mode, never float | `Money` (quantize on construction) |
| INV-3 | `sum(line.cost) == total` exactly (invoice lines add up) | `Allocator` (per-adjustment residual reconciliation) |
| INV-4 | Every entered code reported; pricing never aborts | `PricingEngine` (outcomes are data, not exceptions) |
| INV-5 | Pure/deterministic; line stage before cart stage; cart stage & arbitration on fixed order/base | `PricingEngine` |
| INV-6 | Percentages compound, not add (two 10% ⇒ 19% off) | `PercentPromotion` (reads the running, folded total) |
| **INV-7** | **Deltas sum exactly to `final − list`, no residue, no rounding line; amount == its explanation's fold** | **`PricingEngine` ledger + `Allocator`** (amount is a projection of provenance) |
| **INV-8** | **Adjustments are recorded in the order they were applied** (line stage, then cart first-occurrence order) | **`PricingEngine`** (appends in fold order) |

The code-identity rule (case-insensitive matching) keeps its single owner, `normalize_code` in
`model.py`. A malformed *catalog file* remains the one deliberate hard failure
(`PromotionDefinitionError` at load), distinct from a shopper's bad code.

**How INV-7 is structural, not checked.** The amount is *read from* the ledger; the residual pennies are
attributed to real cart-adjustment shares by the allocator, never to a phantom line. So there is no code
path that could produce an amount the deltas don't sum to, and none that invents a rounding adjustment.
The property holds because of where the numbers come from, not because a validator re-checks them.

---

## 10. The cases traced through the design

Settled rules in force: BOGO free = `qty // N`; cart discounts fold on the running subtotal;
percentages compound; ROUND_HALF_UP; lines allocated (per adjustment) to sum to the total;
case-insensitive codes; non-stackable arbitration by largest discount (kind- and scope-agnostic) on the
stackable-only base, ties by first entry.

### Stage-2 cases (explanations + non-stackable)

**B1 — WIDGET 12.50×2, `SAVE10`.** List 25.00. `SAVE10` (stackable) → 10% of 25.00 = 2.50 → 22.50.
- Cart explanation: `list 25.00 → SAVE10 −2.50 → 22.50`. Deltas sum **−2.50** = 22.50 − 25.00. ✓
- Line (the one line): `25.00 → SAVE10 −2.50 → 22.50`.

**B2 — COFFEE 4.00×4, WIDGET 12.50×1, `["COFFEE3","SAVE10"]`.** List 16.00 + 12.50 = 28.50. Line stage:
`COFFEE3` free = 4//3 = 1 → COFFEE −4.00 → 12.00. Post-line subtotal 24.50. Cart stage: `SAVE10` 10% of
24.50 = 2.45 → **22.05**. Both stackable, both apply.
- Cart explanation (application order): `list 28.50 → COFFEE3 −4.00 → SAVE10 −2.45 → 22.05`. Deltas sum
  **−6.45** = 22.05 − 28.50. ✓
- COFFEE line: `16.00 → COFFEE3 −4.00 → SAVE10 −1.20 → 10.80`.
- WIDGET line: `12.50 → SAVE10 −1.25 → 11.25`. (Allocation of 2.45: 12.00/24.50·2.45 = 1.20,
  12.50/24.50·2.45 = 1.25.) Line costs sum 22.05 = total. ✓

**B3 — WIDGET 50.00×1, `["SAVE10","TENOFF"]`, both non-stackable.** At the post-line subtotal 50.00:
`SAVE10` → 5.00, `TENOFF` → 10.00. Arbitration: **TENOFF wins** (10.00 > 5.00). Total 50.00 − 10.00 =
**40.00**.
- Cart explanation: `list 50.00 → TENOFF −10.00 (applied) → SAVE10 (superseded by TENOFF, Δ0) → 40.00`.
  Applied deltas sum **−10.00**; the superseded entry is Δ0, so the sum is exact. ✓
- `CodeReport`: TENOFF `APPLIED`; SAVE10 `SUPERSEDED(by=TENOFF, forgone_discount=5.00)` — support reads
  "SAVE10 was valid but TENOFF saved you more (10.00 vs 5.00)."

**B4 — WIDGET 150.00×1, `["SAVE10","TENOFF"]`, both non-stackable.** At 150.00: `SAVE10` → 15.00,
`TENOFF` → 10.00. **SAVE10 wins** (15.00 > 10.00). Total **135.00**. TENOFF `SUPERSEDED(by=SAVE10)`. ✓

**B5 — WIDGET 100.00×1, `["SAVE10","TENOFF"]`, both non-stackable.** At 100.00: `SAVE10` → 10.00,
`TENOFF` → 10.00 — a **tie**. First entered (`SAVE10`) wins. Total **90.00**. TENOFF
`SUPERSEDED(by=SAVE10)`. ✓

**B6 — every earlier acceptance case, unchanged.** No stage-1 case uses a non-stackable code, and each
has at most one cart-stage discount, so arbitration is a no-op and per-adjustment allocation equals lump
allocation. Totals and line costs are byte-for-byte the stage-1 values; explanations are additive
output. ✓ (Stage-1 traces reproduced below.)

### Stage-1 cases (still exact — case B6)

| # | Trace | Total |
|---|---|---|
| A1 | line 12.50×2 = 25.00; no promos | **25.00** |
| A2 | subtotal 25.00; PCT 10% → 2.50 | **22.50** |
| A3 | subtotal 25.00; AMT 10.00 (≤25) | **15.00** |
| A4 | COFFEE 16.00; BOGO free 4//3=1 → −4.00 | **12.00** |
| A5 | COFFEE 16.00 → BOGO −4.00 → 12.00; +WIDGET 12.50 = 24.50; PCT 10% → −2.45 | **22.05** (coffee 10.80, widget 11.25) |
| A6 | WIDGET 12.50; NOPE unresolved → `UNKNOWN` | **12.50** |
| A7 | WIDGET 1.00; AMT 10.00 → clamp min(10, 1.00) → 0.00 | **0.00** |
| F1 | subtotal 25.00; two 10% codes: 25.00 → 22.50 → 20.25 | **20.25** (19% off, compounding) |
| F2 | `["SAVE10","save10"]` on 25.00: one application | **22.50**; one `CodeReport(APPLIED, times_entered=2)` |

A5 remains the load-bearing multi-line/allocation case; F1 pins compounding; F2 pins case-insensitive
dedupe. Each now also carries an explanation, produced by the same fold that produces its total.

---

## 11. Edge and adversarial cases the build must cover (beyond the table)

Named now so the implementation objective's exit criteria can be derived adversarially:

- **Empty cart / quantity-0 line / quantity < 0** — as stage 1: total 0.00; promos `INAPPLICABLE`;
  qty < 0 rejected at `CartLine` construction. Explanations still exist: `list 0.00 → 0.00`, no
  adjustments, sum trivially exact.
- **Superseded code carries Δ0 into the sum.** The exactness invariant (INV-7) holds *with* superseded
  entries present, because their delta is exactly ZERO — a test must assert this, not just the
  all-applied case.
- **A single qualifying non-stackable code, no rival** — applies normally; nobody is superseded.
- **A non-stackable code that does not qualify** (e.g. non-stackable BOGO whose SKU is absent) →
  `INAPPLICABLE`, and it does **not** supersede or get superseded — it lost to nothing.
- **Three+ qualifying non-stackable codes** → exactly one winner (largest; tie by first entry); every
  other is `SUPERSEDED(by=winner)`.
- **Non-stackable winner alongside stackable cart codes** → the winner and the stackables all apply,
  compounding in first-occurrence order; the arbitration compares would-be discounts on the
  stackable-only base (§5).
- **Cross-scope non-stackable (owner-confirmed, no acceptance case)** → a non-stackable BOGO (LINE) vs a
  non-stackable PCT/AMT (CART): compare their would-be discount *amounts* on the common base, biggest
  wins, ties by first entry — the engine reads only the amount, not the kind/scope. Worked example:
  COFFEE 4.00×3 + WIDGET 20.00×1, codes `["COFFEE3","TENOFF"]` both non-stackable. COFFEE3 would save
  4.00 (one free); TENOFF would save 10.00. **TENOFF wins**; COFFEE3 `SUPERSEDED(by=TENOFF,
  forgone=4.00)`. This path has no acceptance case, so it must carry its own test.
- **Two cart discounts on a multi-line cart** → per-adjustment allocation; every line's explanation
  names each code with its exact share; residue lives in a real share; line costs sum to total (the case
  that exercises the stage-2 allocator beyond stage-1 behavior).
- **All lines free after BOGO (subtotal 0) then a cart promo** → no division by zero in the allocator;
  the cart promo is `INAPPLICABLE`; explanations end at 0.00 exactly.
- **Rounding-sensitive PCT** (10% of 12.33 = 1.233) → quantized once in `Money`, ROUND_HALF_UP; the
  quantized delta is what the ledger records, so the explanation and amount share the rounded value.
- **Malformed definitions file / non-boolean `stackable`** → `PromotionDefinitionError` at load.
- **Determinism** → same cart twice yields byte-identical output, explanations included (pure function).

---

## 12. Module map (the buildable skeleton)

```
money.py        Money                                    — INV-2
model.py        Sku, PromotionCode, CustomerId, normalize_code, CartLine, Cart   — code identity
promotions.py   Scope, Promotion(+stackable), Percent/Amount/BogoPromotion,
                DiscountResult, CartView                 — extension axis, ADR 0002/0007; INV-6
catalog.py      PromotionCatalog, kind registry, stackable flag, PromotionDefinitionError  — file seam
pricing.py      PricingEngine.price(cart, catalog) -> PricedCart
                — order + dedupe + non-stackable arbitration + clamp + classify + ledger
                — INV-1/4/5/7/8, ADR 0006/0007
allocation.py   Allocator.allocate(line_amounts, cart_adjustments) -> per-line Shares  — INV-3, ADR 0003/0006
result.py       PricedLine, PricedCart, CodeOutcome(+SUPERSEDED), CodeReport(+superseded_by),
                Adjustment, AdjustmentStatus, Explanation
cli.py          JSON stdin -> Cart -> price() -> PricedCart -> JSON stdout (now incl. explanations) — thin adapter
```

Public entry point: `pricing.PricingEngine().price(cart, catalog)` (equivalently a module-level
`price(cart, catalog)`), plus `PromotionCatalog.load(path)`. The change from stage 1 is concentrated in
`pricing.py` (arbitration + ledger), `allocation.py` (per-adjustment), and `result.py` (explanation
vocabulary); `money.py` and `model.py` are untouched; `catalog.py` and `cli.py` gain thin, additive
edits.

---

## 13. What is deliberately left to the implementer (not pre-made here)

Per the method, the internal design is the Worker's: whether the ledger is a dedicated accumulator class
or engine-internal state; whether `CartView` is a concrete adapter or a small dataclass; how the kind
registry and the arbitration probe are spelled; the residual-tiebreak data structure; error-message and
`reason` wording; the JSON shape of a serialized explanation; the CLI argument shape. This document fixes
the **seams, owners, invariants, ordering, the non-stackable selection rule, and the extension axis** —
the shape a build must conform to — and no more.

---

## 14. Product decisions — settled, and open

### Settled (stage 1, still in force)

Per-line cost = the invoice line (lines sum to total); BOGO = one free per N present; cart codes stack
in a fixed first-occurrence order and percentages compound (two 10% ⇒ 19% off); duplicate codes counted
once and reported as duplicated; retiring a code = removing it (→ `UNKNOWN`); ROUND_HALF_UP; codes
case-insensitive; definitions file is JSON. (ADRs 0001–0005.)

### Settled this stage (grounded by the B-cases + owner answers, final round; ADR 0006, 0007)

- **The explanation is the source of truth for the amount.** Amount = list + sum(deltas), produced by
  one fold; no separate description path (INV-7/INV-8). No synthetic rounding line — residue lives in
  real cart-adjustment shares.
- **Non-stackable conflicts only with other non-stackable.** Stackable codes always stack.
- **Largest discount wins; ties broken by first-occurrence entry order; the loser is `SUPERSEDED`,
  naming the winner** (B3/B4/B5).
- **Grouping (owner):** *one flat rule* — non-stackable simply "cannot sit next to another
  non-stackable." No named groups, nothing more elaborate. At most one non-stackable promotion applies
  per cart.
- **Kind/scope (owner):** arbitration is **kind- and scope-agnostic** — "if two of them can't be
  combined, the bigger one wins; it doesn't matter what kind they are." A non-stackable BOGO (LINE) and a
  non-stackable PCT/AMT (CART) compete by discount amount on the common (stackable-only) base.
- **Superseded metadata (owner):** the superseded entry **shows what the beaten code would have saved**
  (`CodeReport.forgone_discount`, and `Adjustment.would_be_delta`) — "that's the sentence support reads
  to the customer" — while contributing ZERO to the price.

All three questions raised in the prior round are now answered by the owner (final round) and folded in
above; nothing is left open.

Minor design calls I made (state, not questions, but easily changed): the list price is the
explanation's **anchor** (`list_total`), renderable as a leading "list price" row, rather than a
delta-bearing adjustment; superseded codes appear in the **cart** explanation only, not in per-line
explanations (they moved no line).
