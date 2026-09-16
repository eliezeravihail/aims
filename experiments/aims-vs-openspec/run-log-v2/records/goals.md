---
title: "goals"
date: 2026-09-16
---

## Insights

### What the product is
A cart-pricing service. Given a cart — a customer id, a list of lines (each a SKU, a list unit
price, a quantity), and a list of promotion-code strings the customer entered — priced **for a market**,
it returns the cost of **each line** and the cost of the **whole cart** (tax-inclusive), the **tax**
borne by each line and the cart, reports the fate of each code entered, and — for each line and for the
cart — an **explanation**: the ordered list of adjustments that took it from list price to the final
price, now including tax (see `design/stage-3.md`).

### Markets and tax (stage 3)
A cart is priced for one of two **markets**, each with its own VAT law; the market is a pricing context
(`price(cart, catalog, market)`), not a property of the cart, and the promotions catalog is shared.
- **NORTH** (the original behavior, preserved exactly): listed prices are tax-**exclusive**; VAT 17% is
  added to the discounted cart net, rounded **half-up, once at the cart level**; lines stay net.
- **SOUTH**: listed prices are tax-**inclusive** (shelf price contains 20% VAT); promotions apply to the
  gross; each line reports its tax, rounded **half-even, per line**; cart tax = **Σ line tax**, equal to
  the invoice exactly.
The discount pipeline is **tax-agnostic** — it prices the listed number as-is in both markets — and tax
is a post-pass owned by a `Market` abstraction (see `architecture.md`, ADR 0008/0009).

### Why the explanation exists (stage 2)
Finance, support, and auditors must be able to answer "why is this 22.05?". The explanation is the
answer: an ordered, exact provenance from list price to final price. Two things are the whole point and
are checked hard — the deltas **sum exactly** to (final − list), to the cent, with no residue and no
synthetic "rounding" line; and the explanation is **what actually happened, in the order it happened**,
so the amount and its explanation can never disagree.

### Core use scenario (start to useful result)
A shopper's cart arrives as `COFFEE 4.00 x4, WIDGET 12.50 x1` with codes `["COFFEE3","SAVE10"]`.
The service resolves each code against an operator-maintained definitions file, applies the
buy-3-get-1-free on COFFEE (one coffee free), then 10% off the resulting cart, and returns the
per-line costs, a cart total of `22.05`, and a per-code report (both codes applied). An unknown code
in that same cart would be reported as unknown and would not stop the rest from pricing.

### Promotions in scope (three kinds; codes are added/retired constantly, kinds are stable)
- **PCT** — a percentage off the whole cart (`SAVE10` = 10% off).
- **AMT** — a fixed amount off the whole cart (`TENOFF` = 10.00 off).
- **BOGO** — on one named SKU, one unit free for every N of that SKU in the cart
  (`COFFEE3` = one COFFEE free for every 3 present: `free = qty // N`; owner confirmed).

The set of live codes and their parameters comes from a **data file the operator edits without an
engineer**. Adding/retiring a code is a data edit, never a code change. Adding a new *kind* of
promotion is a code change, and is expected to be localized (one new promotion type).

### Non-stackable promotions (stage 2, owner-confirmed final round)
A promotion definition may be marked **non-stackable** (a data-file flag; default is stackable). One flat
rule: non-stackable means only "cannot sit next to another non-stackable" — no named groups, nothing more
elaborate. When two or more non-stackable promotions qualify on one cart, the **one that gives the
customer the larger discount is applied and the others are not**; the comparison is **kind- and
scope-agnostic** ("the bigger one wins, it doesn't matter what kind") — a non-stackable BOGO and a
non-stackable percentage compete purely on the discount amount; a tie is broken in favour of the one
**entered first**. A superseded code is still valid — it must appear, marked not applied, naming the code
that superseded it **and what it would have saved** (the sentence support reads to the customer).
Stackable codes always stack.

## Decisions
- The output is per-line cost + whole-cart cost + a per-code report + a per-line and cart-wide
  **explanation**. A code the customer entered is never silently ignored: it is reported as applied,
  unknown, inapplicable-with-reason, or superseded-by-another-code.
