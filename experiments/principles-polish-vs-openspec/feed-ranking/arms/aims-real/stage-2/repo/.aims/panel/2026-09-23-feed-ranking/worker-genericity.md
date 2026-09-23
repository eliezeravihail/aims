# Feed ranking, stage 1: design (axis: correct genericity)

Design only. Signatures and a few lines of code appear where they pin down a boundary. Nothing here is
an implementation.

## 0. The genericity stance in one paragraph

Every seam uses the **least specific type that is still complete for its consumer**, and nothing more
general than every producer can honestly supply. The change axes are **known**, so the calibration
is not guesswork. They are listed in §1. The design absorbs exactly those axes:

- **X1:** the weight values change (operator, no code).
- **X2:** a reload lands while requests are in flight, or fails.
- **X3:** where weights come from. Today that is a TOML file; tests use an in-memory value.
- **X4:** the entry path (library call or CLI).

It does **not** generalize over the non-goals: the signal set (no plugins), per-user weights,
non-linear scoring, filters. So the three signals are three named fields, not a `Mapping[str, Decimal]`.
The score is one explicit formula, not a `Scorer` strategy. The weight source is a plain
`Callable[[], Weights]`, not a `WeightSource` class hierarchy.

## 1. Change axes and what absorbs each one

| Axis | Absorbed by | Change cost |
|---|---|---|
| X1 weight values change | TOML file + `FeedService.reload()` | Edit the file and reload. No code change. |
| X2 reload races or fails | Immutable `Weights` snapshot, read once per request. Swap only on successful load. | None: this holds by construction. |
| X3 weight source | `WeightLoader = Callable[[], Weights]` injected into `FeedService` | Write a new zero-arg function. The core and service are untouched. |
| X4 entry path | The CLI is a thin adapter over the same `FeedService`, `Candidate` and `FeedRequest`. | A new adapter. The rules do not move. |
| *not an axis:* signal set | Three named fields plus the `SIGNAL_NAMES` constant | Would touch `signals`, `weights` and `candidates`. Accepted: plugins are a non-goal. |
| *not an axis:* per-user weights | Not built. The core takes `Weights` **by value**, so a later "choose which Weights" step would not reopen the core. That falls out for free; nothing is built for it. | n/a |

## 2. Module skeleton

The package is `feedrank/`, standard library only. Dependencies point downward: each module lists only
modules that appear above it.

```
feedrank/
  signals.py      SIGNAL_NAMES, SignalValue, exact_number()      (foundation: the basis + number repr)
  weights.py      Weights, WeightConfigError                      -> signals
  candidates.py   Candidate, FeedRequest, InvalidRequest          -> signals
  ranking.py      FeedEntry, Feed, rank_feed()                    -> weights, candidates   (pure core)
  service.py      FeedService, WeightLoader                       -> weights, candidates, ranking
  config_file.py  load_weights_file()                             -> weights               (TOML adapter)
  cli.py          main(), JSON request/feed adapter               -> service, config_file, candidates
  __main__.py     calls cli.main()
  __init__.py     re-exports the public names below
```

- **Functional core:** `signals`, `weights`, `candidates` and `ranking` are pure, immutable and do no I/O.
- **Imperative shell:** `service` holds the one piece of mutable state (the current `Weights`
  reference). `config_file` and `cli` do the I/O.
- **Separation from config:** `ranking` never imports `service` or `config_file`. The core does not know
  that weights come from a file, that they can be reloaded, or that a service exists.

## 3. Numeric representation (hard decision b, stated first because every type depends on it)

**Decision.**

- Signals, weights and scores are all `decimal.Decimal`.
- Every score is computed **exactly**, in a module-private context:
  `Context(prec=MAX_PREC, traps=[Inexact, InvalidOperation])`.
- "Equal score" means **`Decimal` equality of the exact sums**. Exact equality means the mathematical
  value of the decimal numbers the producer supplied. There is no epsilon and no rounding.

