"""Existing behavior (single currency). Ships with the code."""
from ledger import Ledger
from model import Entry
import api
import report


def _fresh():
    lg = Ledger()
    lg.open_account("cash", "Cash")
    lg.open_account("rev", "Revenue")
    return lg


def test_transfer_and_balances():
    lg = _fresh()
    api.transfer(lg, "rev", "cash", 1000)
    assert lg.balance("cash") == 1000
    assert lg.balance("rev") == -1000


def test_trial_balance_is_zero():
    lg = _fresh()
    api.transfer(lg, "rev", "cash", 1000)
    api.transfer(lg, "cash", "rev", 300)
    assert report.trial_balance(lg) == 0


def test_unbalanced_rejected():
    lg = _fresh()
    try:
        lg.post([Entry("cash", 500), Entry("rev", -400)])
    except ValueError:
        return
    assert False, "expected ValueError on unbalanced transaction"


def test_statement():
    lg = _fresh()
    api.transfer(lg, "rev", "cash", 1000)
    lines, bal = report.statement(lg, "cash")
    assert lines == [1000] and bal == 1000


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print("ok", n)
    print("all base ledger tests passed")
