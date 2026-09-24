# Feed ranking, stage 1: design from the encapsulation axis

Axis: **correct encapsulation**. Each rule has one owner that enforces it and cannot be bypassed. Every
value that crosses a public seam is a published type. The caller tells objects what to do instead of
reading their state and deciding outside them. The design aims to make every rule **true by
construction**: an object that exists is valid. If a rule has no such object, it lives on the single
path that every entry path goes through.

Design only. Signatures and short sketches appear only where they make a boundary concrete.

---

## 1. Shape in one paragraph

Two concepts form a pure **core**. `Weights` is one immutable, validated weight version. It carries a
version id derived from its own content and owns the score formula. `Candidate` is one immutable,
validated item. A core `rank()` function owns the order: duplicate-id rejection, score descending,
then id ascending. **`FeedService`** is the only stateful object. It holds exactly one current
`Weights` reference, and it owns startup refusal, reload fallback and "one version per request". It
gets weights through a **`WeightSource` port** (`load() -> Weights`) and never learns where they come
from. The only production adapter is a private JSON-file source, wired together by one composition
function. A thin CLI sits on the public API. Numbers are **exact decimals** (§6).

```
              feed_ranking (public surface: __init__.py)
   cli.py ──► _compose.py ──► service.py ──► core/ ◄── _json_config.py
   (argv/     (wires file     (FeedService,   (Weights,     (JsonFileWeightSource:
    JSON I/O)  source→svc)     WeightSource)   Candidate,    file → Weights)
                                               rank, Feed)
                         all ──► errors.py (no dependencies)
```
Dependencies point inward toward `core/` and `errors.py`, and there are no cycles. `core/` imports
only `errors.py` and the stdlib (`decimal`, `hashlib`, `enum`, `dataclasses`, `types`).

---

## 2. Module skeleton

```
feed_ranking/
  __init__.py          # the public API: re-exports listed in §3, nothing else
  errors.py            # FeedRankingError, WeightConfigError, InvalidRequest
  core/
    __init__.py        # core's published names: SignalName, Weights, WeightsVersion, Candidate,
                       #   Feed, RankedItem, rank
    _numeric.py        # PRIVATE: to_exact(raw) -> Decimal; EXACT (the one arithmetic Context)
    _signals.py        # SignalName (StrEnum); PRIVATE read_named_values(); PRIVATE SignalProblem
    candidate.py       # Candidate
    weights.py         # Weights, WeightsVersion
    ranking.py         # rank(weights, candidates) -> tuple[RankedItem, ...]
    feed.py            # Feed, RankedItem
  service.py           # WeightSource (Protocol, the port), FeedService
  _json_config.py      # PRIVATE adapter: JsonFileWeightSource
  _compose.py          # load_service(config_path) -> FeedService   (composition root)
  cli.py               # main(argv) -> int
  __main__.py          # sys.exit(cli.main(sys.argv[1:]))
```

Underscore modules are implementation. They are not re-exported, and no module outside their package
imports them. The tests of the JSON adapter are the one exception.

---

## 3. Public signatures (the whole published surface)

```python
# feed_ranking/__init__.py re-exports exactly:
from .service import FeedService, WeightSource
from ._compose import load_service
from .core import Candidate, SignalName, Weights, WeightsVersion, Feed, RankedItem
from .errors import FeedRankingError, WeightConfigError, InvalidRequest
```

### core

