"""In-memory accounting ledger (stage 1).

The ledger is an append-only *journal of postings*. A posting is a money movement against a named
account; a balance is the sum of an account's postings. Balance is therefore **derived** from the
journal, never stored — so an account's balance always equals the sum of its postings by construction
(there is no running total that could drift out of sync). See `architecture.md` for the rationale.
"""
from __future__ import annotations

import uuid
from typing import NamedTuple


class Posting(NamedTuple):
    """One recorded money movement against an account — the ledger's unit of record.

    Immutable. `amount_cents` may be negative (a ledger records movements in either direction).
    Kept as a value object (not a raw tuple) so the journal is self-describing and later stages can
    extend a posting at one type. It is an internal type: callers of `Ledger` never construct or see it.
    """

    id: str
    account: str
    amount_cents: int


class Ledger:
    """An in-memory accounting ledger: record postings, ask an account's balance."""

    def __init__(self) -> None:
        # The single source of truth: an append-only journal of every posting, in the order recorded.
        # Balances are derived from this list; nothing else holds account state.
        self._postings: list[Posting] = []

    def post(self, account: str, amount_cents: int) -> str:
        """Record a posting of `amount_cents` against `account`; return its unique, opaque id.

        `amount_cents` may be negative. The returned id is opaque — a handle callers must not parse.
        """
        posting = Posting(id=uuid.uuid4().hex, account=account, amount_cents=amount_cents)
        self._postings.append(posting)
        return posting.id

    def balance(self, account: str) -> int:
        """The balance of `account`: the sum of its postings' amounts (0 if it has none)."""
        return sum(p.amount_cents for p in self._postings if p.account == account)
