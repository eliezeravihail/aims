"""Application operations over the ledger. Single currency assumed."""
from model import Entry


def transfer(ledger, src_id, dst_id, amount):
    """Move `amount` (cents) from src to dst as one balanced transaction."""
    if amount <= 0:
        raise ValueError("transfer amount must be positive")
    ledger.post([Entry(src_id, -amount), Entry(dst_id, amount)])
