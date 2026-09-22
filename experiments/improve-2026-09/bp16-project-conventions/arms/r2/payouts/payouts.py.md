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
- The fee/remainder split lives in `settle_preview`; `Settlements.settle` is that function plus the
  recording step, so a preview can never drift from what a settlement actually pays out.
- The platform row is emitted whenever `platform_fee_bps` is non-zero, even if the fee floors to 0
  cents: the row is the statement that a fee was charged, and finance reconciles against it.

## Discussions
- `settle_preview` asserts conservation at the seam it introduces (`fee + remainder == total`), the way
  `refunds.py` does. The payee rows are left to `_allocate`'s own contract, so degenerate `shares`
  (no positive weight) still return `[]` rather than newly raising.
- `_allocate` gives the whole rounding leftover to the largest-share payee. That is deliberate (the lead
  partner is the residual party by contract) and is the precise reason a fee must not sit in `shares`.
