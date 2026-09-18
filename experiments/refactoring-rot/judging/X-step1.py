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
    """The amount owed for an order, in whole cents: subtotal minus an optional
    order-level discount.

    discount is None, ("pct", n) for n percent off the subtotal (0-100,
    half-even rounding), or ("amt", cents) for a fixed amount off. The total is
    clamped so it never goes below 0.
    """
    sub = subtotal(lines)
    if discount is None:
        return sub
    kind, value = discount
    if kind == "pct":
        off = _round_half_even(Decimal(sub) * Decimal(value) / Decimal(100))
    elif kind == "amt":
        off = value
    else:
        raise ValueError("unknown discount kind: %r" % (kind,))
    return max(0, sub - off)
