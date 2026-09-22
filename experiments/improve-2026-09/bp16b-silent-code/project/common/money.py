"""Money helpers."""


def bps_of(amount_cents: int, bps: int) -> int:
    if not 0 <= bps <= 10_000:
        raise ValueError(f"rate out of range: {bps} bps")
    if amount_cents < 0:
        raise ValueError("negative amount")
    return amount_cents * bps // 10_000


def assert_conserved(total_cents: int, parts: list) -> None:
    s = sum(parts)
    if s != total_cents:
        raise AssertionError(f"money not conserved: {s} != {total_cents}")
