"""Adversarial tests for the multi-currency adaptation.

Covers the new behavior and the interactions the change implies across all
modules, in addition to the preserved single-currency behavior guarded by
test_ledger.py (which passes unchanged)."""
from ledger import Ledger
from model import Entry, Account
import api
import report


def _fresh():
    lg = Ledger()
    lg.open_account("cash", "Cash")
    lg.open_account("rev", "Revenue")
    return lg


# --- per-currency, independent balances -------------------------------------

def test_balances_are_independent_per_currency():
    lg = _fresh()
    api.transfer(lg, "rev", "cash", 1000, "USD")
    api.transfer(lg, "rev", "cash", 700, "EUR")
    assert lg.balance("cash", "USD") == 1000
    assert lg.balance("cash", "EUR") == 700
    assert lg.balance("rev", "USD") == -1000
    assert lg.balance("rev", "EUR") == -700


def test_default_currency_is_usd_everywhere():
    lg = _fresh()
    api.transfer(lg, "rev", "cash", 250)          # default USD
    assert lg.balance("cash") == 250              # default USD read
    assert lg.balance("cash", "USD") == 250
    assert lg.balance("cash", "EUR") == 0         # untouched currency reads 0


def test_explicit_currency_leaves_other_untouched():
    lg = _fresh()
    api.transfer(lg, "rev", "cash", 500, "EUR")
    assert lg.balance("cash", "EUR") == 500
    assert lg.balance("cash", "USD") == 0         # USD never moved


def test_unused_currency_reads_zero():
    lg = _fresh()
    assert lg.balance("cash", "JPY") == 0
    assert Account("x", "X").balance("USD") == 0


# --- same-currency-per-transaction rule (owned by Ledger.post) --------------

def test_mixed_currency_transaction_rejected():
    lg = _fresh()
    try:
        lg.post([Entry("cash", 500, "USD"), Entry("rev", -500, "EUR")])
    except ValueError as e:
        assert "mixed-currency" in str(e)
        # nothing was applied
        assert lg.balance("cash", "USD") == 0
        assert lg.balance("rev", "EUR") == 0
        assert lg.transactions == []
        return
    assert False, "expected ValueError on mixed-currency transaction"


def test_double_entry_still_enforced_within_currency():
    lg = _fresh()
    try:
        lg.post([Entry("cash", 500, "EUR"), Entry("rev", -400, "EUR")])
    except ValueError as e:
        assert "unbalanced" in str(e)
        return
    assert False, "expected ValueError on unbalanced same-currency transaction"


def test_same_currency_balanced_transaction_posts():
    lg = _fresh()
    lg.post([Entry("cash", 500, "EUR"), Entry("rev", -500, "EUR")])
    assert lg.balance("cash", "EUR") == 500
    assert lg.balance("rev", "EUR") == -500


# --- trial_balance_by_currency: group, never sum across ---------------------

def test_trial_balance_by_currency_groups_and_balances():
    lg = _fresh()
    api.transfer(lg, "rev", "cash", 1000, "USD")
    api.transfer(lg, "rev", "cash", 700, "EUR")
    assert report.trial_balance_by_currency(lg) == {"USD": 0, "EUR": 0}


def test_trial_balance_by_currency_never_sums_across():
    # A ledger deliberately imbalanced per-currency (via direct single-currency
    # posts to a suspense account) must report each currency separately, never a
    # single cross-currency number that would cancel.
    lg = _fresh()
    lg.open_account("susp", "Suspense")
    lg.post([Entry("cash", 100, "USD"), Entry("susp", -100, "USD")])
    lg.post([Entry("rev", -100, "EUR"), Entry("susp", 100, "EUR")])
    totals = report.trial_balance_by_currency(lg)
    assert totals == {"USD": 0, "EUR": 0}
    # And an imbalance in one currency does not leak into another:
    lg2 = _fresh()
    lg2.accounts["cash"].apply(100, "USD")   # unbalanced on purpose (bookkeeping owner)
    lg2.accounts["cash"].apply(50, "EUR")
    assert report.trial_balance_by_currency(lg2) == {"USD": 100, "EUR": 50}


def test_trial_balance_by_currency_empty_ledger():
    lg = _fresh()
    assert report.trial_balance_by_currency(lg) == {}


# --- trial_balance backward compatibility -----------------------------------

def test_trial_balance_single_currency_returns_int():
    lg = _fresh()
    api.transfer(lg, "rev", "cash", 1000)
    api.transfer(lg, "cash", "rev", 300)
    assert report.trial_balance(lg) == 0
    assert isinstance(report.trial_balance(lg), int)


def test_trial_balance_empty_ledger_is_zero_int():
    lg = _fresh()
    assert report.trial_balance(lg) == 0


def test_trial_balance_raises_on_multiple_currencies():
    lg = _fresh()
    api.transfer(lg, "rev", "cash", 1000, "USD")
    api.transfer(lg, "rev", "cash", 700, "EUR")
    try:
        report.trial_balance(lg)
    except ValueError as e:
        assert "trial_balance_by_currency" in str(e)
        return
    assert False, "expected ValueError when ledger holds multiple currencies"


# --- statement still reports the default-currency closing balance -----------

def test_statement_reports_amounts_and_usd_balance():
    lg = _fresh()
    api.transfer(lg, "rev", "cash", 1000, "USD")
    api.transfer(lg, "rev", "cash", 700, "EUR")
    lines, bal = report.statement(lg, "cash")
    assert lines == [1000, 700]     # all legs touching the account, signed amounts
    assert bal == 1000              # closing balance is the default-currency (USD) one


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print("ok", n)
    print("all multi-currency tests passed")
