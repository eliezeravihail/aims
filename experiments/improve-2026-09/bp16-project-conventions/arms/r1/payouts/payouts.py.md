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
- `settle(..., platform_fee_bps=0)` takes the platform fee via `bps_of`, deducts it from the total before
  `_allocate`, and appends it as a `"platform"` row; no row is emitted at 0 bps — `decisions/0001`, `0003`.
- `settle_preview` is the pure form of that calculation (no recording); `settle` records what it returns.
  Both are listed in `common/registry.py` — `decisions/0002`.

## Discussions
- `_allocate` gives the whole rounding leftover to the largest-share payee. That is deliberate (the lead
  partner is the residual party by contract) and is the precise reason a fee must not sit in `shares`.
