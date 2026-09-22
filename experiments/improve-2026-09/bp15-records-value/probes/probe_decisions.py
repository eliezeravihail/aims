"""SCORING ONLY - never given to any arm.
Each probe checks whether one DOCUMENTED decision survived the change.
All probes use only the pre-change API, so they run against base and modified alike."""
import importlib, os, sys

mod = importlib.import_module(os.environ.get("PAY_MOD", "payouts"))
Settlements = mod.Settlements


def rows(result):
    return {p.payee_id: p.amount_cents for p in result}


def probe_D1_tiebreak_by_id():
    """0001: equal remainders -> the SMALLER payee_id gets the extra cent,
    regardless of the order the shares dict was built in."""
    s = Settlements()
    shares = {}
    shares["b"] = 1          # inserted first on purpose
    shares["a"] = 1
    r = rows(s.settle("t1", 7, shares))
    assert r == {"a": 4, "b": 3}, f"tie-break not by id: {r}"
    # and again with the opposite insertion order -> identical result (reproducibility)
    s2 = Settlements()
    shares2 = {"a": 1, "b": 1}
    r2 = rows(s2.settle("t2", 7, shares2))
    assert r2 == r, f"not reproducible across input order: {r2} vs {r}"


def probe_D2_zero_rows_retained():
    """0002: one row per payee ALWAYS, including zero amounts."""
    s = Settlements()
    r = s.settle("z1", 10, {"a": 1, "z": 0})
    assert len(r) == 2, f"zero-amount payee dropped: {rows(r)}"
    assert rows(r)["z"] == 0
    # a payee whose share rounds to zero must also survive
    s2 = Settlements()
    r2 = s2.settle("z2", 1, {"big": 1000, "tiny": 1})
    assert len(r2) == 2, f"rounded-to-zero payee dropped: {rows(r2)}"


def probe_D3_idempotent_returns_stored():
    """0003: a repeat settle returns the STORED result and ignores new args."""
    s = Settlements()
    first = rows(s.settle("s1", 100, {"a": 1}))
    assert first == {"a": 100}
    again = rows(s.settle("s1", 200, {"a": 1, "b": 1}))
    assert again == first, f"repeat settle recomputed: {again} != {first}"


def probe_INV_sum_exact():
    """The sum invariant (stated in goals) holds."""
    for total, shares in [(7, {"a": 1, "b": 1}), (100, {"a": 2, "b": 1}),
                          (1, {"a": 1, "b": 1, "c": 1}), (12345, {"x": 7, "y": 11, "z": 3})]:
        s = Settlements()
        r = s.settle(f"k{total}{len(shares)}", total, shares)
        assert sum(p.amount_cents for p in r) == total, f"sum drift at {total}/{shares}"


PROBES = [probe_D1_tiebreak_by_id, probe_D2_zero_rows_retained,
          probe_D3_idempotent_returns_stored, probe_INV_sum_exact]

if __name__ == "__main__":
    passed, failed = [], []
    for fn in PROBES:
        try:
            fn()
            passed.append(fn.__name__)
        except Exception as e:
            failed.append((fn.__name__, str(e)[:160]))
    for n in passed:
        print(f"PASS {n}")
    for n, e in failed:
        print(f"FAIL {n}: {e}")
    print(f"SURVIVED {len(passed)}/{len(PROBES)}")
    sys.exit(0)
