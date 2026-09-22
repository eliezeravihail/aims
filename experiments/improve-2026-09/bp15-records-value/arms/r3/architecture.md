# Architecture

Two elements:

- `_allocate(total, shares)` — the **single owner of the sum invariant**. It is the only place that decides
  how the total is divided and where the remainder lands. Nothing outside it may adjust a payout amount.
- `Settlements` — owns settlement identity and the once-only guarantee. It stores the *result*, and answers a
  repeat settlement from that store.

Change axes we expect: new deduction kinds (fees), new preview/dry-run entry points. Both must go *through*
`_allocate`, never around it — the sum invariant has one owner and adding a second adjustment site is how the
penny drift returns.
