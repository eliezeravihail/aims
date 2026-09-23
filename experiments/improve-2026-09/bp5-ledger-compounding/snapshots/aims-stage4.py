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
    `at` is the integer time the movement is stamped with; a balance asked as of a point in time sums
    only the postings up to it. Kept as a value object (not a raw tuple) so the journal is
    self-describing and later stages can extend a posting at one type. It is an internal type: callers
    of `Ledger` never construct or see it.
    """

    id: str
    account: str
    amount_cents: int
    currency: str
    at: int


class Ledger:
    """An in-memory accounting ledger: record postings, ask an account's balance."""

    def __init__(self) -> None:
        # The single source of truth: an append-only journal of every posting, in the order recorded.
        # Balances are derived from this list; nothing else holds account state.
        self._postings: list[Posting] = []
        # Ids of postings that have been voided. A voided posting stays in the journal (the journal
        # is append-only and keeps the full record) but is excluded from every derived balance, at
        # any as-of time. Not a second copy of balance state — just which journal entries the
        # derivation skips.
        self._voided: set[str] = set()

    def post(
        self, account: str, amount_cents: int, currency: str = "USD", *, at: int = 0
    ) -> str:
        """Record a posting of `amount_cents` against `account` in `currency` at time `at`; return its id.

        `amount_cents` may be negative. `currency` tags the posting's unit (default "USD", the
        stage-1 single-currency behavior). `at` is the integer time the posting is stamped with
        (default 0, so a caller that does not track time places every posting at the same instant and
        sees unchanged balances). The returned id is opaque — a handle callers must not parse.
        """
        posting = Posting(
            id=uuid.uuid4().hex,
            account=account,
            amount_cents=amount_cents,
            currency=currency,
            at=at,
        )
        self._postings.append(posting)
        return posting.id

    def void(self, posting_id: str) -> None:
        """Remove the effect of the posting with `posting_id` from every balance, at any as-of time.

        A voided posting stays in the append-only journal (its record is not deleted) but contributes
        nothing to any balance thereafter — current or `as_of` any point in time — as if it had never
        moved money. This is a retroactive nullification, not a reversing posting: a counter-posting
        would only cancel the original for balances asked at or after the reversal's time, whereas a
        void erases the posting's effect uniformly across all as-of queries. Idempotent: voiding an
        unknown or already-voided id is a no-op (an unknown id matches no journal entry and so excludes
        nothing). Other postings are unaffected.
        """
        self._voided.add(posting_id)

    def balance(self, account: str, currency: str = "USD", *, as_of: int | None = None) -> int:
        """The balance of `account` in `currency`: the sum of its postings in that currency (0 if none).

        Currencies never mix — only postings whose currency matches are summed. `as_of` bounds the sum
        to postings stamped at time `at <= as_of`; `as_of=None` (the default) sums all of them, so a
        caller that does not query point-in-time sees the same balance as before. Voided postings are
        excluded at any as-of time. `currency` defaults to "USD", so a single-currency (stage-1) caller
        sees the same balance as before.
        """
        return sum(
            p.amount_cents
            for p in self._postings
            if p.account == account
            and p.currency == currency
            and p.id not in self._voided
            and (as_of is None or p.at <= as_of)
        )
