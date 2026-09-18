"""Order pricing. Plain style on purpose: bare integer cents, plain functions,
tuples for structured values. No classes, no value objects. A change should keep
this grain."""
from decimal import Decimal, ROUND_HALF_EVEN


def _round_half_even(x):
    return int(Decimal(x).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def subtotal(lines):
    # lines: list of (unit_price_cents, qty)
    return sum(unit_price * qty for unit_price, qty in lines)


def order_total(lines, discount=None):
    """The amount owed for an order, in whole cents: the subtotal, less an
    optional order-level discount. discount is ("pct", n) for n percent off the
    subtotal (0-100, half-even), ("amt", cents) for a fixed amount off, or None.
    The total never goes below 0."""
    amount = subtotal(lines)
    if discount is not None:
        kind, value = discount
        if kind == "pct":
            amount -= _round_half_even(Decimal(amount * value) / 100)
        elif kind == "amt":
            amount -= value
    return max(0, amount)
