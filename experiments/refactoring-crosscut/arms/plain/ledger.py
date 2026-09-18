"""The ledger: posts balanced transactions and tracks per-currency account balances.
A transaction is a list of Entry that all share one currency and whose amounts sum
to 0 (double-entry within the currency)."""
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
        """Post a balanced, single-currency transaction (entries sum to zero)."""
        currencies = {e.currency for e in entries}
        if len(currencies) > 1:
            raise ValueError(f"mixed-currency transaction: {sorted(currencies)}")
        total = sum(e.amount for e in entries)
        if total != 0:
            raise ValueError(f"unbalanced transaction: sums to {total}, not 0")
        for e in entries:
            self.accounts[e.account_id].apply(e.amount, e.currency)
        self.transactions.append(entries)

    def balance(self, account_id, currency="USD"):
        return self.accounts[account_id].balance(currency)
