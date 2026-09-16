---
title: "0003 — Cart-discount allocation to lines"
date: 2026-09-16
---

## Status
Accepted. The owner confirmed (final round): a line's cost is what the customer pays for it — the
invoice line — and the line prices add up to the total. Allocation is now unconditional (INV-3).

## Context
The output demands both per-line cost and cart cost. PCT/AMT discount the *whole cart*. If per-line
costs must reconcile to the total (the natural reading of "what each line costs, and what the whole
cart costs"), a cart-level discount has to be attributed back to lines — introducing a rounding
problem: naive proportional shares at 2dp need not sum to the discount.

## Decision
- Per-line cost **includes** an allocated share of cart-level discounts, so
  `sum(line.cost) == cart.total` exactly at 2dp (**INV-3**).
- One `Allocator` owns it. Policy: allocate the *total* cart-stage discount across lines in proportion
  to each line's post-line-stage amount, quantize each share to 2dp, then distribute the leftover
  residual pennies deterministically (largest fractional remainder, ties by line order) so the shares
  sum exactly to the discount.
- Guards: if the post-line subtotal is `0`, there is nothing to allocate (all lines already `0`); a
  line's share never exceeds its own amount, so no line goes negative; when the discount is clamped to
  the subtotal (INV-1), every line resolves to `0`.

## Consequences
- The rounding residual is visible and testable, not an accidental penny drift.
- The allocation stayed its own owner precisely so the answer to "invoice line vs pre-discount line"
  moved one component and nothing else; the owner chose the invoice line, and the `Allocator` is that
  owner.

## Alternatives rejected
- Letting each line round independently and hoping the sum matches — fails INV-3 on ordinary inputs.
- Folding each cart discount and re-allocating per fold — more passes, same result; one final
  allocation is simpler and equally correct.
