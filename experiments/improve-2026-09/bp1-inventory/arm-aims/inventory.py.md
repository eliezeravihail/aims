---
title: "inventory.py"
date: 2026-09-20
hash: "sha256:c5af6be3be800783fa509cdeb8e195babffda23f2ada660be4d188ba0cb8a0be"
---
## Insights
- The load-bearing invariant is the availability rule, and its single owner is `Inventory.available`.
  Availability is **derived** — `added(sku) - reserved(sku, now)` — and never stored as a mutable
  counter. This is what makes R1/R2/R4 structural rather than defended: there is no second copy of
  "available" that could disagree with the reservation ledger.
- Idempotent release (R2 tail / unknown-id no-op) is the reason a reservation must be a first-class
  ledger entry keyed by id, not a bare decrement of a counter: a counter cannot tell whether an id was
  already released, so double-release would inflate availability above added stock (violating R1). The
  ledger + `dict.pop(id, None)` gives idempotency for free.
- Stage 2 (expiry) rides the same derivation seam the architecture named. `expiry` is a **ground fact**
  on the ledger entry, but "expired" is **derived** against the injected `now` — never stored — exactly
  as availability itself is derived and never stored. So R5/R7 are structural, not swept: an expired
  hold is simply not counted by `_reserved(sku, now)`, so releasing it later removes an entry that
  already held zero units and cannot double-count (R7). No background clock, no expiry-sweep pass, no
  stored "expired" flag that could disagree with `now`. R6 (determinism) follows because the only time
  source is the injected `now`; the module reads no wall clock.

## Decisions
- Ground truth is two facts only: `_added[sku]` (total added, monotonic) and `_reservations[id] ->
  _Reservation(sku, qty)` (the outstanding-holds ledger). `available` and `_reserved` are pure
  derivations; nothing else stores an availability number. Owner of the availability rule:
  `Inventory.available` (with `_reserved` naming the "outstanding for sku" term of the rule).
  *(Superseded by the stage-2 decisions below: the ledger entry gains an `expiry` field and the
  derivations gain a `now` parameter; the two-facts-only, derived-not-stored shape is preserved.)*
- **[stage 2]** Expiry is absorbed at the derivation seam, not bolted beside `available`. `_Reservation`
  gains `expiry: Optional[float] = None` (a ground fact: the instant the hold lapses; `None` = never).
  The single "outstanding for sku" term `_reserved` grows a `now` parameter and counts a reservation
  only while `expiry is None or expiry > now`; `available(sku, *, now=0.0)` threads `now` through to it.
  The availability rule keeps its one owner — the rule `available == added - reserved` is unchanged; only
  the definition of `reserved` became time-aware. No parallel "expired filter" path was added (that would
  be a second owner of holdings). This is the seam extension `architecture.md` anticipated ("extend
  behind the ground-truth representation without reopening `available`'s rule").
- **[stage 2]** Time is **injected**, never read. `available`/`reserve` take `*, now: float = 0.0`; the
  default 0.0 makes every stage-1 call (`reserve(sku, qty)`, `available(sku)`) behave bit-for-bit as
  before, since with `expiry=None` throughout the `now` value is inert. `reserve` gains a positional
  `ttl_seconds: Optional[float] = None`; when given, `expiry = now + ttl_seconds` (so `ttl_seconds=0`
  expires at `now`), and validation runs against `available(sku, now=now)` so units freed by
  already-expired holds are reservable at `now`.
- **[stage 2]** Expiry is modelled as a **lifetime on the reservation** (an instant from which the hold
  ceases), not as a synthetic ledger entry or a stored expired-state. The "expired" condition is a
  derived predicate on `(expiry, now)`, matching how availability is derived — no inert stand-in.
- **[stage 3]** `confirm(id)` makes a hold **permanent by reusing the `expiry is None` representation**
  — it `_replace`s the ledger entry's `expiry` with `None`, adding no new state. "Confirmed" *is*
  "permanent", and "permanent" already meant `expiry is None`, so a separate `confirmed` flag would be
  a second, redundant representation of permanence that `_reserved` would have to consult — a concept
  cram (an inert stand-in) and a second owner of the expiry rule. Setting expiry to None keeps the one
  owner: `_reserved` already counts an `expiry is None` hold at every `now`, so R8 is structural, not a
  new branch. Confirm reads via `dict.get`, so an unknown/released id is a no-op and cannot resurrect a
  released hold.
- **[stage 3]** `reserve_up_to(sku, qty, *, now)` is a **best-effort sibling** of `reserve`, not a flag
  on it: it validates `qty > 0`, then records `min(qty, available(sku, now))` units. It reads the
  availability owner (`available`) and takes the min rather than re-deriving or adding a parallel
  path — so R9 (`reserved_qty == min(qty, available)`) and R1 (the hold always fits) are structural.
  It never raises InsufficientStock; the requirement to return a real id even when 0 units are
  available means a **0-unit hold is a genuine ledger entry** (releasable/confirmable, counted as 0 by
  `_reserved`), uniform with any other hold — a degenerate qty, not an inert concept stand-in. The hold
  is permanent (`expiry=None`); `reserve_up_to` takes no ttl.
- **[stage 3]** Extracted `_record(sku, qty, expiry) -> str` as the **single ledger-write seam**
  (behavior-preserving refactor first, per "make the change easy, then make the easy change"): id
  generation + the `self._reservations[id] = _Reservation(...)` write now live in one owner, and both
  `reserve` (after its availability check) and `reserve_up_to` (with an already-fitted qty) commit
  through it. `reserve`'s validate-before-record order (R4 all-or-nothing) is unchanged — validation
  still runs before `_record` is called.
- `reserve` validates (qty > 0, then qty <= available) **before** any mutation, then records — giving
  R4 all-or-nothing on both the ValueError and the InsufficientStock path.
- `add_stock` and `reserve` reject qty <= 0 at the boundary with `ValueError` (fail fast); the card
  states add qty as > 0, treated here as a precondition.
- Reservation ids are `uuid4().hex` (opaque, R3) with a regeneration loop guarding against collision
  so uniqueness is structural, not merely probabilistic.

## Discussions
- Availability could be kept as an O(1) per-sku counter incremented/decremented on reserve/release
  instead of summed over the ledger. Rejected: that reintroduces a second stored copy of the
  availability fact that must be kept in sync with the ledger — two owners, drift risk — to buy a
  performance win no stage-1 requirement asks for. The derived form keeps one owner; `_reserved`'s
  O(n-reservations) scan is acceptable absent any performance requirement.
- `_Reservation` is a 2-field NamedTuple rather than a plain tuple: it costs nothing and names the
  `(sku, qty)` pair as the concept it is. It deliberately owns no behavior/rule — the availability
  rule lives in `Inventory`, not in the reservation — so it is not an anemic-model smell, just a typed
  record. A bare tuple would have been equally correct; the named form was kept for readability only.
