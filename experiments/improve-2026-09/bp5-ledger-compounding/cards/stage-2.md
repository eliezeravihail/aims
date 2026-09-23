# Stage 2 — multi-currency

Extend `ledger.py`. Accounts can now hold amounts in multiple currencies, tracked separately.

## API changes (backward compatible)
```python
    def post(self, account: str, amount_cents: int, currency: str = "USD") -> str:
        """As before, now tagged with a currency (default 'USD')."""
    def balance(self, account: str, currency: str = "USD") -> int:
        """Balance of account IN THAT currency (sum of that currency's postings). 0 if none. Default 'USD'."""
```
- R4 balances are per (account, currency); currencies never mix. Existing single-currency calls behave as USD.
