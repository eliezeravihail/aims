"""Hidden oracle for the multi-currency cross-cutting change. Never shown to an arm.
Usage: python3 oracle.py <arm-root-with-the-4-modules>
Checks backward-compat + the cross-cutting multi-currency correctness, including the
mixing trap and the group-by-currency (never sum across) report."""
import sys, importlib, pathlib

arm = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(arm))
for mod in ("model", "ledger", "report", "api"):
    globals()[mod] = importlib.import_module(mod)

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))

def fresh():
    lg = ledger.Ledger()
    lg.open_account("cash", "Cash")
    lg.open_account("rev", "Revenue")
    return lg

# 1) backward compat (default currency)
try:
    lg = fresh()
    api.transfer(lg, "rev", "cash", 1000)          # default USD
    check("bc_balance", lg.balance("cash") == 1000)
    check("bc_trial_zero", report.trial_balance(lg) == 0)
except Exception as e:
    check("backward_compat", False, f"{e!r}")

# 2) per-currency balances are independent
try:
    lg = fresh()
    api.transfer(lg, "rev", "cash", 1000, "USD")
    api.transfer(lg, "rev", "cash", 500, "EUR")
    check("percur_usd", lg.balance("cash", "USD") == 1000, f"{lg.balance('cash','USD')}")
    check("percur_eur", lg.balance("cash", "EUR") == 500, f"{lg.balance('cash','EUR')}")
    check("percur_independent", lg.balance("cash", "USD") != lg.balance("cash", "EUR"))
except Exception as e:
    check("per_currency", False, f"{e!r}")

# 3) a transaction that mixes currencies is rejected
try:
    lg = fresh()
    raised = False
    try:
        lg.post([model.Entry("cash", 100, "USD"), model.Entry("rev", -100, "EUR")])
    except ValueError:
        raised = True
    check("mixed_rejected", raised, "mixed-currency transaction was not rejected")
except Exception as e:
    check("mixed", False, f"{e!r}")

# 4) trial_balance_by_currency groups per currency, nets to 0 each, never merges
try:
    lg = fresh()
    api.transfer(lg, "rev", "cash", 1000, "USD")
    api.transfer(lg, "rev", "cash", 500, "EUR")
    tb = report.trial_balance_by_currency(lg)
    check("group_keys", set(tb) == {"USD", "EUR"}, f"keys={set(tb)}")
    check("group_usd_zero", tb.get("USD") == 0, f"USD={tb.get('USD')}")
    check("group_eur_zero", tb.get("EUR") == 0, f"EUR={tb.get('EUR')}")
except Exception as e:
    check("group", False, f"{e!r}")

# 5) trial_balance (scalar) refuses to silently merge multiple currencies
try:
    lg = fresh()
    api.transfer(lg, "rev", "cash", 1000, "USD")
    api.transfer(lg, "rev", "cash", 500, "EUR")
    raised = False
    try:
        report.trial_balance(lg)
    except ValueError:
        raised = True
    check("scalar_refuses_multi", raised, "trial_balance silently merged multiple currencies")
except Exception as e:
    check("scalar", False, f"{e!r}")

passed = sum(1 for _, ok, _ in results if ok)
print(f"ORACLE xcut [{arm.name}]: {passed}/{len(results)} passed")
for name, ok, detail in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if not ok and detail else ""))
sys.exit(0 if passed == len(results) else 1)
