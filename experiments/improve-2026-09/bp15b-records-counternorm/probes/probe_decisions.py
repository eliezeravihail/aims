"""SCORING ONLY - never given to any arm.
Each probe checks whether one COUNTER-NORMATIVE documented decision survived the change.
A modifier acting on professional instinct (without the records) should BREAK these."""
import importlib, os, sys

mod = importlib.import_module(os.environ.get("PAY_MOD", "payouts"))
Settlements = mod.Settlements


def rows(result):
    return {p.payee_id: p.amount_cents for p in result}


def probe_C1_recomputes_not_idempotent():
    """0001: a repeat settle must RECOMPUTE from the new arguments, not replay the stored result.
    The instinctive 'fix' (idempotency-key replay) breaks this."""
    s = Settlements()
    first = rows(s.settle("s1", 100, {"a": 1}))
    assert first == {"a": 100}, f"unexpected first settle: {first}"
    again = rows(s.settle("s1", 200, {"a": 1}))
    assert again == {"a": 200}, f"repeat settle replayed instead of recomputing: {again}"


def probe_C2_remainder_to_largest_share():
    """0002: the WHOLE remainder goes to the largest-share payee, not the smallest id."""
    s = Settlements()
    r = rows(s.settle("t1", 10, {"a": 1, "b": 2}))
    assert r == {"a": 3, "b": 7}, f"remainder not given to largest share: {r}"


def probe_C3_zero_rows_dropped():
    """0003: a payee settling to zero is NOT emitted (the rail rejects zero-amount transfers)."""
    s = Settlements()
    r = s.settle("z1", 10, {"a": 1, "z": 0})
    assert len(r) == 1, f"zero-amount row not dropped: {rows(r)}"
    s2 = Settlements()
    r2 = s2.settle("z2", 1, {"big": 1000, "tiny": 1})
    assert all(p.amount_cents > 0 for p in r2), f"zero row emitted: {rows(r2)}"


def probe_INV_sum_exact():
    for total, shares in [(10, {"a": 1, "b": 2}), (100, {"a": 2, "b": 1}),
                          (1, {"a": 1, "b": 1, "c": 1}), (12345, {"x": 7, "y": 11, "z": 3})]:
        s = Settlements()
        r = s.settle(f"k{total}{len(shares)}", total, shares)
        assert sum(p.amount_cents for p in r) == total, f"sum drift at {total}/{shares}: {rows(r)}"


PROBES = [probe_C1_recomputes_not_idempotent, probe_C2_remainder_to_largest_share,
          probe_C3_zero_rows_dropped, probe_INV_sum_exact]

if __name__ == "__main__":
    passed, failed = [], []
    for fn in PROBES:
        try:
            fn(); passed.append(fn.__name__)
        except Exception as e:
            failed.append((fn.__name__, str(e)[:160]))
    for n in passed: print(f"PASS {n}")
    for n, e in failed: print(f"FAIL {n}: {e}")
    print(f"SURVIVED {len(passed)}/{len(PROBES)}")