**What gets converted, and how.** `signals.exact_number(value) -> Decimal` is the single owner of
"what counts as a number here":

| Input | Result |
|---|---|
| `Decimal` | Taken as-is, then checked to be finite. |
| `int` (but not `bool`) | `Decimal(value)` |
| `float` | `Decimal(repr(value))`: the shortest decimal that round-trips to that float. Non-finite floats are rejected. |
| `bool`, `str`, `None`, anything else | Rejected: "not a number" (`None` gives "missing"). |
| `-0` | Normalized to `0`, so a score can never print as `-0`. |

**How each boundary produces exact values.**

- **TOML config:** `config_file` parses with `tomllib.load(fp, parse_float=Decimal)`. The text
  `0.1` becomes `Decimal('0.1')` directly. TOML's `nan` and `inf` also arrive as `Decimal` and are
  rejected as non-finite.
- **CLI request JSON:** parsed with `json.loads(parse_float=Decimal)`. `NaN` and `Infinity` arrive as
  float and are rejected by `exact_number`.
- **Library callers:** may pass `Decimal`, `int` or `float`.

**The trap from the brief.** Weights r=0.1, a=0.2. Item x has r=0.3; item y has a=0.15.

- Both scores are exactly `Decimal('0.03')`. They are equal, so id ascending decides.
- Binary float gives `0.030000000000000002` vs `0.03`. The item that wins would be picked by
  rounding noise, not by id.

**Why not the alternatives.**

- **Float with exact `==`.** The tie rule would be decided by binary representation error, not by the
  numbers the product talks about. Which item "wins" would depend on which weight happened to carry
  which rounding error. That is deterministic but dishonest: the rule says *equal* scores go by id, and
  0.03 = 0.03.
- **Float with an epsilon.** The PO said exact, no epsilon. An epsilon is also not transitive
  (a≈b, b≈c, a≉c), so the sort key stops being a total order and the output depends on input order.
- **Rounding scores to N places.** This is arbitrary, and it merges genuinely unequal scores into
  false ties. It is an epsilon under another name.
- **`Decimal(float)` (binary-exact conversion).** This is exact about the *binary* value, so it brings the
  trap back. Checked: `0.1·0.4` vs `0.5·0.08` are equal as decimals, but
  `Decimal(0.1)*Decimal(0.4) != Decimal(0.5)*Decimal(0.08)`. The shortest-repr conversion is injective,
  so distinct floats stay distinct, and it recovers the decimal the caller wrote.
- **`fractions.Fraction`.** Exact too, but every input is a finite decimal, so `Decimal` is already exact
  under the right context. `Decimal` also prints a score a person can read (`0.58`, not `29/50`).
  Fraction brings no extra power.
- **`Decimal` in the default context (prec 28).** Rejected: this is a real trap. Two 17-digit signals
  multiply to 34 digits and get silently rounded. Two unequal exact scores can then round equal (a false
  tie), or the reverse. So the exact context is required. The `Inexact` trap makes "exactness was lost"
  an immediate crash, never a silently wrong order. It cannot fire for `*` and `+` at `MAX_PREC`; it is
  the stated invariant made loud.

**Cost.** `Decimal` is slower than float. There is no performance requirement (§13 is conditional),
and C `_decimal` handles a few hundred candidates easily. Noted, not optimized.

## 4. Types crossing each seam

All are `@dataclass(frozen=True, slots=True)` unless noted.

```python
# signals.py
SIGNAL_NAMES: Final = ("recency", "affinity", "popularity")   # the one list of signal names
SignalValue: TypeAlias = Decimal | int | float                  # what a producer may hand in
def exact_number(value: object) -> Decimal: ...                 # raises ValueError(reason); internal
```

