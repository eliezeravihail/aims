"""Order pricing. Plain style on purpose: bare integer cents, plain functions,
tuples for structured values. No classes, no value objects. A change should keep
this grain."""
from decimal import Decimal, ROUND_HALF_EVEN


def _round_half_even(x):
    return int(Decimal(x).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def subtotal(lines):
    # lines: list of (unit_price_cents, qty)
    return sum(unit_price * qty for unit_price, qty in lines)


def order_total(lines):
    """The amount owed for an order: currently just the subtotal, in whole cents."""
    return subtotal(lines)
