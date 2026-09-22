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

    The platform takes `platform_fee_bps` basis points of `total_cents`, floored
    to the cent, emitted as an extra row for `PLATFORM_PAYEE_ID`; the payees
    split what is left. A zero fee adds no platform row.
    """
    fee = bps_of(total_cents, platform_fee_bps)
    rows = _allocate(total_cents - fee, shares)
    if not rows:
        # No payee carries a share: nothing is split and no fee is taken.
        return []

    if fee:
        rows.append(Payout(PLATFORM_PAYEE_ID, fee))
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
        """Preview a settlement without recording it. See :func:`settle_preview`."""
        return settle_preview(total_cents, shares, platform_fee_bps)
