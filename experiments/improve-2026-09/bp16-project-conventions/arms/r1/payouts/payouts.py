"""Payout settlement: split a total across payees."""

from dataclasses import dataclass
from typing import Dict, List

from common.money import assert_conserved, bps_of


@dataclass(frozen=True)
class Payout:
    payee_id: str
    amount_cents: int


PLATFORM_PAYEE_ID = "platform"


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
    """Return the rows a settlement would produce, without recording anything.

    The platform fee is `platform_fee_bps` of `total_cents`, deducted **before** the
    split and emitted as its own `PLATFORM_PAYEE_ID` row; the payees divide only the
    remainder, so the fee is never touched by the rounding remainder rule
    (`decisions/0003`). With `platform_fee_bps` of 0 no platform row is emitted.
    """
    fee_cents = bps_of(total_cents, platform_fee_bps)
    payees_cents = total_cents - fee_cents
    assert_conserved(total_cents, [payees_cents, fee_cents])

    rows = _allocate(payees_cents, shares)
    if platform_fee_bps:
        rows.append(Payout(PLATFORM_PAYEE_ID, fee_cents))
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
