"""The ledger: posts balanced transactions and tracks per-currency account balances.
A transaction's entries must all be one currency, and within that currency their
amounts must sum to 0 (double-entry). Both rules are owned here, in post()."""
from model import Account, Entry


class Ledger:
    def __init__(self):
        self.accounts = {}       # id -> Account
        self.transactions = []   # list of list[Entry]

    def open_account(self, account_id, name):
        acct = Account(account_id, name)
        self.accounts[account_id] = acct
        return acct

    def post(self, entries):
        """Post a balanced single-currency transaction.

        One owner for both transaction rules: all entries must share one currency
        (mixing is rejected), and within that currency the amounts must sum to zero.
        """
        currencies = {e.currency for e in entries}
        if len(currencies) > 1:
            raise ValueError(f"mixed currencies in one transaction: {sorted(currencies)}")
        total = sum(e.amount for e in entries)
        if total != 0:
            raise ValueError(f"unbalanced transaction: sums to {total}, not 0")
        for e in entries:
            self.accounts[e.account_id].apply(e.amount, e.currency)
        self.transactions.append(entries)

    def balance(self, account_id, currency="USD"):
        return self.accounts[account_id].balance(currency)
