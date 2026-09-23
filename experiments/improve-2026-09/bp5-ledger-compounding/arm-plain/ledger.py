"""In-memory accounting ledger (stage 1).

A Ledger records postings against named accounts. Each posting has an
amount in integer cents (which may be negative), a currency, a time, and
gets a unique, opaque id. An account's balance is the sum of its postings
in a given currency; currencies are tracked separately and never mix.
"""

from __future__ import annotations

import itertools


class Ledger:
    """A minimal in-memory accounting ledger.

    Postings are stored as (id, amount_cents, currency, at) tuples grouped
    by account. Balances are computed by summing an account's posting
    amounts for a single currency, so an account with no postings in that
    currency has a balance of 0. Each posting carries an integer time
    ``at``; a balance may be queried as of a point in time.
    """

    def __init__(self) -> None:
        # account name -> list of (posting_id, amount_cents, currency, at)
        self._postings: dict[str, list[tuple[str, int, str, int]]] = {}
        # monotonic counter backing the opaque posting ids
        self._ids = itertools.count(1)
        # ids of voided postings; excluded from every balance
        self._voided: set[str] = set()

    def post(
        self, account: str, amount_cents: int, currency: str = "USD", *, at: int = 0
    ) -> str:
        """Record a posting against ``account`` and return its unique id.

        ``amount_cents`` may be negative. ``currency`` tags the posting and
        defaults to ``"USD"``. ``at`` stamps the posting with an integer
        time (default ``0``). The returned id is opaque (its format is not
        part of the contract) and unique across the ledger.
        """
        posting_id = f"p{next(self._ids)}"
        self._postings.setdefault(account, []).append(
            (posting_id, amount_cents, currency, at)
        )
        return posting_id

    def balance(
        self, account: str, currency: str = "USD", *, as_of: int | None = None
    ) -> int:
        """Return the sum of ``account``'s postings in ``currency``.

        Only postings tagged with ``currency`` (default ``"USD"``) are
        summed; currencies never mix. When ``as_of`` is given, only
        postings whose time ``at`` is ``<= as_of`` are counted;
        ``as_of=None`` (the default) counts all postings. Returns 0 when
        the account has no matching postings.
        """
        return sum(
            amount
            for _id, amount, cur, at in self._postings.get(account, ())
            if cur == currency
            and _id not in self._voided
            and (as_of is None or at <= as_of)
        )

    def void(self, posting_id: str) -> None:
        """Remove the effect of the posting ``posting_id`` from all balances.

        The voided posting no longer contributes to any balance, whether
        current or queried as of any time; all other postings are
        unaffected. Voiding an unknown or already-voided id is a no-op, so
        this method is idempotent.
        """
        self._voided.add(posting_id)
