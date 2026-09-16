---
title: "0006 — Explanation as the source of truth (the pricing ledger)"
date: 2026-09-16
---

## Status
Accepted (stage-2 design).

## Context
Finance, support, and auditors must be able to answer "why is this 22.05?". Every price — each line and
the cart — must ship with its **explanation**: the ordered list of adjustments from list price to final
price, each naming what it was (a promotion code, or the list price itself) and the exact money delta it
contributed. Two properties are the whole point and will be checked hard:
1. the deltas **sum exactly** to (final − list), to the cent, with no residue and **no synthetic
   "rounding" line** that exists only to make the arithmetic close;
2. the explanation is **what actually happened, in the order it happened** — if the amount and the
   explanation ever disagree, the feature is worthless.

The failure mode to design out: computing the amount on one code path and *describing* it on another.
Any such split can drift, and property 2 is then unenforceable.

## Decision
- **The explanation is the source of truth; the amount is a projection of it.** The engine accumulates a
  **ledger**: as it folds each discount it appends the matching `Adjustment` in the *same operation* that
  moves the running amount. The reported `PricedLine.cost` / `PricedCart.total` are then *read from* the
  ledger as `list_total + sum(delta)`. There is no path that changes a price without recording why, and
  none that records an adjustment without moving the price. Amount/explanation agreement (INV-7/INV-8) is
  therefore a property of the shape, not a validator run afterward.
- **No rounding line.** The penny residue from allocating a cart discount to lines is folded into the
  real per-code shares by the `Allocator` (ADR 0003, now per adjustment), never emitted as a phantom
  "rounding" adjustment. Cart-level deltas are exact `Money` folds, so the cart explanation sums with no
  residue at all.
- **Vocabulary** (`result.py`): `Adjustment(code, delta, status, superseded_by?, would_be_delta?)`,
  `AdjustmentStatus{APPLIED, SUPERSEDED}`, `Explanation(list_total, adjustments, final)`. The list price
  is the explanation's **anchor** (`list_total`), not a delta-bearing adjustment. A superseded code (ADR
  0007) carries delta ZERO, so exactness holds with it present.
- **Allocator allocates per adjustment.** To give each line's explanation an exact per-code share, the
  allocator attributes *each* cart-stage adjustment across lines (sum of shares == that adjustment,
  exactly), extending ADR 0003 (which allocated the lump total). On any cart with at most one cart-stage
  discount — every A- and B-case — this is arithmetically identical to lump allocation, so no earlier
  total or line cost changes.
- **CodeReport and Explanation are two projections of one computation**, built from the same engine pass,
  so they cannot disagree. Kept as distinct types (different shapes, different consumers) — not §10
  duplication.

## Consequences
- The engine gains a ledger responsibility (INV-7/INV-8); the allocator's interface changes from "total"
  to "per adjustment". `money.py` and `model.py` are untouched.
- Whether the ledger is a dedicated accumulator class or engine-internal state is the Worker's mechanism
  choice; the invariant (one write moves amount and provenance together; amount is a projection) is fixed.

## Alternatives rejected
- **Compute the total, then reconstruct an explanation from the inputs afterward** — the exact split that
  lets amount and explanation drift; rejected as unenforceable for property 2.
- **A trailing "rounding" adjustment to absorb the residue** — explicitly forbidden by the requirement;
  the residue belongs in real per-code shares (the allocator's job).
- **Merge CodeReport into Explanation** — they carry different things (unknown/inapplicable codes have no
  delta; explanations are per-line/cart with deltas). Two projections, one computation.
