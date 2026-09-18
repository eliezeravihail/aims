"""Hidden oracle for the refactoring-principles validation. Never shown to an arm.

Usage: python3 oracle_test.py <path-to-arm-dir-containing-pricing.py>
Runs the arm's adapted pricing.py against a battery that includes the S4 traps:
market-1 preservation, the discount->line ALLOCATION (Sigma line_finals == order_final),
and per-line tax on the DISCOUNTED amount (not the undiscounted line).
"""
import sys
import importlib
import pathlib
from decimal import Decimal

arm_dir = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(arm_dir))
m = importlib.import_module("pricing")

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))

def fields(r):
    return (getattr(r, "order_final"), list(getattr(r, "line_finals")), list(getattr(r, "line_taxes")))

# --- Market 1 preserved (the out-of-scope behavior) ---
try:
    check("m1_none", m.order_total(m.Order([m.Line(1000, 1), m.Line(500, 2)])) == 2000)
    check("m1_pct", m.order_total(m.Order([m.Line(1000, 1), m.Line(500, 1)], ("pct", 10))) == 1350)
    check("m1_amt", m.order_total(m.Order([m.Line(1000, 1)], ("amt", 250))) == 750)
    check("m1_amt_clamped", m.order_total(m.Order([m.Line(100, 1)], ("amt", 250))) == 0)
except Exception as e:
    check("m1_behavior", False, f"exception: {e!r}")

# --- Case A: pct discount, clean allocation, tax on DISCOUNTED lines (the S4) ---
try:
    r = m.price_market2(m.Order([m.Line(1000, 1), m.Line(500, 1)], ("pct", 10)), Decimal("0.2"))
    of, lf, lt = fields(r)
    check("A_order_final", of == 1350, f"got {of}")
    check("A_alloc_sums", sum(lf) == of, f"line_finals={lf} sum={sum(lf)} order_final={of}")
    check("A_alloc_values", lf == [900, 450], f"got {lf}")
    check("A_tax_on_discounted", lt == [180, 90], f"got {lt} (undiscounted would be [200,100] = the S4)")
except Exception as e:
    check("A_market2", False, f"exception: {e!r}")

# --- Case B: amt discount with a remainder penny (largest-remainder allocation) ---
try:
    r = m.price_market2(m.Order([m.Line(333, 1), m.Line(333, 1), m.Line(334, 1)], ("amt", 100)), Decimal("0.2"))
    of, lf, lt = fields(r)
    check("B_order_final", of == 900, f"got {of}")
    check("B_alloc_sums", sum(lf) == of, f"line_finals={lf} sum={sum(lf)} order_final={of}")
    check("B_alloc_values", lf == [300, 300, 300], f"got {lf}")
    check("B_tax", lt == [60, 60, 60], f"got {lt}")
except Exception as e:
    check("B_market2", False, f"exception: {e!r}")

# --- Case C: half-even tax rounding on discounted lines, no discount ---
try:
    r = m.price_market2(m.Order([m.Line(2, 1), m.Line(6, 1)]), Decimal("0.25"))
    of, lf, lt = fields(r)
    check("C_order_final", of == 8, f"got {of}")
    check("C_alloc_sums", sum(lf) == of, f"line_finals={lf}")
    check("C_tax_half_even", lt == [0, 2], f"got {lt} (0.5->0, 1.5->2 half-even)")
except Exception as e:
    check("C_market2", False, f"exception: {e!r}")

passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"ORACLE for {arm_dir.name}: {passed}/{total} checks passed")
for name, ok, detail in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if (not ok and detail) else ""))
sys.exit(0 if passed == total else 1)
