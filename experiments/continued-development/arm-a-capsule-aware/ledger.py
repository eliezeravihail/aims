"""A tiny append-only ledger. Balance is DERIVED from the entries, never stored."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    account: str
    delta: int          # positive = deposit, negative = withdrawal (in cents)
    memo: str = ""


@dataclass(frozen=True)
class Statement:
    account: str
    entries: list[Entry]
    closing_balance: int


class Ledger:
    def __init__(self) -> None:
        self._entries: list[Entry] = []   # the single source of truth
        # Memo of balance DERIVED from the entries. Not a second source of truth:
        # every value here is reconstructible by summing self._entries, and any
        # entry is dropped (invalidated) the moment its account is posted to, so
        # the memo can never silently drift (see insights/dev/stored-balance-drift).
        self._balance_memo: dict[str, int] = {}

    def post(self, account: str, delta: int, memo: str = "") -> None:
        if delta == 0:
            raise ValueError("zero-delta entry is meaningless")
        self._entries.append(Entry(account, delta, memo))
        # Invalidate the derived memo for this account. On the next read it is
        # re-derived from the entries, so the entries remain the sole authority.
        self._balance_memo.pop(account, None)

    def balance(self, account: str) -> int:
        # Fast path: O(1) when the memo is warm. Cold reads re-derive from the
        # append-only entries (O(n)) and memoize the result. The memo is purely a
        # cache of that derivation — never an independently mutated field.
        cached = self._balance_memo.get(account)
        if cached is not None:
            return cached
        derived = sum(e.delta for e in self._entries if e.account == account)
        self._balance_memo[account] = derived
        return derived

    def entries(self, account: str) -> list[Entry]:
        return [e for e in self._entries if e.account == account]

    def statement(self, account: str) -> Statement:
        # Entries plus the closing (current) balance, both derived from the
        # single source of truth. Reuses balance() so the memo covers it too.
        return Statement(
            account=account,
            entries=self.entries(account),
            closing_balance=self.balance(account),
        )
