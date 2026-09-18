# Step 2 — a second market with per-line tax

A second market needs a **per-line breakdown with tax**. Add:

`line_charges(lines, discount, tax_rate)` → a list, in line order, of `(final_cents, tax_cents)` per line,
where:

- `final_cents` is that line's share of the order's discounted total — the order-level discount **allocated
  across the lines** (proportional to each line's gross, remainder pennies by largest remainder), so the
  line finals **sum exactly** to `order_total(lines, discount)`.
- `tax_cents = round_half_even(final_cents * tax_rate)` — tax on the line's **discounted** amount.

The first market is unchanged: `order_total(...)` and the existing tests must still pass. Keep the module's
plain style.
