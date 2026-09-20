"""Money allocation for the billing engine.

Splits a total amount of money (in integer cents) across weighted parts.
"""


def allocate(total_cents: int, weights: list[int]) -> list[int]:
    """Split `total_cents` across parts in proportion to `weights`.

    Returns a list of integer-cent shares, one per weight, that sum EXACTLY to
    `total_cents`. Uses the largest-remainder method: floor each share, then hand
    the leftover cents one at a time to the parts with the largest fractional
    remainders (ties broken by lowest index).
    """
    if total_cents < 0:
        raise ValueError("total_cents must be non-negative")
    if not weights or any(w < 0 for w in weights) or sum(weights) == 0:
        raise ValueError("weights must be non-empty and sum to a positive value")

    total_weight = sum(weights)
    scaled = [total_cents * w for w in weights]
    shares = [s // total_weight for s in scaled]
    leftover = total_cents - sum(shares)

    # distribute leftover cents to the largest remainders (stable by index on ties)
    order = sorted(range(len(weights)), key=lambda i: (-(scaled[i] % total_weight), i))
    for k in range(leftover):
        shares[order[k]] += 1
    return shares


def allocate_discount(total_discount_cents: int, line_totals: list[int]) -> list[int]:
    """Allocate a cart-level discount across lines in proportion to line totals.

    Delegates to `allocate` so the sum-preservation invariant holds here too.
    """
    return allocate(total_discount_cents, line_totals)


def split_shipping(fee_cents: int, line_totals: list[int]) -> list[int]:
    """Split a flat shipping fee across order lines in proportion to line totals.

    Delegates to `allocate` so the sum-preservation invariant (R-sum) holds here
    too: the per-line shipping charges sum EXACTLY to `fee_cents`.
    """
    return allocate(fee_cents, line_totals)
