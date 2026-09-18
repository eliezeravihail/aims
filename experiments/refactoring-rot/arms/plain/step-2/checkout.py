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


def line_charges(lines, discount, tax_rate):
    """Per-line breakdown for the second market: a list, in line order, of
    (final_cents, tax_cents) per line.

    final_cents is the line's share of order_total(lines, discount) -- the
    order-level discount allocated across the lines proportional to each line's
    gross (unit_price * qty), with the leftover pennies handed to the largest
    remainders (ties by line order). The finals therefore sum exactly to
    order_total(lines, discount).

    tax_cents = _round_half_even(final_cents * tax_rate), i.e. tax on the line's
    discounted amount.
    """
    grosses = [unit_price * qty for unit_price, qty in lines]
    total_gross = sum(grosses)
    order_tot = order_total(lines, discount)

    if total_gross == 0:
        # No basis to allocate against; every line's share is zero. (order_tot
        # is already 0 here, since subtotal is 0 and the discount only reduces.)
        finals = [0 for _ in lines]
    else:
        # Exact integer largest-remainder allocation. floor share numerator is
        # order_tot * gross; the remainder ranks who gets a leftover penny.
        floors = []
        remainders = []
        for gross in grosses:
            num = order_tot * gross
            floors.append(num // total_gross)
            remainders.append(num % total_gross)
        leftover = order_tot - sum(floors)
        # Hand each leftover penny to the largest remainder; ties by line order.
        order = sorted(range(len(lines)), key=lambda i: (-remainders[i], i))
        finals = list(floors)
        for i in order[:leftover]:
            finals[i] += 1

    return [
        (final, _round_half_even(Decimal(final) * Decimal(str(tax_rate))))
        for final in finals
    ]
