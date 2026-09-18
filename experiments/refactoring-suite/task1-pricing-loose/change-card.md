# Change request — a second market with per-line tax (customer-facing breakdown)

You are handed an existing, working order-pricing module (`pricing.py` + `test_pricing.py`). It serves one
market: `order_total(order)` returns a single final total.

A **second market** shows the customer a **per-line breakdown**: for each line, the amount the customer is
**charged for that line** and the **tax** on it (tax = the market rate applied to that line's charge,
half-even rounding). The customer must be able to **add up the per-line charges and get the order's total
charge** (what they actually pay for the whole order).

Expose:

```python
def price_market2(order: Order, tax_rate: Decimal) -> Market2Result
```

with fields `order_final: int`, `line_finals: list[int]` (the per-line charge, in line order), and
`line_taxes: list[int]`.

Market 1 is unchanged — `order_total(order)` keeps returning exactly what it does today and the existing
`test_pricing.py` must pass **unchanged**. Money is integer cents; `round_half_even` already exists in the
module. Discount kinds are `("pct", n)` and `("amt", cents)`.

Deliver the adapted `pricing.py`. Do not edit `test_pricing.py`.
