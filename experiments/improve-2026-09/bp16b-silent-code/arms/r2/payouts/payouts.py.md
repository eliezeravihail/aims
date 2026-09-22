# payouts.py

## Insights
- This module looks self-contained and is not. Three house rules that bind every change here live outside
  it: rate math belongs to `common.money.bps_of` (`decisions/0001`), new public operations must be listed in
  `common/registry.py` (`decisions/0002`), and a fee is never a synthetic payee (`decisions/0003`).
- `payouts/refunds.py` is the reference for how a rate is applied in this service.

## Decisions
- Rate arithmetic via `common.money.bps_of`, never inlined — `decisions/0001`.
- New public operations registered in `common/registry.py` — `decisions/0002`.
- A fee is deducted before the split, never given a weight in `shares` — `decisions/0003`.
- The platform fee is computed once in `_rows`, which `settle` and `settle_preview` share, so the
  preview cannot drift from what is actually recorded — `settle_preview` is registered as
  `payouts.settle_preview` per `decisions/0002`.

## Discussions
- `_rows` calls `common.money.bps_of` unconditionally, so a rate above 100% or a negative total is
  rejected on every settlement rather than only on fee-bearing ones.
- `_allocate` gives the whole rounding leftover to the largest-share payee. That is deliberate (the lead
  partner is the residual party by contract) and is the precise reason a fee must not sit in `shares`.
