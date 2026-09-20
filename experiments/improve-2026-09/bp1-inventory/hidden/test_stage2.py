"""Hidden stage-2 probes (expiry). Stage-1 tests must also still pass."""
import importlib.util, os, pytest

def load(path):
    spec = importlib.util.spec_from_file_location("inv2", path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

inv = load(os.environ.get("INV_PATH", "inventory.py"))


def test_ttl_reservation_expires_frees_units():
    i = inv.Inventory(); i.add_stock("a", 10)
    i.reserve("a", 4, ttl_seconds=10, now=0.0)
    assert i.available("a", now=5.0) == 6      # still held before expiry
    assert i.available("a", now=10.0) == 10    # expired at now=10 (expiry<=now)
    assert i.available("a", now=99.0) == 10

def test_no_ttl_never_expires():
    i = inv.Inventory(); i.add_stock("a", 10)
    i.reserve("a", 4, now=0.0)                  # no ttl
    assert i.available("a", now=10_000.0) == 6

def test_expired_units_reusable():
    i = inv.Inventory(); i.add_stock("a", 5)
    i.reserve("a", 5, ttl_seconds=2, now=0.0)
    assert i.available("a", now=1.0) == 0
    # after expiry, can reserve again
    rid2 = i.reserve("a", 5, now=3.0)
    assert i.available("a", now=3.0) == 0 and isinstance(rid2, str)

def test_release_of_expired_no_double_count():
    i = inv.Inventory(); i.add_stock("a", 10)
    rid = i.reserve("a", 4, ttl_seconds=5, now=0.0)
    assert i.available("a", now=6.0) == 10      # expired
    i.release(rid)                              # releasing expired is a no-op
    assert i.available("a", now=6.0) == 10       # not 14

def test_mixed_ttl_and_permanent():
    i = inv.Inventory(); i.add_stock("a", 10)
    i.reserve("a", 3, now=0.0)                  # permanent
    i.reserve("a", 4, ttl_seconds=5, now=0.0)  # expires at 5
    assert i.available("a", now=1.0) == 3
    assert i.available("a", now=5.0) == 7        # only the ttl one freed
