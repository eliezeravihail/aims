import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from ledger import Ledger


def test_balance_is_sum_of_entries():
    L = Ledger()
    L.post("alice", 1000, "open")
    L.post("alice", -250, "coffee")
    assert L.balance("alice") == 750


def test_unknown_account_is_zero():
    assert Ledger().balance("nobody") == 0
