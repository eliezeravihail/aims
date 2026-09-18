"""Reporting over the ledger. Balances are per-currency; totals are grouped by
currency and never summed across currencies."""


def trial_balance_by_currency(ledger):
    """Total of all account balances, grouped per currency: {currency: total_cents}.
    In a balanced ledger every currency's total is 0. Currencies are never summed together."""
    totals = {}
    for acct in ledger.accounts.values():
        for currency, amount in acct.balances.items():
            totals[currency] = totals.get(currency, 0) + amount
    return totals


def trial_balance(ledger):
    """Single-currency trial balance: the sum of all account balances as one int
    (0 in a balanced ledger). Raises if the ledger holds more than one currency,
    since a single cross-currency total is not meaningful."""
    totals = trial_balance_by_currency(ledger)
    if len(totals) > 1:
        raise ValueError(
            f"trial_balance spans multiple currencies {sorted(totals)}; "
            f"use trial_balance_by_currency"
        )
    return next(iter(totals.values()), 0)


def statement(ledger, account_id, currency="USD"):
    """The account's entries in one currency across all transactions, and its closing
    balance in that currency. Scoped to one currency so the listed lines and the
    reported balance are always the same currency (coherent)."""
    lines = []
    for txn in ledger.transactions:
        for e in txn:
            if e.account_id == account_id and e.currency == currency:
                lines.append(e.amount)
    return lines, ledger.balance(account_id, currency)
