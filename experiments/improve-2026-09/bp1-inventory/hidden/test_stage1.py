"""Hidden stage-1 acceptance + probes. Run against each arm's inventory.py.
Usage: copied next to an arm's inventory.py, then `python3 -m pytest` (or run_stage.py)."""
import importlib.util, os, pytest

def load(path):
    spec = importlib.util.spec_from_file_location("inv", path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

INV = os.environ.get("INV_PATH", "inventory.py")
inv = load(INV)


def test_add_and_available():
    i = inv.Inventory(); i.add_stock("a", 10)
    assert i.available("a") == 10

def test_unknown_sku_available_zero():
    assert inv.Inventory().available("nope") == 0

def test_reserve_decrements():
    i = inv.Inventory(); i.add_stock("a", 10)
    rid = i.reserve("a", 3)
    assert isinstance(rid, str) and i.available("a") == 7

def test_reserve_over_available_raises_and_no_change():
    i = inv.Inventory(); i.add_stock("a", 5)
    with pytest.raises(inv.InsufficientStock):
        i.reserve("a", 8)
    assert i.available("a") == 5

def test_reserve_nonpositive_raises():
    i = inv.Inventory(); i.add_stock("a", 5)
    with pytest.raises(ValueError):
        i.reserve("a", 0)

def test_release_restores():
    i = inv.Inventory(); i.add_stock("a", 10)
    rid = i.reserve("a", 4)
    assert i.available("a") == 6
    i.release(rid)
    assert i.available("a") == 10

def test_release_idempotent():
    i = inv.Inventory(); i.add_stock("a", 10)
    rid = i.reserve("a", 4)
    i.release(rid); i.release(rid); i.release("bogus")
    assert i.available("a") == 10

def test_unique_ids():
    i = inv.Inventory(); i.add_stock("a", 10)
    ids = {i.reserve("a", 1) for _ in range(5)}
    assert len(ids) == 5

def test_invariant_never_negative():
    i = inv.Inventory(); i.add_stock("a", 3)
    i.reserve("a", 3)
    assert i.available("a") == 0
    with pytest.raises(inv.InsufficientStock):
        i.reserve("a", 1)