```python
# weights.py
class WeightConfigError(Exception):
    """A weight config was rejected. str(err) names the problem (and the file, when there is one)."""

@dataclass(frozen=True, slots=True)
class Weights:
    recency: Decimal
    affinity: Decimal
    popularity: Decimal
    version: str = field(init=False)     # derived: content id of the (normalized) values

    def __post_init__(self) -> None: ...  # exact_number each; finite, >= 0; at least one > 0; set version
    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> "Weights": ...   # exactly SIGNAL_NAMES as keys
    def score(self, candidate: "Candidate") -> Decimal: ...             # THE formula, exact context
```

**Notes on `Weights`.**

- Construction accepts `SignalValue` per field. `__post_init__` normalizes each one through
  `exact_number`, so every path funnels through the same check.
- `score(candidate)` takes the `Candidate` itself. That is the complete and least type: it needs exactly
  the three signals, and `Candidate` is their only carrier. A `HasSignals` Protocol would be a decorative
  interface with one implementer.
- **`version` is derived from content, not minted.** It is the first 12 hex characters of the SHA-256 of
  the canonical text `"affinity=<a>;popularity=<p>;recency=<r>"`. Each value is normalized fixed-point,
  so `0.50` and `0.5` give the same id.
- **Why derive the version.** Every producer can honestly supply it: a file, a test lambda, or any
  future source. No producer has to invent ids or counters. It is stable across restarts, and the same
  weights always get the same id.
- **Rejected version schemes.** A reload counter is not restart-stable, and every source would have to
  share it. An operator-written `version` key would add a config field no one asked for, and would break
  "exactly the three names". File mtime or path depends on the source, so it fails the ceiling for
  non-file producers.
- **Assumption:** "id of the weight config used" is satisfied by a content id.

```python
# candidates.py
class InvalidRequest(Exception):
    item_id: str | None     # the offending item, when one is identifiable
    signal: str | None      # the offending signal, when the problem is a signal
    problem: str            # human text: "missing", "not a number", "not finite", "outside [0, 1]",
                            # "empty id", "duplicate id", "malformed request: ..."

@dataclass(frozen=True, slots=True)
class Candidate:
    item_id: str
    recency: Decimal
    affinity: Decimal
    popularity: Decimal
    def __post_init__(self) -> None: ...  # id: str, non-empty; each signal via exact_number, in [0, 1]

@dataclass(frozen=True, slots=True)
class FeedRequest:
    user: str
    candidates: tuple[Candidate, ...]    # accepts any Iterable[Candidate]; stored as tuple
    def __post_init__(self) -> None: ...  # tuple-ize; user is str; reject duplicate item_id
```

**Notes on the request types.**

- `Candidate` fields accept `SignalValue` or `None`. `None` means "absent", so the rule that all three
  signals must be present has one owner. The JSON adapter passes `obj.get(name)`.
- The error carries `item_id` and `signal` as structured fields because the product requires the error
  to *name* them. Tests assert the fields, not the message text.
- `FeedRequest.candidates` accepts **`Iterable[Candidate]`**, the weakest thing a producer can supply
  (a list, a generator, a query result). It is materialized once to a tuple, because the duplicate check
  and the sort both need to iterate it. Asking for a `Sequence` would over-constrain producers.
- `user`: the only rule is "is a `str`". Assumption: no emptiness rule was stated, so none is invented.

```python
# ranking.py   (pure core)
@dataclass(frozen=True, slots=True)
class FeedEntry:
    item_id: str
    score: Decimal

@dataclass(frozen=True, slots=True)
class Feed:
    user: str                          # carried identity, echoed; not used in ranking
    weights_version: str
    entries: tuple[FeedEntry, ...]     # score desc, then item_id ascending (code point)

def rank_feed(weights: Weights, request: FeedRequest) -> Feed: ...
```

- **`FeedEntry` is id + score only.** That is the consumer's floor: "each with its computed score".
  Returning the full `Candidate` would re-expose signals the caller already has.
