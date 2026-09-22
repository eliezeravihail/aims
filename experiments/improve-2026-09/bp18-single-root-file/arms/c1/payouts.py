"""Payout settlement: split a total across payees."""

from dataclasses import dataclass
from typing import Dict, List

#: Basis points in a whole unit: 1 bp = 1/10000.
BPS_PER_UNIT = 10_000

#: Payee id carried by the platform-fee row.
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
    """The fee in whole cents, rounded down."""
    if not 0 <= platform_fee_bps <= BPS_PER_UNIT:
        raise ValueError(
            f"platform_fee_bps must be between 0 and {BPS_PER_UNIT}, got {platform_fee_bps}"
        )
    return total_cents * platform_fee_bps // BPS_PER_UNIT


def _split(total_cents: int, shares: Dict[str, int], platform_fee_bps: int = 0) -> List[Payout]:
    """Deduct the platform fee, then split what remains across the payees.

    The fee is taken off the top, so the payee rows and the platform row together
    account for every cent of ``total_cents``.
    """
    fee_cents = _platform_fee(total_cents, platform_fee_bps)
    rows = _allocate(total_cents - fee_cents, shares)
    if fee_cents > 0:
        rows.append(Payout(PLATFORM_PAYEE_ID, fee_cents))
    return rows


class Settlements:
    """Records settlements by id."""

    def __init__(self) -> None:
        self._done: Dict[str, List[Payout]] = {}

    def settle_preview(
        self, total_cents: int, shares: Dict[str, int], platform_fee_bps: int = 0
    ) -> List[Payout]:
        """The rows `settle` would produce for these inputs. Records nothing."""
        return _split(total_cents, shares, platform_fee_bps)

    def settle(
        self,
        settlement_id: str,
        total_cents: int,
        shares: Dict[str, int],
        platform_fee_bps: int = 0,
    ) -> List[Payout]:
        result = _split(total_cents, shares, platform_fee_bps)
        self._done[settlement_id] = result
        return list(result)
