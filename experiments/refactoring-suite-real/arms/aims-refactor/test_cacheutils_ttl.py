"""Tests for the optional TTL (time-to-live) added to LRI/LRU.

Time is driven by a fake monotonic clock injected into the cacheutils
module namespace, so expiry is exercised deterministically (no real
sleeps). One real-sleep test at the end guards the real clock wiring.
"""
import time as _real_time

import pytest

from boltons import cacheutils
from boltons.cacheutils import LRU, LRI


class FakeClock:
    """Stand-in for the ``time`` module: only ``monotonic`` is used."""
    def __init__(self):
        self.now = 1000.0

    def monotonic(self):
        return self.now

    def advance(self, secs):
        self.now += secs


@pytest.fixture
def clock(monkeypatch):
    fc = FakeClock()
    monkeypatch.setattr(cacheutils, 'time', fc)
    return fc


@pytest.mark.parametrize('cls', [LRI, LRU])
def test_ttl_none_never_expires(cls, clock):
    # ttl=None (default) => behavior exactly as today: no expiry.
    cache = cls(max_size=4)
    cache['a'] = 1
    clock.advance(10 ** 9)
    assert cache['a'] == 1
    assert 'a' in cache
    assert cache.get('a') == 1


@pytest.mark.parametrize('cls', [LRI, LRU])
def test_all_read_paths_treat_expired_as_absent(cls, clock):
    cache = cls(max_size=4, ttl=10)
    cache['a'] = 1

    # still live at exactly ttl (expired only when MORE than ttl elapsed)
    clock.advance(10)
    assert cache['a'] == 1
    assert 'a' in cache
    assert cache.get('a') == 1

    # now push past ttl relative to the (unchanged, read doesn't restart) write
    clock.advance(0.001)
    # 1) subscription raises KeyError
    with pytest.raises(KeyError):
        cache['a']
    # 2) get returns the default
    sentinel = object()
    assert cache.get('a', sentinel) is sentinel
    assert cache.get('a') is None
    # 3) membership is False
    assert 'a' not in cache


@pytest.mark.parametrize('cls', [LRI, LRU])
def test_setitem_restarts_clock(cls, clock):
    cache = cls(max_size=4, ttl=10)
    cache['a'] = 1
    clock.advance(9)
    cache['a'] = 2          # write restarts the ttl clock
    clock.advance(9)        # 18s since first write, but only 9s since restart
    assert cache['a'] == 2
    assert 'a' in cache
    clock.advance(2)        # now 11s since restart -> expired
    assert 'a' not in cache


@pytest.mark.parametrize('cls', [LRI, LRU])
def test_setdefault_restarts_clock(cls, clock):
    cache = cls(max_size=4, ttl=10)
    cache['a'] = 1
    clock.advance(11)       # expired
    # setdefault sees an absent (expired) key, inserts default, restarts clock
    assert cache.setdefault('a', 99) == 99
    assert cache['a'] == 99
    clock.advance(9)
    assert cache['a'] == 99  # still live under the restarted clock


@pytest.mark.parametrize('cls', [LRI, LRU])
def test_update_restarts_clock(cls, clock):
    cache = cls(max_size=4, ttl=10)
    cache['a'] = 1
    clock.advance(9)
    cache.update({'a': 5})
    clock.advance(9)
    assert cache['a'] == 5  # update restarted the clock


@pytest.mark.parametrize('cls', [LRI, LRU])
def test_expired_read_counts_as_miss(cls, clock):
    cache = cls(max_size=4, ttl=10)
    cache['a'] = 1
    clock.advance(20)
    # A subscript miss on an expired key behaves like a missing key.
    with pytest.raises(KeyError):
        cache['a']
    assert cache.miss_count == 1
    assert cache.soft_miss_count == 0
    # get() on the (still expired) key: miss + soft_miss, like a normal absent get
    assert cache.get('a') is None
    assert cache.miss_count == 2
    assert cache.soft_miss_count == 1


@pytest.mark.parametrize('cls', [LRI, LRU])
def test_on_miss_regenerates_expired(cls, clock):
    calls = []

    def on_miss(k):
        calls.append(k)
        return 'gen-%d' % len(calls)

    cache = cls(max_size=4, ttl=10, on_miss=on_miss)
    assert cache['a'] == 'gen-1'   # first miss regenerates
    clock.advance(5)
    assert cache['a'] == 'gen-1'   # still live, no regen
    assert len(calls) == 1
    clock.advance(6)               # 11s since (re)write -> expired
    assert cache['a'] == 'gen-2'   # expired => treated absent => regenerated
    assert len(calls) == 2


@pytest.mark.parametrize('cls', [LRI, LRU])
def test_ttl_coexists_with_max_size_eviction(cls, clock):
    cache = cls(max_size=2, ttl=100)
    cache['a'] = 1
    cache['b'] = 2
    cache['c'] = 3          # evicts 'a' by size, unrelated to ttl
    assert 'a' not in cache
    assert len(cache) == 2
    assert cache['b'] == 2 and cache['c'] == 3
    # ttl still applies to the survivors
    clock.advance(101)
    assert 'b' not in cache
    assert 'c' not in cache


@pytest.mark.parametrize('cls', [LRI, LRU])
def test_initial_values_are_stamped(cls, clock):
    cache = cls(max_size=4, ttl=10, values={'a': 1})
    assert cache['a'] == 1
    clock.advance(11)
    assert 'a' not in cache


def test_ttl_validation():
    with pytest.raises(ValueError):
        LRI(ttl=0)
    with pytest.raises(ValueError):
        LRU(ttl=-5)
    # None and positive numbers are accepted
    LRI(ttl=None)
    LRU(ttl=0.5)


def test_lru_read_recency_with_ttl(clock):
    # LRU overrides __getitem__ (moves-to-front). A live read still updates
    # recency so it survives an eviction that a stale entry does not.
    lru = LRU(max_size=2, ttl=100)
    lru['a'] = 1
    lru['b'] = 2
    assert lru['a'] == 1   # 'a' now most-recently-used
    lru['c'] = 3           # evicts least-recently-used, which is 'b'
    assert 'b' not in lru
    assert lru['a'] == 1
    assert lru['c'] == 3


def test_real_clock_expiry():
    # Belt-and-suspenders: exercise the real time.monotonic wiring.
    cache = LRI(max_size=2, ttl=0.05)
    cache['a'] = 1
    assert cache['a'] == 1
    _real_time.sleep(0.08)
    assert 'a' not in cache
    with pytest.raises(KeyError):
        cache['a']