- **`rank_feed` is the whole ranking rule.** It scores each candidate with `weights.score`, sorts by the
  key `(-score, item_id)`, and stamps `weights.version`, all from the **one** `Weights` value it
  received. It has no path to any holder, so it cannot re-read weights mid-request.
- **`user` never enters the core's decision.** `rank_feed` only copies it into the `Feed`. The sort key
  and `score` never see it; the shape does not invite it.

```python
# service.py   (the imperative shell around the core)
WeightLoader: TypeAlias = Callable[[], Weights]   # returns valid Weights or raises WeightConfigError

class FeedService:
    def __init__(self, load_weights: WeightLoader) -> None: ...  # loads once; raises => no service
    def rank(self, request: FeedRequest) -> Feed: ...             # query: one snapshot, then rank_feed
    def reload(self) -> None: ...                                  # command: load; swap on success only
```

- **Why the weight seam is `Callable[[], Weights]` and not a Protocol or ABC.** The consumer
  (`FeedService`) needs exactly one ability: "give me fresh valid weights". A zero-argument callable is
  that ability and nothing more.
- **Every producer can supply it:** `functools.partial(load_weights_file, path)`, `lambda: Weights(...)`
  in tests, and any future source.
- **Validity is guaranteed by construction, not by trusting the loader.** A loader can only return a
  `Weights`, and a `Weights` can only exist valid.

```python
# config_file.py   (adapter: TOML text -> Weights)
def load_weights_file(path: Path) -> Weights: ...
```

**Config file format:** a flat TOML table containing exactly the three weights.

```toml
recency = 0.5
affinity = 0.3
popularity = 0.2
```

- TOML because it is in the stdlib (`tomllib`, 3.11), friendly for operators to edit, rejects duplicate
  keys natively, and supports `parse_float=Decimal` so the operator's `0.1` stays exact.
- **Rejected: JSON config.** Python's `json` silently keeps the last of duplicate keys. It would need a
  hook just to get safety that TOML already has.
- This adapter translates `OSError` and `tomllib.TOMLDecodeError` into `WeightConfigError("<path>: …")`.
  It then delegates *all* weight rules to `Weights.from_mapping` and prefixes the path onto any
  rejection.

### Public API (`feedrank/__init__.py`)

`Weights`, `WeightConfigError`, `Candidate`, `FeedRequest`, `InvalidRequest`, `Feed`, `FeedEntry`,
`FeedService`, `WeightLoader`, `SignalValue`, `load_weights_file`.

`rank_feed` stays module-level in `feedrank.ranking`. Tests import it directly, but it is not advertised:
the product's entry is the service, which owns version consistency.

```python
service = FeedService(partial(load_weights_file, Path("/etc/feedrank/weights.toml")))
feed = service.rank(FeedRequest("u1", [Candidate("a", recency=0.9, affinity=0.1, popularity=0.5)]))
service.reload()        # raises WeightConfigError on a bad file; service keeps the old Weights
```

### CLI surface

```
python -m feedrank rank --weights PATH [--request FILE]      # request JSON from FILE or stdin
```

**Input:**

```json
{"user": "u1", "candidates": [{"id": "a", "recency": 0.9, "affinity": 0.1, "popularity": 0.5}]}
```

**Output** (stdout):

```json
{"user":"u1","weights_version":"…","feed":[{"id":"a","score":"0.58"}]}
```

**Behavior:**

- Scores are emitted as JSON **strings** of the normalized fixed-point `Decimal`. A JSON number would be
  re-parsed as a float by most consumers and would lose the exactness the tie rule depends on.
  Formatting is the CLI's job; the library returns `Decimal`.
- The CLI adapter checks JSON shape only: a top-level object, `user` is a string, `candidates` is an
  array of objects, and each object's keys are a subset of `{"id", *SIGNAL_NAMES}`.
