---
title: "architecture"
date: 2026-09-20
---
## Insights
- The one consequential, hard-to-reverse choice at stage 1 is **where the source of truth lives**:
  is a balance an authoritative stored number, or is it *derived* from the postings? The card's R1
  ("balance = sum of postings") names the postings as ground truth, so the ledger is modelled as an
  **append-only journal of postings** and every balance is a **pure derivation** over that journal.
  Nothing stores a running total, so there is no second copy of the truth that could drift out of sync
  with the postings — the R1 invariant holds *by construction*, not by maintenance.

## Decisions
- **One owner for R1/R4 (balance = sum of matching postings).** Balance is computed in exactly one
  place — `Ledger.balance`, by summing the amounts of the journal's postings for that account. There is
  no parallel per-account total to keep in step; this is the single home of the rule. When later stages
  add operations that change balances (e.g. reversals), they add *postings* to the journal rather than
  adjusting a stored total, so R1 keeps its one owner. **Multi-currency (R4) was absorbed inside this
  owner**, not beside it: `balance` sums postings matching *both* account and currency, so "currencies
  never mix" is guaranteed by the same by-construction derivation — no second, trailing per-currency
  filter and no reopen. **Point-in-time balance (R5) was absorbed the same way**: `balance` gained an
  `as_of` bound as one more predicate clause in the same sum (account AND currency AND `at <= as_of`), so
  the as-of cut is derived by construction inside the one owner — again no trailing filter, no reopen.
  **Void (R6) was absorbed the same way — as a derivation exclusion, not by adding a posting.** The earlier
  note here ("later operations that change balances add postings rather than adjusting a total") holds for a
  *reversal* (a movement / counter-posting stamped at its own time); a **void** is a different concept — a
  retroactive nullification that must erase a posting's effect at *every* as-of instant — so it is owned as
  one more predicate clause in `balance` (`p.id not in self._voided`), keeping R1 derived by construction.
  The voided posting stays in the append-only journal; `self._voided` is a `set` of skipped ids, not a
  second balance store. See `ledger.py.md` for why a counter-posting would be value-wrong for intermediate
  as-of queries.
- **The posting is a first-class value object, not a raw tuple.** The journal holds `Posting` values
  (an immutable record of `id`, `account`, `amount_cents`, `currency`), so the journal is self-describing
  and later stages can extend a posting (e.g. a timestamp, a reversal link) at one type rather than
  threading a wider tuple through call sites. This is the domain's core unit of record; it earns its
  place. **The `currency` field is the first realization of this extension seam** — multi-currency was
  added by widening the one value type, exactly as anticipated, with no change to the journal's shape or
  the derived-balance model. **The `at` field is the second realization of the same seam** — the integer
  posting time was added by widening the one value type again (exactly the "timestamp" this record
  anticipated), with no change to the journal's shape or the derived-balance model.
- **Ids are opaque and unique (R2), sourced independently of ordering.** `post` mints each id with
  `uuid.uuid4().hex`. It is opaque (a caller cannot parse ordering or count out of it) and unique across
  the ledger. This is preferred over a monotonic counter, which would be unique but *transparent* —
  leaking creation order and the number of postings, i.e. not opaque.
- **Module skeleton (buildable shape).** One module `ledger.py`, Python 3, stdlib only. Public seam:
  `Ledger.__init__(self) -> None`,
  `Ledger.post(self, account: str, amount_cents: int, currency: str = "USD") -> str`,
  `Ledger.balance(self, account: str, currency: str = "USD") -> int`. The `currency` parameter defaults
  to "USD", so the stage-1 two-argument seam remains call-compatible. `Posting` is an internal value type
  (an implementation detail behind the seam; not part of the published API the external test suite imports).

## Discussions
- **Stored running total vs derived balance — rejected: stored.** A `dict[account -> int]` running total
  gives O(1) balance but creates a second source of truth that must be updated in lockstep with the
  postings; it is the classic dual-bookkeeping drift risk and is *concept-wrong* (it makes the balance
  authoritative when R1 says the postings are). The card states no performance requirement, so the O(n)
  derivation is not a cost worth taking that risk for. Derived balance chosen.
- **Per-account index vs a single journal list — chose a single list.** A `dict[account -> list]` index
  would speed up `balance` but is a second structure to keep in sync with the append-only journal, for a
  performance need the card does not state. A single append-only `list[Posting]` is the concept-correct,
  minimal representation of a journal; the index can be added later behind the unchanged seam if a real
  performance force appears. (Subtractive pass: the index pays for nothing today.)
- **uuid4 uniqueness is statistical, not counter-guaranteed.** uuid4's collision probability (~2^-122)
  is negligible for an in-memory ledger, and it is the honest way to get an *opaque* token. The
  alternative that guarantees uniqueness deterministically — a counter — was rejected because it defeats
  opacity (R2). Recorded as a conscious trade-off, not an oversight.
