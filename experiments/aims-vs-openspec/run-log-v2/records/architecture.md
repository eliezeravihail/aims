---
title: "architecture"
date: 2026-09-16
---

## Insights

### Shape of the system
A single-process library with a thin CLI adapter. A cart is priced **for a market**. Data flows one way:

```
definitions file ──▶ Catalog ──▶ [Promotion]        (resolve codes; report unknowns; read stackable)
        Cart ──────────────────▶ PricingEngine ─────────────────────────────▶ PricedCart ──▶ CLI (JSON)
     Market (NORTH|SOUTH) ───────┐  │  DISCOUNT PIPELINE (tax-agnostic, on LISTED prices):
                                 │  ├─ line stage: BOGO adjusts its target lines
                                 │  ├─ arbitrate: among non-stackable, keep the largest (ties by 1st entry)
                                 │  ├─ cart stage: PCT/AMT fold onto the running subtotal (clamp ≥ 0)
                                 │  ├─ ledger: each fold appends an ordered Adjustment (amount = fold of ledger)
                                 │  └─ Allocator: spread EACH cart-stage adjustment back over lines to 2dp
                                 └─ TAX PASS (Market): net/tax/gross per line & cart; append the tax
                                    entry so each explanation walks LISTED → GROSS
```

The **ledger** is the stage-2 backbone of the explanation feature: the engine appends an `Adjustment`
in the same operation that moves the amount, and the reported `total`/`cost` are *read from* the ledger
(`list + sum(deltas)`). Amount and explanation are one computation, so they cannot disagree (INV-7/8).

**The discount pipeline is tax-agnostic (stage 3, ADR 0008).** In both markets, promotions apply to the
**listed price as it stands** (NORTH listed = net, SOUTH listed = gross) — identical arithmetic, only the
meaning of the number differs, and that meaning is the market's. So the whole discount machine above is
unchanged and market-unaware; **tax is a post-pass** owned by a new `Market` abstraction, appended after
discounts. The engine appends the market's tax entry to the ledger, so INV-7/8 now span the tax step too.

### Components and the single responsibility each owns
- **`money.py` — `Money`.** The one place that knows money is 2dp `Decimal`; owns all money arithmetic
  and quantization. **Stage 3 (ADR 0009):** quantization takes a **rounding mode, default half-up** — the
  mechanism is Money's, the mode-choice is the market's. `percent`/`fraction`/construction carry the
  parameter; no other component quantizes. Reason to change: the money representation rule.
- **`model.py` — `Cart`, `CartLine`, `Sku`, `PromotionCode`, `CustomerId`.** The input vocabulary and
  its light structural validation (quantity ≥ 0, price is `Money`). Also owns the **one code-identity
  rule** — the casefold normalization by which `SAVE10` and `save10` are the same code — used by both
  the catalog (resolution) and the engine (dedupe), so there is a single owner of "same code". Reason
  to change: the input shape or what makes two codes equal.
- **`promotions.py` — `Promotion` interface + `PercentPromotion`, `AmountPromotion`, `BogoPromotion`,
  `Scope`.** Each promotion owns *its own* discount math and *its own* applicability rule, and declares
  two classification attributes the engine reads to place it: **`scope`** (LINE|CART) and **`stackable`**
  (stage 2 — `False` ⇒ conflicts with other non-stackable promotions). Reason to change: how a kind
  computes / when it applies. **This is the extension axis** — a new kind is a new class here.
- **`catalog.py` — `PromotionCatalog`.** Owns the definitions-file format and the code→promotion
  resolution, including "unknown code". Reads the optional `stackable` flag (stage 2; default true) and
  attaches it to the promotion. The only component that touches the file. Reason to change: the file
  format or how a kind is spelled on disk (a per-kind parser registry).
- **`pricing.py` — `PricingEngine`.** Owns the *order* of application (line stage before cart stage;
  cart stage folds onto the running total in **first-occurrence entry order** — deterministic, INV-5),
  the **non-stackable arbitration** (stage 2 — among qualifying non-stackable promotions keep the single
  largest, ties by first entry; losers `SUPERSEDED`), the non-negativity clamp (INV-1), the **dedupe of
  repeated codes**, the mapping of each promotion's result to APPLIED / UNKNOWN / INAPPLICABLE /
  SUPERSEDED, and the **ledger** that records each applied adjustment in fold order (INV-7/8). Reason to
  change: the stacking/ordering/dedupe/arbitration rules. Holds no per-kind math and no money-rounding.
