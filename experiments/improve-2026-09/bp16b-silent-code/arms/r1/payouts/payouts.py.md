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
- The platform fee is `bps_of(total, platform_fee_bps)`, deducted from the total before `_allocate`
  and appended as a `PLATFORM_PAYEE_ID` row; a zero rate adds no row — `decisions/0003`.
- `settle_preview` is `settle` without the recording step: both build their rows through `_rows`, so
  a preview can never drift from what settling produces. Registered — `decisions/0002`.

## Discussions
- `_allocate` gives the whole rounding leftover to the largest-share payee. That is deliberate (the lead
  partner is the residual party by contract) and is the precise reason a fee must not sit in `shares`.
- `_rows` returns `[]` for an empty/zero weight table, as `_allocate` always has, and skips the
  conservation check in that one degenerate case; whenever there is anything to split it asserts the
  rows sum to the original total via `common.money.assert_conserved`.
