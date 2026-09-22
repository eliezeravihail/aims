# payouts.py

## Insights

- Three properties of this module read as defects and are deliberate: it recomputes instead of replaying
  (`decisions/0001`), it gives the whole remainder to the biggest payee (`0002`), and it drops zero rows
  (`0003`). Each was "fixed" once by someone following good instinct, and each fix caused a production
  incident. If you are about to correct one of them, the ADR is the thing to read first.
- `_allocate` is the one owner of division, remainder placement, and which rows exist. A deduction that is
  applied *after* allocation would break the exact-sum property and sit outside all three rules above.

## Decisions

- Repeat settlement **recomputes and overwrites**; no idempotency replay — `decisions/0001`.
- The **whole remainder goes to the largest-share payee** — `decisions/0002`.
- **Zero-amount rows are dropped** (the payment rail rejects the batch) — `decisions/0003`.

## Discussions

- `weight_total <= 0` returns an empty list rather than raising: a settlement with no active payees is a
  normal end-of-month state, and the rail is happy with an empty batch.
- We keep `self._done` even though nothing reads it: it is the audit trail of what this service last computed
  for an id, read by the ops dashboard out-of-process. It is not a cache, and must not become one.
