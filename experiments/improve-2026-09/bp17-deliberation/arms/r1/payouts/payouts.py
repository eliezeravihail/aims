"""Payout settlement."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Payout:
    payee_id: str
    amount_cents: int


@dataclass(frozen=True)
class Settlement:
    settlement_id: str
    total_cents: int
    payouts: List[Payout]
    #: Set on a reversal entry: the id of the settlement whose amounts this entry undoes.
    reverses: Optional[str] = None


REVERSAL_SUFFIX = "-reversal"


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

    def settle(self, settlement_id: str, total_cents: int, shares: Dict[str, int]) -> Settlement:
        entry = Settlement(settlement_id, total_cents, _allocate(total_cents, shares))
        self._entries.append(entry)
        return entry

    def reverse(self, settlement_id: str) -> Settlement:
        """Undo `settlement_id` by appending a linked reversal entry.

        The reversal carries the negated amounts of the original, so the two entries
        together net to zero for every payee. The original entry is left untouched:
        the ledger is append-only (see `decisions/0001`).

        Raises KeyError if the settlement id is unknown, and ValueError if it has
        already been reversed -- a second reversal would leave a non-zero net.
        """
        original = self.get(settlement_id)
        for e in self._entries:
            if e.reverses == settlement_id:
                raise ValueError(f"settlement already reversed: {settlement_id}")
        entry = Settlement(
            settlement_id + REVERSAL_SUFFIX,
            -original.total_cents,
            [Payout(p.payee_id, -p.amount_cents) for p in original.payouts],
            reverses=settlement_id,
        )
        self._entries.append(entry)
        return entry

    def entries(self) -> List[Settlement]:
        return list(self._entries)

    def get(self, settlement_id: str) -> Settlement:
        for e in self._entries:
            if e.settlement_id == settlement_id:
                return e
        raise KeyError(settlement_id)
