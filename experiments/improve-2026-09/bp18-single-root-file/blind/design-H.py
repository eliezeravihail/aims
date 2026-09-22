"""Payout settlement: split a total across payees."""

from dataclasses import dataclass
from typing import Dict, List

BPS_DENOMINATOR = 10_000

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


def settle_preview(
    total_cents: int, shares: Dict[str, int], platform_fee_bps: int = 0
) -> List[Payout]:
    """Return the payout rows a settlement would produce, recording nothing.

    The platform fee is ``platform_fee_bps`` basis points of ``total_cents``,
    rounded down to the cent; what is left over is split across ``shares`` as
    usual. The platform row, when there is one, comes last. Rows sum exactly
    to ``total_cents`` whenever the shares are allocatable at all.
    """
    if not 0 <= platform_fee_bps <= BPS_DENOMINATOR:
        raise ValueError(f"platform_fee_bps out of range: {platform_fee_bps}")

    if sum(shares.values()) <= 0:
        # Nothing to split across (no payees, or non-positive weights): keep
        # the long-standing "settles to nothing" answer rather than charging a
        # fee against a split that never happened.
        return []

    fee_cents = total_cents * platform_fee_bps // BPS_DENOMINATOR
    rows = _allocate(total_cents - fee_cents, shares)
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
        result = settle_preview(total_cents, shares, platform_fee_bps)
        self._done[settlement_id] = result
        return list(result)

    def settle_preview(
        self, total_cents: int, shares: Dict[str, int], platform_fee_bps: int = 0
    ) -> List[Payout]:
        """Rows :meth:`settle` would produce, without recording anything."""
        return settle_preview(total_cents, shares, platform_fee_bps)
