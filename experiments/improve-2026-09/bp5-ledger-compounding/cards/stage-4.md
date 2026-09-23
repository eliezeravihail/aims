# Stage 4 — void a posting

Extend `ledger.py`. A posting can be voided (its effect removed).

## API addition
```python
    def void(self, posting_id: str) -> None:
        """Remove the effect of the posting with this id from all balances. Voiding an unknown or
        already-voided id is a no-op (idempotent)."""
```
- R6 after void(id), that posting contributes nothing to any balance (current or as-of any time >= its own).
  All other postings unaffected. R7 all stage-1..3 behavior preserved.
