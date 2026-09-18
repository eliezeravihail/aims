# Results — real-repo adaptation (boltons LRI/LRU + TTL)

**Run 2026-09-18.** Both arms adapted a **real third-party library** (`mahmoud/boltons`, `cacheutils.py`) to
add a `ttl` option, on identical checkouts. Primary reading is runnable: the library's own 23-test suite
(behavior preserved) + a hidden 14-check TTL oracle.

## Correctness (runnable) — no gap

| Arm | `pytest tests/test_cacheutils.py` (preserve) | hidden TTL oracle | added lines |
|---|---|---|---|
| **aims-refactor** | **23 passed** (unchanged) | **14/14** | **31** |
| **plain** | **23 passed** (unchanged) | **14/14** | **53** |

Both arms **caught the cross-cutting trap** the module hides: the liveness check had to reach `cache[key]`,
`cache.get(...)`, **and** `key in cache` (inherited from `dict`, so it bypasses `__getitem__`), across both
`LRI` **and** `LRU` (which overrides `__getitem__`). Neither shipped a wrong result; both preserved existing
behavior. On a real, non-trivial module a capable model with no method still gets it right.

## Where the method differed — one owner, in-place vs a parallel structure

Same correctness; different structure, and it favors the method:

- **aims-refactor** put the expiry **in the recency link node** (widened the node from 4 to 5 fields as a
  behavior-preserving refactor, then turned the seam live) and a single `_is_expired(link)` predicate that
  all three read sites call. Because the expiry travels **with the entry**, the existing linked-list removal
  (`__delitem__`, `pop`, `popitem`, `max_size` eviction) drops it automatically — **no cleanup code added to
  those paths**. One owner for the liveness rule, one owner for the write-clock stamp. 31 lines.
- **plain** kept a **parallel `self._insert_times` dict** keyed beside the store. Correct — but a second
  structure that must be kept in sync, so it had to add pop/cleanup code to `__delitem__`, `pop`, `popitem`,
  the eviction path, and `copy()`. 53 lines, touching more methods. This is the §5 "a rule/rep spread across
  several places" cost the document warns about — here it stayed correct, but it is more surface to drift as
  the class evolves.

**Cost:** aims-refactor ~129k tokens vs plain ~82k (~1.6×), spent on the explicit characterize/preserve/
re-trace passes and the refactor-then-change split.

## Conclusion (consistent across every run in this repo)

- **`refactoring-principles.md` is validated again, and no bug surfaced:** on a real library with a genuine
  cross-cutting one-owner trap, the aims-refactor arm produced a correct, behavior-preserving change **and**
  the tighter structure (expiry co-located, fewer touch points) the document prescribes.
- **The correctness gap between method and no-method is ~zero even on real code at this scale** — a capable
  model is already correct. The method's measured value is **structural**: one-owner ownership, an in-place
  representation instead of a parallel map, a refactor-then-change split, and durable records — smaller diff,
  fewer methods touched. That advantage compounds over a module's lifetime and many edits; a single change,
  even on a real library this size, does not turn it into a *correctness* difference.
- **To find a correctness-discriminating case** you need scale the model cannot hold in its head at once —
  a large, multi-module change over a long-lived codebase where the plain instinct scatters or drifts across
  edits (where the historical S4 actually occurred). That is a materially larger experiment than this thread's
  budget; recorded here as the honest next step, not run.
