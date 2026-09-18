"""The ledger: posts balanced transactions and tracks account balances.
A transaction is a list of Entry that (1) are all in the same currency and
(2) whose amounts sum to 0 (double-entry, within that currency)."""
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
        """Post a valid transaction: one currency, entries summing to zero.

        This is the single owner of transaction validity — both the
        same-currency rule and the double-entry (sum-to-zero) rule live here.
        """
        currencies = {e.currency for e in entries}
        if len(currencies) > 1:
            raise ValueError(
                f"mixed-currency transaction: {sorted(currencies)}; "
                f"a transaction must be a single currency")
        total = sum(e.amount for e in entries)
        if total != 0:
            raise ValueError(f"unbalanced transaction: sums to {total}, not 0")
        for e in entries:
            self.accounts[e.account_id].apply(e.amount, e.currency)
        self.transactions.append(entries)

    def balance(self, account_id, currency="USD"):
        return self.accounts[account_id].balance(currency)
