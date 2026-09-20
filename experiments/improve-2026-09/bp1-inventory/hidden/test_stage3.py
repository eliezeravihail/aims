"""Hidden stage-3 probes (confirm + partial). Stage 1 & 2 must still pass."""
import importlib.util, os, pytest

def load(path):
    spec = importlib.util.spec_from_file_location("inv3", path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

inv = load(os.environ.get("INV_PATH", "inventory.py"))


def test_confirm_makes_permanent():
    i = inv.Inventory(); i.add_stock("a", 10)
    rid = i.reserve("a", 4, ttl_seconds=5, now=0.0)
    i.confirm(rid)
    assert i.available("a", now=100.0) == 6     # would have expired at 5, but confirmed → still held

def test_confirm_unknown_noop():
    i = inv.Inventory(); i.add_stock("a", 10)
    i.confirm("bogus")                          # no crash, no effect
    assert i.available("a", now=0.0) == 10

def test_reserve_up_to_partial():
    i = inv.Inventory(); i.add_stock("a", 5)
    rid, got = i.reserve_up_to("a", 8, now=0.0)
    assert got == 5 and isinstance(rid, str)
    assert i.available("a", now=0.0) == 0

def test_reserve_up_to_full_when_enough():
    i = inv.Inventory(); i.add_stock("a", 10)
    rid, got = i.reserve_up_to("a", 3, now=0.0)
    assert got == 3 and i.available("a", now=0.0) == 7

def test_reserve_up_to_nothing_available():
    i = inv.Inventory(); i.add_stock("a", 2)
    i.reserve("a", 2, now=0.0)
    rid, got = i.reserve_up_to("a", 5, now=0.0)
    assert got == 0

def test_reserve_up_to_respects_expiry():
    i = inv.Inventory(); i.add_stock("a", 10)
    i.reserve("a", 10, ttl_seconds=5, now=0.0)  # all held, expires at 5
    rid, got = i.reserve_up_to("a", 4, now=6.0)  # after expiry → 10 available
    assert got == 4

def test_reserve_up_to_nonpositive_raises():
    i = inv.Inventory(); i.add_stock("a", 5)
    with pytest.raises(ValueError):
        i.reserve_up_to("a", 0, now=0.0)