```python
class SignalName(StrEnum):
    RECENCY = "recency"; AFFINITY = "affinity"; POPULARITY = "popularity"

WeightsVersion = NewType("WeightsVersion", str)       # e.g. "w-3f9a0c1d2e4b5a67"

class Weights:                                        # immutable; __slots__; no setters, no getters of w
    def __init__(self, values: Mapping[str, float | int]) -> None: ...   # raises WeightConfigError
    @property
    def version(self) -> WeightsVersion: ...          # derived from content, not passed in
    def score(self, candidate: Candidate) -> Decimal: ...   # THE formula; exact

class Candidate:                                      # immutable; __slots__
    def __init__(self, item_id: str, signals: Mapping[str, float | int]) -> None: ...  # raises InvalidRequest
    @property
    def item_id(self) -> str: ...
    def signal(self, name: SignalName) -> Decimal: ...   # read-only; used by Weights.score

@dataclass(frozen=True, slots=True)
class RankedItem:
    item_id: str
    score: Decimal                                    # exact; see §6

@dataclass(frozen=True, slots=True)
class Feed:
    user: str
    weights_version: WeightsVersion
    items: tuple[RankedItem, ...]                     # highest score first; () for no candidates

def rank(weights: Weights, candidates: Iterable[Candidate]) -> tuple[RankedItem, ...]: ...
    # raises InvalidRequest on a duplicate id. Published by core for the service; NOT re-exported
    # at the package top level, because the product's entry point is FeedService.
```

### service (the port and the stateful owner)

```python
class WeightSource(Protocol):
    def load(self) -> Weights: ...
    # Contract: return a Weights, or raise WeightConfigError naming the problem. Every failure the
    # source knows about (I/O, format) is translated into WeightConfigError.

class FeedService:
    def __init__(self, source: WeightSource) -> None: ...
        # Loads once. If that fails, WeightConfigError propagates and no FeedService exists.
    def reload(self) -> WeightsVersion: ...
        # Loads a new Weights and swaps it in atomically, returning its version.
        # On WeightConfigError: re-raises, and the previous Weights stays active.
    def rank(self, user: str, candidates: Iterable[Candidate]) -> Feed: ...
        # Raises InvalidRequest (duplicate id). Candidate validity was settled when each
        # Candidate was built.
```

`reload()` breaks command–query separation on purpose: it returns the version it installed. The caller
needs to know *which* version went live, and reading it back afterwards could race another reload.

### composition and CLI

```python
def load_service(config_path: str | os.PathLike[str]) -> FeedService: ...
    # FeedService(JsonFileWeightSource(config_path)). This is the one place that knows weights come
    # from a file.

def main(argv: Sequence[str]) -> int: ...
```

**CLI surface:**

```
python -m feed_ranking --weights PATH [REQUEST_FILE]      # the request is read from stdin if omitted
```

- Request JSON: `{"user": "u1", "candidates": [{"id": "a", "signals": {"recency": 0.9, "affinity": 0.1, "popularity": 0.5}}, ...]}`
- Output (stdout): `{"user": "u1", "weights_version": "w-…", "items": [{"id": "a", "score": "0.58"}, ...]}`.
  The score is a **JSON string** holding plain decimal text (`format(score.normalize(), "f")`). A JSON
  number would be parsed back into a float by most consumers, and that would bring back the problem
  from §6.
- Exit codes: `0` success; `2` invalid weights (the service refused to start); `3` invalid request;
  `1` anything else. Errors print as one line on stderr: `error: <message>`.
- A CLI run is one process with one startup, so "reload" in the CLI *is* a restart. The explicit
  reload call is `FeedService.reload()` for an embedding host. The CLI has no long-running mode
  because that would be network or REPL serving, which is a non-goal.

The CLI owns only the *shape* of its JSON request: it must be a JSON object, `user` must be a string,
`candidates` must be a list, and each entry must be `{id, signals}`. A shape violation raises
`InvalidRequest`. Everything else goes through `Candidate` and `FeedService.rank`.

---

## 4. Types crossing each seam

| Seam | Direction | Types crossing | Never crosses |
|---|---|---|---|
| Caller → `FeedService.rank` | in | `str` (user), `Iterable[Candidate]` | raw dicts, floats |
| `FeedService` → caller | out | `Feed` (`RankedItem`, `WeightsVersion`, `Decimal`) | `Weights` object, source |
| `WeightSource` → `FeedService` | in | `Weights` (or `WeightConfigError`) | paths, JSON, dicts, `OSError`, `JSONDecodeError` |
| `FeedService` → core `rank` | in | one `Weights` snapshot, `tuple[Candidate, ...]` | `user`, the source, the service |
| core `rank` → `FeedService` | out | `tuple[RankedItem, ...]` | scores as floats |
| `Weights.score` ← `Candidate` | in | `Candidate` (reads `signal(name) -> Decimal`) | `user`, `item_id` |
| Host → `FeedService.reload` | out | `WeightsVersion` (or `WeightConfigError`) | the new `Weights` |
| CLI → library | both | only the public names in §3 | anything underscored |

