"""Payout settlement: split a total across payees."""

from dataclasses import dataclass
from typing import Dict, List

from common.money import assert_conserved, bps_of

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

    return [Payout(p, base[p]) for p in payees]


def _rows(total_cents: int, shares: Dict[str, int], platform_fee_bps: int) -> List[Payout]:
    """Rows for one settlement: the fee is deducted first, the payees split the rest.

    The fee is never a weight in ``shares`` (``decisions/0003``), so it is exactly
    ``bps_of(total_cents, platform_fee_bps)`` and the allocator's rounding leftover
    still goes to the lead payee.
    """
    fee_cents = bps_of(total_cents, platform_fee_bps)

    rows = _allocate(total_cents - fee_cents, shares)
    if not rows:
        # No payee to split across: there is no settlement, and no fee to take.
        return rows

    if platform_fee_bps:
        # A fee was charged, so the row is emitted even when it rounds down to zero:
        # finance reconciles the platform cut per settlement against rate x total.
        rows.append(Payout(PLATFORM_PAYEE_ID, fee_cents))

    assert_conserved(total_cents, [r.amount_cents for r in rows])
    return rows


def settle_preview(
    total_cents: int, shares: Dict[str, int], platform_fee_bps: int = 0
) -> List[Payout]:
    """Return the rows ``settle`` would produce, without recording anything."""
    return _rows(total_cents, shares, platform_fee_bps)


class Settlements:
    def __init__(self) -> None:
        self._done: Dict[str, List[Payout]] = {}

    def settle(
        self,
        settlement_id: str,
        total_cents: int,
        shares: Dict[str, int],
        platform_fee_bps: int = 0,
    ) -> List[Payout]:
        result = _rows(total_cents, shares, platform_fee_bps)
        self._done[settlement_id] = result
        return list(result)
