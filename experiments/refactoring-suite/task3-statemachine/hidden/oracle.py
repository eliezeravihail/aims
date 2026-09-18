"""Hidden oracle for task3-statemachine. Never shown to an arm.
Usage: python3 oracle.py <arm-dir-with-orders.py>
Checks existing transitions preserved AND cancel's guard + refund side-effect."""
import sys, importlib, pathlib

arm = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(arm))
o = importlib.import_module("orders")
results = []

def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))

def fresh(*events):
    order = o.Order()
    for e in events:
        o.transition(order, e)
    return order

def raises(order, event):
    try:
        o.transition(order, event)
        return False
    except o.IllegalTransition:
        return True
    except Exception:
        return False

# preserved behavior
try:
    check("happy_path", fresh("pay", "ship", "deliver").status == "DELIVERED")
    check("illegal_ship_from_pending", raises(o.Order(), "ship"))
    check("illegal_deliver_from_paid", raises(fresh("pay"), "deliver"))
except Exception as e:
    check("preserved", False, f"exception: {e!r}")

# cancellation
try:
    a = fresh()  # PENDING
    o.transition(a, "cancel")
    check("cancel_pending_status", a.status == "CANCELLED", f"status={a.status}")
    check("cancel_pending_no_refund", a.refunded is False, f"refunded={a.refunded}")

    b = fresh("pay")  # PAID
    o.transition(b, "cancel")
    check("cancel_paid_status", b.status == "CANCELLED", f"status={b.status}")
    check("cancel_paid_refunded", b.refunded is True, f"refunded={b.refunded}")

    check("cancel_shipped_illegal", raises(fresh("pay", "ship"), "cancel"))
    check("cancel_delivered_illegal", raises(fresh("pay", "ship", "deliver"), "cancel"))
except Exception as e:
    check("cancellation", False, f"exception: {e!r}")

passed = sum(1 for _, ok, _ in results if ok)
print(f"ORACLE statemachine [{arm.name}]: {passed}/{len(results)} passed")
for name, ok, detail in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if not ok and detail else ""))
sys.exit(0 if passed == len(results) else 1)
