"""Reporting over the ledger. Balances are grouped by currency and never summed
across currencies."""


def trial_balance_by_currency(ledger):
    """Total of all account balances, grouped by currency: {currency: cents}.
    Never sums across currencies. In a balanced ledger every value is 0."""
    totals = {}
    for acct in ledger.accounts.values():
        for currency, cents in acct.balances.items():
            totals[currency] = totals.get(currency, 0) + cents
    return totals


def trial_balance(ledger):
    """Sum of all account balances as a single int (in a balanced, single-currency
    ledger this is 0). Raises if the ledger holds more than one currency, since a
    single total would sum across currencies — use trial_balance_by_currency then."""
    totals = trial_balance_by_currency(ledger)
    if len(totals) > 1:
        raise ValueError(
            "ledger holds multiple currencies; use trial_balance_by_currency")
    return next(iter(totals.values()), 0)


def statement(ledger, account_id):
    """The account's entries across all transactions, and its closing balance."""
    lines = []
    for txn in ledger.transactions:
        for e in txn:
            if e.account_id == account_id:
                lines.append(e.amount)
    return lines, ledger.balance(account_id)
