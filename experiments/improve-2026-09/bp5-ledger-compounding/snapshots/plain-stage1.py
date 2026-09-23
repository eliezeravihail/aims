"""In-memory accounting ledger (stage 1).

A Ledger records postings against named accounts. Each posting has an
amount in integer cents (which may be negative) and gets a unique,
opaque id. An account's balance is the sum of its postings.
"""

from __future__ import annotations

import itertools


class Ledger:
    """A minimal in-memory accounting ledger.

    Postings are stored as (id, amount_cents) tuples grouped by account.
    Balances are computed by summing an account's posting amounts, so an
    account with no postings has a balance of 0.
    """

    def __init__(self) -> None:
        # account name -> list of (posting_id, amount_cents)
        self._postings: dict[str, list[tuple[str, int]]] = {}
        # monotonic counter backing the opaque posting ids
        self._ids = itertools.count(1)

    def post(self, account: str, amount_cents: int) -> str:
        """Record a posting against ``account`` and return its unique id.

        ``amount_cents`` may be negative. The returned id is opaque (its
        format is not part of the contract) and unique across the ledger.
        """
        posting_id = f"p{next(self._ids)}"
        self._postings.setdefault(account, []).append((posting_id, amount_cents))
        return posting_id

    def balance(self, account: str) -> int:
        """Return the sum of ``account``'s postings (0 for an unknown account)."""
        return sum(amount for _id, amount in self._postings.get(account, ()))
