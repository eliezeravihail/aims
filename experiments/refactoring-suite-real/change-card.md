# Change request — add per-entry TTL to boltons' LRI/LRU cache

You are handed the real `boltons` library (`boltons/cacheutils.py` + its test suite `tests/test_cacheutils.py`).
Add an **optional time-to-live (TTL)** to the `LRI` cache (and therefore to `LRU`, which subclasses it).

## The requirement

- `LRI.__init__` (and `LRU.__init__`) gains an optional keyword `ttl=None`. `ttl` is a number of **seconds**.
- When `ttl` is set, an entry that was inserted more than `ttl` seconds ago is **expired**, and every read
  path must treat an expired entry as **absent**:
  - `cache[key]` raises `KeyError` (a miss),
  - `cache.get(key, default)` returns `default`,
  - `key in cache` is `False`.
- **Writing** a key (`cache[key] = value`, `setdefault`, `update`) (re)starts that key's TTL clock.
- `ttl=None` (the default) means **no expiry** — behavior is exactly as today.

## Constraints

- **Preserve all existing behavior.** The existing `tests/test_cacheutils.py` must pass **unchanged** (every
  test there constructs caches without `ttl`). Do not edit the test file.
- Keep it correct under the cache's existing mechanics (the recency linked list, `max_size` eviction, hit/
  miss counting, `LRU`).

Deliver the adapted `boltons/cacheutils.py` (and any tests you add in a separate file).
