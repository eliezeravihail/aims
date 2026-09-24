# Feed ranking, stage 1: design (clean-code axis)

Design only. Signatures and a few illustrative lines show where the boundaries are. There is no implementation.

**Axis bias.** Keep the moving parts few, give every fact one home, and hunt smells. The design has
seven small modules, two error types and no third-party dependency. It has no Protocol classes, no
locks, no strategy objects and no logging. Each part answers to a force named below. Everything else
was cut (see §8).

---

## 1. Module skeleton

```
feed_ranking/
  __init__.py     public re-exports only (the names in §2); no logic
  __main__.py     `from feed_ranking.cli import main; raise SystemExit(main())`
  errors.py       ConfigError, RequestError                    (boundary vocabulary)
  exact.py        how numbers are represented: exact decimals  (hard decision b)
  scoring.py      SIGNAL_NAMES, Candidate, Weights             (per-item rules + the formula)
  feed.py         FeedRequest, RankedItem, Feed, rank()        (request rules + ordering)
  config.py       load_weights(path)                           (file adapter: weights file -> Weights)
  service.py      FeedService, WeightsSource                   (hard decision a: the one mutable spot)
  cli.py          main(argv)                                   (optional one-shot CLI)
tests/            unittest (stdlib), one test module per source module + test_scenario.py
```

Each module has a one-sentence reason to exist:

| Module | Why it exists |
|---|---|
| `errors.py` | Both errors are raised in more than one module and caught in `cli.py`. A shared leaf module keeps imports acyclic. |
| `exact.py` | Decision (b) is one fact: "every number is an exact decimal, including numbers read from JSON". It has three users (`scoring`, `config`, `cli`). |
| `scoring.py` | Holds what makes one number per item: the input rules for an item and for the weights, plus the formula. `Candidate` and `Weights` share a module so that `Weights.score(candidate)` creates no import cycle. |
| `feed.py` | Rules at the request level (duplicate ids) and the output order. These change for different reasons than the per-item arithmetic. |
| `config.py` | The only module that does file I/O. It keeps `service` testable with a lambda and keeps `scoring` free of I/O. |
| `service.py` | The single piece of mutable state: which `Weights` are current. |
| `cli.py` | Lets someone run the product (the core scenario) without writing Python. It is the only place that knows the output JSON shape. |

Import direction (acyclic; arrows point toward the more stable modules):
`cli -> service -> config -> scoring -> exact`, with `cli -> exact` for JSON input, `feed -> scoring`,
`service -> feed`, and every module `-> errors`. The ranking core (`scoring`, `feed`) never imports
`config`, `service` or `cli`.

**Dependencies.** Standard library only: `dataclasses`, `decimal`, `hashlib`, `json`, `argparse`,
`sys`, `os`, `collections.abc`. Tests use `unittest`, so there is no dev dependency either. No runtime
dependency is proposed, so nothing needs arguing.

---

## 2. Public signatures (the whole public surface)

```python
# errors.py
class ConfigError(Exception):
    """The weights config is unusable. str(e) names the problem (and the file when there is one)."""

class RequestError(Exception):
    """A ranking request violates the input contract; the whole request is rejected."""
    item_id: str | None      # the offending item, when one is identifiable
    signal: str | None       # the offending signal, when the problem is a signal
    def __init__(self, message: str, *, item_id: str | None = None, signal: str | None = None): ...
```

```python
# exact.py  — decision (b)
EXACT: decimal.Context   # prec=MAX_PREC, Emax=MAX_EMAX, Emin=MIN_EMIN, traps=[InvalidOperation, Overflow, Inexact]

def to_decimal(value: object) -> decimal.Decimal:
    """int | float | Decimal -> finite Decimal. bool, str, None, NaN and ±inf raise ValueError(reason).
    A float is read as its shortest round-trip literal (Decimal(repr(f))). -0 is folded to 0."""

def loads_json(text: str) -> object:
    """json.loads with parse_float=Decimal: JSON numbers keep their exact decimal text."""
```

