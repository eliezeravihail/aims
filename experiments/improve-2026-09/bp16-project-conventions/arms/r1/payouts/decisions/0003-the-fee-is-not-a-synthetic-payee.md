# 0003 — a platform fee is NOT modelled as a synthetic payee weight

- Status: accepted

## The elementary solution we rejected

The obvious way to add a platform cut to a weighted split is to put the platform in as another payee: give
it a weight alongside the real payees and let `_allocate` divide everything in one pass. It is less code,
it reuses the allocator exactly, and the total still conserves. We tried it. **Do not do it again.**

## Why it is wrong here

`_allocate` hands its rounding leftover to the largest-share payee. With the platform in the weight table,
the platform becomes eligible to receive that leftover — so the fee is no longer the fee: it is the fee plus
or minus a rounding cent, varying by settlement. Finance reconciles the platform cut against an exact
expected figure (`rate × total`), and a fee that wanders by a cent fails that reconciliation every time.
A share-weighted platform also silently changes every payee's amount, because the denominator grows.

## Decision
A fee is **deducted from the total before** the split, and emitted as its own row. The payees then divide
what remains. The fee amount must equal `bps_of(total, rate)` exactly, untouched by the remainder rule.

## Consequence
Never add the platform (or any fee recipient) to `shares`. Deduct first, split the remainder, append the
fee row.