`Decimal` is the one foundational type that crosses seams. It is fixed stdlib, and it *is* the
published numeric representation (§6), not an implementation detail being leaked. `Weights` crosses
exactly one seam: the port, inbound. The service never hands a `Weights` out. Callers see only its
`WeightsVersion`, so no caller can hold a weight object and score with it outside the service.

---

## 5. Error vocabulary

```python
class FeedRankingError(Exception): ...                 # base; hosts catch this to catch all of ours

class WeightConfigError(FeedRankingError):
    problem: str            # e.g. "affinity: must be >= 0 (got -0.1)"; "missing weight: popularity";
                            #      "unknown weight: freshness"; "all weights are 0: at least one must be > 0";
                            #      "cannot read file: No such file or directory"; "not valid JSON (line 3, col 5)";
                            #      "duplicate name in file: recency"; "top level must be a JSON object"
    origin: str | None      # where it came from, e.g. the file path; set by the adapter, None from Weights

class InvalidRequest(FeedRankingError):
    reason: str             # e.g. "must be in [0, 1] (got 1.2)", "not a number (got 'high')",
                            #      "missing signal", "unknown signal", "item id must be a non-empty string",
                            #      "duplicate item id"
    item_id: object | None  # the id exactly as given (may be "" or a non-string); None for a
                            #   request-shape error (CLI)
    signal: str | None      # the signal name as given (a SignalName value, or the unknown key)
```

There is **one type per distinct handling**. A host handles a config rejection one way (refuse to
start, or keep serving and alert) and a request rejection another way (reject the call). No subtype
exists that nobody would catch separately. Structured fields exist so tests and hosts can assert *which*
item and signal failed without parsing the message. `str(err)` renders
`item 'b': signal 'recency': must be in [0, 1] (got 1.2)`.

Neither error type wraps process-fatal failures such as `MemoryError`. A bug inside a
`WeightSource` (any exception other than `WeightConfigError`) propagates unchanged. It still cannot
install anything, as §7 shows.

**The first problem is reported, in a fixed order.** For weights: missing names in canonical order
(recency, affinity, popularity), then unknown names sorted, then per-value checks in canonical order,
then the all-zero check. For a request: candidates in input order; within one candidate, the id first,
then missing, unknown, and values in the same order as for weights. Duplicate detection happens in
`rank`, after every candidate exists, and names the first repeated id in input order.

---

## 6. Hard decision (b): what "equal score" means numerically

**Decision.** Signals, weights and scores are **exact decimals** (`decimal.Decimal`). Each input number
is canonicalized once, at the boundary, to the **shortest decimal that round-trips its IEEE-754 double**,
which is `Decimal(repr(float(x)))`. Scores are computed with **exact** decimal multiplication and addition. Two
scores are "equal" exactly when they are equal as `Decimal` values, with no epsilon.

In the example from the package: 0.1 becomes `0.1`, 0.3 becomes `0.3`, 0.2 becomes `0.2`, and 0.15
becomes `0.15`. Then x = `0.1·0.3 + 0.2·0 + 0·p = 0.03` and y = `0.1·0 + 0.2·0.15 = 0.03`. The scores
are equal, so the tie-break applies and x comes before y by id. In the core scenario, a = `0.58` and
b = c = `0.55` exactly, where float arithmetic gives `0.5800000000000001`.

**Why this is honest.** The numbers the operator and caller *wrote* are decimals: `0.1` in a JSON file,
and `0.1` as a Python literal (whose `repr` is `"0.1"`). The PO asked for exact equality with no epsilon.
Exact equality is only meaningful over exact arithmetic on the values people meant. Binary floats
give a tie-break that depends on rounding artifacts and on the order of the terms in the sum.
Going through the double first means a library caller passing the float `0.1` and a JSON caller writing
`0.1` get the **same** value, and so the same order and the same version id.

