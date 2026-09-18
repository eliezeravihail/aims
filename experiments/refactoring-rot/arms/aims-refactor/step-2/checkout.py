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


def _allocate(total, weights):
    """Split a whole (bare cents) across buckets in proportion to weights so the
    parts SUM EXACTLY to total. Floor each proportional share, then hand the
    leftover pennies to the largest fractional remainders (largest-remainder
    method), ties broken by bucket order. A zero total or all-zero weights gives
    all zeros. Returns one int per weight, in order. This is the single owner of
    the Σ parts == whole conservation invariant."""
    n = len(weights)
    g = sum(weights)
    if g == 0:
        return [0] * n
    shares = [total * w // g for w in weights]
    remainders = [total * w % g for w in weights]
    leftover = total - sum(shares)
    for i in sorted(range(n), key=lambda i: (-remainders[i], i))[:leftover]:
        shares[i] += 1
    return shares


def line_charges(lines, discount, tax_rate):
    """A per-line breakdown of a discounted order, in line order. Returns a list of
    (final_cents, tax_cents) per line, where final_cents is the line's share of
    order_total(lines, discount) — the order-level discount allocated across lines
    in proportion to each line's gross (unit_price*qty), remainder pennies by
    largest remainder — so the line finals SUM EXACTLY to order_total(lines,
    discount). tax_cents is the tax on that discounted share, half-even:
    round_half_even(final_cents * tax_rate). tax_rate is a Decimal fraction."""
    total = order_total(lines, discount)
    grosses = [unit_price * qty for unit_price, qty in lines]
    finals = _allocate(total, grosses)
    return [(final, _round_half_even(final * tax_rate)) for final in finals]
