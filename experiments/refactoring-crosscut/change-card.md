# Change request — support multiple currencies

You are handed a small **double-entry ledger** across four modules (`model.py`, `ledger.py`, `api.py`,
`report.py`) plus `test_ledger.py`. Today every amount is a bare integer of cents in a **single, implicit
currency**. Add **multi-currency** support. This touches every module.

## Requirements

- Every amount now carries a **currency** — a 3-letter code like `"USD"`, `"EUR"`. Add a `currency`
  parameter with default `"USD"` wherever an amount enters:
  - `Entry(account_id, amount, currency="USD")`
  - `api.transfer(ledger, src_id, dst_id, amount, currency="USD")`
- An account holds a **balance per currency** — it can hold USD and EUR independently.
  `ledger.balance(account_id, currency="USD")` returns that currency's balance.
- A single transaction's entries must **all be the same currency**; a transaction that mixes currencies is
  rejected with `ValueError`. (Double-entry still holds **within** the currency: the entries sum to zero.)
- Add `report.trial_balance_by_currency(ledger)` → a dict `{currency: total_cents}` (each currency's total
  across all accounts). It must **group by currency and never sum across currencies**.
- **Backward compatibility (do not edit `test_ledger.py`):** the existing single-currency API must keep
  working unchanged — `api.transfer(lg, a, b, amount)`, `ledger.balance(id)`, and `report.trial_balance(lg)`
  behave exactly as today when only the default currency is used (`report.trial_balance(lg)` still returns
  the single int total; you may make it raise if the ledger holds *more than one* currency, directing the
  caller to `trial_balance_by_currency`). The existing `test_ledger.py` must pass **unchanged**.

Deliver the adapted modules (and any tests you add). Keep the code coherent — do not scatter currency checks
and per-currency bookkeeping across the modules in a way that could disagree.