- **Assumption:** unknown keys on a candidate are rejected. This fails fast on misspelt signal names;
  none was said to be tolerated. Everything else goes to `Candidate` and `FeedRequest`.
- Shape errors become `InvalidRequest(item_id=<id if known>, signal=None, problem="malformed request: …")`.
  Errors are prefixed with the candidate's position (`candidates[3]`) so an empty id is still locatable.

| Exit code | Meaning |
|---|---|
| 0 | Feed printed |
| 1 | Request rejected (`InvalidRequest`, printed on stderr) |
| 2 | argparse usage error |
| 3 | Weight config rejected at startup: the process refuses to rank (`WeightConfigError` on stderr) |

- The CLI is one-shot, so "restart" is its reload. The explicit reload call lives in the library API.
  The CLI has no reload subcommand: a one-shot process has nothing to reload *into*.

## 5. Hard decision (a): where "one valid weight version per request" lives

**Decision.** The rule is owned by **`FeedService.rank`**. It reads `self._weights` **exactly once** into
a local, and hands that immutable value to `rank_feed`, which scores, sorts and stamps the version from
that single object. Two structural facts make this sufficient:

1. **No invalid or partial `Weights` can exist.** `Weights.__post_init__` is the only construction path,
   and it validates all three fields before the object escapes. The value is frozen, and its fields are
   immutable `Decimal`s.
2. **The swap is a single reference store, done only after a successful load.**

   ```python
   def reload(self) -> None:
       with self._reload_lock:              # serializes reloads, never taken by rank()
           fresh = self._load_weights()     # may raise -> nothing assigned, old weights stay
           self._weights = fresh            # one reference store
   ```

   `__init__` calls the same private `_load_weights` path. A raise there means no `FeedService` object
   exists, which is "the service refuses to start".

**Concurrency.** A request that started before a swap holds its local reference to the old `Weights` and
finishes with it. A request that starts after the swap sees the new one. There is no mix.

- A single attribute load or store of a reference is atomic in CPython, including free-threaded builds.
  Since the referent is immutable, there is nothing to tear.
- `rank()` takes **no lock**. Readers never wait on a reload's file I/O.
- The reload lock exists for one present force: two concurrent reloads must not interleave. Without it,
  A could load an older file, B could load a newer one and store it, and then A would store the stale
  value.

**"Reports the rejection."** `reload()` raises `WeightConfigError`. The exception *is* the report, to
whoever called reload. It keeps command–query separation: reload changes state and returns nothing.
Afterwards the service is observably unchanged, because the next `Feed.weights_version` is the old one.
Any other exception from a custom loader also propagates without a swap.

**Rejected alternatives.**

- **A read-write lock held for the whole ranking pass.** It is correct, but it only buys what
  immutability already gives, and it makes requests wait on reload I/O.
- **Passing the service or holder into the core.** The core could re-read weights between items. That
  is exactly the mix the rule forbids, and the core would then know weights are reloadable.
- **A mutable `Weights` updated field by field.** Partial states would become representable.
- **Validating in `reload()` before assigning.** That would be a second owner of weight validity. The
  constructor already owns it.
- **Storing `last_error` on the service.** No consumer reads it. The caller of `reload()` already holds
  the exception.

## 6. Error vocabulary

There are two public error types, one per distinct handling. There is no base class (see §9).

| Error | Raised by | Handling | Example messages |
|---|---|---|---|
| `WeightConfigError` | `Weights` (values), `Weights.from_mapping` (names), `load_weights_file` (I/O, TOML syntax) | Startup: the service does not exist (CLI exit 3). Reload: old weights kept, caller reports. | `weights.toml: missing weight 'popularity'`; `unknown weight 'freshness'`; `weight 'recency' is negative (-0.1)`; `weight 'affinity' is not finite (NaN)`; `weight 'recency' is not a number ('0.5')`; `all weights are zero; at least one must be > 0`; `cannot read weights.toml: No such file or directory`; `invalid TOML: … (line 3)` |
| `InvalidRequest(item_id, signal, problem)` | `Candidate`, `FeedRequest`, the CLI JSON adapter | Request rejected whole; nothing ranked (CLI exit 1). | `item 'b': signal 'affinity' is outside [0, 1] (1.2)`; `item 'b': signal 'recency' is missing`; `item 'c': signal 'popularity' is not finite (NaN)`; `candidates[2]: empty id`; `item 'a': duplicate id`; `malformed request: 'candidates' must be an array` |

