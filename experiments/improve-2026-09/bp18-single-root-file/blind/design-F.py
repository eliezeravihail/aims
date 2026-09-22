"""Payout settlement: split a total across payees."""

from dataclasses import dataclass
from typing import Dict, List

PLATFORM_PAYEE_ID = "platform"
BPS_DENOMINATOR = 10_000


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
    return total_cents * platform_fee_bps // BPS_DENOMINATOR


def _rows(total_cents: int, shares: Dict[str, int], platform_fee_bps: int) -> List[Payout]:
    """The rows a settlement of these figures produces. Records nothing."""
    fee = _platform_fee(total_cents, platform_fee_bps)
    # The fee is deducted *before* the split, so `_allocate` stays the single owner of division and
    # of where the rounding remainder lands (it stays with the largest-share payee — decisions/0002).
    rows = _allocate(total_cents - fee, shares)
    if fee > 0:
        # A zero fee is not emitted: the payment rail rejects a zero-amount row, and with it the whole
        # batch (decisions/0003). Payees pushed to zero by the fee are dropped by `_allocate` already.
        rows.append(Payout(PLATFORM_PAYEE_ID, fee))
    return rows


def settle_preview(
    total_cents: int, shares: Dict[str, int], platform_fee_bps: int = 0
) -> List[Payout]:
    """The rows `settle` would produce for these figures, without recording anything."""
    return _rows(total_cents, shares, platform_fee_bps)


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
        # Deliberately recomputes and overwrites on every call; no idempotency replay — decisions/0001.
        result = _rows(total_cents, shares, platform_fee_bps)
        self._done[settlement_id] = result
        return list(result)

    # Available on the recorder too, so a caller holding one can price a settlement without
    # recording it. It must never read or write `self._done` (decisions/0001).
    settle_preview = staticmethod(settle_preview)