- **`market.py` — `Market` interface + `NorthMarket`, `SouthMarket`, `TaxBreakdown` (stage 3).** The
  country's VAT law as an object: owns the rate, whether the listed price is tax-inclusive or exclusive,
  the tax rounding **mode and level** (per line vs per cart), and how tax joins the explanation. Told the
  discount-priced (final **listed**) amounts, it returns the cart's `net/tax/gross` `TaxBreakdown` (both
  markets), a per-line breakdown **where the market requires one** (SOUTH; NORTH returns `None` — per-line
  tax is SOUTH-only), and the tax entry that carries each explanation to the gross. Holds **no** discount
  logic. Reason to change: a market's tax law, or adding a market. **This is the tax extension axis** — a
  new country is a new class here, no engine edit.
- **`allocation.py` — `Allocator`.** Owns the invariant that per-line **listed** costs sum exactly to the
  cart **listed** subtotal after cart-level discounts (INV-3), with deterministic penny reconciliation.
  SOUTH per-line tax rides on the already-allocated line grosses; the allocator is unchanged. Stage 2: allocates
  **each cart-stage adjustment** across lines (not just the lump total), so each line's explanation names
  each cart code with its exact share and the residue lives in a real adjustment, never a rounding line.
  Reason to change: the allocation policy.
- **`result.py` — `PricedCart`, `PricedLine`, `CodeReport`, `Explanation`, `Adjustment`.** The output
  vocabulary. A `CodeReport` carries the outcome (APPLIED / UNKNOWN / INAPPLICABLE / **SUPERSEDED**), a
  reason (INAPPLICABLE), `superseded_by` + `forgone_discount` (SUPERSEDED), and `times_entered`. An
  **`Explanation`** is the ordered ledger `list_total → adjustments → final`; stage 3 its `final` is the
  **gross** and its last entry is the tax step. `PricedCart` carries an `Explanation`, a cart-level
  **`TaxBreakdown` (net/tax/gross, stage 3)**, `market`, and `total` = gross. `PricedLine` carries an
  `Explanation`, its `cost` (the final listed amount — net in NORTH exactly as today, gross in SOUTH), and
  a **`TaxBreakdown | None`** — present in SOUTH, **`None` in NORTH** (per-line tax is SOUTH-only; owner).
  `Adjustment` gains a **`TAX`** status and a `tax_amount` (the tax portion shown even when its delta is
  ZERO for embedded tax). Reason to change: the reported shape.
- **`cli.py`.** Pure translation JSON↔domain around the library; reads the **market** from input, emits
  tax fields; contains no pricing rule.

### Seams (what crosses, and what is hidden)
- **Catalog → Engine:** resolved `Promotion` objects and a list of unknown codes cross; the file
  format never does. The engine cannot tell JSON from TOML.
