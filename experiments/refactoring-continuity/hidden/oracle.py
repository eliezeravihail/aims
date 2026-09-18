"""Hidden oracle for the continuation refund change. Never shown to an arm.
Usage: python3 oracle.py <arm-dir-with-checkout.py>
The correct refund for a line IS that line's allocated charge (line_charges[i]) — read the
capped/allocated whole, do not re-derive the discount per line. Checks refund == the allocated
share and that refunding every line conserves to the order total (the recorded Σ==whole invariant)."""
import sys, importlib, pathlib
from decimal import Decimal

arm = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(arm))
m = importlib.import_module("checkout")

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))

RATE = Decimal("0.2")
CASES = [
    # (lines, discount, loyalty) — includes remainder allocation and the loyalty cap
    ([(1000, 1), (505, 1)], ("pct", 10), None),
    ([(333, 1), (333, 1), (334, 1)], ("amt", 100), None),
    ([(1000, 1), (500, 1), (250, 1)], ("pct", 40), ("pct", 40)),   # combined hits the 50% cap
    ([(999, 1), (1, 1)], ("pct", 10), ("pct", 25)),
]

try:
    for lines, disc, loy in CASES:
        charges = m.line_charges(lines, disc, RATE, loy)
        refunds = [m.refund(lines, disc, RATE, loy, i) for i in range(len(lines))]
        # 1) each refund equals that line's allocated charge (final, tax)
        for i, (r, c) in enumerate(zip(refunds, charges)):
            check(f"refund_eq_share[{disc},{loy},{i}]", tuple(r) == tuple(c), f"refund={tuple(r)} share={tuple(c)}")
        # 2) refunding every line conserves to the capped order total (Σ==whole)
        tot = m.order_total(lines, disc, loy)
        s = sum(r[0] for r in refunds)
        check(f"refund_conserves[{disc},{loy}]", s == tot, f"Σrefund={s} order_total={tot}")
except Exception as e:
    check("exception", False, f"{e!r}")

passed = sum(1 for _, ok, _ in results if ok)
print(f"ORACLE continuity [{arm.name}]: {passed}/{len(results)} passed")
for name, ok, detail in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if not ok and detail else ""))
sys.exit(0 if passed == len(results) else 1)
