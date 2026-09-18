"""Reporting over the ledger. Single currency assumed — totals are bare ints."""


def trial_balance(ledger):
    """Sum of all account balances. In a balanced ledger this is 0."""
    return sum(acct.balance for acct in ledger.accounts.values())


def statement(ledger, account_id):
    """The account's entries across all transactions, and its closing balance."""
    lines = []
    for txn in ledger.transactions:
        for e in txn:
            if e.account_id == account_id:
                lines.append(e.amount)
    return lines, ledger.balance(account_id)