- **Engine → Promotion (Tell, Don't Ask):** the engine hands each promotion a read-only view of the
  current pricing state and is *told* a `DiscountResult`; it never reads a promotion's parameters to
  decide the discount itself. Per-kind math stays inside the promotion. The engine reads only the
  declarative attributes `scope` and `stackable` to place and arbitrate — never the discount logic.
- **Engine → Allocator (stage 2):** the engine hands the allocator the post-line line amounts and the
  ordered cart-stage adjustments (`code, amount`) and is told each line's `Share` of each adjustment.
  The allocator owns the arithmetic; the engine owns which adjustments exist and in what order.
- **Engine → Market (tax pass, stage 3):** after discounts, the engine hands the market each line's and
  the cart's final **listed** amount (and the line breakdowns, for the cart) and is *told* a
  `TaxBreakdown` and an optional tax `Adjustment`. The market owns all tax math and the rounding
  mode/level; the engine owns the ledger (it appends the entry) and the assembly. The engine never
  inspects a rate — it reads the market as it reads a promotion's `scope`/`stackable`.
- **Library → CLI:** the library is the whole product; the CLI (or a future HTTP handler) is a thin
  adapter over `price(cart, catalog, market) -> PricedCart`.
- **Boundary vocabulary:** only domain types + `Decimal` cross public seams — never `json` structures,
  never a promotion's concrete class outside `promotions.py`/`catalog.py`. `Market` and `TaxBreakdown`
  are domain abstractions and may cross.

## Decisions

### Structural invariants (with their single enforcement point)
- **INV-1 Non-negative cart total.** Enforced once, in `PricingEngine`, by clamping the running cart
  amount to `≥ 0` as each cart-stage discount folds in. No other path writes the total.
- **INV-2 Money is 2dp; Money is the sole quantizer — rounding *mode* is a parameter (stage 3).**
  Enforced in `Money` (quantized on construction, mode default half-up). No other component quantizes;
  no component other than a `Market` chooses a non-default mode (ADR 0009). `float` forbidden near money.
- **INV-3 Lines sum to the *listed* subtotal.** Enforced once, in `Allocator`: per-line **listed** costs
  sum exactly to the cart's listed subtotal at 2dp, by deterministic residual distribution. Stage 3, tax
  reconciliation is market-specific: **SOUTH** distributes tax to lines (gross = listed, so lines sum to
  the gross total *and* line taxes sum to the cart tax); **NORTH** holds VAT only at the cart (lines stay
  net, so `sum(line.cost) == cart.net`, and the cart adds VAT once to reach the gross total). This is the
  honest consequence of "NORTH tax once at cart, SOUTH tax per line".
- **INV-9 net + tax == gross** (stage 3). For every tax breakdown produced (each SOUTH line, both carts),
  exactly at 2dp. Owner: `Market` (breakdown construction; in SOUTH the residue lives in `net = gross −
  tax`, never a rounding line).
- **INV-10-N / INV-10-S market tax rule** (stage 3). NORTH: `cart.tax == half_up(net · 17%)`, once at
  cart; **lines carry no per-line tax** (`PricedLine.tax is None` — SOUTH-only feature). Owner:
  `NorthMarket`. SOUTH: each `line.tax == half_even(line_gross · rate/(1+rate))`, per line; `cart.tax == Σ
  line.tax`, exact. Owner: `SouthMarket`.
- **INV-11 reported total is the gross** (stage 3). `PricedCart.total == cart.tax.gross`, the
  tax-inclusive amount the customer pays. Owner: `PricingEngine`/`Market`.
- **INV-4 Every entered code is reported, pricing never aborts.** Enforced by `PricingEngine`
  treating unknown/inapplicable as data (a `CodeReport`), never as control flow / exception.
- **INV-5 Deterministic, order-defined pricing.** The pricing function is pure — the same cart prices
  identically every time. Line stage strictly before cart stage; within the cart stage, first-occurrence
  entry order (a fixed order, per the owner's "same cart, same answer"). No promotion sees another's
  private state.
- **INV-6 Percentages compound, they do not add.** Each cart-stage discount folds onto the running
  total, so two 10% codes take 19% off, not 20%. Enforced by `PercentPromotion` computing off
  `view.running_total()` (the folded total), never off the original subtotal.
- **INV-7 Deltas sum exactly; amount is a projection of its explanation.** For every line and the cart,
  `list_total + sum(adjustment.delta) == final(== gross)`, exact to the cent, no residue, no synthetic
  rounding line. Enforced structurally: the reported amount is *read from* the ledger the fold builds, and
  the allocator attributes the rounding residue to real cart-adjustment shares. A superseded adjustment
  carries delta ZERO. **Stage 3:** the tax entry is part of the ledger — NORTH `VAT` delta = +tax (net →
  gross), SOUTH `VAT` delta = ZERO (embedded, `tax_amount` shown) — so exactness spans the tax step.
  Owners: `PricingEngine` (ledger) + `Allocator` (residue) + `Market` (tax entry content).
- **INV-8 Ordered provenance.** Adjustments are recorded in the order applied — line stage first, then
  cart stage in first-occurrence order, then the tax entry last (stage 3) — the same order the engine
  folds. Owner: `PricingEngine`.

### Applicability is decided by effect, uniformly — plus supersession (stage 2)
A known code is **APPLIED** when it produces a discount greater than zero on this cart, and
**INAPPLICABLE** (with a reason) when it is known but yields nothing here — whether because its BOGO
SKU is absent, because the SKU is present but quantity < N, or because the cart subtotal is already 0.
Each promotion decides its own applicability and returns either a positive discount or an
`Inapplicable(reason)` (Tell, Don't Ask); the engine only maps that to the report.

Stage 2 adds one outcome ahead of "did it do anything": a known code that *would* discount can still lose
the **non-stackable arbitration** to a rival, in which case it is **SUPERSEDED** (naming the winner), not
INAPPLICABLE. The order is: resolve → each promotion reports would-be effect → the engine arbitrates
among qualifying non-stackable codes → winners and stackables are APPLIED, non-stackable losers are
SUPERSEDED, would-be-nothing codes are INAPPLICABLE, unresolved codes are UNKNOWN. Per-kind effect stays
in the promotion; selection stays in the engine.

### Non-stackable arbitration (ADR 0007)
`stackable` is a declarative attribute of a promotion (from the definitions file, default true), read by
the engine exactly as `scope` is. One flat rule (owner): non-stackable means only "cannot sit next to
another non-stackable" — no named groups; at most one non-stackable promotion applies per cart.
Non-stackable conflicts **only** with other non-stackable; stackable codes always stack. Arbitration is
**kind- and scope-agnostic** (owner: "the bigger one wins, it doesn't matter what kind"): the engine
compares each qualifying non-stackable candidate's discount *amount* on the stackable-only base (a LINE
candidate against the line amounts, a CART candidate against the subtotal), keeps the single largest
(ties by first-occurrence entry order), and marks the rest SUPERSEDED — carrying `superseded_by` and the
`forgone_discount` support reads to the customer. A non-stackable winner may itself be line-scoped, so
arbitration is its own engine step (after stackable line promotions set the base, before the winner is
committed to its stage). This is a selection rule over resolved promotions — the engine's territory — and
adds no per-kind branching (it reads only the discount amount each promotion already computes).

### The two-stage model (why, not just what)
BOGO changes what a *line* costs; PCT/AMT change what the *order* costs, computed on the already
line-discounted subtotal — pinned by case A5 (`24.50 × 0.90 = 22.05`, not `28.50 × 0.90`). So a
promotion declares a `Scope` (`LINE` | `CART`), and the engine applies all `LINE` promotions before
any `CART` promotion. Scope is a genuine domain attribute of a promotion, **not** a `kind` switch: the
engine orders by scope and never branches on kind, so a new kind slots into an existing stage with no
engine edit.

## Discussions

### Change axes the structure is built to absorb
- **A new market / country tax law** → one new `Market` class (rate, inclusive/exclusive, rounding
  mode+level, tax-entry shape); no change to the discount pipeline, engine discount logic, or output
  vocabulary. The tax pass is the seam. (Stage 3, ADR 0008 — the tax extension axis.)
- **A new promotion kind** → one new `Promotion` subclass + one catalog registry entry; declares its
  scope; no change to engine, allocator, or output. (Localized-extension objective for a later stage.)
- **New codes / retired codes** → a data edit to the definitions file; no code change.
- **A new output channel (CLI → HTTP)** → a new adapter over the same `price()` entry point.
- **A new discount *stage*** (e.g. a gift-card/tender-level discount that must apply after cart
  discounts) → a new `Scope` member + its ordering in the engine. Named as the seam; out of scope now.
- **Non-stackable *groups*** (named exclusion sets) → the owner explicitly ruled these out ("one rule:
  two of them can't sit together; nothing more elaborate"). One global set is the product rule, not an
  interim default. Recorded as a *possible* future axis only — a group id + per-group arbitration — not
  something the current design leaves a seam for.

### Deliberately not generalized (no speculative abstraction)
- No rules-engine / condition-DSL for promotions — three concrete kinds with fixed parameters.
- No multi-currency, no per-promotion eligibility windows/thresholds beyond BOGO's SKU match, unless
  the owner adds them (they would land as promotion state + an `Inapplicable` reason, not new seams).
