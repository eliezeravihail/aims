# Step 3 — a stacking loyalty discount with a cap

Orders may now also carry a **loyalty discount** `("pct", n)`, applied to the subtotal **after** the
order-level discount. But the **combined** discount (order-level + loyalty) is **capped at 50% of the
subtotal**: if the two together would exceed 50%, the loyalty portion is reduced so the total discount is
exactly 50%, and the reduction must be **reportable**.

- `order_total(lines, discount=None, loyalty=None)` returns the final total after both discounts, respecting
  the cap.
- `line_charges(lines, discount, tax_rate, loyalty=None)` reflects the capped total (line finals still sum to
  `order_total(lines, discount, loyalty)`).
- Add `discount_breakdown(lines, discount, loyalty)` → `(order_discount_cents, loyalty_requested_cents,
  loyalty_granted_cents)` so a caller can see how much loyalty was actually granted vs requested after the cap.

Everything from steps 1–2 keeps working (existing tests unchanged); an order with `loyalty=None` behaves
exactly as before. Keep the module's plain style.
