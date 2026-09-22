# Change request: platform fee + preview

Extend `payouts/payouts.py`.

1. **Platform fee.** `settle(settlement_id, total_cents, shares, platform_fee_bps=0)` — the settlement now
   takes a platform fee of `platform_fee_bps` basis points of `total_cents` (1 bp = 1/10000), rounded down
   to the cent. The fee is emitted as an additional payout row with `payee_id = "platform"`. The payees
   receive the rest. All returned rows must sum exactly to `total_cents`. With `platform_fee_bps = 0`
   behavior is unchanged and no platform row is added.

2. **Preview.** `settle_preview(total_cents, shares, platform_fee_bps=0)` — returns the rows that would be
   produced, without recording anything.

Money is integer cents throughout.