**Why exactness is bounded, and so safe.** After canonicalization, every value has at most 17
significant digits and an exponent inside the double range, roughly 1e-324 to 1.8e308. So every
product has at most 34 significant digits, and the exact sum of three products needs at most about
1,000 digits even with extreme weights. Arithmetic uses one module-owned context:

```python
# core/_numeric.py (private)
EXACT = decimal.Context(prec=decimal.MAX_PREC, Emax=decimal.MAX_EMAX, Emin=decimal.MIN_EMIN,
                        traps=[decimal.Inexact, decimal.Rounded, decimal.InvalidOperation])
def to_exact(raw: object) -> Decimal   # rejects bool and non-(int|float) values ("not a number"), and
                                        # non-finite values ("must be finite"): NaN, ±inf, or an int
                                        # too large for a double (OverflowError); -0.0 becomes 0
```

- `Weights.score` calls `EXACT.multiply` and `EXACT.add` explicitly. It **never uses the ambient
  thread context**, because a host that sets `decimal.getcontext().prec = 6` would otherwise silently
  round scores and merge distinct ones. With `prec=MAX_PREC`, multiplication and addition are exact;
  only division could blow up, and division is never used.
- The trapped `Inexact` and `Rounded` signals do not validate input. They assert the exactness
  invariant, so a future change that breaks it fails loudly instead of mis-ordering items.
- The sort key is `(score.copy_negate(), item_id)`. `copy_negate` is exact and ignores the context,
  whereas unary `-score` rounds to the ambient context and could merge two distinct scores. This detail
  is recorded because it is exactly the kind of mistake that passes tests.

**Stated consequence (assumption).** A number written with more than about 17 significant digits is read
as the double nearest to it. For example, `"1.00000000000000001"` is read as `1.0`, so it is a valid
signal. This is the documented meaning of "a number" in this service. It is not clamping: range
checks run *after* canonicalization, and a value outside the range after that step is rejected.

**Rejected alternatives**

| Alternative | Why rejected |
|---|---|
| Float scores compared with `==` | Mathematically equal scores split (x ≠ y). The order depends on floating-point rounding, not on the rule. |
| Epsilon comparison | The PO said exact, no epsilon. It is also non-transitive, so the sort order becomes ill-defined. |
| Round scores to N places | An epsilon in disguise. It merges genuinely different scores, and N is arbitrary. |
| `Fraction` of the float values | Exact, but of the *wrong* number: `Fraction(0.1) ≠ 1/10`, so x ≠ y still. |
| `json` with `parse_float=Decimal` (exact text) | A float caller and a JSON caller would disagree on the same written `0.1`. Unbounded digits and exponents (such as `1e-999999999`, a valid signal) make exact arithmetic unbounded. |
| Integer fixed-point at some scale | Needs a scale, which means rounding inputs, which is the epsilon problem again. |

**Cost.** Decimal arithmetic runs in microseconds per item. The product states no performance
requirement (§13 of the principles does not apply), and the candidate list is small per request.

---

## 7. Hard decision (a): where "one valid weight version per request" lives

**Decision.** Three structural facts, each owned in one place, make a mixed or invalid ranking
**unrepresentable** instead of guarded against:

1. **Only valid weights exist.** (Owner: `Weights.__init__`.) Validation happens in the constructor
   itself, not in a factory next to it. No code path can hold a `Weights` that breaks a weight rule,
   whichever `WeightSource` produced it, a test fake included. The object is immutable: values sit in a
   `MappingProxyType`, the class uses `__slots__`, and it has no mutators. The version id is *computed*
   from the canonical values, so a version cannot be paired with the wrong weights.
2. **A request sees exactly one snapshot.** (Owner: `FeedService.rank`.) It reads `self._current`
   **once**, at entry, into a local variable, and passes that single `Weights` value to `core.rank`. The
   `Feed` is stamped with `weights.version` from that same local. `core.rank` receives a value, not the
   service or the source, so it cannot re-read anything part-way through. Mixing would need a second
   read, and none exists.
