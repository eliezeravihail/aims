# Real-repo adaptation — boltons LRI/LRU + TTL (aims-refactor vs plain)

Escalates the [synthetic suite](../refactoring-suite/) to a **real third-party library**: `mahmoud/boltons`
(pure-Python, its own pytest suite). The change is a genuine feature addition to a non-trivial module.

## Setup

- **Target:** `boltons/cacheutils.py` — the `LRI` cache (a `dict` subclass with a recency linked list and
  `max_size` eviction) and its subclass `LRU`. Cloned read-only via the anonymous git lane; the arms work on
  copies, so nothing is pushed to boltons.
- **Change (`change-card.md`):** add an optional `ttl=None` (seconds) so an entry older than `ttl` is treated
  as **absent** on every read path — `cache[key]`, `cache.get(...)`, and `key in cache` — with `ttl=None`
  preserving today's behavior exactly.
- **The real trap (one-owner across access paths):** `__contains__` is inherited from `dict` (it bypasses
  `__getitem__`), **and** `LRU` *overrides* `__getitem__`. So the liveness check has to be owned in one place
  reached by all three paths and both classes; a naive TTL added only to `LRI.__getitem__` leaves `key in
  cache` and `LRU` reads wrong. This is the kind of cross-cutting interaction a small module can't stress but
  a real one does.

## Reading (rubric-free, runnable)

- **Behavior preserved:** `python3 -m pytest tests/test_cacheutils.py -q` must stay **23 passed** (the test
  file unedited).
- **New requirement:** `hidden/oracle.py` — 14 checks across `in`/`get`/`[]`, refresh-on-write, `LRU`
  inheritance, eviction-with-ttl, and `ttl=None` preservation. Both were **validated against a reference TTL
  patch** (23 pass + oracle 14/14) before any arm ran, and the reference confirmed the `LRU.__getitem__` trap
  is load-bearing.

`arms/<arm>/cacheutils.py` keeps each arm's delivered module (not the whole vendored library); `results.md`
records the readings.