```python
# scoring.py
SIGNAL_NAMES: tuple[str, ...] = ("recency", "affinity", "popularity")

@dataclass(frozen=True, slots=True)
class Candidate:
    id: str
    recency: Decimal
    affinity: Decimal
    popularity: Decimal
    # __post_init__: id is a non-empty str; each signal goes through to_decimal and must lie in [0, 1].
    #   Otherwise RequestError(item_id=..., signal=...). The fields are stored as the normalized Decimals.
    @classmethod
    def from_mapping(cls, raw: object) -> "Candidate": ...
    #   raw must be a Mapping that has "id" and all of SIGNAL_NAMES. Other keys are ignored (assumption A2).

@dataclass(frozen=True, slots=True)
class Weights:
    recency: Decimal
    affinity: Decimal
    popularity: Decimal
    # __post_init__: each value goes through to_decimal, is finite and >= 0, and at least one is > 0.
    #   Otherwise ConfigError naming the weight and the problem.
    @classmethod
    def from_mapping(cls, raw: object) -> "Weights": ...
    #   raw must be a Mapping whose key set is exactly SIGNAL_NAMES. The error names the missing and unknown keys.
    @property
    def version(self) -> str: ...          # "w-" + first 12 hex digits of sha256 over the canonical values
    def score(self, candidate: Candidate) -> Decimal: ...
    #   with localcontext(EXACT): return self.recency*c.recency + self.affinity*c.affinity + self.popularity*c.popularity
```

```python
# feed.py
@dataclass(frozen=True, slots=True)
class FeedRequest:
    user: str
    candidates: tuple[Candidate, ...]      # __post_init__: user is a str; tuple(candidates); duplicate id -> RequestError(item_id=dup)
    @classmethod
    def from_mapping(cls, raw: object) -> "FeedRequest": ...   # {"user": str, "candidates": [ {...}, ... ]}

@dataclass(frozen=True, slots=True)
class RankedItem:
    id: str
    score: Decimal

@dataclass(frozen=True, slots=True)
class Feed:
    weights_version: str
    items: tuple[RankedItem, ...]

def rank(request: FeedRequest, weights: Weights) -> Feed:
    """Pure. Score each candidate with `weights` and sort by (-score, id). Empty in, empty out."""
```

```python
# config.py
def load_weights(path: str | os.PathLike[str]) -> Weights:
    """Read and parse the file, then Weights.from_mapping. OSError, bad UTF-8 and bad JSON become
    ConfigError(f"{path}: ..."); a ConfigError from Weights is re-raised with the path prefixed."""
```

```python
# service.py
WeightsSource = Callable[[], Weights]      # raises ConfigError when it cannot produce valid weights

class FeedService:
    def __init__(self, source: WeightsSource) -> None: ...   # calls source() once; ConfigError propagates, so no service exists
    @classmethod
    def from_file(cls, path: str | os.PathLike[str]) -> "FeedService": ...  # cls(lambda: load_weights(path))
    @property
    def weights(self) -> Weights: ...       # the version currently in effect (for an operator to confirm a reload)
    def reload(self) -> None: ...           # ConfigError propagates, and the current weights stay unchanged
    def rank(self, request: FeedRequest) -> Feed: ...        # return rank(request, self._weights)
```

```python
# cli.py
def main(argv: Sequence[str] | None = None) -> int: ...
```

`__init__` re-exports `FeedService`, `WeightsSource`, `FeedRequest`, `Candidate`, `Feed`, `RankedItem`,
`Weights`, `rank`, `load_weights`, `ConfigError` and `RequestError`. `exact` stays internal.

### CLI surface

```
python -m feed_ranking --weights PATH [REQUEST_FILE]      # the request is read from stdin when REQUEST_FILE is omitted
```

- Input is a request JSON: `{"user": "u1", "candidates": [{"id": "a", "recency": 0.9, "affinity": 0.1, "popularity": 0.5}, ...]}`.
- Output on stdout: `{"weights_version": "w-3f2a…", "items": [{"id": "a", "score": "0.58"}, ...]}`.
  Scores are **JSON strings** holding the exact decimal text. The stdlib `json` cannot emit a Decimal as
  a number without losing exactness, and a string is honest.
