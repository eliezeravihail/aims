# Decisions & discussions

The deliberations behind this project — only what the code and its own documentation cannot convey.
Read this file in full; it is meant to stay short. If something here is obvious from the code, delete it.

---

## Undoing / correcting a settlement: we recompute, we do not replay

**Looks like:** `settle` writes `self._done[settlement_id]` but never reads it before computing — as if an
idempotency guard was forgotten and the store were write-only.

**It is deliberate.** The industry-standard idempotency-key pattern (a repeat request replays the stored
response) is what everyone here expected, us included. We do not do it.

**Why — and none of this is in the code:** upstream issues **corrections**, and a corrected settlement keeps
the **same id** on purpose, because the downstream ledger is append-only and reconciles latest-wins.
Replaying the stored split would keep reporting the pre-correction numbers forever while the ledger
reconciles against figures we never recomputed.

**Rejected:** adding `if settlement_id in self._done: return ...`. It was added once in good faith and froze
three corrected settlements at their stale split; found a week later in reconciliation. Do not add it.

---

## The rounding remainder goes to the largest-share payee

**Looks like:** a systematic fairness bug — the same (largest) partner gains a cent on every settlement.

**Why:** the partner agreement makes the **lead partner** the residual party; it absorbs rounding in both
directions and reconciles the residue on its own statement. Spreading the residue "fairly" sends unexplained
one-cent differences to partners who have no line item for them, and each one opens a ticket.

**Rejected:** largest-remainder with an id tie-break (the neutral, standard choice — wrong *here*, not
wrong in general); round-robin across settlements (needs state we deliberately do not keep).

---

## Zero-amount rows are dropped

**Looks like:** silent data loss — N payees in, fewer rows out.

**Why:** the emitted rows go straight to the **payment rail**, which rejects a zero-amount transfer and
rejects the **whole batch** with it. One zero row fails every payout in that batch. The rail is third-party
and cannot be made lenient; this is the only place that knows the rows are rail-bound.

**Rejected:** one row per payee including zeros (the natural, lossless choice). It shipped once and failed an
evening batch on `AMOUNT_MUST_BE_POSITIVE`. A new fee is exactly the kind of change that pushes a payee to
zero — keep them out of the emitted rows.
