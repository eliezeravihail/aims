"""Payout settlement: split a total across payees."""

from dataclasses import dataclass
from typing import Dict, List

#: Payee id used for the platform's own fee row.
PLATFORM_PAYEE_ID = "platform"

#: One basis point is 1/10000, so this many basis points make up the whole.
_BPS_DENOMINATOR = 10_000


@dataclass(frozen=True)
class Payout:
    payee_id: str
    amount_cents: int


def _platform_fee_cents(total_cents: int, platform_fee_bps: int) -> int:
    """Fee on ``total_cents``, in whole cents, always rounded down."""
    if not 0 <= platform_fee_bps <= _BPS_DENOMINATOR:
        raise ValueError(
            f"platform_fee_bps must be between 0 and {_BPS_DENOMINATOR}, got {platform_fee_bps}"
        )
    # Floor division on a non-negative numerator is the required round-down.
    return total_cents * platform_fee_bps // _BPS_DENOMINATOR


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


def _settle_rows(total_cents: int, shares: Dict[str, int], platform_fee_bps: int) -> List[Payout]:
    """The rows a settlement of ``total_cents`` produces, fee row included.

    The fee comes off the top; what is left is split among ``shares`` exactly as
    before, so payee rows plus the platform row sum to ``total_cents``.
    """
    fee_cents = _platform_fee_cents(total_cents, platform_fee_bps)

    if sum(shares.values()) <= 0:
        # No payee can absorb the remainder of the split. Emitting only a platform row
        # here would not sum to total_cents, so — as before the fee existed — we emit
        # nothing at all.
        return []

    rows = _allocate(total_cents - fee_cents, shares)
    if fee_cents > 0:
        # A zero-cent fee gets no row: these rows go to the payment rail, which rejects
        # the whole batch over a zero-amount transfer.
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
        result = _settle_rows(total_cents, shares, platform_fee_bps)
        self._done[settlement_id] = result
        return list(result)

    def settle_preview(
        self,
        total_cents: int,
        shares: Dict[str, int],
        platform_fee_bps: int = 0,
    ) -> List[Payout]:
        """The rows :meth:`settle` would produce, recording nothing."""
        return _settle_rows(total_cents, shares, platform_fee_bps)
