# Change card — add proportional shipping-fee split

The billing engine in `allocate.py` splits money across weighted parts. Add one capability:

> **`split_shipping(fee_cents, line_totals)`** — split a single flat shipping fee across the order's lines
> in proportion to each line's total, returning the per-line shipping charge in integer cents.

Keep all existing behavior. Deliver the design/implementation for the new capability, consistent with the
existing code's grain.
