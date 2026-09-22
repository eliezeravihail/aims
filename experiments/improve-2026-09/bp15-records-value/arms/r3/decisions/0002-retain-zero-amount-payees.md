# 0002 — zero-amount payees stay in the result

- Status: accepted

## The doubt

A payee whose share rounds to 0 (or whose weight is 0) produces a `Payout(p, 0)` row. Emitting rows worth
nothing looks like noise, and the first instinct — ours included — is to filter them out.

## Decision

**Keep every payee in the result, including zero amounts.** The result has exactly one row per payee in
`shares`, always.

## Rejected alternative (and why)

- **Filter out zero rows.** Cleaner output, and nothing in this module notices the difference. But the
  downstream reconciliation job joins payouts against the expected payee roster and treats a *missing* row as
  "settlement incomplete — hold the batch", while a zero row is a valid settled-nothing. Filtering silently
  stalled a payout batch. The cost of the wrong choice is entirely outside this file, which is why nothing
  here warns you.

## Consequence

The row-per-payee property is a contract, not an artifact. **Any change must not drop rows**, including when
a new deduction pushes a payee to zero.