3. **A reload is build-then-swap.** (Owner: `FeedService.reload`.) `new = self._source.load()` runs
   completely, including all validation in `Weights.__init__`, *before* the one assignment
   `self._current = new`. On any exception the assignment is never reached, so the last valid weights
   stay current. A `WeightConfigError` is re-raised to the reload caller, which is how the service
   "reports the rejection". Startup is the same load inside `__init__`: if it fails, the constructor
   raises and **no service object exists**. "Refuses to start" is therefore a property of construction,
   not a flag.

```python
class FeedService:
    __slots__ = ("_source", "_current", "_reload_lock")
    def __init__(self, source):  self._source = source; self._current = source.load(); self._reload_lock = Lock()
    def reload(self):
        with self._reload_lock:
            new = self._source.load()      # may raise: nothing has changed yet
            self._current = new            # single reference assignment: atomic
            return new.version
    def rank(self, user, candidates):
        weights = self._current            # the one read per request
        return Feed(user, weights.version, rank(weights, candidates))
```

**Concurrency.** The process is single, but a host may call it from several threads. Reading and
assigning one object reference is atomic, both in CPython and in free-threaded builds. Because each
`Weights` is immutable, readers need no lock: a request in flight keeps its old snapshot alive, and
the new one serves the next request. The **reload lock** exists for one reason: two overlapping
reloads could otherwise finish out of order and install the older file's content last. Serializing
load and swap together makes "the last reload call wins" true.

**Which version a request uses** is defined as the version active when `rank` was *entered*. A reload
that completes during a request affects only later requests.

**Rejected alternatives**

| Alternative | Why rejected |
|---|---|
| A mutable weights object updated in place | A request could see a mix of two versions, and a failed reload could leave a partial update. Reverting would need a second, special-case owner. |
| Validate in the source, or in a `Weights.parse` factory, with a plain constructor | Any other source or caller could build an invalid `Weights`. Validity would have two paths. |
| A read–write lock held for the whole request | It blocks reloads behind long requests for no benefit, because an immutable snapshot already gives isolation. |
| Pass the source (or the service) into the ranking core | The core would know where weights come from, and could re-read them mid-request. That breaks both the seam and the rule. |
| Return a `ReloadResult(ok, error)` instead of raising | This would make "rejected" a value that callers can ignore. Raising cannot be ignored silently, and the state is unchanged either way. |
| Operator-supplied version field in the file | Operators forget to change it, so two different weight sets could share an id. A content-derived id cannot lie. |
| A separate `ActiveWeights` holder class | See §10: its only client would be `FeedService`, with no second force behind it. |

**Version id (assumption).** `WeightsVersion` is `"w-"` followed by the first 16 hex digits of the
SHA-256 of the canonical text `affinity=<d>;popularity=<d>;recency=<d>`, with normalized decimals. The
same weights give the same id: writing `0.5` or `0.50`, or reloading an unchanged file, does not create a
new version. Different weights give different ids (a 64-bit prefix, which is ample at operator scale).
"The id of the weight config used" therefore identifies exactly the numbers that ranked the request.

---

## 8. Rule → owner → every entry path

The entry paths are: **L** = library `FeedService.rank`; **S** = startup (`FeedService(source)`,
`load_service`, CLI `--weights`); **R** = `FeedService.reload`; **C** = CLI request; **X** = a custom
`WeightSource`.

