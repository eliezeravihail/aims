---
title: "ledger.py"
date: 2026-09-20
hash: "sha256:2826cd19a689171661d5bf4abf404b22ca936d94a6e6c1b4ed5725b33858f8ae"
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

## Discussions
- **uuid4 uniqueness is statistical.** Collision probability (~2^-122) is negligible for an in-memory
  ledger; this is the accepted cost of an *opaque* token. A counter would guarantee uniqueness but defeat
  opacity, so it was rejected. If a future stage ever needs a hard uniqueness guarantee it can keep a
  `set` of minted ids — not built now, as R2 is met and the set pays for nothing today.
- **Verified against the card at filing** (throwaway smoke run, then deleted): unknown account → `0`;
  `post` returns a `str`; `500` then `-200` → `300`; a negative-only account → negative balance (R3);
  a zero-amount posting is recorded with a valid id; 1000 identical postings yield 1000 distinct ids
  (R2); accounts are isolated; `balance` returns `int` for both empty and populated accounts.
