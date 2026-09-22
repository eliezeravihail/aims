"""Payout settlement: split a total across payees."""

from dataclasses import dataclass
from typing import Dict, List


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


class Settlements:
    """Records settlements by id."""

    def __init__(self) -> None:
        self._done: Dict[str, List[Payout]] = {}

    def settle(self, settlement_id: str, total_cents: int, shares: Dict[str, int]) -> List[Payout]:
        if settlement_id in self._done:
            return list(self._done[settlement_id])
        result = _allocate(total_cents, shares)
        self._done[settlement_id] = result
        return list(result)
