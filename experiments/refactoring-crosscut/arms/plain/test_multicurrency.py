"""Multi-currency behavior."""
from ledger import Ledger
from model import Entry
import api
import report


def _fresh():
    lg = Ledger()
    lg.open_account("cash", "Cash")
    lg.open_account("rev", "Revenue")
    return lg


def test_per_currency_balances():
    lg = _fresh()
    api.transfer(lg, "rev", "cash", 1000)            # USD default
    api.transfer(lg, "rev", "cash", 500, "EUR")
    assert lg.balance("cash") == 1000
    assert lg.balance("cash", "EUR") == 500
    assert lg.balance("cash", "GBP") == 0            # unseen currency -> 0
    assert lg.balance("rev", "EUR") == -500


def test_mixed_currency_rejected():
    lg = _fresh()
    try:
        lg.post([Entry("cash", 100, "USD"), Entry("rev", -100, "EUR")])
    except ValueError:
        return
    assert False, "expected ValueError on mixed-currency transaction"


def test_double_entry_still_enforced_within_currency():
    lg = _fresh()
    try:
        lg.post([Entry("cash", 100, "EUR"), Entry("rev", -90, "EUR")])
    except ValueError:
        return
    assert False, "expected ValueError on unbalanced transaction"


def test_trial_balance_by_currency():
    lg = _fresh()
    api.transfer(lg, "rev", "cash", 1000)
    api.transfer(lg, "rev", "cash", 500, "EUR")
    assert report.trial_balance_by_currency(lg) == {"USD": 0, "EUR": 0}


def test_trial_balance_raises_when_multi_currency():
    lg = _fresh()
    api.transfer(lg, "rev", "cash", 1000)
    api.transfer(lg, "rev", "cash", 500, "EUR")
    try:
        report.trial_balance(lg)
    except ValueError:
        return
    assert False, "expected ValueError: ambiguous single-currency trial_balance"


def test_statement_filters_by_currency():
    lg = _fresh()
    api.transfer(lg, "rev", "cash", 1000)
    api.transfer(lg, "rev", "cash", 500, "EUR")
    lines_usd, bal_usd = report.statement(lg, "cash")
    lines_eur, bal_eur = report.statement(lg, "cash", "EUR")
    assert lines_usd == [1000] and bal_usd == 1000
    assert lines_eur == [500] and bal_eur == 500


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print("ok", n)
    print("all multi-currency tests passed")
