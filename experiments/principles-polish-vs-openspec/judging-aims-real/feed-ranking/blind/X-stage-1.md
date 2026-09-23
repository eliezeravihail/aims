# Design X — stage 1

# Feed ranking — stage 1 architecture

Design only. The signatures below pin the boundaries; there is no implementation. Product decisions and
their provenance are in [`goals.md`](goals.md); the substrate is in [`base-dependencies.md`](base-dependencies.md).

## 1. Shape

A **pure core** and a **thin shell**.

- **Core** (no I/O, no mutable state): `Weights` is one validated, immutable weight version that owns the
  score formula and derives its own version id. `Candidate` is one validated item. `FeedRequest` is one
  validated request. `rank_feed(weights, request)` owns the order.
- **Shell**: `FeedService` holds the only mutable state, which is the current `Weights` reference. It
  owns startup refusal, reload fallback, and the rule that each request uses exactly one weight version.
  It gets weights from an injected zero-argument callable, so it never knows where weights come from.
  `config_file` turns a TOML file into `Weights`. `cli` is a one-shot JSON adapter.
- **Numbers** are exact decimals (§6). One module owns what "a number" means; another owns which signals
  exist.

```
feed_ranking/
  __init__.py      public re-exports (§3); no logic
  __main__.py      raise SystemExit(cli.main())
  numbers.py       Number, exact_number(), canonical_text(), EXACT context             [core foundation]
  signals.py       SIGNAL_NAMES, read_signal_fields()                                  [core foundation]
  weights.py       Weights, WeightConfigError                                          [core]  -> numbers, signals
  request.py       Candidate, FeedRequest, InvalidRequest                              [core]  -> numbers, signals
  ranking.py       RankedItem, Feed, rank_feed()                                       [core]  -> weights, request
  service.py       FeedService, WeightLoader                                           [shell] -> weights, request, ranking
  config_file.py   load_weights_file()                                                 [shell] -> weights
  cli.py           main()                                                              [shell] -> service, config_file, request, numbers
```

Imports are acyclic and point toward `numbers` and `signals`, which import nothing from the package. The
core never imports `service`, `config_file` or `cli`.
The only dependency is the standard library (`decimal`, `hashlib`, `tomllib`, `json`, `argparse`,
`threading`, `dataclasses`, `functools`). Tests use `unittest`.

## 2. Change axes the shape absorbs, and those it deliberately doesn't

| Axis | Absorbed by | Cost of the change |
|---|---|---|
| Weight values change (operator) | TOML file + `FeedService.reload()` | Edit the file and reload; no code |
| A reload fails, or lands during requests | Immutable `Weights`; one snapshot read per request; swap only after a full load | None: holds by construction |
| Where weights come from | `WeightLoader = Callable[[], Weights]` injected into `FeedService` | A new zero-argument function; core and service untouched |
| Entry path (library or CLI) | CLI is an adapter over the same public types | A new adapter; no rule moves |
| *Not an axis:* the signal set, the formula, per-user weights | Three named fields and one formula | A 4th signal would touch `signals.SIGNAL_NAMES`, `Weights`, `Candidate`. Accepted: stage 1 says three |

## 3. Public surface

