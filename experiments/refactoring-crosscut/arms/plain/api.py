"""Application operations over the ledger. Multi-currency."""
from model import Entry


def transfer(ledger, src_id, dst_id, amount, currency="USD"):
    """Move `amount` (cents) in `currency` from src to dst as one balanced transaction."""
    if amount <= 0:
        raise ValueError("transfer amount must be positive")
    ledger.post([Entry(src_id, -amount, currency), Entry(dst_id, amount, currency)])
