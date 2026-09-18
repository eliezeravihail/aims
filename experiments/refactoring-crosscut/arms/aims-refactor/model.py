"""Core domain: accounts and entries. Every amount is a bare integer of minor
units (cents) and carries a 3-letter currency code (a bare string, default
"USD"); amount and currency travel as separate primitives, plain style. An
account holds one balance per currency, independently."""


class Account:
    def __init__(self, account_id, name):
        self.id = account_id
        self.name = name
        self.balances = {}  # currency -> cents; missing currency reads as 0

    def apply(self, amount, currency="USD"):
        self.balances[currency] = self.balances.get(currency, 0) + amount

    def balance(self, currency="USD"):
        return self.balances.get(currency, 0)


class Entry:
    """One leg of a transaction: a signed amount in a currency against an account."""
    def __init__(self, account_id, amount, currency="USD"):
        self.account_id = account_id
        self.amount = amount  # cents, signed
        self.currency = currency  # 3-letter code