```python
# numbers.py, signals.py (internal foundation; not re-exported)
Number: TypeAlias = int | float          # what a producer may hand in for a signal or weight
def exact_number(x: object) -> Decimal: ...      # ValueError "not a number" / "not finite"
def canonical_text(d: Decimal) -> str: ...       # the one printed form of a value (§7)
SIGNAL_NAMES: Final = ("recency", "affinity", "popularity")
def read_signal_fields(raw: Mapping[str, object], leading: tuple[str, ...] = ()) -> dict[str, object]: ...
                                          # keys exactly leading + SIGNAL_NAMES; ValueError "missing 'x'" / "unknown 'y'"

# weights.py
class WeightConfigError(Exception):
    problem: str                          # e.g. "missing weight 'popularity'"
    source: str | None                    # e.g. the file path; None when built in code

@dataclass(frozen=True, slots=True, init=False)   # eq, hash, repr generated from the fields
class Weights:
    recency: Decimal                      # stored canonical (§6)
    affinity: Decimal
    popularity: Decimal
    def __init__(self, *, recency: Number, affinity: Number, popularity: Number) -> None: ...
                                          # each exact_number, >= 0; at least one > 0 -> else WeightConfigError
    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> "Weights": ...   # key set exactly SIGNAL_NAMES
    @property
    def version(self) -> str: ...         # "w-" + sha256(canonical text)[:16]  (§7)
    def score(self, candidate: "Candidate") -> Decimal: ...   # THE formula, in EXACT

# request.py
class InvalidRequest(Exception):
    problem: str                          # "outside [0, 1] (1.2)", "missing", "duplicate id", ...
    item_id: str | None                   # the offending item when identifiable
    signal: str | None                    # the offending signal when the problem is a signal

@dataclass(frozen=True, slots=True, init=False)
class Candidate:
    item_id: str
    recency: Decimal
    affinity: Decimal
    popularity: Decimal
    def __init__(self, item_id: str, *, recency: Number, affinity: Number, popularity: Number) -> None: ...
                                          # id non-empty str; each signal exact_number, in [0, 1]
    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> "Candidate": ...  # keys exactly {"id", *SIGNAL_NAMES}

@dataclass(frozen=True, slots=True, init=False)
class FeedRequest:
    user: str
    candidates: tuple[Candidate, ...]
    def __init__(self, user: str, candidates: Iterable[Candidate]) -> None: ...  # user is str; no duplicate item_id

# ranking.py
@dataclass(frozen=True, slots=True)
class RankedItem:
    item_id: str
    score: Decimal

@dataclass(frozen=True, slots=True)
class Feed:
    weights_version: str
    items: tuple[RankedItem, ...]         # score desc, then item_id asc (code point); () when no candidates

def rank_feed(weights: Weights, request: FeedRequest) -> Feed: ...

# service.py
WeightLoader: TypeAlias = Callable[[], Weights]   # returns valid Weights or raises WeightConfigError

class FeedService:
    def __init__(self, load_weights: WeightLoader) -> None: ...   # loads once; raise => no service
    def rank(self, request: FeedRequest) -> Feed: ...
    def reload(self) -> None: ...                                  # load, then swap; raise => unchanged

# config_file.py
def load_weights_file(path: str | os.PathLike[str]) -> Weights: ...

# cli.py
def main(argv: Sequence[str] | None = None) -> int: ...
```

Typical embedding:

```python
service = FeedService(functools.partial(load_weights_file, "/etc/feed_ranking/weights.toml"))
feed = service.rank(FeedRequest("u1", [Candidate("a", recency=0.9, affinity=0.1, popularity=0.5)]))
service.reload()          # WeightConfigError on a bad file; the service keeps its previous weights
```

`__init__` re-exports `Weights`, `WeightConfigError`, `Candidate`, `FeedRequest`, `InvalidRequest`,
`RankedItem`, `Feed`, `FeedService`, `WeightLoader` and `load_weights_file`. That is the contract.
`rank_feed`, `numbers` and `signals` stay internal. Tests import `feed_ranking.ranking` directly.

**Construction contract.** The value types write their own `__init__`, so the published signature is
true: it takes `Number` and the attributes are `Decimal`. `init=False` keeps the generated equality, hash
and repr. Signals and weights are keyword-only, so a call can't swap two of them by position. **Arity is
Python's rule; values are the product's.** A missing or unknown keyword is a `TypeError`: a programming
error in the caller's source that a type checker flags, not a rejected request. Every *value*, including
`None` or `"0.5"`, is data, and the constructor rejects it naming item and signal. Data whose key set is
only known at run time goes through `from_mapping`, the one owner of "missing" and "unknown". Reporting
those from the constructor would need sentinel defaults, which make the signature lie that signals are
optional and create a second owner.

## 4. Seams and the types that cross them

| Seam | Crosses | Never crosses |
|---|---|---|
| caller → `FeedService.rank` | `FeedRequest` | dicts, raw JSON |
| `FeedService` → caller | `Feed` (`RankedItem`, `str` version, `Decimal`) | `Weights`, the loader |
| loader → `FeedService` | `Weights`, or `WeightConfigError` | paths, TOML, `OSError`, `TOMLDecodeError` |
| `FeedService` → `rank_feed` | one `Weights` value, one `FeedRequest` | the service, the loader |
| `config_file` → core | a `Mapping` into `Weights.from_mapping` | — |
| `cli` → library | public names; decoded JSON into `Candidate.from_mapping`; `numbers.canonical_text` to print scores | `exact_number`, `EXACT`, `rank_feed` |