- **`ValueError` from `exact_number` is internal.** `Weights` and `Candidate` catch it and translate it
  into their own error, adding the name. It never crosses a public seam.
- **The `Inexact` or `InvalidOperation` trap is left uncaught** if it ever fires. It would be an
  unactionable bug in the design's own invariant, so it falls instead of being wrapped.

## 7. Rule ownership

The entry paths are:

- **L:** `FeedService.rank` (library)
- **C:** CLI `rank`
- **S:** startup (`FeedService.__init__`, reached by a library caller and by the CLI)
- **R:** `FeedService.reload`

| Rule | Owner (one) | Entry paths that reach it, and how |
|---|---|---|
| What counts as a number (finite, not bool or str, exact decimal; -0 becomes 0) | `signals.exact_number` | L, C via `Candidate`; S, R via `Weights` |
| Weights: exactly the three names (missing or unknown is invalid) | `Weights.from_mapping` (with `SIGNAL_NAMES`) | S, R via `load_weights_file` to `from_mapping`; a library caller building from a dict uses the same method |
| Weights: each finite and ≥ 0, at least one > 0, never rescaled | `Weights.__post_init__` | S, R (file), plus any direct `Weights(...)` built by a library caller or a test |
| Config file syntax and readability become a named error | `config_file.load_weights_file` | S, R when the loader is the file loader; C always (S) |
| Invalid at startup: refuse to start | `FeedService.__init__` (does not catch) | S (library); C maps it to exit 3 |
| Invalid on reload: keep last valid and report | `FeedService.reload` (assigns only after the load returns; raises) | R |
| Weight version id | `Weights.version` (derived) | Stamped into every `Feed` by `rank_feed`: L, C |
| One weight version per request (no mix, no partial) | `FeedService.rank` (single snapshot read) plus `Weights` immutability | L, C (the CLI calls `service.rank`) |
| Signal contract: present, finite, in [0, 1]; error names item and signal | `Candidate.__post_init__` | L (the caller constructs `Candidate`); C (the adapter passes `obj.get(name)` into `Candidate`) |
| Item id is a non-empty `str` | `Candidate.__post_init__` | L, C |
| No duplicate ids in a request | `FeedRequest.__post_init__` | L, C |
| Request JSON shape (object, arrays, no unknown keys) | `cli` adapter | C only. This is a representation rule, not a product rule, so there is no second owner. |
| Score = w_r·r + w_a·a + w_p·p, exact, nothing else | `Weights.score` | L, C via `rank_feed` |
| Order: score desc, then id ascending by code point | `rank_feed` sort key `(-score, item_id)` | L, C |
| Empty candidates gives an empty feed | Falls out of `rank_feed`: no special case, it returns `Feed(entries=())` | L, C |
| `user` does not affect score or order | Structural: neither `Weights.score` nor the sort key receives `user` | L, C |
| Score display (fixed-point string) | `cli` | C |

## 8. Test plan (test-first)

Tests are written before each module and use `unittest`/stdlib. They exercise the core without I/O.

