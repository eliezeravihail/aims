"""Core domain: accounts and entries. Multi-currency: every amount is a bare
integer of minor units (cents) tagged with a 3-letter currency code (default
"USD"). Plain style — currency is a bare string, not a value object."""


class Account:
    def __init__(self, account_id, name):
        self.id = account_id
        self.name = name
        self.balances = {}  # currency -> cents; the one owner of per-currency bookkeeping

    def apply(self, amount, currency):
        self.balances[currency] = self.balances.get(currency, 0) + amount

    def balance(self, currency):
        return self.balances.get(currency, 0)


class Entry:
    """One leg of a transaction: a signed amount, in a currency, against an account."""
    def __init__(self, account_id, amount, currency="USD"):
        self.account_id = account_id
        self.amount = amount  # cents, signed
        self.currency = currency
