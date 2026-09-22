"""Payout settlement."""

from dataclasses import dataclass
from typing import Dict, List, Set


@dataclass(frozen=True)
class Payout:
    payee_id: str
    amount_cents: int


@dataclass(frozen=True)
class Settlement:
    settlement_id: str
    total_cents: int
    payouts: List[Payout]


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
    return [Payout(p, base[p]) for p in payees]


class Ledger:
    """Holds every settlement this service has made."""

    def __init__(self) -> None:
        self._entries: List[Settlement] = []
        self._reversed: Set[str] = set()

    def settle(self, settlement_id: str, total_cents: int, shares: Dict[str, int]) -> Settlement:
        entry = Settlement(settlement_id, total_cents, _allocate(total_cents, shares))
        self._entries.append(entry)
        return entry

    def reverse(self, settlement_id: str) -> Settlement:
        """Undo a settlement by appending a compensating entry.

        The ledger is append-only, so nothing is removed: the reversal is a new
        entry whose payouts are the original ones negated, leaving each payee's
        net effect at zero. The amounts are negated rather than re-allocated
        from ``-total_cents``, because allocation is not symmetric under
        negation (floor division and the leftover cent would shift a cent
        between payees). A settlement can be reversed only once.
        """
        entry = self.get(settlement_id)
        if settlement_id in self._reversed:
            raise ValueError(f"settlement already reversed: {settlement_id}")
        reversal = Settlement(
            f"{settlement_id}:reversal",
            -entry.total_cents,
            [Payout(p.payee_id, -p.amount_cents) for p in entry.payouts],
        )
        self._entries.append(reversal)
        self._reversed.add(settlement_id)
        return reversal

    def entries(self) -> List[Settlement]:
        return list(self._entries)

    def get(self, settlement_id: str) -> Settlement:
        for e in self._entries:
            if e.settlement_id == settlement_id:
                return e
        raise KeyError(settlement_id)
