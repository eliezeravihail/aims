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
    """Return the rows `settle` would produce, without recording anything.

    The platform fee is deducted from the total *before* the split and emitted as
    its own row, so it is exactly `bps_of(total_cents, platform_fee_bps)` and is
    never touched by the allocator's remainder rule (`decisions/0003`).
    """
    fee = bps_of(total_cents, platform_fee_bps)
    payee_total = total_cents - fee
    assert_conserved(total_cents, [payee_total, fee])

    rows = _allocate(payee_total, shares)
    if platform_fee_bps:
        rows.append(Payout(PLATFORM_PAYEE_ID, fee))
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
