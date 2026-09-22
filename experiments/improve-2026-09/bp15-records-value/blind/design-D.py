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
        return [Payout(p, 0) for p in payees]

    base: Dict[str, int] = {}
    remainders = []
    allocated = 0
    for p in payees:
        exact = total_cents * shares[p]
        q, r = divmod(exact, weight_total)
        base[p] = q
        allocated += q
        remainders.append((r, p))

    leftover = total_cents - allocated
    remainders.sort(key=lambda t: (-t[0], t[1]))
    for i in range(leftover):
        base[remainders[i][1]] += 1

    return [Payout(p, base[p]) for p in payees]


def _settle_rows(total_cents: int, shares: Dict[str, int], platform_fee_bps: int = 0) -> List[Payout]:
    """Rows for a settlement: the payee split, plus a platform fee row if one applies.

    The fee is ``platform_fee_bps`` basis points of ``total_cents``, rounded down to
    the cent; the payees split whatever is left. The rows therefore sum to exactly
    ``total_cents``. With a fee of 0 bps no platform row is produced at all.
    """
    if not 0 <= platform_fee_bps <= BPS_DENOMINATOR:
        raise ValueError("platform_fee_bps must be between 0 and %d" % BPS_DENOMINATOR)
    if platform_fee_bps == 0:
        return _allocate(total_cents, shares)

    fee_cents = total_cents * platform_fee_bps // BPS_DENOMINATOR
    rows = _allocate(total_cents - fee_cents, shares)
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
        if settlement_id in self._done:
            return list(self._done[settlement_id])
        result = _settle_rows(total_cents, shares, platform_fee_bps)
        self._done[settlement_id] = result
        return list(result)

    def settle_preview(
        self,
        total_cents: int,
        shares: Dict[str, int],
        platform_fee_bps: int = 0,
    ) -> List[Payout]:
        """The rows ``settle`` would produce, without recording anything."""
        return _settle_rows(total_cents, shares, platform_fee_bps)
