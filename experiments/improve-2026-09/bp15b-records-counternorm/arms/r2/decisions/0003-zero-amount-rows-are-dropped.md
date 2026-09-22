# 0003 — zero-amount rows are dropped from the result

- Status: accepted

## What this looks like

`_allocate` ends with `... if base[p] > 0`, silently discarding payees that came out at zero. It looks like
data loss: the caller passed N payees and got fewer rows back, with nothing said about it.

## The doubt, and the decision

"Never silently drop rows" is the rule we would normally follow, and a row-per-payee result is what a caller
expects. We deliberately do the opposite: **a payee that settles to zero is not emitted at all.**

## Why (this rationale exists nowhere in the code)

The emitted rows go straight to the **payment rail**, which rejects a zero-amount transfer — and it rejects
the **whole batch**, not the offending row. One zero row fails every payout in that batch. The rail is a
third-party API we do not control and cannot make lenient. Filtering here is the only place that knows the
rows are rail-bound.

## Rejected alternative

- **Keep one row per payee, including zeros** — the natural, "lossless" choice, and the one that will be
  proposed. It was shipped once and failed an entire evening batch on the rail's `AMOUNT_MUST_BE_POSITIVE`.

## Consequence

Any change that can push a payee's amount to zero — **a new fee is exactly such a change** — must keep that
payee out of the emitted rows. Do not "restore" zero rows for completeness.
