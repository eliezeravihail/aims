"""In-memory accounting ledger (stage 1).

A Ledger records postings against named accounts. Each posting has an
amount in integer cents (which may be negative), a currency, and gets a
unique, opaque id. An account's balance is the sum of its postings in a
given currency; currencies are tracked separately and never mix.
"""

from __future__ import annotations

import itertools


class Ledger:
    """A minimal in-memory accounting ledger.

    Postings are stored as (id, amount_cents, currency) tuples grouped by
    account. Balances are computed by summing an account's posting amounts
    for a single currency, so an account with no postings in that currency
    has a balance of 0.
    """

    def __init__(self) -> None:
        # account name -> list of (posting_id, amount_cents, currency)
        self._postings: dict[str, list[tuple[str, int, str]]] = {}
        # monotonic counter backing the opaque posting ids
        self._ids = itertools.count(1)

    def post(self, account: str, amount_cents: int, currency: str = "USD") -> str:
        """Record a posting against ``account`` and return its unique id.

        ``amount_cents`` may be negative. ``currency`` tags the posting and
        defaults to ``"USD"``. The returned id is opaque (its format is not
        part of the contract) and unique across the ledger.
        """
        posting_id = f"p{next(self._ids)}"
        self._postings.setdefault(account, []).append(
            (posting_id, amount_cents, currency)
        )
        return posting_id

    def balance(self, account: str, currency: str = "USD") -> int:
        """Return the sum of ``account``'s postings in ``currency``.

        Only postings tagged with ``currency`` (default ``"USD"``) are
        summed; currencies never mix. Returns 0 when the account has no
        postings in that currency.
        """
        return sum(
            amount
            for _id, amount, cur in self._postings.get(account, ())
            if cur == currency
        )
