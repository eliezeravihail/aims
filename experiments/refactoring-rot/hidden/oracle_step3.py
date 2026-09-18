"""Semantics-agnostic consistency oracle for step 3 (loyalty cap). Never shown to an arm.
Usage: python3 oracle_step3.py <arm-dir-with-checkout.py>
Catches a rot-induced regression without pinning the exact loyalty math:
preservation (loyalty=None), conservation (Sigma line_finals == order_total),
loyalty-monotonicity, the 50% cap, and discount_breakdown internal consistency."""
import sys, importlib, pathlib
from decimal import Decimal

arm = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(arm))
m = importlib.import_module("checkout")

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))

LINES = [(1000, 1), (500, 1), (333, 3)]  # subtotal 2499
SUB = 2499

def finals(lines, discount, loyalty):
    return [f for (f, _t) in m.line_charges(lines, discount, Decimal("0.2"), loyalty)]

try:
    # 1) preservation: loyalty=None == no-loyalty behavior (steps 1-2 intact)
    for d in (None, ("pct", 10), ("amt", 300)):
        check(f"preserve_total_{d}", m.order_total(LINES, d, None) == m.order_total(LINES, d))
        base = [f for (f, _t) in m.line_charges(LINES, d, Decimal("0.2"))]
        withn = finals(LINES, d, None)
        check(f"preserve_lines_{d}", base == withn, f"{base} vs {withn}")

    # 2) conservation with loyalty: Sigma line finals == order_total(...,loyalty)
    for d in (None, ("pct", 10)):
        for loy in (("pct", 20), ("pct", 60)):
            ot = m.order_total(LINES, d, loy)
            s = sum(finals(LINES, d, loy))
            check(f"conserve_{d}_{loy}", s == ot, f"sum={s} order_total={ot}")

    # 3) loyalty never increases the price
    for d in (None, ("pct", 10)):
        check(f"monotone_{d}", m.order_total(LINES, d, ("pct", 30)) <= m.order_total(LINES, d, None))

    # 4) combined discount capped at 50% of subtotal (final >= 50% - rounding slack)
    ot_capped = m.order_total(LINES, ("pct", 40), ("pct", 40))  # 80% requested -> capped to 50%
    check("cap_50pct", ot_capped >= SUB - (SUB - SUB // 2) - 1, f"order_total={ot_capped}, subtotal={SUB}")

    # 5) discount_breakdown internal consistency
    od, req, grant = m.discount_breakdown(LINES, ("pct", 40), ("pct", 40))
    total_disc = SUB - m.order_total(LINES, ("pct", 40), ("pct", 40))
    check("breakdown_sums", od + grant == total_disc, f"od={od} grant={grant} total_disc={total_disc}")
    check("grant_le_request", grant <= req, f"grant={grant} req={req}")
    check("grant_nonneg", grant >= 0, f"grant={grant}")
except Exception as e:
    check("exception", False, f"{e!r}")

passed = sum(1 for _, ok, _ in results if ok)
print(f"ORACLE rot-step3 [{arm.name}]: {passed}/{len(results)} passed")
for name, ok, detail in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if not ok and detail else ""))
sys.exit(0 if passed == len(results) else 1)