| Rule | Single owner | Entry paths that reach it (and how) |
|---|---|---|
| Weights: exactly recency/affinity/popularity (missing or unknown → invalid) | `Weights.__init__`, via the private `_signals.read_named_values` | S, R, X → `source.load()` → `Weights(...)`. There is no other constructor. |
| Weight value finite and ≥ 0 | `Weights.__init__` (with `_numeric.to_exact` for "is a finite number") | S, R, X as above |
| At least one weight > 0 | `Weights.__init__` | S, R, X |
| Weights never rescaled and need not sum to 1 | `Weights.__init__` stores the canonical values as given; no code anywhere normalizes | S, R, X |
| What "a number" is (not bool, int or float, finite, shortest decimal) | `core/_numeric.to_exact` | Weights (S, R, X) and Candidate (L, C) both call it |
| Config file readable, valid JSON, an object, no duplicate keys | `JsonFileWeightSource.load` (`object_pairs_hook` detects duplicates) | S, R when composed by `load_service` / CLI |
| Invalid config at startup → refuse to start | `FeedService.__init__`: no instance exists without a `Weights` | S (library: the exception propagates; CLI: exit 2) |
| Invalid reload → keep last valid, report | `FeedService.reload` (build-then-swap, re-raise) | R |
| Never rank with partial or invalid weights | By construction: `Weights.__init__` (only valid objects) plus `FeedService.reload` (swap only after a full load) | S, R, L |
| One weight version per request | `FeedService.rank` (a single snapshot read) plus `Weights` immutability | L, C |
| Response carries the version used | `FeedService.rank` stamps `Feed` from the same snapshot; `Weights.version` is derived from content | L, C |
| score = w_r·r + w_a·a + w_p·p, nothing else | `Weights.score(candidate)`, which takes only a `Candidate` and reads only its three signals | L, C, through `core.rank` |
| Exact arithmetic, and so exact equality | `Weights.score` using `_numeric.EXACT` | L, C |
| Signal present and known (missing or unknown → reject, naming item and signal) | `Candidate.__init__` via `read_named_values` | L (the caller builds Candidates); C (the CLI builds Candidates) |
| Signal a finite number in [0, 1]; never clamped, zero-filled or dropped | `Candidate.__init__` | L, C |
| Item id a non-empty string | `Candidate.__init__` | L, C |
| Duplicate id in a request → reject | `core.rank` | L, C, through `FeedService.rank` (the only production caller) |
| Order: score descending, then id ascending by code point | `core.rank` sort key `(score.copy_negate(), item_id)` | L, C |
| Empty candidates → empty feed | `core.rank`: no special case, because sorting nothing gives `()`, and the Feed still carries the version | L, C |
| `user` affects neither score nor order | `FeedService.rank`: `user` goes only into `Feed`, never into `core.rank` or `Weights.score` (neither accepts it) | L, C |
| Weight change only by explicit reload (no watching) | `FeedService`: `load()` is called only in `__init__` and `reload` | S, R |
| Request JSON shape (CLI only) | `cli._parse_request` | C |

Every rule has exactly one row and one owner. The two "by construction" rows name the two owners
whose *combination* makes the invariant hold. Each owner enforces a different half: which weights may
exist, and when they may become current.

---

## 9. Test plan (test-first; each test targets the owner, plus one path test per entry)

Tests are ordered by build sequence. Each group is written before its owner exists.

**T1 `_numeric.to_exact`** (owner: what a number is)
- `0.1` → `Decimal("0.1")`; `1` → `Decimal("1.0")`; `1e-05` round-trips; `-0.0` → `0`.
- `True` and `False` are rejected as not a number. `"0.5"`, `None` and `Decimal("0.5")` are also
  rejected as not a number; the published inputs are int and float only.
- `nan`, `inf` and `-inf` → must be finite. `10**400` → must be finite (overflow).
- `"1.00000000000000001"`-style input → documented nearest-double reading, asserted.

**T2 `Weights`** (owner: weight validity, version, formula)
- The valid scenario `{recency .5, affinity .3, popularity .2}` constructs.
- Missing `popularity`; unknown `freshness` (alongside all three); an empty mapping → `WeightConfigError`,
  and `problem` names it.
- Negative (`-0.1`), NaN, inf, string, bool, None → rejected, naming the signal.
- All zero → rejected ("at least one must be > 0"). `{0, 0, 5e-324}` → accepted.
- Weights summing to 1.7 are accepted, and the score is **not** rescaled: weights `(2, 0, 0)` with recency
  `0.5` give a score of exactly `1`.
