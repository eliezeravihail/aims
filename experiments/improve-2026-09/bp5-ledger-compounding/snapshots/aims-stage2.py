"""In-memory accounting ledger.

The ledger is an append-only *journal of postings*. A posting is a money movement against a named
account, tagged with a currency; a balance is the sum of an account's postings **in one currency**.
Balance is therefore **derived** from the journal, never stored — so an account's balance always
equals the sum of its matching postings by construction (there is no running total that could drift
out of sync). Currencies never mix: a balance sums only the postings whose currency it asks for.
See `architecture.md` for the rationale.
"""
from __future__ import annotations

import uuid
from typing import NamedTuple


class Posting(NamedTuple):
    """One recorded money movement against an account — the ledger's unit of record.

    Immutable. `amount_cents` may be negative (a ledger records movements in either direction).
    `currency` tags the movement's unit; a balance is asked per currency and never mixes units.
    Kept as a value object (not a raw tuple) so the journal is self-describing and later stages can
    extend a posting at one type. It is an internal type: callers of `Ledger` never construct or see it.
    """

    id: str
    account: str
    amount_cents: int
    currency: str


class Ledger:
    """An in-memory accounting ledger: record postings, ask an account's balance."""

    def __init__(self) -> None:
        # The single source of truth: an append-only journal of every posting, in the order recorded.
        # Balances are derived from this list; nothing else holds account state.
        self._postings: list[Posting] = []

    def post(self, account: str, amount_cents: int, currency: str = "USD") -> str:
        """Record a posting of `amount_cents` against `account` in `currency`; return its opaque id.

        `amount_cents` may be negative. `currency` tags the posting's unit (default "USD", the
        stage-1 single-currency behavior). The returned id is opaque — a handle callers must not parse.
        """
        posting = Posting(
            id=uuid.uuid4().hex, account=account, amount_cents=amount_cents, currency=currency
        )
        self._postings.append(posting)
        return posting.id

    def balance(self, account: str, currency: str = "USD") -> int:
        """The balance of `account` in `currency`: the sum of its postings in that currency (0 if none).

        Currencies never mix — only postings whose currency matches are summed. `currency` defaults to
        "USD", so a single-currency (stage-1) caller sees the same balance as before.
        """
        return sum(
            p.amount_cents
            for p in self._postings
            if p.account == account and p.currency == currency
        )
