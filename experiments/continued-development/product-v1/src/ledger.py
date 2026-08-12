"""A tiny append-only ledger. Balance is DERIVED from the entries, never stored."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    account: str
    delta: int          # positive = deposit, negative = withdrawal (in cents)
    memo: str = ""


class Ledger:
    def __init__(self) -> None:
        self._entries: list[Entry] = []   # the single source of truth

    def post(self, account: str, delta: int, memo: str = "") -> None:
        if delta == 0:
            raise ValueError("zero-delta entry is meaningless")
        self._entries.append(Entry(account, delta, memo))

    def balance(self, account: str) -> int:
        # Derived on read from the append-only entries — deliberately not cached.
        return sum(e.delta for e in self._entries if e.account == account)

    def entries(self, account: str) -> list[Entry]:
        return [e for e in self._entries if e.account == account]