- Version: the same content gives the same version; `0.5` and `0.50` give the same version; any change
  gives a different version; the version is not settable.
- Immutability: no attribute assignment succeeds (`AttributeError`, from slots or frozen).
- Formula: the core scenario gives `0.58` / `0.55` exactly. **The float trap**: weights `(0.1, 0.2, 0)`,
  x `(0.3, 0, p)` and y `(0, 0.15, p)` both score `Decimal("0.03")`, and they are equal.
- The ambient context is ignored: with `getcontext().prec = 3`, a score needing 20 digits is still
  exact.

**T3 `Candidate`** (owner: signal contract, id)
- Empty id `""` → `InvalidRequest(item_id="")`. A non-string id (`5`) → rejected. `" "` → accepted
  (non-empty, as stated).
- Missing signal, unknown extra signal → rejected, naming the item and that signal.
- `-0.01`, `1.01`, NaN, inf, `"0.5"`, bool → rejected, naming the item and signal. `0` and `1`
  exactly → accepted (the boundaries).
- There is no clamping: `1.2` is rejected, not stored as `1`.

**T4 `core.rank`** (owner: order, tie, duplicates)
- Empty → `()`. One item → that item. Many → descending order.
- A tie by exact equality → id ascending by code point: ids `"9"` and `"10"` with equal scores give
  `"10"` first. The trap pair x/y is ordered by id, **not** split by float noise.
- A near-tie (scores differing in the 20th digit) keeps score order and does **not** fall back to the id.
- Permutation invariance: 200 seeded shuffles of the same candidates give an identical output.
- A duplicate id (at any positions) → `InvalidRequest(item_id=dup, reason="duplicate item id")`.
- A score needing more than 28 digits still sorts correctly (this guards the `copy_negate` choice).

**T5 `FeedService`** with a fake `WeightSource` (a scripted list of `Weights`, or errors)
- Startup: the fake raises `WeightConfigError` → the constructor raises, so no instance exists.
- Reload is valid → it returns the new version, and the **next** `rank` carries the new version and
  new scores.
- Reload is invalid → it raises `WeightConfigError`, and the next `rank` still uses the **previous**
  version and scores.
- Reload A→B→(invalid)→ rank: the version is B.
- The source raises a non-domain exception (`RuntimeError`) → it propagates, and the previous weights
  remain.
- **Reload during a request** (deterministic, no threads): the candidates are a generator that calls
  `service.reload()` after yielding the first item. Every score in that feed uses the old weights, and
  the feed's version is the old version. The next request uses the new version.
- `user` does not matter: the same candidates for `"u1"` and `"u2"` give identical `items`, and
  `Feed.user` echoes the value given.
- Empty candidates → `Feed(user, version, ())`, not an error.
- Concurrency smoke test (threads): N threads rank while one thread reloads repeatedly between two
  weight sets. Every feed's scores equal the recomputation under the version the feed names; none is a
  mix.
- Overlapping reloads: a slow fake load plus a fast one, started in order, finish in that order.

**T6 `JsonFileWeightSource`** (tmp files)
- A missing file, a directory, or invalid JSON → `WeightConfigError` with `origin` = path and a clear
  `problem`.
- A top-level array → rejected. A duplicate key `"recency"` twice → rejected; it is **not** silently
  last-wins.
- A `NaN` literal in the file → rejected by `Weights` (the finite rule has one owner), with the path in
  `origin`.
- A valid file → a `Weights` whose version equals `Weights({...}).version` built directly.

**T7 CLI** (end-to-end, a few cases)
- The core scenario → stdout JSON items `a, b, c` with scores `"0.58"`, `"0.55"`, `"0.55"`, a version,
  and exit 0.
- Bad weights → exit 2, a one-line stderr message naming the problem, and empty stdout.
- A bad signal → exit 3, with the message naming the item and signal. Malformed request JSON → exit 3.
- Empty `candidates` → `"items": []`, exit 0.

The **pyramid**: T1–T4 are pure, fast unit tests and form the bulk. T5 uses fakes. T6 and T7 are
the few integration and end-to-end tests.