- **Product-rule invariants** (must always hold, see `architecture.md` for where each is enforced):
  1. A cart total is never negative.
  2. Every money amount is shown to 2 decimal places in a single currency, exact to the cent.
  3. An unknown or inapplicable code is reported as such and does not abort pricing of the rest of
     the cart.
  4. **A line's cost is what the customer pays for that line — the invoice line — and the line costs
     add up to the cart total** (owner). Cart-level discounts are allocated back to lines so that the
     per-line **listed** costs sum exactly to the listed subtotal. Stage 3: this reconciliation is on the
     *listed* amount; how tax reconciles differs by market — SOUTH lines are gross and sum to the gross
     total (line taxes sum to the cart tax); NORTH lines stay net and sum to the cart *net*, with VAT
     added once at the cart to reach the total (INV-3, INV-10-N/S).
  5. **Pricing is deterministic**: the same cart priced twice gives the same answer (owner). The
     pricing function is pure and every ordering it depends on is fixed, not incidental.
  6. **Every price ships with an exact, ordered explanation** (stage 2). The deltas sum exactly to
     (final − list) with no residue and no synthetic rounding line, and the amount is *produced by
     folding the explanation*, so amount and explanation cannot disagree (INV-7/INV-8). Stage 3: the
     explanation walks to the **gross** price and its final entry is the tax step, so the explanation
     accounts for the tax too.
  7. **Tax is market-specific and exact** (stage 3). `net + tax == gross` on every tax breakdown produced
     (INV-9); NORTH VAT is computed once at cart, half-up, lines net with **no per-line tax figure**
     (INV-10-N); SOUTH tax is per-line half-even and the cart tax is the sum of the line taxes (INV-10-S);
     **per-line tax appears on SOUTH invoices only** (owner); the reported total is the gross (INV-11).
- **Non-stackable arbitration** (stage 2): among qualifying non-stackable promotions, exactly one — the
  largest discount, ties by first entry — applies; the rest are reported `SUPERSEDED`, naming the
  winner. Non-stackable conflicts only with non-stackable; stackable always stacks.

## Discussions
### Non-goals (this product deliberately does not do)
- No inventory, shipping, currency conversion, or payment/tender step. (Tax entered in stage 3, as a
  per-market VAT post-pass — see ADR 0008; still no multi-currency.)
- No persistence, no network service, no UI, no user accounts — a single-process compute of a price.
- No promotion kinds beyond PCT / AMT / BOGO in this stage (the design leaves a localized seam for a
  fourth kind, but does not build one).
- Not a promotion *authoring* or admin tool — the operator edits the definitions file by hand.

### Resolved product decisions (owner, final round — nothing open)
Each was surfaced, not guessed; each is isolated so it edits one owner, not the architecture:
1. **Per-line cost = the invoice line; lines sum to the total.** Cart discounts are allocated
   (INV-4). Owner: `Allocator`.
2. **BOGO = one free for every N present** (`free = qty // N`): three in the cart → one free.
   Owner: `BogoPromotion`.
3. **Cart-level codes stack deterministically; percentages compound.** Any fixed order is fine as
   long as the same cart always gives the same answer; two 10% codes take **19% off, not 20%** —
   each cart-stage discount folds onto the running total (percentages compound, they do not add).
   Owner: `PricingEngine` (applies cart-stage codes in first-occurrence order — deterministic).
4. **A duplicate code counts once**, and the per-code report says it was entered more than once
   (carries the entry count). Owner: `PricingEngine` (resolve/dedupe) + `CodeReport`.
5. **Retiring a code = removing its entry from the file**; a typed code that is gone is reported
   **unknown**. No inactive/expired state. Owner: `PromotionCatalog`.
6. **Money rounding is a fixed mode** (ROUND_HALF_UP): exact-to-the-cent and repeatable. Owner:
   `Money`.
7. **Codes are case-insensitive** (`SAVE10` == `save10`): one code-identity normalization rule
   (casefold), used by both resolution and dedupe. Owner: `PromotionCode` normalization.
8. **Definitions-file format: JSON** (owner deferred the choice; stdlib `json`). Owner:
   `PromotionCatalog`.

### Stage-2 decisions (settled by the B-cases + owner answers, final round — nothing open)
Settled: explanation is the source of truth for the amount (ADR 0006); non-stackable conflicts only with
non-stackable, largest wins, ties by first entry, loser `SUPERSEDED` (ADR 0007). The three questions
raised in the prior round were answered by the owner and folded in: (1) **one flat rule, no named
groups** — at most one non-stackable applies; (2) arbitration is **kind- and scope-agnostic** — a
non-stackable BOGO can compete with a non-stackable cart code, bigger amount wins; (3) the superseded
entry **shows the forgone discount** (what it would have saved), contributing zero to the price.
