"""The ledger: posts balanced transactions and tracks account balances.
Single currency assumed — a transaction is a list of Entry whose amounts sum to 0
(double-entry)."""
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
        """Post a balanced transaction (entries sum to zero)."""
        total = sum(e.amount for e in entries)
        if total != 0:
            raise ValueError(f"unbalanced transaction: sums to {total}, not 0")
        for e in entries:
            self.accounts[e.account_id].apply(e.amount)
        self.transactions.append(entries)

    def balance(self, account_id):
        return self.accounts[account_id].balance
