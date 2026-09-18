# Blind design review — multi-currency cross-cutting change (X vs Y)

Sealed mapping (revealed after scoring): **X = plain, Y = aims-refactor**. Judged blind, on the base's plain
grain (bare int cents, currency as a bare string). Both arms passed the 10-check oracle + existing tests.

## Result: essentially a TIE (plain by a hair on one arguably-out-of-scope point)

- **model.py, ledger.py, api.py — equivalent** (the load-bearing 75% of the change). Both absorb the one
  forced representation change (Account int -> per-currency `balances` dict) in one place; both own the
  same-currency-per-transaction rule solely in `Ledger.post` (beside sum-to-zero); both keep currency a bare
  string default "USD" — neither imports a `Money`/`Currency` value object (the plain grain held; no
  over-abstraction regression).
- **report.py — the only real difference, and it splits:**
  - **aims (Y) wins DRY:** `trial_balance` is a thin wrapper over `trial_balance_by_currency` (grouping logic
    in ONE place, backward-compat a 2-line guard). plain (X) repeats the per-currency summing expression in
    both `trial_balance` and `trial_balance_by_currency` — a benign, non-divergent duplication.
  - **plain (X) wins coherence:** it made `statement` currency-aware (filters lines by currency, returns the
    matching-currency balance). aims (Y) left `statement` unchanged — faithful to "preserve out-of-scope"
    (the card never named statement), but on multi-currency data its `lines` span all currencies while the
    returned balance is USD-only: a latent reconciliation incoherence.
- **Verdict: plain narrowly, close to a tie.** Avoiding the latent `statement` incoherence edges out the DRY
  tidiness. But the judge notes: if `statement` is out of scope (the card never named it, and aims preserved
  the single-currency API verbatim), the verdict flips to aims on the DRY point. The heart of the change
  (model/ledger/api) is equally strong in both.

## The lesson (folded into the doc)
aims left `statement` alone under "preserve out-of-scope" (§4), when it should have re-traced it under §6: an
existing reader that now runs on the change's NEW data shape is an implied interaction, even if the card
never named it. `refactoring-principles.md` §6 sharpened to say so.
