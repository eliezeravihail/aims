"""Payout settlement: split a total across payees."""

from dataclasses import dataclass
from typing import Dict, List

#: Basis points per unit: 1 bp = 1/10000.
_BPS_DENOMINATOR = 10_000

#: Payee id used for the platform fee row.
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


def _compute(total_cents: int, shares: Dict[str, int], platform_fee_bps: int) -> List[Payout]:
    """Rows for one settlement: the platform fee, then the split of what is left."""
    if not 0 <= platform_fee_bps <= _BPS_DENOMINATOR:
        raise ValueError(f"platform_fee_bps out of range: {platform_fee_bps!r}")

    # Nothing is payable, so nothing is settled -- and no fee is taken. Skipping the
    # guard here would emit a lone platform row for a settlement that never split.
    if sum(shares.values()) <= 0:
        return []

    fee_cents = total_cents * platform_fee_bps // _BPS_DENOMINATOR
    rows = _allocate(total_cents - fee_cents, shares)
    # A zero-amount row is dropped like any other: the payment rail rejects the whole
    # batch on a zero transfer, and dropping it leaves the rows summing to the total.
    if fee_cents > 0:
        rows.append(Payout(PLATFORM_PAYEE_ID, fee_cents))
    return rows


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
        result = _compute(total_cents, shares, platform_fee_bps)
        self._done[settlement_id] = result
        return list(result)

    def settle_preview(
        self,
        total_cents: int,
        shares: Dict[str, int],
        platform_fee_bps: int = 0,
    ) -> List[Payout]:
        """The rows `settle` would produce, recording nothing."""
        return _compute(total_cents, shares, platform_fee_bps)
