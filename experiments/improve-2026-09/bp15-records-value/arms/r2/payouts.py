"""Payout settlement: split a total across payees."""

from dataclasses import dataclass
from typing import Dict, List

PLATFORM_PAYEE_ID = "platform"
_BPS_PER_UNIT = 10_000


@dataclass(frozen=True)
class Payout:
    payee_id: str
    amount_cents: int


def _split(total_cents: int, shares: Dict[str, int]) -> List[Payout]:
    """Largest-remainder split of ``total_cents`` across ``shares``.

    One row per payee, in payee_id order; remainder ties break by payee_id
    ascending (decisions/0001) and zero amounts are kept (decisions/0002).
    """
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


def _allocate(total_cents: int, shares: Dict[str, int], platform_fee_bps: int = 0) -> List[Payout]:
    """Divide ``total_cents`` into the payout rows that sum to it exactly.

    The single owner of the sum invariant. Deductions are taken *here*, off the
    top, and the payees are split the remainder — never by adjusting an amount
    after the split, which is where penny drift comes from.

    ``platform_fee_bps`` basis points of ``total_cents`` (1 bp = 1/10000),
    rounded down to the cent, become one extra row for ``PLATFORM_PAYEE_ID``,
    appended after the payee rows. A fee of 0 bps adds no such row and leaves
    the result identical to a plain split.
    """
    fee_cents = total_cents * platform_fee_bps // _BPS_PER_UNIT
    rows = _split(total_cents - fee_cents, shares)
    if platform_fee_bps:
        # The row is emitted whenever a fee was charged, even when it rounds to
        # zero cents: dropping rows is what decisions/0002 rules out.
        rows.append(Payout(PLATFORM_PAYEE_ID, fee_cents))
    return rows


def settle_preview(total_cents: int, shares: Dict[str, int], platform_fee_bps: int = 0) -> List[Payout]:
    """Return the rows a settlement *would* produce, recording nothing.

    Deliberately a free function with no access to any store: previewing can
    neither record a settlement nor answer from a recorded one (decisions/0003).
    """
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
        # A repeat id returns what was paid and ignores every argument,
        # the fee included — it never recomputes (decisions/0003).
        if settlement_id in self._done:
            return list(self._done[settlement_id])
        result = _allocate(total_cents, shares, platform_fee_bps)
        self._done[settlement_id] = result
        return list(result)

    # Reachable from the class for convenience, still storeless: as a
    # staticmethod it has no `self`, so the previewing path cannot touch the
    # paying path's store.
    settle_preview = staticmethod(settle_preview)
