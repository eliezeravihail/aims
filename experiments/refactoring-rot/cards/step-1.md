# Step 1 — order-level discount

The order may carry one **order-level discount**: `("pct", n)` (n percent off the subtotal, 0–100) or
`("amt", cents)` (a fixed amount off), or `None`.

Extend `order_total` to take it: `order_total(lines, discount=None)` returns the subtotal minus the discount,
in whole cents (half-even for the percentage; the fixed amount is clamped so the total never goes below 0).

Keep the existing behavior: `order_total(lines)` with no discount, and the existing `test_checkout.py`, must
still pass **unchanged**. **Match the module's existing plain style** (bare int cents, plain functions).