`Decimal` crosses seams freely. It is stdlib, fixed by the substrate, and it is the published numeric
representation (§6), not an implementation detail.

## 5. Error vocabulary

Two public error types, one per distinct handling. No shared base: no caller handles "either" the same
way, and the CLI maps them to different exit codes.

| Error | Raised by | Handling | Messages name |
|---|---|---|---|
| `WeightConfigError` | `Weights` (values, names), `load_weights_file` (I/O, TOML syntax, duplicate keys) | Startup: no service exists (CLI exit 3). Reload: previous weights kept; the reload caller reports it | the source (file path) and the problem: `weights.toml: weight 'recency' is negative (-0.1)`, `missing weight 'popularity'`, `unknown weight 'freshness'`, `all weights are zero`, `weight 'affinity' is not finite (nan)` |
| `InvalidRequest` | `Candidate`, `FeedRequest`, the CLI's JSON shape check | Whole request rejected; nothing ranked (CLI exit 4) | item and signal: `item 'b': signal 'affinity' is outside [0, 1] (1.2)`, `item 'b': signal 'recency' is missing`, `duplicate item id 'a'`, `candidates[2]: item id must be a non-empty string` |

- The `ValueError` that `numbers` and `signals` raise is internal. `Weights` and `Candidate` each
  translate it once, adding the name that only they know.
- A `decimal` trap firing inside `EXACT` means the exactness invariant broke. It is a defect, not a user
  error, so it propagates unwrapped.
- Each constructor reports the **first** problem in a fixed order: id, then names, then values in
  `SIGNAL_NAMES` order, then the all-zero check. The CLI reports candidates in input order.

## 6. Hard decision (b): what "equal score" means

**Decision.** Signals, weights and scores are `Decimal`. Every input number is canonicalized once, in
`numbers.exact_number`, to **the shortest decimal that round-trips its IEEE-754 double**:
`Decimal(repr(float(x)))`. Scores are computed with exact multiplication and addition in a module-owned
context, `EXACT = Context(prec=MAX_PREC, Emax=MAX_EMAX, Emin=MIN_EMIN, traps=[Inexact, Rounded, InvalidOperation])`.
"Equal" means `Decimal` value equality, with no epsilon.

`exact_number` accepts `int` and `float`, and rejects `bool`, `str`, `None` and anything else as "not a
number". It rejects NaN, ±inf and an `int` too large for a double as "not finite". It folds `-0` to `0`.

**The trap from the brief.** Weights r=0.1, a=0.2, p=0; x (r=0.3, a=0) and y (r=0, a=0.15). Both score
`0.03` exactly, so they are equal and x comes before y by id. Binary floats would give
`0.030000000000000002` vs `0.03`, and x would win on rounding noise.

**Why this canonicalization, and not "parse the JSON/TOML text exactly".**
- **One meaning of a number on every path.** A library caller passing the float `0.1`, a JSON request
  saying `0.1` and a TOML file saying `0.1` all become `Decimal("0.1")`. Configs and requests parse with
  the stdlib's default float parsing, so no parser needs a special hook.
- **Exactness stays bounded.** After canonicalization every value has at most 17 significant digits and
  an exponent inside the double range, so an exact score never needs more than about 960 digits.
  (Verified: `1.7976931348623157e308·1 + 5e-324·5e-324` has 957.) Parsing the text exactly would let a
  valid signal like `1e-999999999` make an exact sum need a billion digits.
- **The cost, stated.** A number written with more than about 17 significant digits is read as its
  nearest double. That is the documented meaning of "a number" here. It is not clamping: range checks
  run after canonicalization.

**Two details that pass every ordinary test and still break ranking.**
- `Weights.score` calls `EXACT.multiply` and `EXACT.add` explicitly. It never uses the ambient thread
  context: a host that sets `getcontext().prec = 6` would otherwise round scores and merge distinct ones.
- The sort key is `(score.copy_negate(), item_id)`, not `(-score, item_id)`. Unary minus rounds to the
  ambient context (28 digits by default). Verified: `-Decimal("1" + "0"*40 + "1")` loses its last digit.
  `copy_negate` is exact.