| Decision | Tests (all assert observable behavior) |
|---|---|
| **Numbers** (`exact_number` through `Weights` and `Candidate`) | `float('nan')`, `float('inf')`, `-inf`, `Decimal('NaN')`, `Decimal('sNaN')`, `Decimal('Infinity')` are rejected as not finite. `True` is rejected as not a number (bool is not a number). `"0.5"` is rejected as not a number. `None` is rejected as missing. `0.1` becomes `Decimal('0.1')`, not the binary expansion. `-0.0` is accepted as 0. |
| **Weights: names** | Missing `popularity` gives an error naming it. An extra `freshness` gives an error naming it. An empty mapping names all missing weights. |
| **Weights: values** | A negative weight is rejected. NaN/inf are rejected. All-zero is rejected. `{1, 0, 0}` is accepted. Weights summing to 3.7 are accepted, and scores are not rescaled (assert the exact score). `0.50` and `0.5` give the same `version`. Different weights give different `version`s. |
| **Config file** (`tmp_path`) | Valid file: the weights are equal. Missing file, unreadable file, TOML syntax error, duplicate key, `nan` literal, and string value each raise `WeightConfigError` whose text contains the path and the problem. |
| **Startup** | `FeedService(loader_that_raises)` raises and no instance exists. CLI with a bad weights file exits 3, prints nothing on stdout, and the stderr message names the problem. |
| **Reload** | A loader backed by a mutable test cell. Valid → valid: the next `rank` shows the new `weights_version` and new scores. Valid → invalid: `reload()` raises `WeightConfigError`, and the next `rank` still uses the old version and old scores. Invalid → valid again recovers. A loader raising an arbitrary `RuntimeError` also leaves the old weights. |
| **Reload between requests** | rank, reload, rank: the two feeds carry different versions, and each feed's scores match its own version exactly. |
| **Reload during a request (no mix)** | Inject a `Weights` snapshot, then call `rank_feed` directly while the service reloads. Deterministic form: a loader that swaps the service's weights *from inside* a candidate iteration is not possible, because the request is materialized first. So we assert structurally: 1) `rank_feed` depends on its `weights` argument only (it gives the same result regardless of later service state). 2) A threaded stress test: N threads rank while one thread reloads between two weight sets, and every feed's scores equal `rank_feed(W_version, request)` for the version it reports. |
| **Concurrent reloads** | Two threads reload with loaders returning A and B in a forced order (with barriers). The final version is the one whose load finished last *under the lock*, with no stale overwrite. |
| **Candidates** | For each signal: missing, `None`, NaN, inf, `-0.01`, `1.01`, string, bool. Each is rejected with `item_id` and `signal` set. Exactly `0` and exactly `1` are accepted. An empty id is rejected. A non-str id is rejected. A duplicate id is rejected with `item_id` set. One bad item among many rejects the whole request, and no partial feed is returned. |
| **Ordering** | Empty gives `Feed(entries=())`. One item gives one entry. Many items come back in score-descending order. Exact tie: ids `"9"` and `"10"` give `"10"` first (code point). The goals.md core scenario gives `a (0.58), b (0.55), c (0.55)`. |
| **Float-equality tie** | Weights r=0.1, a=0.2, p=0. Items `y` (r=0.3) and `x` (a=0.15) give scores exactly equal, ordered `x`, `y` by id. The same data passed as Python floats gives the same result. `0.1·0.4` vs `0.5·0.08` also ties. The regression guard fails if anyone switches to float or to `Decimal(float)`. |
| **Precision** | 17-significant-digit signals and weights. Two candidates whose exact scores differ in the 30th digit are ordered by score, not tied. This guards against the default prec-28 context. |
| **`user` independence** | The same candidates with different `user` values give identical entries. |
| **CLI** | The golden request produces the golden JSON (scores as strings). A malformed request (not an object, missing `candidates`, unknown key) exits 1 with the position named. JSON `NaN` input exits 1, naming item and signal. |

The pyramid: most tests are pure unit tests on `Weights`, `Candidate`, `FeedRequest` and `rank_feed`. There
are a few service tests with an in-memory loader, and a handful of file/CLI tests.

## 9. Subtractive pass (each element, and the present force that keeps it)

**Kept:**

