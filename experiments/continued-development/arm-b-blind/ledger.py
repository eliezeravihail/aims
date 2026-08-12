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
        # Memoized balances derived from _entries. Never an independent field:
        # invalidated on every write so it can always be recomputed from entries.
        self._balance_cache: dict[str, int] = {}

    def post(self, account: str, delta: int, memo: str = "") -> None:
        if delta == 0:
            raise ValueError("zero-delta entry is meaningless")
        self._entries.append(Entry(account, delta, memo))
        # Drop the derived value for the touched account so the next read
        # recomputes it from the authoritative entries.
        self._balance_cache.pop(account, None)

    def balance(self, account: str) -> int:
        # Derived from the append-only entries, memoized per account so repeated
        # lookups are O(1); a cache miss recomputes from the single source of truth.
        cached = self._balance_cache.get(account)
        if cached is not None:
            return cached
        total = sum(e.delta for e in self._entries if e.account == account)
        self._balance_cache[account] = total
        return total

    def entries(self, account: str) -> list[Entry]:
        return [e for e in self._entries if e.account == account]

    def statement(self, account: str) -> tuple[list[Entry], int]:
        """Return the account's entries alongside its closing balance."""
        return self.entries(account), self.balance(account)