**Rejected.**

| Alternative | Why not |
|---|---|
| Float, compared with `==` | Mathematically equal scores split. The tie-break is decided by representation error, not by the rule |
| Epsilon, or rounding to N places | The rule is exact equality. An epsilon is also non-transitive, so the sort order is ill-defined |
| `Decimal(float)`, the exact binary value | Brings the trap back: `Decimal(0.1)*Decimal(0.3) != Decimal(0.2)*Decimal(0.15)` |
| Parse JSON/TOML text exactly (`parse_float=Decimal`) | Unbounded digits and exponents; two paths could disagree on the same written number |
| `Decimal` in the default context | Precision 28 silently rounds products of 17-digit values into false ties |
| `fractions.Fraction` | Exact, but it adds nothing over `Decimal` here and prints `29/50` |

## 7. Hard decision (a): one valid weight version per request

**Decision.** Three facts, each with one owner, make a mixed or invalid ranking unrepresentable.

1. **Only valid weights exist.** Owner: `Weights.__init__`. There is no other constructor, so a
   test fake or a future loader can't produce invalid weights either. The object is frozen.
2. **A request reads the current weights once.** Owner: `FeedService.rank`. It copies `self._weights` into
   a local and passes that one value to `rank_feed`. `rank_feed` scores, sorts and stamps
   `Feed.weights_version` from that same value. It has no path back to the service, so it can't re-read.
3. **A reload builds, then swaps.** Owner: `FeedService.reload`. The loader runs to completion, including
   all validation, before the single assignment `self._weights = fresh`. If it raises, nothing was
   assigned. `__init__` calls the same load, so a failure there means no `FeedService` exists. That is
   what "refuses to start" means.

```python
def reload(self) -> None:
    with self._reload_lock:                 # only reloads take it; rank() never does
        fresh = self._load_weights()        # may raise: nothing has changed yet
        self._weights = fresh               # one reference store
def rank(self, request):
    weights = self._weights                 # the one read per request
    return rank_feed(weights, request)
```

**Concurrency.** A host may call the service from several threads. Loading and storing one reference is
atomic, and the referent is immutable, so a request in flight keeps its old snapshot and the next request
gets the new one. `rank` takes no lock. The **reload lock** exists for one reason: two overlapping reloads
could otherwise finish out of order and install an older file's content last.

**Reporting a rejection.** `reload()` raises `WeightConfigError` to its caller, and the state is unchanged.
It returns nothing on success (command–query separation). The next `Feed.weights_version` shows which
version is live.

**Version id.** The id is `"w-"` followed by the first 16 lowercase hex digits of the SHA-256 of the
ASCII bytes of `"recency=<r>;affinity=<a>;popularity=<p>"`. The fields are in `SIGNAL_NAMES` order, with
no spaces. Each value is written as `numbers.canonical_text(v)`, which is
`format(v.normalize(EXACT), "f")`. That is plain fixed-point with no exponent, no trailing zeros and no
trailing point. `EXACT` is explicit because `normalize()` rounds to the ambient precision (verified: under
`prec = 3`, `0.123456` becomes `0.123`). The CLI prints scores with the same function. The text depends
only on the stored `Decimal` value, and that value is fixed by §6. It does not depend on `repr` formatting
or on the host context, so the id is stable across processes and Python versions. Examples:

| Weights | Canonical text | Id |
|---|---|---|
| `0.5, 0.3, 0.2` (or `0.50, …`) | `recency=0.5;affinity=0.3;popularity=0.2` | `w-d10d332756fa52f8` |
| `2, 0, 0` (or `2.0, 0, -0.0`) | `recency=2;affinity=0;popularity=0` | `w-e6244fe68e726f5a` |

The same weights give the same id, so reloading an unchanged file keeps it, and any change gives a new
one. The id can't be paired with the wrong weights, which an operator-written version field could be.

**Rejected.** Mutating weights in place (a request could see a mix; a failed reload could leave a partial
state). A read-write lock held for the whole request (immutability already isolates it, and requests
would wait on file I/O). Passing the service or loader into the core (the core could re-read mid-request).
Validating in `reload()` (a second owner of weight validity). A `ReloadResult` value (a rejection
becomes ignorable). An operator-written version field or a reload counter (can lie, or isn't stable
across restarts).

