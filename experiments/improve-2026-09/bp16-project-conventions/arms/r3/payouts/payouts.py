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


def settle_preview(
    total_cents: int, shares: Dict[str, int], platform_fee_bps: int = 0
) -> List[Payout]:
    """Return the rows a settlement would produce, recording nothing.

    The platform fee is deducted from the total *before* the split and emitted as its
    own row, never as a weight in `shares` (`decisions/0003`), so it is exactly
    `bps_of(total_cents, platform_fee_bps)` and never absorbs the rounding leftover.
    The payees divide what remains. With `platform_fee_bps` of 0 there is no fee row.
    """
    fee_cents = bps_of(total_cents, platform_fee_bps)

    rows = _allocate(total_cents - fee_cents, shares)
    if platform_fee_bps:
        rows.append(Payout(PLATFORM_PAYEE_ID, fee_cents))

    if rows:
        assert_conserved(total_cents, [r.amount_cents for r in rows])
    return rows


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
        result = settle_preview(total_cents, shares, platform_fee_bps)
        self._done[settlement_id] = result
        return list(result)

    def settle_preview(
        self, total_cents: int, shares: Dict[str, int], platform_fee_bps: int = 0
    ) -> List[Payout]:
        """Preview a settlement's rows without recording it."""
        return settle_preview(total_cents, shares, platform_fee_bps)
