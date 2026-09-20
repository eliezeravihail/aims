---
title: "ledger.py"
date: 2026-09-20
hash: "sha256:61f7a32b430cec91ff7ea5be0bb27bbc5c5cfad584d0a50fb1a3fbcbf72800ee"
---
## Insights
- `ledger.py` is the whole stage-1 product: `Ledger` plus its internal `Posting` value type. The file's
  organizing idea is that it holds an **append-only journal** (`_postings`) and derives every balance
  from it — there is no stored per-account total, so R1 (balance = sum of postings) cannot drift.
- `balance` is O(n) over the whole journal (it filters by account each call). This is deliberate: the
  card states no performance requirement, and a single journal avoids a second structure to keep in sync.
  If a real performance force appears later, add a per-account index *behind* the unchanged public seam.

## Decisions
- **Balance is derived, never stored.** `Ledger.balance` is the one owner of R1; it sums the matching
  postings. No running total is kept. Later balance-changing operations must add postings, not adjust a
  total, to preserve this single owner.
- **`Posting` is an internal `NamedTuple`, not part of the public API.** The external test suite imports
  only `Ledger` (with `post`/`balance`); `Posting` is an implementation detail behind the seam. It is a
  value object (not a raw tuple) so the journal is self-describing and extensible at one type — this was
  the revise-round fix for primitive obsession on the core unit of record.
- **Ids: `uuid.uuid4().hex`.** Satisfies R2 (unique + opaque). Chosen over a monotonic counter, which is
  unique but transparent (leaks order/count) and so fails "opaque" — the revise-round fix for id opacity.
- **Currency is a tag on the posting; balance is per (account, currency).** `Posting` gained a
  `currency` field (extended at the one type, exactly the seam `architecture.md` anticipated — no new
  parallel structure, no reopen of a rule's owner). `balance` still owns R1/R4 in one place: it sums the
  postings matching *both* account and currency, so currencies never mix (R4) by the same by-construction
  derivation. `post`/`balance` default `currency="USD"`, so every stage-1 single-currency call is
  unchanged (a USD posting summed by a USD balance). A currency is an attribute of the money movement, not
  a synthetic entity — modelling it as a field keeps it concept-correct.
- **Time is a stamp on the posting; balance is bounded per as-of instant (R5).** `Posting` gained an
  `at: int` field — the second realization of the extension seam, added exactly like `currency` (widen the
  one value type, no new parallel structure, no reopen). `post` gains keyword-only `at: int = 0`; `balance`
  gains keyword-only `as_of: int | None = None` and adds one predicate clause `(as_of is None or p.at <=
  as_of)` inside the *same* comprehension that already owns R1/R4. So `balance` still owns R1/R4/R5 in one
  place, summing postings matching account AND currency AND (when bounded) time — currencies never mix and
  the as-of cut is by the same by-construction derivation, not a trailing filter. Defaults (`at=0`,
  `as_of=None`) leave every stage-1/stage-2 call bit-for-bit unchanged. `at` is an attribute of the money
  movement (an opaque integer ordering, not a clock), modelled as a field — concept-correct, like currency,
  not a synthetic entity. This is an EXTEND at the seam `architecture.md` named ("a timestamp"), not a
  reopen of an owner.

- **Void is a retroactive exclusion, not a reversing posting (R6).** `void(posting_id)` marks a posting
  id as voided in a `set[str]` (`self._voided`); `balance` gained one more predicate clause `p.id not in
  self._voided` inside the *same* comprehension that already owns R1/R4/R5. The voided posting stays in the
  append-only journal (the record is preserved, matching the accounting meaning of "void" — the entry is
  not deleted) but contributes to no balance at any as-of time. This is an EXTEND at the same derivation
  seam that absorbed `currency` and `as_of` — a third exclusion predicate in the one owner — **not** the
  "reversals add postings" mechanism `architecture.md` anticipated. That note was for a *reversal*, which
  is a movement (a counter-posting stamped at its own time). Void is a different concept: it must erase the
  posting's effect uniformly across *all* as-of queries, including instants between the original posting's
  time and any later moment — a counter-posting cannot do that (it only cancels for balances asked at/after
  the reversal's time), so modelling void as a reversing posting would be both concept-wrong and
  value-wrong for intermediate as-of queries. Voiding is idempotent (set membership): an unknown id matches
  no journal entry and excludes nothing; an already-voided id re-adds to the set as a no-op. R1 keeps its
  one owner — `balance` still derives by construction, and `_voided` is metadata about which entries the
  derivation skips, not a second copy of any balance total. R7 (stage-1..3) is bit-for-bit preserved:
  with `_voided` empty the new clause changes nothing.

## Discussions
- **Physically deleting the posting from `_postings` was rejected.** Removing the entry would also make it
  contribute nothing, but it violates the recorded append-only-journal invariant and destroys the audit
  record that the posting ever existed — void in accounting keeps the entry and marks it void. Excluding by
  id at derivation time preserves the journal and is concept-correct.
- **uuid4 uniqueness is statistical.** Collision probability (~2^-122) is negligible for an in-memory
  ledger; this is the accepted cost of an *opaque* token. A counter would guarantee uniqueness but defeat
  opacity, so it was rejected. If a future stage ever needs a hard uniqueness guarantee it can keep a
  `set` of minted ids — not built now, as R2 is met and the set pays for nothing today.
- **Verified against the card at filing** (throwaway smoke run, then deleted): unknown account → `0`;
  `post` returns a `str`; `500` then `-200` → `300`; a negative-only account → negative balance (R3);
  a zero-amount posting is recorded with a valid id; 1000 identical postings yield 1000 distinct ids
  (R2); accounts are isolated; `balance` returns `int` for both empty and populated accounts.