---

## 10. Subtractive pass: what was cut, and what stays with its force

**Cut**
- **`ActiveWeights` / version-holder class.** Its only client was `FeedService`, and holding the current
  weights is the service's single piece of state. A separate class added a seam that no change-axis uses.
- **`Ranking` intermediate (version + items) and a public `Candidates` collection type.** The pairing of
  version and items happens in one three-line method. The duplicate-id rule has one owner in `rank`.
  Neither type answered a force.
- **`SignalValues` value object.** `Candidate` owning its three decimals is enough. Only `Weights.score`
  reads them, through `signal(name)`.
- **A `Score` wrapper.** `Decimal` *is* the stated representation. Wrapping it would only hide what the
  contract promises callers (exact values they can compare).
- **A `WeightsVersion` class.** A `NewType` gives the type distinction at no runtime cost, and no
  behaviour hangs on it.
- **Per-problem error subclasses** (`MissingWeight`, `NegativeSignal`, …). They would be dead subtypes,
  because nobody handles them differently. Structured fields carry the detail instead.
- **`ReloadResult` / status objects.** Raising replaces them (§7).
- **A CLI `check-weights` command, a long-running CLI mode, and a `--reload` flag.** None was asked for.
  A one-shot CLI is a restart, and reload belongs to the library host.
- **Collecting *all* problems per config or request.** The first problem, in a fixed order, is
  deterministic and names the problem, which is what was asked.
- **A read lock on requests, a history of versions, file watching, logging inside `reload`.** Each
  lacks a force. The caller of `reload` receives the rejection and decides how to log it.
- **A `from_config_file` classmethod on `FeedService`.** It would make the service depend on the file
  adapter (policy depending on detail). It moved into `_compose.load_service`.

**Kept, each with its present force**
- **`WeightSource` port.** The goal requires that the core not know where weights come from. It also
  lets T5 script reload success and failure without files.
- **`Weights` as a validating, immutable value with a derived version.** It is the single owner of
  weight validity and of the version-to-content pairing, and it makes hard decision (a) structural.
- **`Candidate` validating in its constructor.** It is the single owner of the signal contract, and
  every candidate that exists is valid ("trusting inside").
- **`_numeric` (to_exact + EXACT).** It is the single owner of hard decision (b), and it is shared by
  weights and signals.
- **The reload lock.** It guarantees the last reload wins when reloads overlap. Nothing else would.
- **`_compose.load_service`.** It is the composition root, so `service.py` never imports the file adapter.
- **The private `SignalProblem`.** `read_named_values` is shared by two owners that report different
  error types. The private problem is translated at each owner and never escapes `core/`.

## 11. Concept-fit pass

- `Weights` is a **value**: one weight version. It is not a "config object"; *config* is the adapter's
  word for where it came from. The version is the value's **derived identity**, not a label attached to it.
- An empty candidate list gives a **`Feed` with zero items**. It is not `None` and not an error.
- The tie-break is **part of the order key**. It is not a score perturbation such as adding `ε·id`.
- A reload rejection is a **first-class error**. It is not modelled as "the reload returned the old
  version".
- `user` is an **attribute of the response**, an identity echo. It is not a ranking input with no
  effect: the ranking functions do not accept it at all.
- A duplicate id is a **request rejection** owned by the step that sees the whole request. It is not a
  filter that keeps the first occurrence.
- "Refuses to start" is **the absence of a service object**. It is not a `started=False` state.

## 12. Assumptions (stated, simple)

1. An extra unknown signal key on a *candidate* is rejected. This mirrors the rule for weights, and it
   stops a misspelled signal name from being silently ignored.
2. The version id is content-derived (§7). Reloading identical weights keeps the same id.
3. A number means the nearest IEEE-754 double, read as its shortest decimal (§6).
4. `user` is any `str`, carried verbatim. The product states no validity rule for it.
5. The first problem is reported, in a fixed deterministic order (§5).
6. The CLI emits scores as decimal strings, so they survive JSON consumers exactly.
