"""Hidden oracle for the boltons TTL adaptation. Never shown to an arm.
Usage: python3 oracle.py <arm-root-containing-boltons/>
Checks the TTL contract across all three read paths (in / get / []), refresh-on-write,
LRU inheritance, eviction-with-ttl, and ttl=None preservation. Real sleeps with margins.
The existing 23-test suite is run separately (pytest) by the harness."""
import sys, importlib, pathlib, time

arm = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(arm))
cu = importlib.import_module("boltons.cacheutils")
LRI, LRU = cu.LRI, cu.LRU

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))

# ttl=None -> no expiry, all three paths present after a pause
try:
    c = LRI(max_size=10)
    c["a"] = 1
    time.sleep(0.2)
    check("none_in", ("a" in c) is True)
    check("none_get", c.get("a") == 1)
    check("none_getitem", c["a"] == 1)
except Exception as e:
    check("ttl_none", False, f"{e!r}")

# ttl set -> present before expiry, absent (all three paths) after
try:
    c = LRI(max_size=10, ttl=0.15)
    c["a"] = 1
    check("fresh_in", ("a" in c) is True)
    check("fresh_get", c.get("a") == 1)
    check("fresh_getitem", c["a"] == 1)
    time.sleep(0.30)
    check("expired_in", ("a" in c) is False, f"'a' in c = {'a' in c}")
    check("expired_get", c.get("a", "X") == "X", f"get={c.get('a','X')!r}")
    got_keyerror = False
    try:
        _ = c["a"]
    except KeyError:
        got_keyerror = True
    check("expired_getitem_raises", got_keyerror)
except Exception as e:
    check("ttl_set", False, f"{e!r}")

# writing refreshes the TTL clock
try:
    c = LRI(max_size=10, ttl=0.2)
    c["a"] = 1
    time.sleep(0.12)
    c["a"] = 2            # rewrite resets the clock
    time.sleep(0.12)      # 0.24s since first write, 0.12s since rewrite -> still live
    check("refresh_in", ("a" in c) is True, f"'a' in c = {'a' in c}")
    check("refresh_value", c.get("a") == 2, f"get={c.get('a')!r}")
except Exception as e:
    check("refresh", False, f"{e!r}")

# LRU inherits the TTL behavior
try:
    c = LRU(max_size=10, ttl=0.15)
    c["a"] = 1
    check("lru_fresh", "a" in c and c["a"] == 1)
    time.sleep(0.30)
    check("lru_expired", ("a" in c) is False and c.get("a", "X") == "X")
except Exception as e:
    check("lru_ttl", False, f"{e!r}")

# eviction still respects max_size with ttl set
try:
    c = LRI(max_size=3, ttl=100)
    for i in range(6):
        c[i] = i
    check("eviction_len", len(c) <= 3, f"len={len(c)}")
except Exception as e:
    check("eviction", False, f"{e!r}")

passed = sum(1 for _, ok, _ in results if ok)
print(f"ORACLE boltons-ttl [{arm.name}]: {passed}/{len(results)} passed")
for name, ok, detail in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if not ok and detail else ""))
sys.exit(0 if passed == len(results) else 1)
