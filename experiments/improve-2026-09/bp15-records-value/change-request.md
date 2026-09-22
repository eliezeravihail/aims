# Change request: platform fee + preview

Extend `payouts.py`. Keep existing behavior working.

1. **Platform fee.** `settle(settlement_id, total_cents, shares, platform_fee_bps=0)` — before the total is
   split among the payees, deduct a platform fee of `platform_fee_bps` basis points of `total_cents`
   (1 bp = 1/10000), rounded **down** to the cent. The fee becomes an additional payout row with
   `payee_id = "platform"`. The remaining amount is split among the payees in `shares` as before.
   The returned rows (payees **plus** the platform row) must sum **exactly** to `total_cents`.
   If `platform_fee_bps` is `0`, behavior is unchanged and **no** platform row is added.

2. **Preview.** `settle_preview(total_cents, shares, platform_fee_bps=0)` — returns the payout rows that
   *would* be produced, **without recording anything**.

Money is integer cents throughout. No external dependencies.
