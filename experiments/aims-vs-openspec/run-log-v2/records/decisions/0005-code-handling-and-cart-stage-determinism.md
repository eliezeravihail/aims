---
title: "0005 — Code handling and cart-stage determinism"
date: 2026-09-16
---

## Status
Accepted (owner answers, final round).

## Context
The owner fixed how entered codes are matched, de-duplicated, ordered, and rounded, and gave two
worked facts: two 10% codes take 19% off (not 20%), and `SAVE10` == `save10`.

## Decision
- **Determinism (INV-5).** Pricing is a pure function of the cart; the same cart always yields the
  same answer. Cart-stage codes are applied in **first-occurrence entry order** — a fixed order, which
  is all "same cart, same answer" requires (the owner explicitly left the order to us provided it is
  stable).
- **Percentages compound (INV-6).** Each cart-stage discount folds onto the running total, so a PCT is
  computed off the folded total, never the original subtotal — two 10% codes ⇒ 0.9 × 0.9 = 0.81 ⇒
  19% off. (This makes multiple PCTs order-independent as a bonus, reinforcing determinism.)
- **Case-insensitive code identity.** Two entered strings denote the same code iff their casefold is
  equal. This normalization is a single rule owned with the `PromotionCode` concept and used by *both*
  catalog resolution and engine dedupe, so there is one owner of "same code".
- **Duplicates counted once, reported as duplicated.** After normalization, a repeated code applies a
  single time; its `CodeReport` records `times_entered > 1` (first-occurrence spelling echoed). This
  holds for unknown codes too (reported once, with the count).
- **Retirement = deletion.** A retired code is simply absent from the definitions file and resolves to
  **UNKNOWN**; there is no inactive/expired state.
- **Applicability by effect.** A known code is APPLIED iff it yields a discount > 0, else INAPPLICABLE
  with a reason (BOGO SKU absent; SKU present but qty < N; subtotal already 0). One uniform rule.

## Consequences
- Ordering/dedupe/normalization mapping lives in `PricingEngine`; the identity rule lives with
  `PromotionCode`; per-kind applicability lives in each `Promotion`. No component learns another's job.
- No promotion-eligibility windows, thresholds, or priority scheme exist — not needed and not built.

## Alternatives rejected
- **Applying each duplicate occurrence** — the owner chose count-once.
- **Percentages that add** (two 10% ⇒ 20%) — the owner chose compounding (19%).
- **An order-independent canonical sort of cart codes** — unnecessary; determinism only needs a fixed
  order, and first-occurrence order is the simplest stable one and is already meaningful to a reader.
