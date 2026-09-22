"""Payout settlement."""

from dataclasses import dataclass
from typing import Dict, List


REVERSAL_SUFFIX = ":reversal"


@dataclass(frozen=True)
class Payout:
    payee_id: str
    amount_cents: int


@dataclass(frozen=True)
class Settlement:
    settlement_id: str
    total_cents: int
    payouts: List[Payout]


def _reversal_id(settlement_id: str) -> str:
    return settlement_id + REVERSAL_SUFFIX


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
        """Undo a settlement by appending a reversing entry.

        The ledger is append-only, so the original entry stays put and the
        money goes back through a mirror entry posted after it. Each payout
        is negated as stored rather than re-allocated from a negative total:
        allocation rounds and hands the remainder to the lead payee, so a
        fresh allocation would not cancel the original cent for cent.
        """
        entry = self.get(settlement_id)
        reversal_id = _reversal_id(settlement_id)
        for e in self._entries:
            if e.settlement_id == reversal_id:
                raise ValueError(f"settlement {settlement_id!r} is already reversed")
        reversal = Settlement(
            reversal_id,
            -entry.total_cents,
            [Payout(p.payee_id, -p.amount_cents) for p in entry.payouts],
        )
        self._entries.append(reversal)
        return reversal

    def entries(self) -> List[Settlement]:
        return list(self._entries)

    def get(self, settlement_id: str) -> Settlement:
        for e in self._entries:
            if e.settlement_id == settlement_id:
                return e
        raise KeyError(settlement_id)
