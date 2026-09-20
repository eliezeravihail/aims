# Stage 3 — as-of-time balances

Extend `ledger.py`. Every posting happens at a time, and a balance can be queried as of a point in time.

## API changes (backward compatible)
```python
    def post(self, account, amount_cents, currency="USD", *, at: int = 0) -> str:
        """...now stamped with an integer time `at` (default 0)."""
    def balance(self, account, currency="USD", *, as_of: int | None = None) -> int:
        """Sum of that account+currency's postings whose time `at` <= as_of. as_of=None means all postings."""
```
- R5 balance as_of T counts only postings with at <= T; as_of=None counts all. Existing calls (no at/as_of) unchanged.
