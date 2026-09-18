"""Core domain: accounts and entries. Single currency assumed throughout —
every amount is a bare integer of minor units (cents). Plain style."""


class Account:
    def __init__(self, account_id, name):
        self.id = account_id
        self.name = name
        self.balance = 0  # cents

    def apply(self, amount):
        self.balance += amount


class Entry:
    """One leg of a transaction: a signed amount against an account."""
    def __init__(self, account_id, amount):
        self.account_id = account_id
        self.amount = amount  # cents, signed
