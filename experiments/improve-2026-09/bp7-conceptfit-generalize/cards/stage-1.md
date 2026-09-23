# Task: promotional pricing engine (stage 1)

Build a small Python module `promo.py` for applying promotional rules to a shopping cart.
All money is in integer **cents**. No external dependencies.

## Required API (names are contractual — a hidden test suite imports exactly these)

**Cart**
- `Cart()` — empty cart.
- `cart.add_item(sku: str, category: str, unit_price: int, qty: int) -> None` — add a line.
- `cart.subtotal() -> int` — sum of `unit_price * qty` over all lines.

**Rule constructors** (three kinds):
- `PercentOff(category: str, percent: int)` — discount = `percent`% of the summed price of lines whose
  `category` matches, using integer floor division (`base * percent // 100`).
- `AmountOffOver(threshold: int, amount: int)` — discount = `amount` if `cart.subtotal() >= threshold`, else 0.
- `BuyXGetY(sku: str, x: int, y: int)` — for lines matching `sku`: every group of `x + y` units makes `y`
  units free; discount = `(qty // (x + y)) * y * unit_price`, summed over matching lines.

**Engine**
- `Engine(rules: list)` — holds a list of rule objects.
- `engine.total(cart) -> int` — apply **all** rules and return `max(0, subtotal - total_discount)`.
  Discounts from multiple rules add together. The final total is floored at 0.

## Notes
- Unknown category / sku simply contribute no discount.
- Empty cart → subtotal 0 → total 0.
- Keep it clean and correct; you will later be asked to extend it.
