"""Payout settlement: split a total across payees."""

from dataclasses import dataclass
from typing import Dict, List

BPS_DIVISOR = 10_000
PLATFORM_PAYEE_ID = "platform"


@dataclass(frozen=True)
class Payout:
    payee_id: str
    amount_cents: int


def _allocate(total_cents: int, shares: Dict[str, int]) -> List[Payout]:
    payees = sorted(shares)
    weight_total = sum(shares.values())
    if weight_total <= 0:
        return []

    base: Dict[str, int] = {}
    allocated = 0
    for p in payees:
        q = total_cents * shares[p] // weight_total
        base[p] = q
        allocated += q

    leftover = total_cents - allocated
    if leftover:
        lead = min(payees, key=lambda p: (-shares[p], p))
        base[lead] += leftover

    return [Payout(p, base[p]) for p in payees if base[p] > 0]


def _platform_fee(total_cents: int, platform_fee_bps: int) -> int:
    """Fee in cents: `platform_fee_bps` basis points of the total, rounded down."""
    if not 0 <= platform_fee_bps <= BPS_DIVISOR:
        raise ValueError(f"platform_fee_bps out of range: {platform_fee_bps}")
    return total_cents * platform_fee_bps // BPS_DIVISOR


def settle_preview(
    total_cents: int, shares: Dict[str, int], platform_fee_bps: int = 0
) -> List[Payout]:
    """Return the payout rows a settlement would produce, recording nothing.

    The platform fee is taken off the top and the remainder is split across
    `shares`. With `platform_fee_bps` of 0 no platform row is produced and the
    rows are exactly what splitting `total_cents` alone would give; otherwise
    the payee rows plus the platform row sum to `total_cents` exactly.
    """
    fee = _platform_fee(total_cents, platform_fee_bps)
    rows = _allocate(total_cents - fee, shares)
    if platform_fee_bps == 0:
        return rows
    if PLATFORM_PAYEE_ID in shares:
        raise ValueError(f"{PLATFORM_PAYEE_ID!r} is reserved for the fee row")

    # Whatever the split could not hand out (no positive weights) stays with the
    # platform row, so the rows always account for the whole total.
    unallocated = total_cents - fee - sum(r.amount_cents for r in rows)
    return rows + [Payout(PLATFORM_PAYEE_ID, fee + unallocated)]


class Settlements:
    """Records settlements by id."""

    def __init__(self) -> None:
        self._done: Dict[str, List[Payout]] = {}

    def settle(
        self,
        settlement_id: str,
        total_cents: int,
        shares: Dict[str, int],
        platform_fee_bps: int = 0,
    ) -> List[Payout]:
        result = settle_preview(total_cents, shares, platform_fee_bps)
        self._done[settlement_id] = result
        return list(result)

    def settle_preview(
        self, total_cents: int, shares: Dict[str, int], platform_fee_bps: int = 0
    ) -> List[Payout]:
        """Preview a settlement without recording it."""
        return settle_preview(total_cents, shares, platform_fee_bps)
