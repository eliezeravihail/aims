"""Reporting over the ledger. Multi-currency: totals are grouped by currency and
never summed across currencies."""


def _currencies(ledger):
    """Every currency that appears in any account balance."""
    seen = set()
    for acct in ledger.accounts.values():
        seen.update(acct.balances.keys())
    return seen


def trial_balance(ledger, currency=None):
    """Sum of all account balances for a single currency. In a balanced ledger
    this is 0. For backward compatibility `currency` defaults to the ledger's
    sole currency (USD if empty); raises if the ledger holds more than one and no
    currency is named."""
    if currency is None:
        present = _currencies(ledger)
        if len(present) > 1:
            raise ValueError(
                f"trial_balance is ambiguous across currencies {sorted(present)}; "
                "use trial_balance_by_currency or pass currency=")
        currency = next(iter(present)) if present else "USD"
    return sum(acct.balance(currency) for acct in ledger.accounts.values())


def trial_balance_by_currency(ledger):
    """Per-currency trial balance: {currency: total_cents}. Never sums across
    currencies. In a balanced ledger every value is 0."""
    totals = {}
    for currency in _currencies(ledger):
        totals[currency] = sum(acct.balance(currency) for acct in ledger.accounts.values())
    return totals


def statement(ledger, account_id, currency="USD"):
    """The account's entries in `currency` across all transactions, and its
    closing balance in that currency."""
    lines = []
    for txn in ledger.transactions:
        for e in txn:
            if e.account_id == account_id and e.currency == currency:
                lines.append(e.amount)
    return lines, ledger.balance(account_id, currency)
