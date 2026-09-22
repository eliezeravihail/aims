# 0001 — all rate arithmetic goes through `common.money.bps_of`

- Status: accepted

## Decision
Any basis-point / percentage arithmetic in this service calls `common.money.bps_of(amount, bps)`.
Never inline `amount * bps // 10000` (or any variant) at the call site.

## Why
`bps_of` carries the house guards: it rejects a rate outside `0..10000` and a negative amount instead of
producing a silently wrong figure. Inlined rate math shipped twice without those guards — once a negative
amount produced a negative "fee" that flowed into a payout, once a rate above 100% produced negative payee
amounts that still summed correctly and so passed every conservation check.

The inline one-liner is the obvious thing to write and it looks harmless. It is the thing we are ruling out.

## Consequence
A new deduction, fee, penalty or rate of any kind in `payouts.py` imports and calls
`common.money.bps_of`. `payouts/refunds.py` is the reference example.
