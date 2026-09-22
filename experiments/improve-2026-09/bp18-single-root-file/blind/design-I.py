"""Payout settlement: split a total across payees."""

from dataclasses import dataclass
from typing import Dict, List

PLATFORM_PAYEE_ID = "platform"
_BPS_DIVISOR = 10_000


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
    """Fee in cents: `platform_fee_bps` basis points of the total, rounded down."""
    if platform_fee_bps <= 0:
        return 0
    return total_cents * platform_fee_bps // _BPS_DIVISOR


def _rows(total_cents: int, shares: Dict[str, int], platform_fee_bps: int) -> List[Payout]:
    """The rows for one settlement: the platform fee, then the split of what is left.

    The fee is deducted *before* `_allocate`, so `_allocate` stays the single owner of the
    division and of where the rounding remainder lands (`decisions/0002`), and the rows still
    sum to `total_cents` exactly. A zero-amount platform row is not emitted, for the same
    reason a zero-amount payee row is not (`decisions/0003`).
    """
    if sum(shares.values()) <= 0:
        # No active payees: nothing is being split, so no fee is taken either.
        return []

    fee = _platform_fee(total_cents, platform_fee_bps)
    rows = _allocate(total_cents - fee, shares)
    if fee > 0:
        rows.append(Payout(PLATFORM_PAYEE_ID, fee))
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
        result = _rows(total_cents, shares, platform_fee_bps)
        self._done[settlement_id] = result
        return list(result)

    def settle_preview(
        self,
        total_cents: int,
        shares: Dict[str, int],
        platform_fee_bps: int = 0,
    ) -> List[Payout]:
        """The rows `settle` would produce, without recording anything.

        Deliberately not a read-through of `self._done`: `settle` recomputes on every call
        (`decisions/0001`), and a preview must not turn that store into a cache.
        """
        return _rows(total_cents, shares, platform_fee_bps)