| Element | Force |
|---|---|
| `exact_number` | One owner for "what is a number". Both weights and signals need it, and hard decision (b) depends on it. |
| `SIGNAL_NAMES` | The exact-names rule for weights and the unknown-key check in the JSON adapter both need the one list. |
| `Weights` (with `version`) | The weight-validity rule, the formula, and the version id. It is the value that crosses the seam. |
| `Candidate` | The signal contract and the id rule, with the item named in errors. |
| `FeedRequest` | The duplicate-id rule, and the carried `user`. |
| `FeedEntry` and `Feed` | The required output shape (ordered entries with score, plus version). |
| `rank_feed` | Order, tie-break and version stamping from one snapshot. It is pure and testable without a service. |
| `FeedService` | The only mutable state: current weights, startup refusal, reload fallback. |
| `WeightLoader` alias | Axis X3: the core and service must not know the source. The alias names the seam; it adds no class. |
| Reload lock | Reloads can race each other (stale overwrite). |
| `load_weights_file` | Weights come from a config file (stated). |
| CLI | "A library with an optional small CLI". It is the operator-visible path for "refuses to start". |
| Two error types | Two distinct handlings: config rejected vs request rejected. |

**Cut:**

- A `WeightSource` Protocol or ABC and a `FileWeightSource` class. A callable suffices, so a named
  interface would be decorative.
- A `Scorer` or strategy interface. The formula is fixed; non-linear ranking is a non-goal.
- A `Signals` value type separate from `Candidate`. It would split the signal-contract error from the
  item id it must name. `Candidate` is the only carrier.
- An `ItemId` value type. Its only rule (non-empty str) is owned by `Candidate`, and its ordering is plain
  `str` order. A wrapper would add ceremony at every call site without absorbing any axis.
- A `Score` type or alias. It is a plain `Decimal`.
- A `FeedRankingError` base class. No handler catches "either".
- `FeedService.from_file`. It would make `service` depend on `config_file` (the shell's policy depending
  on a detail). `functools.partial` at the composition root does the same job.
- A `weights_version` query on the service, and a stored `last_reload_error`. No consumer needs them:
  `Feed` carries the version, and the exception carries the rejection.
- A CLI `validate` subcommand and a CLI `reload` subcommand. The first has no stated need; the second
  has nothing to reload in a one-shot process.
- A read-write lock or a lock on the request path. Immutability already gives the guarantee.
- Version counters, operator version labels, and file mtimes. See §4.
- Candidate metadata passthrough. Not asked for.
- Any `Mapping[str, Decimal]`-style generic weights or signals. The signal set is not a change axis.

**Concept-fit pass:**

- `Weights` is a configuration *value*. It is not a "config file object": it knows nothing of paths.
- The version is the *identity of those values*, a derived attribute, not a separately managed counter.
- A rejected config is an *exception*, never a sentinel `Weights` or a zero-weights stand-in.
- An empty feed is a `Feed` with no entries, not an error and not `None`.
- The tie-break is a *component of the sort key*, never a score perturbation such as an id-derived
  epsilon added to the score. A sequence rule is not modelled as a score.
- Absence of a signal is modelled as `None`, rejected by the owner of presence. It is not a default `0`,
  which would be zero-filling, explicitly forbidden.
- `user` is identity carried *alongside* the ranking, not a parameter of it.
- The CLI's JSON shape rule is a representation rule of that adapter, not a second owner of any product
  rule.

## 10. Principles that don't apply at this scale (and why)

- **§14 security:** there is no trust boundary beyond input validation, which is already covered.
- **§13 performance:** no requirement is stated. `Decimal` cost is noted in §3.
- **Layering and hexagonal architecture:** present only as core vs shell. A separate "ports" package for
  one callable port would be structure no axis uses.
- **Idempotency:** `reload()` is naturally idempotent. Reloading an unchanged file yields an equal
  `Weights` with the same `version`.
