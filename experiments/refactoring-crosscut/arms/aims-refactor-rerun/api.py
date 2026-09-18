"""Application operations over the ledger. Amounts carry a currency (default "USD")."""
from model import Entry


def transfer(ledger, src_id, dst_id, amount, currency="USD"):
    """Move `amount` (cents) from src to dst as one balanced transaction, in `currency`."""
    if amount <= 0:
        raise ValueError("transfer amount must be positive")
    ledger.post([Entry(src_id, -amount, currency), Entry(dst_id, amount, currency)])