## 8. Config file and CLI

**Config file** (TOML, UTF-8): a flat table with exactly the three weights.

```toml
recency = 0.5
affinity = 0.3
popularity = 0.2
```

TOML is stdlib (`tomllib`), easy for operators to edit, and rejects duplicate keys natively. JSON's
`json` silently keeps the last duplicate. `load_weights_file` translates `OSError`, `UnicodeDecodeError`
and `TOMLDecodeError` into `WeightConfigError(source=path)`. It delegates every weight rule to
`Weights.from_mapping` and adds the path to any rejection. TOML `nan` and `inf` arrive as floats and are
rejected by `exact_number`. An integer weight (`recency = 1`) is valid.

**CLI.** `python -m feed_ranking --weights PATH [REQUEST_FILE]`. The request is read from stdin when
`REQUEST_FILE` is omitted.

- Request: `{"user": "u1", "candidates": [{"id": "a", "recency": 0.9, "affinity": 0.1, "popularity": 0.5}, ...]}`
- Output (stdout): `{"weights_version": "w-…", "items": [{"id": "a", "score": "0.58"}, ...]}`. Scores
  are JSON strings in `canonical_text`, because a JSON number would be reparsed as a float and lose the
  exactness the tie rule depends on.
- Order: parse arguments, start the service, read the request, decode it, rank it. Bad weights therefore
  win over a bad request, which is what "refuses to start" means. The request is read as bytes, from
  `REQUEST_FILE` or `sys.stdin.buffer`, and decoded as strict UTF-8 before `json.loads`.
- Every outcome has its own code. `cli.main` owns the mapping. It catches only `WeightConfigError`,
  `InvalidRequest` and an `OSError` from the request read. On any error, stdout is empty.

| Exit | Outcome | stderr | Message text owned by |
|---|---|---|---|
| 0 | Feed written | — | — |
| 1 | *Never returned.* Python's status for an uncaught exception, meaning a defect such as a `decimal` trap (§5) | traceback | Python |
| 2 | Usage error | usage line | `argparse` |
| 3 | `WeightConfigError`: the service refused to start | `error: <path>: <problem>` | `WeightConfigError` (the raiser) |
| 4 | `InvalidRequest`: a rule violation, or a request that isn't UTF-8, isn't JSON or has the wrong shape | `error: <problem>` | `InvalidRequest` (the raiser; `cli` for the three representation problems) |
| 5 | Request unreadable: an `OSError` opening or reading `REQUEST_FILE` or stdin (missing, a directory, no permission) | `error: cannot read request <path or stdin>: <strerror>` | `cli` |

- The CLI checks only JSON shape: a top-level object, `user` a string, `candidates` an array of objects.
  Everything else goes through `Candidate.from_mapping` and `FeedRequest`.
- There is no reload subcommand. A one-shot process is a restart; the explicit reload is `FeedService.reload()`
  for a host that embeds the library.

## 9. Rule → owner → entry paths

Entry paths: **L** library `FeedService.rank`; **C** CLI; **S** startup (`FeedService(...)`, CLI
`--weights`); **R** `FeedService.reload`; **D** internal `ranking.rank_feed` (tests only; not public).

