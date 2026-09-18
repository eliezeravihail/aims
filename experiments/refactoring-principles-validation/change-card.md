# Change request — a second market with per-line tax

You are handed an **existing, working** order-pricing module (`pricing.py` + `test_pricing.py`). It serves
one market: `order_total(order)` returns a single final total (subtotal minus the order-level discount).

A **second market** now needs **per-line reporting with tax**. Add it without breaking the first market.

## The new requirement

Expose a new function:

```python
def price_market2(order: Order, tax_rate: Decimal) -> Market2Result
```

returning an object (or namedtuple/dataclass) with exactly these fields:

- `order_final: int` — the order's discounted total in whole cents (**must equal** what market 1 computes for
  the same order).
- `line_finals: list[int]` — each line's final amount in cents **after** the order-level discount has been
  **allocated to the lines**. The list is in line order and **must sum exactly to `order_final`** (distribute
  remainder cents by largest remainder, proportional to each line's gross `total_cents`).
- `line_taxes: list[int]` — each line's tax in cents, computed **on that line's discounted final amount**:
  `line_taxes[i] = round_half_even(line_finals[i] * tax_rate)`.

## Constraints

- **Market 1 is unchanged.** `order_total(order)` must keep returning exactly what it does today, and the
  existing `test_pricing.py` must still pass **unchanged**.
- Money is integer cents; rounding is half-even (`round_half_even` already exists in the module).
- The discount kinds are the existing `("pct", n)` and `("amt", cents)`.

Deliver the adapted `pricing.py` (and any tests you add). The graders will run your `pricing.py` against a
hidden battery of cases.
