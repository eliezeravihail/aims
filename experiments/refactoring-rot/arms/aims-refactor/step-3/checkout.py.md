---
title: "checkout.py"
date: 2026-09-18
hash: "sha256:d47fff07dc39b8a78b06a7655aafe9873b54f40c0813aaea38ca5de8599310cd"
---
## Insights
- The module is deliberately plain: bare integer cents, plain functions, tuples for structured
  values. Changes keep this grain (no classes/value objects).
- `order_total` is the single owner of "the discounted order total": subtotal minus a half-even-rounded
  ("pct", n) or exact ("amt", cents) discount, clamped >= 0. Any per-line view of a discounted order must
  read this number, not re-derive the discount.

## Decisions
- `line_charges(lines, discount, tax_rate)` returns per-line `(final_cents, tax_cents)` in line order.
  It does NOT re-derive the discount — it calls `order_total(lines, discount)` for the whole and
  ALLOCATES that whole across lines. Invariant: `sum(final for final,_ in line_charges) ==
  order_total(lines, discount)` (Σ parts == whole). This keeps `order_total` the one owner of the
  discount rule and avoids the "clean change that ships Σ parts ≠ whole" miss.
- `_allocate(total, weights)` owns the conservation invariant: proportional shares floored, leftover
  pennies handed to the largest fractional remainders (largest-remainder method), ties broken by bucket
  order. It is the one home of remainder-penny distribution; a zero total or all-zero weights (empty
  lines, or gross 0) yields all zeros with no divide-by-zero.
- Tax is per line on the DISCOUNTED share: `_round_half_even(final_cents * tax_rate)`, reusing the
  module's existing half-even rounding owner. `tax_rate` is a Decimal fraction, matching the module's
  Decimal money math. No cross-line tax conservation is claimed (spec fixes only the finals-sum).
- The seam for the new market already existed (`order_total` exposes the whole needed), so this was a
  sibling addition — no restructuring of `order_total`, `subtotal`, or `_round_half_even`. First market
  (`order_total`) preserved bit-for-bit; its tests pass unchanged.

- `discount_breakdown(lines, discount, loyalty)` is the SINGLE owner of the cap/precedence rule. It
  returns `(order_discount_cents, loyalty_requested_cents, loyalty_granted_cents)`. Precedence: the
  order-level discount comes first and is READ as `subtotal - order_total(lines, discount)` (its existing
  owner), never re-derived; loyalty `("pct", n)` is requested off the subtotal and applied after it; the
  COMBINED order+loyalty discount is capped at 50% of the subtotal (`_round_half_even(sub*50/100)`, the
  module's pct convention), so `granted = min(requested, max(0, cap - order_discount))`. A lone order
  discount at/over the cap grants no loyalty; loyalty is never reduced below 0. `requested`/`granted`
  make the reduction reportable (`reduction = requested - granted`).
- The cap rule is NOT scattered: `order_total(lines, discount, loyalty)` reads `granted` from
  `discount_breakdown` and subtracts it; `line_charges(lines, discount, tax_rate, loyalty)` reads the
  capped whole via `order_total(..., loyalty)` and allocates it through `_allocate` unchanged, so the Σ
  parts == whole invariant holds against the capped total. Neither re-computes the cap.
- `loyalty=None` preserves prior behavior bit-for-bit: `order_total` skips the loyalty block (identical
  to the two-arg body); `line_charges` calls `order_total(..., None)`. Existing tests pass unchanged; the
  order-level discount owner (`order_total`) and `_allocate` were not restructured.

## Discussions
- Considered inlining the allocation inside `line_charges`; extracted `_allocate` instead so the
  Σ parts == whole invariant has one named, testable owner and `line_charges` stays single-altitude.
  This mirrors the module's existing private `_round_half_even` helper, so it stays within the grain.
- The loyalty seam already existed: `order_total` was the whole-owner and `line_charges` read it. So the
  cap became a sibling rule with one owner (`discount_breakdown`) rather than a restructuring — matching
  the earlier line-allocation addition. Kept the plain grain: a new plain function returning a tuple,
  reusing `_round_half_even`; no classes, no value objects, no flags threaded through consumers. The cap
  base uses the subtotal (loyalty is "off the subtotal, applied after the order discount"); a lone order
  discount above 50% is left as-is because the requirement reduces only the loyalty portion.
