# Stage 1 — accounting ledger

Build an in-memory accounting ledger as a single module `ledger.py`.

## Public API (exact — the test suite imports these names)
```python
class Ledger:
    def __init__(self) -> None: ...
    def post(self, account: str, amount_cents: int) -> str:
        """Record a posting of amount_cents (may be negative) to account. Return a unique posting id (str)."""
    def balance(self, account: str) -> int:
        """The account's balance in cents = sum of its postings. 0 for an unknown account."""
```
## Rules
- R1 balance(account) = sum of all amounts posted to it (0 if none).
- R2 posting ids are unique and opaque.
- R3 amounts may be positive or negative; balances may be negative.

Deliver `ledger.py` (working Python 3, stdlib only). Build it well.
