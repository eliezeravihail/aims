"""Payout settlement: split a total across payees."""

from dataclasses import dataclass
from typing import Dict, List

BPS_DIVISOR = 10_000

PLATFORM_PAYEE_ID = "platform"


@dataclass(frozen=True)
class Payout:
    payee_id: str
    amount_cents: int


def _allocate(
    total_cents: int, shares: Dict[str, int], platform_fee_bps: int = 0
) -> List[Payout]:
    payees = sorted(shares)
    weight_total = sum(shares.values())
    if weight_total <= 0:
        return []

    # The fee is taken off the top, inside the allocation, so the payee split and its
    # remainder are computed on what is actually left to distribute. Applying a deduction
    # after allocation would break the exact-sum property (see payouts.py.md).
    fee = total_cents * platform_fee_bps // BPS_DIVISOR
    distributable = total_cents - fee

    base: Dict[str, int] = {}
    allocated = 0
    for p in payees:
        q = distributable * shares[p] // weight_total
        base[p] = q
        allocated += q

    leftover = distributable - allocated
    if leftover:
        lead = min(payees, key=lambda p: (-shares[p], p))
        base[lead] += leftover

    rows = [Payout(p, base[p]) for p in payees if base[p] > 0]
    # A fee that rounds down to zero emits no row: the rail rejects the whole batch on a
    # zero-amount transfer (decisions/0003). Dropping it keeps the sum exact either way.
    if fee > 0:
        rows.append(Payout(PLATFORM_PAYEE_ID, fee))
    return rows


def settle_preview(
    total_cents: int, shares: Dict[str, int], platform_fee_bps: int = 0
) -> List[Payout]:
    """Return the rows a settlement would produce, recording nothing."""
    return _allocate(total_cents, shares, platform_fee_bps)


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
        result = _allocate(total_cents, shares, platform_fee_bps)
        self._done[settlement_id] = result
        return list(result)

    # Preview is state-free by construction: it neither reads nor writes ``_done``, so it
    # cannot become the read-through cache `settle` must never grow (decisions/0001).
    settle_preview = staticmethod(settle_preview)
