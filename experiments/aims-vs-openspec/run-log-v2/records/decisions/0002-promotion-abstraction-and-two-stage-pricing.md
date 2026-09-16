---
title: "0002 — Promotion abstraction and two-stage pricing"
date: 2026-09-16
---

## Status
Accepted (stage-1 design).

## Context
Three promotion kinds exist today (PCT, AMT, BOGO) and a fourth is foreseeable. Two of them discount
the whole order; one discounts a specific line. Case A5 fixes that line discounts are computed before
order discounts. The engine must not become a `kind`-switch, or adding a kind becomes shotgun surgery.

## Decision
- A single polymorphic **`Promotion`** interface; `PercentPromotion`, `AmountPromotion`,
  `BogoPromotion` are implementations. Each owns its own discount math and applicability rule. The
  interface earns its place: three real implementations today, a describable fourth tomorrow.
- Each promotion declares a **`Scope`** (`LINE` | `CART`) — a domain attribute, not a kind tag.
- The engine applies **all `LINE`-scope promotions before any `CART`-scope promotion**, and orders by
  scope only — it never branches on kind. Adding a kind touches `promotions.py` + the catalog
  registry, never the engine.
- A promotion, applied, returns a `DiscountResult`: an applied `Discount` (amount + where it lands) or
  `Inapplicable(reason)` (e.g. BOGO's SKU absent). Unknown-vs-inapplicable-vs-applied is data.

## Consequences
- Ordering/stacking rules live in the engine (INV-5); per-kind math lives in the promotion (Tell,
  Don't Ask).
- A future discount *stage* is a new `Scope` member + its place in the engine's order.

## Alternatives rejected
- **Two segregated interfaces** (`LinePromotion` / `CartPromotion`): honest about the two altitudes,
  but for three kinds it splits a coherent family and complicates the catalog; `Scope` on one
  interface captures the same distinction with less machinery. Revisit if line-stage kinds proliferate.
- **One `Promotion.apply` with an internal `if kind == …` in the engine**: rejected — that is the
  god-switch the abstraction exists to prevent.