- Exit codes:
  - `0` success.
  - `1` `RequestError`, with `error: <message>` on stderr.
  - `2` usage error (argparse's own code).
  - `3` `ConfigError`: the service refused to start, with `error: <message>` on stderr.
- The CLI has no reload command. Each invocation is a process start, so a "restart" is the reload. The
  explicit reload call exists on the library API (`FeedService.reload`).

---

## 3. Types that cross each seam

| Seam | Crossing types | Direction |
|---|---|---|
| caller -> library | `FeedRequest` (built from `Candidate`s or `from_mapping`), a `str` path | in |
| library -> caller | `Feed` (`RankedItem`s plus `weights_version: str`), `ConfigError`, `RequestError` | out |
| **weights seam**: service -> source | `WeightsSource = Callable[[], Weights]`, which returns `Weights` or raises `ConfigError` | in |
| service -> ranking core | `Weights` and `FeedRequest` in, `Feed` out (`rank` is pure) | both |
| config -> scoring | `object` (the decoded JSON) into `Weights.from_mapping` | in |
| cli -> library | `object` (decoded JSON) into `FeedRequest.from_mapping`; `Feed` back out, serialized in `cli` | both |

The weights seam is a plain callable, not a Protocol class. A zero-argument function that returns a
validated value object is already the most generic type that is still complete for the consumer:
- the file source is `lambda: load_weights(path)`;
- tests use `lambda: Weights(...)` or a list-popping stub;
- a future source (an environment variable, another format) is another zero-argument function.

The core (`rank`, `Weights.score`) never sees the source at all. It receives a `Weights` value.

`Decimal` crosses the seams freely. It is a foundational stdlib type that will not be replaced.

---

## 4. Error vocabulary

Callers handle failures in exactly two ways, so there are two types (§5 rule: one type per distinct
handling).

| Error | Raised when | Handling | Message names |
|---|---|---|---|
| `ConfigError` | weights file unreadable or not JSON, top level not an object, a missing or unknown weight name, a non-number, NaN or ±inf, a negative value, all zero | at startup the process refuses to start (CLI exit 3); on `reload()` the caller reports it while the service keeps serving the previous version | the file path, the weight name and the problem, e.g. `weights.json: unknown weight 'freshness'; missing weight 'popularity'`, `weights.json: weight 'recency' is negative (-0.1)`, `weights.json: all weights are zero` |
| `RequestError` | request not an object, `user` not a string, `candidates` not a list, an item not an object, an empty or non-string id, a duplicate id, a missing signal, a non-number, NaN or ±inf, a signal outside [0, 1] | reject the whole request (CLI exit 1) | item and signal, e.g. `item 'b': signal 'affinity' is 1.2, outside [0, 1]`, `item 'a': signal 'recency' is missing`, `duplicate item id 'a'`, with `.item_id` and `.signal` set |

**Deliberately not in the vocabulary**
- **A trap raised inside `EXACT`** (`Inexact`/`Overflow` during scoring) is not user-actionable. It means
  the exactness invariant broke. It propagates as the raw `decimal` exception (a defect report) and is
  not wrapped. See §6(b) for the only way to reach it.
- **The `ValueError` from `to_decimal`** is internal. It is translated exactly once, at each of its two
  callers (`Candidate` into `RequestError`, `Weights` into `ConfigError`), because only they know the
  domain name to put in the message.
- **Subtypes** (`DuplicateIdError`, `SignalRangeError`, …) are not defined. No caller handles them
  differently. The structured fields `item_id` and `signal` give programs and tests what they need.

---

## 5. Rule ownership

| Rule | Owner (one home) | Every entry path that reaches it |
|---|---|---|
| score = w_r·r + w_a·a + w_p·p, and nothing else | `Weights.score` | `FeedService.rank` → `rank` → `Weights.score`; direct `rank(req, w)`; CLI → `FeedService.rank` |
| `user` does not affect score or order | `rank`, which never reads `request.user`, and `Weights.score`, whose signature takes only a `Candidate` | same as above |
| numeric representation: exact decimals, no epsilon, exact arithmetic | `exact` (`to_decimal`, `EXACT`, `loads_json`) | `Candidate.__post_init__`, `Weights.__post_init__`, `Weights.score`, `config.load_weights`, `cli` |
| a finite number (no bool, NaN or inf) | `exact.to_decimal` | via `Candidate` and via `Weights` (both constructors, so both `from_mapping` paths as well) |
| order: score descending, then id ascending by code point | `rank`, sort key `(-score, id)` | every ranking path goes through `rank` |
| response carries the weights version used | `rank`, which builds `Feed(weights.version, …)` from the same `Weights` it scored with | every ranking path |
| empty candidates → empty feed | `rank`, with no special case (sorting an empty tuple) | every ranking path |
| weight validity: finite, ≥ 0, at least one > 0 | `Weights.__post_init__` | `Weights(...)`, `Weights.from_mapping`, `load_weights`, `FeedService.__init__`/`reload` via the source |
| weight names: exactly the three | `Weights.from_mapping`. Python keyword construction enforces the names by signature. | `load_weights` → `from_mapping`; direct `from_mapping` |
| weights version identity | `Weights.version` | `rank`, `FeedService.weights`, cli output |
| invalid config at startup → refuse to start | `FeedService.__init__`, which lets `ConfigError` escape, so no instance exists | `FeedService(source)`, `FeedService.from_file`, CLI (exit 3) |
| invalid config on reload → keep the last valid weights and report | `FeedService.reload`, which assigns only after `source()` returns | `FeedService.reload` (the only reload path) |
| one weights version per request; never partial weights | `FeedService.rank` reads `self._weights` once and passes the value; `rank` takes `Weights` as a parameter; `Weights` is immutable and fully valid by construction | `FeedService.rank`, direct `rank` |
| change only on explicit reload (no watching) | `FeedService`, which calls `source` only in `__init__` and `reload` | same |
| signal contract: all three present | `Candidate.from_mapping`. Python keyword construction enforces it by signature. | `FeedRequest.from_mapping` → `Candidate.from_mapping`; CLI |
| signal contract: each in [0, 1]; reject, never clamp | `Candidate.__post_init__` | `Candidate(...)`, `Candidate.from_mapping`, `FeedRequest.from_mapping`, CLI |
| item id: a non-empty string | `Candidate.__post_init__` | same as above |
| no duplicate ids in a request | `FeedRequest.__post_init__` | `FeedRequest(...)`, `FeedRequest.from_mapping`, CLI |
| JSON numbers read exactly | `exact.loads_json` | `config.load_weights`, `cli` |

The `from_mapping` methods do only shape checks: is this a mapping, which keys are present. They then
call the constructor. Every value rule therefore lives in exactly one `__post_init__`, and it holds for
Python callers and JSON callers alike. There is no second validation path.

---

## 6. The two hard decisions

### (a) Where "exactly one valid weights version per request" lives

**Decision.** The guarantee has three parts, each with one owner.
1. **Validity by construction.** A `Weights` object cannot exist unless it is valid, because
   `__post_init__` raises otherwise. A partial or invalid `Weights` is therefore unrepresentable.
2. **Immutability.** `Weights` is `frozen=True, slots=True`. A version can never change after anyone
   has seen it.
3. **Snapshot per request.** `FeedService` is the only mutable holder, with a single attribute
   `_weights`. The steps are:
   - `reload()` builds the new value first (`new = self._source()`). If that raises, nothing has been
     assigned and the old version keeps serving. Otherwise it swaps with one reference assignment
     (`self._weights = new`).
   - `rank()` reads `self._weights` once and passes that value to the pure `rank(request, weights)`.
     That same value also supplies `Feed.weights_version`.

   Because the core takes weights as a *parameter*, a single request cannot see two versions: once
   `rank` has its argument, there is nothing it could re-read.

**Concurrency.** The product says a reload "can happen while requests are being served". In one process
that means threads. Reading or rebinding one attribute reference cannot tear: it is atomic under the GIL,
and the free-threaded 3.13+ build also guarantees an attribute store is never seen half-done. A request
therefore sees either the old object or the new one, and each is whole and valid. **No lock is needed.**

Two reloads racing is the only remaining interleaving. Each assigns a complete, valid `Weights`, and the
last one to finish wins. The product states no ordering requirement between two operator reloads that
overlap, so this is an assumption (A4), not a gap.

**Reporting a rejection.** `reload()` raises `ConfigError` to its caller. Whoever triggered the reload
(an operator command, an admin hook) is the one to report it. The service does not log, so it takes no
dependency on a logging policy. The caller can confirm what is in effect through `FeedService.weights.version`.

**Rejected alternatives**
- **A lock around read and swap.** It protects nothing that the atomic swap does not already protect, and
  it adds a moving part that can be held wrong.
- **Mutating the current `Weights` field by field on reload.** This is exactly how a request would see a
  partial or mixed version.
- **`rank` reading the service's current weights itself**, for example `service.current()` called inside
  `rank`. The core would then know where weights come from, and a second read in the same call could
  straddle a reload.
- **Validating in `FeedService.reload` instead of in `Weights`.** That would put the weight rule in a
  second home, because Python callers building `Weights` directly would bypass it.
- **A copy-on-read or versioned registry keeping old versions.** Nothing asks for history.
- **A file watcher.** A non-goal.

### (b) What "equal score" means numerically

**Decision.**
- **Signals, weights and scores are all `decimal.Decimal`.**
- **Arithmetic is exact.** Scoring runs in the `EXACT` context:
  - `prec=MAX_PREC`, so the product and the sum of finite decimals never round;
  - `Inexact` and `Overflow` are trapped, so if exactness were ever lost the service fails loudly
    instead of ranking dishonestly.
- **"Equal score" means mathematically equal**, compared with Decimal `==` and `<`, which are value
  comparisons (`0.03 == 0.030`). There is no epsilon, as the product decided.

How the brief's trap example comes out:
- `0.1×0.3 = 0.03` and `0.2×0.15 = 0.030`, which are equal.
- The id tie-break therefore applies (`x` before `y`), which is what the operator and the caller meant
  by the numbers they wrote.
- In floats the result would be `0.030000000000000002 > 0.03`, so `x` would win on representation
  noise. That tie-break would look deterministic but it would not be honest.

**How numbers enter**, all in one function (`exact.to_decimal`) plus one JSON rule (`exact.loads_json`):

| Input | Becomes |
|---|---|
| JSON number (config file, CLI request) | `Decimal` of its exact text (`parse_float=Decimal`); `0.1` is exactly one tenth |
| Python `Decimal` | taken as is |
| Python `int` | exact |
| Python `float` | `Decimal(repr(f))`, the shortest literal that round-trips, i.e. what the caller typed. `0.3` becomes `Decimal("0.3")`, not `0.29999999999999998889…` |
| `bool`, `str`, `None`, NaN, ±inf | rejected, because a signal or weight is a finite number |

The value is then passed through `EXACT.plus`. This folds `-0` to `0`, so a `-0` weight is simply zero
and is not negative. It also reports an exponent the context cannot hold as not representable.

**Output.**
- `RankedItem.score` is the exact `Decimal`.
- The CLI prints it as the decimal string (`"0.58"`, `"0.030"`). Trailing zeros are kept as the
  arithmetic produced them. Presentation is not normalized, because nothing asks for that.

**Version identity.** This follows from the same representation:
- `Weights.version` = `"w-" + sha256("recency=<r>;affinity=<a>;popularity=<p>")[:12]`, where each
  value is `.normalize()`d.
- Equal weights therefore always get the same id (`0.5` and `0.50` match), and different weights never
  share one (up to hash collision). The id cannot lie, which an operator-maintained version field could.

**Rejected alternatives**
- **Binary float with exact `==`.** Deterministic but dishonest. It is the trap itself.
- **Float with an epsilon, or rounding to N places.** The product explicitly chose exact equality with no
  epsilon. Rounding adds an arbitrary constant (N) as a hidden product rule, and it makes two scores
  that differ by less than 10^-N tie, which is the opposite dishonesty.
- **`fractions.Fraction`.** It is also exact, but it still needs a decimal input rule, prints `3/100`,
  and needs a lossy or custom conversion to show decimal scores. Decimal gives exactness and readable
  output with one type.
- **Rejecting Python floats outright.** Honest but hostile to library callers. The `repr` rule recovers
  the literal they wrote, and exact binary expansion would bring the trap back.
- **Exact binary expansion `Decimal(f)`** for floats. It brings the trap back through the Python API.

**Residual risk (stated, not designed around).**
- Exponents at the edge of `MAX_EMAX`/`MIN_EMIN`, such as a weight of `1e-999999999999999999` multiplied
  by a signal just as tiny, can underflow and fire the `Inexact` trap. That is a crash, not a wrong
  order.
- Real inputs are nowhere near this. Guarding it would add a digit-budget rule that nobody asked for.

---

## 7. Test plan (test-first; stdlib `unittest`; behavior, not implementation)

Order of writing: `exact` → `scoring` → `feed` → `config` → `service` → `cli`/scenario. Each module's
tests are written before its code. Every test calls only public names, except `test_exact`, which tests
the module that owns decision (b).

**test_exact** (decision b)
- `to_decimal(0.1) == Decimal("0.1")`; `to_decimal(Decimal("0.30"))` is kept; `to_decimal(3) == 3`.
- Rejects `True`, `"0.5"`, `None`, `float("nan")`, `float("inf")`, `Decimal("NaN")`, `Decimal("-Infinity")`.
- `to_decimal(Decimal("-0"))` is `Decimal("0")`, and its sign is not negative.
- `loads_json('{"x": 0.1}')["x"] == Decimal("0.1")` (exact text is kept);
  `loads_json("0.12345678901234567890123")` keeps all its digits.

**test_scoring**
- *Formula*: the core scenario scores are exactly `0.58` and `0.55`. Weights that do not sum to 1
  (`2, 0, 0`) give `2×recency`, i.e. no rescaling.
- *Float-equality tie* (the trap): weights `0.1/0.2/0`, `x(0.3,0,·)` and `y(0,0.15,·)` both score
  exactly `0.03`, and `score(x) == score(y)`.
- *Exactness under many digits*: 20-digit weights and signals give a product equal to the hand-computed
  exact value, with no rounding.
- *Weights validity*:
  - missing name, and unknown extra name (through `from_mapping`), each named in the message;
  - negative, NaN and inf (through `from_mapping`, since JSON cannot carry NaN except via Python's
    extension, which `loads_json` would pass to `to_decimal` for rejection);
  - `0/0/0` gives "all weights are zero";
  - `0/0/0.001` is valid;
  - `-0` is treated as zero, so `-0/0/0` is still all-zero;
  - a non-mapping top level is rejected.
- *Version*: `Weights(0.5,0.3,0.2).version == Weights(Decimal("0.50"),…).version`; different weights
  give different versions; the version is stable across processes (a hard-coded expected string).
- *Candidate contract*:
  - missing signal → `RequestError` with `.item_id` and `.signal` set;
  - `1.0000001`, `-0.0001`, NaN, inf, and a string `"0.5"` are each rejected (never clamped);
  - boundaries `0` and `1` are accepted;
  - an empty id and a non-string id are rejected;
  - extra keys on a candidate are ignored (A2).

**test_feed**
- *Empty / one / many*: `candidates=[]` gives `Feed(version, ())`, not an error; one item gives itself;
  many items come out in score-descending order.
- *Ties*:
  - equal scores order by id ascending;
  - code-point order: `"10"` before `"9"`, and `"B"` before `"a"`;
  - the float-trap pair `x`/`y` ranks `x, y`, and the reversed input order gives the same output
    (order does not depend on input).
- *Duplicate id* → `RequestError(item_id="a")`, including when the two duplicates have different signals.
- *One bad item rejects the whole request*: the valid items are not returned, i.e. nothing is dropped.
- *User independence*: the same candidates with different `user` give identical `Feed`s.
- *Version echo*: `rank(req, w).weights_version == w.version`.
- *Purity*: `rank` does not mutate the request (the frozen types make this true by construction; one
  assertion is enough).

**test_config**
- A valid file loads. A missing file, a directory path, invalid JSON, a top-level list and a file with
  an unknown key each give a `ConfigError` whose message contains the path and the problem.
- Numbers from the file are exact (`0.1` in the file is `Decimal("0.1")` in `Weights`).

**test_service** (decision a; sources are lambdas or stubs, with no files)
- *Startup refusal*: a source that raises `ConfigError` makes `FeedService(source)` raise, and no
  instance exists.
- *Reload success between requests*: rank → reload (with new weights) → rank. The two feeds carry
  different versions, and the second is scored with the new weights.
- *Reload failure*: the source raises on its second call, so `reload()` raises `ConfigError`. After
  that, `service.weights` is the old object, and `rank` still works and reports the old version.
- *No mixing within a request (reload during serving)*: set up two valid weight sets V1 and V2 and a
  source that alternates between them.
  - One thread calls `reload()` in a loop.
  - Other threads rank a large request (about 1,000 candidates) repeatedly.
  - For every returned `Feed`, the test looks up V1 or V2 by `feed.weights_version` and asserts that
    every item's score equals `weights.score(candidate)` for *that* version, and that the order matches.

  This asserts the observable guarantee (scores and version are consistent across the whole feed), not
  the mechanism. It is backed by one deterministic test: rank with V1, `reload()` to V2, rank again. The
  first `Feed` is still entirely V1, because values are immutable.
- *No implicit reload*: a source counting its calls is called once at construction and once per
  `reload()`, and never by `rank`.

**test_cli / test_scenario**
- The core scenario end to end: a temp weights file with `0.5/0.3/0.2` and a stdin request `a,b,c` give
  exit 0, items `a, b, c` with scores `"0.58","0.55","0.55"`, and the version string. The test then
  edits the file and runs again (a restart), which gives the new version and the new scores.
- An invalid weights file gives exit 3 and `error: …` on stderr naming the problem. An invalid request
  gives exit 1, naming the item and signal. A missing `--weights` gives exit 2.

**Adversarial-edge checklist → test**
- empty, one and many → test_feed
- duplicate → test_feed
- NaN, inf and negative:
  - signals → test_scoring
  - weights → test_scoring and test_config
- all-zero weights → test_scoring
- unknown key → test_scoring and test_config
- reload failure → test_service
- reload between requests → test_service
- float-equality tie → test_scoring and test_feed
- `"10"` before `"9"` → test_feed

---

## 8. Subtractive pass: kept vs cut

**Kept, each with the present force that requires it**

| Element | Force |
|---|---|
| `Weights` value object | the weight rules plus a version id; the only type that can cross the weights seam |
| `Candidate` value object | the signal contract and the id rule need one home |
| `FeedRequest` | the duplicate-id rule belongs to the request, not to a single item |
| `Feed`, `RankedItem` | the product's output shape (ordered items with scores plus a version) |
| `FeedService` | the only mutable state; decision (a) |
| `WeightsSource` alias | the seam the goal asks for ("ranking depends on weights without knowing where they come from"); it is a type alias, not a class |
| `FeedService.from_file` | every production caller composes exactly this; one line saves each caller from reimplementing it |
| `FeedService.weights` property | an operator must be able to confirm which version is live after a reload without issuing a fake request |
| `exact` module | decision (b) has one home, and three modules need it |
| `config` module | keeps file I/O out of the core and out of the service, which is tested without files |
| `RequestError.item_id` and `.signal` | the product requires naming them; structured fields let tests and callers check them without parsing strings |
| the CLI | the brief asks for a CLI surface; it is the only way to run the core scenario without writing code |

**Cut**

| Cut | Why |
|---|---|
| a `Signals` type (the triple of signals) | its only purpose would have been to break an import cycle, and co-locating `Candidate` with `Weights` does that with one type fewer. Its [0, 1] rule would have needed the item id for messages, which is inappropriate intimacy. |
| an `ItemId` value object | its single rule (non-empty str) has one home in `Candidate`; a wrapper would be a lazy class |
| a `Score` or `WeightsVersion` type | no rules beyond being a Decimal or an opaque string; they are only echoed and compared |
| a `Protocol` / ABC for the weights source | a `Callable[[], Weights]` alias is complete for the one consumer |
| a `Ranker` class or scoring Strategy interface | learned, non-linear and plugin signals are non-goals, so no change-axis would use the seam (§7 tie-break: over-built) |
| a lock | the atomic swap of an immutable value already gives the guarantee (§6a) |
| logging inside the service | reporting the rejection is done by raising to the reload caller; no logging dependency |
| an operator-written `version` field in the config | it would conflict with "exactly the three names", burden the operator, and could lie |
| a CLI `reload` or `check` subcommand | a one-shot CLI has nothing to reload, and `rank` already reports config errors at start |
| a `FeedRankingError` base class | no caller catches "either error" identically; the CLI maps them to different exit codes |
| per-kind error subclasses | no caller distinguishes them |
| rejecting unknown keys on candidates and request objects | not in the product; needed a shared key-set helper with no good home (A2) |
| wrapping candidate errors with a list index | the message already names the item id; for an empty id there is only one such item to fix |
| pytest | `unittest` covers the plan; this keeps the dev dependency diet at zero |

**Concept-fit pass**
- `Weights` is a value (immutable, and its identity is derived from its content). It is not an entity
  with a lifecycle. The lifecycle ("current version") sits in `FeedService`, where it belongs.
- `rank` is a function, because ordering is a transformation, not a thing with state.
- `Candidate` is an input value, not an entity: nothing tracks it across requests.
- Rejection is modelled as an exception, not as a sentinel score (never `-inf` for a bad item) and not
  as dropping the item. A bad signal is not "a low score".
- The tie-break is part of the sort key in `rank`, where ordering lives. It is not folded into the score,
  e.g. no id-derived epsilon added to scores.
- `user` is a field on `FeedRequest` that nothing reads. This is honest: it is identity carried in the
  contract, not a hidden input.

**Smell hunt (axis)**

| Smell checked | Finding |
|---|---|
| Feature envy | `Weights.score(candidate)` reads the candidate's three fields. The formula belongs to the weights ("weights applied to an item"), and the alternative `Candidate.score(weights)` envies the weights equally, so the owner is the one whose rule it is. |
| Shotgun surgery | Adding a fourth signal is a non-goal. It would touch `SIGNAL_NAMES`, `Candidate`, `Weights` and the formula, all in one module (`scoring.py`), so the change is localized, not scattered. |
| Duplication that is real coupling | "JSON numbers are exact" is used by `config` and `cli` and lives in `exact.loads_json`. "Number → finite Decimal" is used by `Candidate` and `Weights` and lives in `exact.to_decimal`. The [0, 1] and ≥ 0 range checks are different rules, so they are not unified. |
| Middle man | `FeedService.rank` is one line that delegates, but it is the snapshot point of decision (a), not a pass-through. |
| Data class | `Feed` and `RankedItem` are output values with no behavior. That is correct for a result, and is not an anemic model of a concept with rules. |

---

## 9. Stated assumptions

- **A1.** The config file is a JSON object `{"recency": n, "affinity": n, "popularity": n}` encoded in
  UTF-8. JSON is the stdlib-parsable format, and TOML would need `tomllib`, which is equally stdlib but
  a second choice for no gain.
- **A2.** Unknown keys on a candidate and on the request object are ignored. The product requires
  exact key sets only for the weights. Callers may pass richer item objects, and an ignored key cannot
  enter the score, because the score reads three named fields. A typo'd signal name still fails as
  "missing".
- **A3.** `user` must be a string. An empty string is allowed, because no rule is stated. It is not
  echoed in the `Feed`, because the product's output lists items, scores and the version only.
- **A4.** When two reloads overlap, the last to finish wins. No ordering between overlapping operator
  reloads is specified.
- **A5.** Scores are presented in the CLI as exact decimal strings.
