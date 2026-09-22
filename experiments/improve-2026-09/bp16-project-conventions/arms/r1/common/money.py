"""House money helpers. All monetary arithmetic in this service goes through here."""


def bps_of(amount_cents: int, bps: int) -> int:
    """Return `bps` basis points of `amount_cents`, floored, with the house guards.

    Rejects out-of-range rates and negative amounts rather than producing a
    silently wrong figure. 1 bp = 1/10000.
    """
    if not 0 <= bps <= 10_000:
        raise ValueError(f"rate out of range: {bps} bps")
    if amount_cents < 0:
        raise ValueError("negative amount")
    return amount_cents * bps // 10_000


def assert_conserved(total_cents: int, parts: list) -> None:
    """Assert the parts conserve the total exactly. Used at every money seam."""
    s = sum(parts)
    if s != total_cents:
        raise AssertionError(f"money not conserved: {s} != {total_cents}")