| Rule | Owner (exactly one) | Paths |
|---|---|---|
| What a number is: int/float, finite, canonical decimal, `-0` → `0` | `numbers.exact_number` | via `Weights` (S, R) and `Candidate` (L, C, D) |
| How a number is written (version text, CLI scores) | `numbers.canonical_text` | via `Weights.version` (L, C, D); C output |
| Constructor arity: every signal/weight keyword present, none unknown | Python's signature (`TypeError`). A programming error, outside the product rule (§3) | direct `Weights(...)`, `Candidate(...)` in code |
| Weight names on data: exactly the three | `Weights.from_mapping` via `signals.read_signal_fields` | S, R (file), any mapping caller |
| Weight values: finite, ≥ 0; at least one > 0; never rescaled | `Weights.__init__` | S, R, and any direct `Weights(...)` |
| Config file readable, valid TOML, no duplicate keys | `config_file.load_weights_file` | S, R when the loader is the file loader; C |
| Invalid at startup → refuse to start | `FeedService.__init__` (doesn't catch) | S; the CLI maps it to exit 3 |
| Invalid on reload → keep last valid, report | `FeedService.reload` (build, then swap; raise) | R |
| One weight version per request, never partial | `FeedService.rank` (one read) + `Weights` immutability | L, C |
| Response carries the version used | `rank_feed` stamps it from the one `Weights` it scored with | L, C, D |
| Weight version identity | `Weights.version` (derived) | L, C, D |
| Change only on explicit reload | `FeedService`: the loader is called only in `__init__` and `reload` | S, R |
| score = w_r·r + w_a·a + w_p·p, exact, nothing else | `Weights.score`, in `EXACT` | L, C, D via `rank_feed` |
| Signal names on data: exactly the three (missing or unknown → rejected, naming item and signal) | `Candidate.from_mapping` via `signals.read_signal_fields` | C, any mapping caller |
| Signal values: finite, in [0, 1]; never clamped, filled or dropped | `Candidate.__init__` | L, C, D |
| Item id: a non-empty str | `Candidate.__init__` | L, C, D |
| No duplicate ids | `FeedRequest.__init__` | L, C, D |
| Order: score desc, id asc by code point; exact equality | `rank_feed`, key `(score.copy_negate(), item_id)` | L, C, D |
| Empty candidates → empty feed | `rank_feed`, with no special case | L, C, D |
| `user` doesn't affect score or order | Structural: `rank_feed` never reads `request.user`; `Weights.score` takes only a `Candidate` | L, C, D |
| Request JSON shape and UTF-8 | `cli` | C only. A representation rule, not a product rule |
| CLI outcome → exit code and stderr line | `cli.main` (§8 table) | C only |

## 10. Test plan (test-first; `unittest`)

Order of writing: `numbers` → `signals` → `weights` → `request` → `ranking` → `config_file` → `service` →
`cli`. Each module's tests come before its code. Tests assert the public contract. `numbers` is tested
directly because it owns decision (b), and `ranking` is imported directly because `rank_feed` isn't public.

- **numbers**: `0.1` → `Decimal("0.1")`, not its binary expansion; `3` → `3`; `-0.0` → `0`. `True`,
  `"0.5"`, `None`, `Decimal("0.5")` → not a number. NaN, ±inf, `10**400` → not finite. `canonical_text`:
  `0.50` → `"0.5"`, `2` → `"2"`, `1e22` → `"10000000000000000000000"`, and it is unchanged under
  `getcontext().prec = 3`.
- **signals**: exact key set → values; the first missing key, then the first unknown key, are reported in
  a fixed order; `leading` keys are required too.
- **weights**: the scenario `0.5/0.3/0.2` constructs. Missing, unknown and empty mapping → errors naming
  the key. Negative, NaN, inf, string, bool → rejected naming the weight. All zero → rejected;
  `0/0/5e-324` accepted. Sum 1.7 accepted and not rescaled: `(2, 0, 0)` with recency 0.5 scores exactly
  `1`. Version: the two §7 examples as hard-coded strings; equal for `0.5` and `0.50`; different for any
  change. Construction: `Weights(recency=0.5, affinity=0.3)` → `TypeError`, not `WeightConfigError`.
  Formula: scenario scores `0.58` and `0.55` exactly. **Trap**: x and y both score `Decimal("0.03")`. **Ambient context ignored**: with `getcontext().prec = 3`, a score needing 20
  digits is still exact.
- **request**: empty id, non-str id → rejected; `" "` accepted. For each signal: missing, unknown extra,
  `-0.01`, `1.01`, NaN, inf, `"0.5"`, `None`, bool → rejected with `item_id` and `signal` set (missing
  and unknown through `from_mapping`; a missing keyword on the constructor is a `TypeError`). Exactly `0` and `1`
  accepted. `1.2` is rejected, not stored as `1`. Duplicate id at any positions, including with different
  signals → rejected with `item_id`. One bad item among many rejects the whole request.
- **ranking**: empty → `Feed(v, ())`; one; many descending. Exact tie → id ascending, `"10"` before `"9"`,
  `"B"` before `"a"`. The trap pair is ordered by id, and the same data as Python floats gives the same
  result. Near-tie (scores differing in the 30th digit) keeps score order; this guards `copy_negate` and
  the exact context. Permutation invariance over seeded shuffles. `user` independence. The version is
  stamped from the given weights.
- **config_file**: valid file → `Weights` equal to one built in code. Missing file, directory, bad UTF-8,
  TOML syntax error, duplicate key, `nan`, string value, unknown key → `WeightConfigError` with `source` =
  the path and the problem named.
- **service** (in-memory loaders; no files): a loader that raises → the constructor raises. Reload valid →
  the next `rank` has the new version and scores. Reload invalid → raises, and the next `rank` still has
  the old version. A→B→invalid → B. A non-domain `RuntimeError` from the loader → propagates, old weights
  kept. The loader is called once at construction and once per `reload()`, never by `rank`. **No mix
  under concurrency**: N threads rank a large request while one thread alternates reloads between V1 and
  V2; every feed's scores equal `rank_feed(V_named, request)` for the version it names. **Overlapping
  reloads**: with barriers, a slow load of A and a fast load of B; the final version is the last to
  finish under the lock, never a stale overwrite.
- **cli** (end to end): the goals.md scenario → exit 0, items `a, b, c`, scores `"0.58","0.55","0.55"`.
  Edit the file and rerun → new version. Bad weights → exit 3, stderr names the problem, stdout empty; bad
  weights and a bad request together → 3. Bad signal → exit 4, naming item and signal. Malformed JSON,
  missing `candidates`, non-UTF-8 bytes on stdin → exit 4. `REQUEST_FILE` missing, or a directory → exit 5
  naming the path. Unknown flag → 2. Empty `candidates` → `"items": []`.

## 11. What was cut (subtractive pass) and concept fit

**Cut:** a `WeightSource` Protocol or ABC (a callable is complete for its one consumer); a `Scorer`
strategy (the formula is fixed); `Signals`, `ItemId`, `Score` and `WeightsVersion` types (no rule of
their own); a shared error base and per-problem error subclasses (nobody catches them differently);
`FeedService.from_file` (the service would depend on the file adapter; `functools.partial` composes it);
a `current_version` query, a `last_error` field, and a returned version from `reload` (no consumer);
echoing `user` in `Feed` (not in the required response); a lock on the request path; file watching;
logging; CLI `reload` and `validate` subcommands; exact text parsing hooks; `rank_feed` on the public
surface (no consumer outside tests); sentinel defaults so the constructor could report a missing signal (a
second owner, and a signature that lies).

**Kept, with the force behind each.** `numbers` (decision b, shared by weights and signals). `signals`
(which signals exist, shared by weights and candidates; separate from `numbers` because it changes for a
different reason).
`Weights` (weight rules, formula, version identity). `Candidate` (signal contract, id rule).
`FeedRequest` (duplicate ids belong to the whole request). `rank_feed` (order, pure, testable without a
service). `FeedService` (the one mutable state). `WeightLoader` alias (the core must not know the
source). The reload lock (stale overwrite). `config_file` (weights come from a file). The CLI (the
optional small CLI; the operator-visible path for "refuses to start").

**Concept fit.** `Weights` is a value, not a config-file object; the version is its derived identity.
A rejection is an exception, never a sentinel score or a dropped item. The tie-break is part of the sort
key, never a perturbation of the score. An empty feed is a `Feed` with no items. `user` is identity
carried on the request, not a ranking parameter.

## 12. Assumptions (the PO handed these choices back; each is a simple default)

1. Weight config version id = a content hash of the weights (§7).
2. A number means the nearest IEEE-754 double, read as its shortest decimal (§6).
3. Unknown keys on a candidate object are rejected, the same as for weights, so a misspelled signal fails
   fast.
4. `user` must be a `str`; empty is allowed, since no rule was stated. It is not echoed in the response.
5. Overlapping reloads: the last to finish under the lock wins.
6. Each constructor reports its first problem, in a fixed order.
7. Config file format is TOML. The CLI request format is UTF-8 JSON, and CLI scores are decimal strings.
8. "Rejected, naming item and signal" applies to request *data*. A missing constructor keyword in the
   caller's own code is a programming error (`TypeError`), because the signature is the library contract.
9. CLI exit codes are 0/2/3/4/5 (§8). Code 1 is left to Python so a crash is never mistaken for a
   rejection. An unreadable request file is its own outcome, distinct from a rejected request.
