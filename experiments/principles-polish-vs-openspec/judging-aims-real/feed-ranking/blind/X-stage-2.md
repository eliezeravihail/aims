# Design X — stage 2

# Feed ranking — architecture (stage 2: eligibility and diversity)

Design only. The signatures below pin the boundaries; there is no implementation. Product decisions and
their provenance are in [`goals.md`](goals.md) (stage 1, and the "Stage 2" section); the substrate is in
[`base-dependencies.md`](base-dependencies.md). The reasoning behind this revision and the per-axis harvest
are in [`decisions/0002`](decisions/0002-stage2-eligibility-diversity.md). The stage-1 rationale is in
[`decisions/0001`](decisions/0001-stage1-architecture.md).

## 0. What stage 2 changes

Stage 2 adds two rules and the data they need.

- **Eligibility.** An item by a blocked author, or with any muted topic, never appears in the feed.
- **Diversity.** No more than 2 consecutive items in the feed may share an author.

The change lands on three existing owners and adds **no module, no public type, no error type and no
dependency**.

- **`Candidate`** gains `author` and `topics`. They are validated in its constructor like every other item
  field.
- **`FeedRequest`** gains `blocked_authors` and `muted_topics`, validated in its constructor. It also gains
  the query `eligible_candidates()`, which is **the one owner of eligibility**. A `FeedRequest` that exists
  is fully valid, so validity comes before eligibility by construction.
- **`rank_feed`** still owns "the order". It is now a fixed composition of three single-owner steps:
  1. **eligible candidates** (`FeedRequest.eligible_candidates()`);
  2. **the rank order**, using the stage-1 sort key, unchanged;
  3. **the author-run limit**, a private sequence constraint that never sees a score.

`FeedService`, `Weights`, `numbers`, `signals`, `config_file`, `RankedItem` and `Feed`'s fields do not
change. Neither do the exact-decimal decision (§6), one weight version per request (§7), the response
shape, or the CLI exit codes.

## 1. Shape

A **pure core** and a **thin shell**.

- **Core** (no I/O, no mutable state):
  - `Weights` is one validated, immutable weight version. It owns the score formula and derives its own
    version id.
  - `Candidate` is one validated item: signals, author and topics.
  - `FeedRequest` is one validated request: the user, the candidates and the two lists. It owns
    eligibility.
  - `rank_feed(weights, request)` owns the feed order.
- **Shell**:
  - `FeedService` holds the only mutable state, which is the current `Weights` reference. It owns startup
    refusal, reload fallback, and the rule that each request uses exactly one weight version. It gets
    weights from an injected zero-argument callable, so it never knows where weights come from.
  - `config_file` turns a TOML file into `Weights`.
  - `cli` is a one-shot JSON adapter.
- **Numbers** are exact decimals (§6). One module owns what "a number" means; another owns which signals
  exist.

```
feed_ranking/
  __init__.py      public re-exports (§3); no logic                                   [unchanged]
  __main__.py      raise SystemExit(cli.main())                                       [unchanged]
  numbers.py       Number, exact_number(), canonical_text(), EXACT context            [core foundation, unchanged]
  signals.py       SIGNAL_NAMES, read_signal_fields()                                 [core foundation, unchanged]
  weights.py       Weights, WeightConfigError                                         [core, unchanged]  -> numbers, signals
  request.py       Candidate (+author, +topics), FeedRequest (+lists, +eligible_candidates()),
                   InvalidRequest; private _require_id(), _require_id_set()           [core, CHANGED]    -> numbers, signals
  ranking.py       RankedItem, Feed, rank_feed(); private _MAX_SAME_AUTHOR_RUN,
                   _limit_author_runs()                                               [core, CHANGED]    -> weights, request
  service.py       FeedService, WeightLoader                                          [shell, unchanged] -> weights, request, ranking
  config_file.py   load_weights_file()                                                [shell, unchanged] -> weights
  cli.py           main()                                                             [shell, CHANGED: request shape] -> service, config_file, request, numbers
```

- Imports are acyclic and unchanged from stage 1. They point toward `numbers` and `signals`, which import
  nothing from the package. The core never imports `service`, `config_file` or `cli`.
- The only dependency is the standard library (`decimal`, `hashlib`, `tomllib`, `json`, `argparse`,
  `threading`, `dataclasses`, `functools`). Stage 2 adds no import. Tests use `unittest`.

## 2. Change axes the shape absorbs, and those it deliberately doesn't

| Axis | Absorbed by | Cost of the change |
|---|---|---|
| Weight values change (operator) | TOML file + `FeedService.reload()` | Edit the file and reload; no code |
| A reload fails, or lands during requests | Immutable `Weights`; one snapshot read per request; swap only after a full load | None: holds by construction |
| Where weights come from | `WeightLoader = Callable[[], Weights]` injected into `FeedService` | A new zero-argument function; core and service untouched |
| Entry path (library or CLI) | CLI is an adapter over the same public types | A new adapter; no rule moves |
| **The user's block and mute lists (different on every request)** | Request data: `FeedRequest.blocked_authors`, `.muted_topics` | None: they are values, and nothing is stored |
| **Each item's author and topics** | Request data: `Candidate.author`, `.topics` | None |
| **The rank order (formula, tie rule) vs the arrangement** | Two private steps in `ranking.py`. The run limit receives candidates in rank order and never sees a score | Changing the formula or the tie-break touches `Weights.score` or the sort key only; the run limit is untouched |
| *Not an axis:* the signal set, the formula, per-user weights | Three named fields and one formula | A 4th signal would touch `signals.SIGNAL_NAMES`, `Weights`, `Candidate`. Accepted: stage 1 says three |
| *Not an axis:* the diversity key (author), the limit 2 | `candidate.author` read in one function; the named constant `_MAX_SAME_AUTHOR_RUN = 2` | Diversity by topic and a configurable limit are non-goals. Either change reopens `_limit_author_runs` only |
| *Not an axis:* the set of eligibility rules; a filter engine | Two clauses in `FeedRequest.eligible_candidates` | A third rule adds one field and one clause to that one owner. A plug-in engine is a non-goal |
| *Not an axis:* storing the lists | They arrive on each request | A store would become one more producer of the same two `FeedRequest` fields; the core is untouched |

## 3. Public surface

```python
# numbers.py, signals.py (internal foundation; not re-exported) — UNCHANGED
Number: TypeAlias = int | float          # what a producer may hand in for a signal or weight
def exact_number(x: object) -> Decimal: ...      # ValueError "not a number" / "not finite"
def canonical_text(d: Decimal) -> str: ...       # the one printed form of a value (§7)
SIGNAL_NAMES: Final = ("recency", "affinity", "popularity")
def read_signal_fields(raw: Mapping[str, object], leading: tuple[str, ...] = ()) -> dict[str, object]: ...
                                          # keys exactly leading + SIGNAL_NAMES; ValueError "missing 'x'" / "unknown 'y'"

# weights.py — UNCHANGED
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
    def score(self, candidate: "Candidate") -> Decimal: ...   # THE formula, in EXACT; reads only the three signals

# request.py — CHANGED
class InvalidRequest(Exception):          # unchanged type and attributes; new messages only (§5)
    problem: str                          # "outside [0, 1] (1.2)", "duplicate id", "author must be ...", ...
    item_id: str | None                   # the offending item when identifiable
    signal: str | None                    # a signal problem, or an unknown key: the stage-1 meaning (§5)

@dataclass(frozen=True, slots=True, init=False)
class Candidate:
    item_id: str
    author: str                           # NEW  exactly one author id; non-empty; stored as given
    topics: frozenset[str]                # NEW  zero or more topic ids; each non-empty; repeats are one
    recency: Decimal
    affinity: Decimal
    popularity: Decimal
    def __init__(self, item_id: str, *, author: str, topics: Iterable[str],
                 recency: Number, affinity: Number, popularity: Number) -> None: ...
                                          # first problem in fixed order: id, author, topics, then signals
                                          # in SIGNAL_NAMES order (§5)
    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> "Candidate": ...
                                          # keys exactly {"id", "author", "topics", *SIGNAL_NAMES}, via
                                          # read_signal_fields(raw, leading=("id", "author", "topics"))

@dataclass(frozen=True, slots=True, init=False)
class FeedRequest:
    user: str
    candidates: tuple[Candidate, ...]     # every candidate as submitted, eligible or not
    blocked_authors: frozenset[str]       # NEW
    muted_topics: frozenset[str]          # NEW
    def __init__(self, user: str, candidates: Iterable[Candidate], *,
                 blocked_authors: Iterable[str], muted_topics: Iterable[str]) -> None: ...
                                          # first problem in fixed order: user is str, blocked_authors,
                                          # muted_topics, then no duplicate item_id (over ALL candidates)
    def eligible_candidates(self) -> tuple[Candidate, ...]: ...
                                          # NEW  in submission order: the candidates whose author is not
                                          # blocked and none of whose topics is muted

# ranking.py — signatures UNCHANGED; the Feed.items contract is restated
@dataclass(frozen=True, slots=True)
class RankedItem:
    item_id: str
    score: Decimal                        # the item's own stage-1 score, untouched by eligibility or diversity

@dataclass(frozen=True, slots=True)
class Feed:
    weights_version: str
    items: tuple[RankedItem, ...]         # the eligible candidates in rank order (score desc, then item_id
                                          # asc by code point), arranged so that no author has more than 2
                                          # consecutive items; items that cannot be placed are omitted (§9).
                                          # NOT strictly score-descending. () when nothing is eligible

def rank_feed(weights: Weights, request: FeedRequest) -> Feed: ...

# service.py — UNCHANGED
WeightLoader: TypeAlias = Callable[[], Weights]   # returns valid Weights or raises WeightConfigError

class FeedService:
    def __init__(self, load_weights: WeightLoader) -> None: ...   # loads once; raise => no service
    def rank(self, request: FeedRequest) -> Feed: ...
    def reload(self) -> None: ...                                  # load, then swap; raise => unchanged

# config_file.py — UNCHANGED
def load_weights_file(path: str | os.PathLike[str]) -> Weights: ...

# cli.py — signature UNCHANGED; the request JSON grows (§11)
def main(argv: Sequence[str] | None = None) -> int: ...
```

Typical embedding:

```python
service = FeedService(functools.partial(load_weights_file, "/etc/feed_ranking/weights.toml"))
feed = service.rank(FeedRequest(
    "u1",
    [Candidate("a", author="alice", topics=["cats"], recency=0.9, affinity=0.1, popularity=0.5)],
    blocked_authors=["mallory"], muted_topics=[],
))
service.reload()          # WeightConfigError on a bad file; the service keeps its previous weights
```

`__init__` re-exports the same ten names as in stage 1:

- `Weights`, `WeightConfigError`
- `Candidate`, `FeedRequest`, `InvalidRequest`
- `RankedItem`, `Feed`
- `FeedService`, `WeightLoader`, `load_weights_file`

That is the contract. `rank_feed`, `numbers` and `signals` stay internal, and so do the private helpers of
`request.py` and `ranking.py`. Tests import `feed_ranking.ranking` directly.

**Construction contract.** The value types write their own `__init__`, so the published signature is
true. It takes `Number` and `Iterable[str]`, and the attributes are `Decimal` and `frozenset[str]`.
`init=False` keeps the generated equality, hash and repr.

- **Keyword-only, no defaults.** Signals, weights, `author`, `topics` and the two lists are keyword-only,
  so a call can't swap two of them by position. None of them has a default.
- **Arity is Python's rule; values are the product's.** A missing or unknown keyword is a `TypeError`:
  a programming error in the caller's source that a type checker flags, not a rejected request. This is
  how "the lists are required" holds on the library path. A default of `()` would bring back exactly the
  silent failure the product chose against: a caller who forgets the block list would be shown blocked
  content.
- **Stage-1 calls stop working, deliberately.** A call like `FeedRequest("u1", [...])` is now a
  `TypeError`.
- **Every value is data**, and the constructor rejects a bad one, naming the item and the field. That
  includes `None`, `"0.5"`, a bare string or a mapping where a collection of ids is expected, and an empty
  id.
- **Key sets known only at run time** go through `from_mapping`, the one owner of "missing" and "unknown".
  Reporting those from the constructor would need sentinel defaults. They would make the signature lie
  that fields are optional, and they would create a second owner.

### 3.1 What "an id" is: one private owner in `request.py`

Five values are ids:

- the item id;
- the author;
- each topic;
- each blocked author;
- each muted topic.

All five share one meaning: a non-empty `str`, compared exactly (case-sensitive, no stripping, no Unicode
normalization). That is one piece of knowledge, so it has one home: two private functions in `request.py`.

```python
def _require_id(value: object) -> str: ...
    # returns value unchanged if it is a non-empty str;
    # else ValueError "must be a non-empty string (<repr>)"
def _require_id_set(value: object) -> frozenset[str]: ...
    # str / bytes / bytearray       -> ValueError "must be a collection of ids, not a string"
    # Mapping, or not iterable      -> ValueError "must be a collection of ids"
    # else each entry via _require_id, in iteration order; first bad one -> ValueError "[i] must be a non-empty string (<repr>)"
    # result: frozenset (repeats are one entry by construction)
```

- **The same pattern as `numbers`.** The helpers raise a local `ValueError`. `Candidate.__init__` and
  `FeedRequest.__init__` each translate it once into `InvalidRequest`, adding the item or the field name
  that only they know.
- **Behavior-preserving move.** The stage-1 item-id check moves behind `_require_id` with the same
  acceptance set (`" "` is still accepted). Its message is `item id must be a non-empty string (<repr>)`
  from the start, because stage 1 is not built yet: the repr is the only difference from the stage-1
  wording, and no stage-1 test pins that text.
- **Who writes `candidates[i]:`.** An item with an unreadable id has no `item_id` to name it by. So
  `Candidate` raises `InvalidRequest(item_id=None)` with the text above, and on the data path `cli`, the
  only component that knows the array index, prefixes `candidates[i]: `. The CLI adds a location. It
  does not validate the id, so the rule keeps its one owner.
- **Why the string and mapping refusals exist.** A `str` is an `Iterable[str]`, so `topics="sports"`
  would otherwise be read as six one-letter topics. A `dict` would be read as its keys. Both are the
  "malformed topics or list → rejected" case from goals.md, so the refusals serve a stated rule.
- **Why the helpers stay private.** Both callers live in `request.py`, so a separate module would publish
  a seam nobody crosses.

## 4. Seams and the types that cross them

| Seam | Crosses | Never crosses |
|---|---|---|
| caller → `FeedService.rank` | `FeedRequest` (with both lists; items with author and topics) | dicts, raw JSON, a pre-filtered candidate list |
| `FeedService` → caller | `Feed` (`RankedItem`, `str` version, `Decimal`) | `Weights`, the loader, authors, topics, anything about removed items |
| loader → `FeedService` | `Weights`, or `WeightConfigError` | paths, TOML, `OSError`, `TOMLDecodeError` |
| `FeedService` → `rank_feed` | one `Weights` value, one `FeedRequest` | the service, the loader |
| `rank_feed` → `FeedRequest` (internal) | the query `eligible_candidates()` → `tuple[Candidate, ...]` | `request.candidates`, the lists, `user`: ranking never evaluates eligibility itself |
| rank order → run limit (private, in `ranking.py`) | `Sequence[Candidate]` in rank order → `tuple[Candidate, ...]` | scores, `Weights`, the sort key |
| `config_file` → core | a `Mapping` into `Weights.from_mapping` | — |
| `cli` → library | public names; decoded candidate objects into `Candidate.from_mapping`; the two decoded list values passed **as is** into `FeedRequest`; `numbers.canonical_text` to print scores | `exact_number`, `EXACT`, `rank_feed`, `_require_id*`. The CLI never validates an id |

- **`Decimal` and `frozenset[str]` cross seams freely.** Both are stdlib and fixed by the substrate.
  `Decimal` is the published numeric representation (§6). `frozenset[str]` is the published
  representation of a collection of ids: it states the rule itself, since repeats mean one entry and
  matching is membership.

## 5. Error vocabulary

Two public error types, one per distinct handling. There is no shared base: no caller handles "either" the
same way, and the CLI maps them to different exit codes. **Stage 2 adds no error type.** Every new
rejection is handled like a stage-1 one: the whole request is rejected and nothing is ranked.

**Absence is never an error.** An ineligible item, or one the diversity rule omits, is simply missing from
the feed. If nothing is eligible, the result is `Feed(version, ())`.

| Error | Raised by | Handling | Messages name |
|---|---|---|---|
| `WeightConfigError` | `Weights` (values, names), `load_weights_file` (I/O, TOML syntax, duplicate keys) | Startup: no service exists (CLI exit 3). Reload: previous weights kept; the reload caller reports it | the source (file path) and the problem: `weights.toml: weight 'recency' is negative (-0.1)`, `missing weight 'popularity'`, `unknown weight 'freshness'`, `all weights are zero`, `weight 'affinity' is not finite (nan)` |
| `InvalidRequest` | `Candidate`, `FeedRequest`, the CLI's JSON shape check | Whole request rejected; nothing ranked (CLI exit 4) | the item and the signal or field, as below |

`InvalidRequest` messages. Stage-1 messages are unchanged; the stage-2 rows are new.

| Raised by | Condition | `problem` text (CLI stderr `error: <problem>`) | `item_id` / `signal` |
|---|---|---|---|
| `Candidate` | signal out of range, missing or unknown (stage 1) | `item 'b': signal 'affinity' is outside [0, 1] (1.2)`, `item 'b': signal 'recency' is missing` | `'b'` / `'affinity'` |
| `FeedRequest` | duplicate id (stage 1) | `duplicate item id 'a'` | `'a'` / `None` |
| `Candidate.__init__`; `cli` adds the `candidates[i]: ` prefix (§3.1) | item id unreadable (stage 1) | `candidates[2]: item id must be a non-empty string ('')` | `None` / `None` |
| `Candidate.from_mapping` | `author` or `topics` key absent | `item 'b': author is missing`, `item 'b': topics is missing` | `'b'` / `None` |
| `Candidate.from_mapping` | unknown key (stage-1 rule; e.g. a misspelled `topics`) | `item 'b': unknown 'topic'` | `'b'` / `'topic'` |
| `Candidate.__init__` | bad author | `item 'b': author must be a non-empty string (None)` | `'b'` / `None` |
| `Candidate.__init__` | topics is a `str`, `bytes` or `bytearray` | `item 'b': topics must be a collection of ids, not a string` | `'b'` / `None` |
| `Candidate.__init__` | topics is a mapping, or not iterable (e.g. `None`, `3`) | `item 'b': topics must be a collection of ids` | `'b'` / `None` |
| `Candidate.__init__` | bad topic entry | `item 'b': topics[1] must be a non-empty string ('')` | `'b'` / `None` |
| `FeedRequest.__init__` | a list is a `str`, `bytes` or `bytearray` | `blocked_authors must be a collection of ids, not a string` | `None` / `None` |
| `FeedRequest.__init__` | a list is a mapping, or not iterable (e.g. `None`) | `muted_topics must be a collection of ids` | `None` / `None` |
| `FeedRequest.__init__` | bad list entry | `muted_topics[0] must be a non-empty string (3)` | `None` / `None` |
| `cli` (shape) | a list key absent from the JSON | `request: 'blocked_authors' is missing` | `None` / `None` |

- **Internal errors are translated once.** The `ValueError`s raised by `numbers`, `signals` and the
  `request.py` id helpers are internal. `Weights`, `Candidate` and `FeedRequest` each translate them once,
  adding the name that only they know. Each stage-2 row above is one distinct message. The `__init__`
  rows are the §3.1 helper texts, prefixed by the owner with the item and field.
- **How `Candidate.from_mapping` sets `signal`.** It translates the one rejection from
  `read_signal_fields`, which names the key. `signal` is that key unless the key is a leading field (`id`,
  `author`, `topics`), which is not a signal, so `signal` is `None`. A missing signal and an unknown key
  keep their stage-1 treatment: an unknown key is read as a misspelled signal (Assumption 3), and the
  stage-1 suite pins `signal` for it.
- **Defects propagate.** A `decimal` trap firing inside `EXACT` means the exactness invariant broke. It is
  a defect, not a user error, so it propagates unwrapped.
- **Each constructor reports the first problem, in a fixed order:**
  - `Weights`: names, then values in `SIGNAL_NAMES` order, then the all-zero check.
  - `Candidate`: id, author, topics, then signals in `SIGNAL_NAMES` order.
  - `FeedRequest`: user, `blocked_authors`, `muted_topics`, then duplicate ids.
  - The CLI checks shape first, then builds candidates in input order, then the `FeedRequest`. So a
    request with a bad candidate *and* a bad list reports the candidate.
- **Which entry is named can vary for a `set`.** An index names an entry's position in iteration order,
  which for JSON is the array index. A library caller who passes a `set` with two bad entries may see
  either one named first. A list is deterministic.
- **A `TypeError` from a missing keyword** in library code is Python's, not the product's (§3).

## 6. Stage-1 decision: what "equal score" means (unchanged)

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

## 7. Stage-1 decision: one valid weight version per request (unchanged)

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

## 8. Stage-2 decision (a): where "an ineligible item never appears" lives

**Decision.** Eligibility is a **filter**. Its one owner is the query `FeedRequest.eligible_candidates()`.
It runs after validation by construction, and before scoring by construction.

```python
def eligible_candidates(self) -> tuple[Candidate, ...]:
    return tuple(c for c in self.candidates
                 if c.author not in self.blocked_authors and self.muted_topics.isdisjoint(c.topics))
```

Three properties make this hold on every path.

1. **Validity comes first, structurally.** `eligible_candidates` is a method of a `FeedRequest`, and a
   `FeedRequest` exists only once the following have all passed:
   - every candidate, eligible or not, through `Candidate.__init__`;
   - `user` and both lists;
   - id uniqueness over **all** candidates.

   No ordering statement is needed, because filtering a request that failed validation cannot be
   expressed. So an item that would have been filtered out still rejects the request if it is invalid,
   for example a blocked item with a signal of `1.2`, or a muted twin of an eligible item's id.
2. **One funnel on every entry path.** The library path L (`FeedService.rank`), the CLI path C (`cli` →
   `FeedService.rank`) and the internal path D (`rank_feed` directly) produce a `Feed` only through
   `rank_feed`. `rank_feed` gets its candidates **only** from `request.eligible_candidates()`; it never reads
   `request.candidates` or the lists. D is the lowest path, and it filters too, so no path sits beneath the
   filter.
3. **It comes before scoring and arrangement.** Ineligible items are never scored, so no sentinel score
   can exist and nothing is "shown low". They never enter the run limit either. So an ineligible item
   between two runs of one author does not break the run: `a1[A] a2[A] x[X, blocked] a3[A]` → `a1 a2`.

`Weights.score` reads only the three signals, so author, topics and the lists can never enter a score.

**Why `FeedRequest`, not `Candidate`.** The rule relates two things: the user's lists and the item's
metadata. The lists belong to the request, and only the request holds both. This is the same argument
that put duplicate ids on `FeedRequest` in stage 1: the rule is about the request as a whole.

**Residual, stated.** Python cannot stop a future edit to `ranking.py` from reading `request.candidates`,
which would silently bring blocked items back. `candidates` stays public, because it is the request as
submitted and a stage-1 public field. The guard is behavioral: a blocked top-score item is asserted
absent on paths D, L and C (§14). The invariant is recorded in `architecture.md`.

**Rejected.**

| Alternative | Why not |
|---|---|
| Score an ineligible item `-inf`, or add a penalty term | Concept cram: a filter modelled as a score. The item would still exist and could still be shown low. `Decimal('-Infinity')` would also trip the `EXACT` traps |
| Drop ineligible items inside `FeedRequest.__init__` (store only the eligible ones) | The value would no longer be the request that was sent, and equality and repr would hide data. It blurs "validated" with "filtered" |
| Filter in `FeedService.rank` | Path D would surface ineligible items, and the shell would own a domain rule |
| Filter in `cli` | L and D bypass it. It becomes a second owner the day it is copied |
| Filter after diversity | Wrong result: blocked items would shape the runs (`a1 a2 x a3` would admit `a3`) |
| Filter before validation (skip validating ineligible items) | Violates "validity first" (goals.md) |
| `Candidate.is_eligible(blocked, muted)` | The candidate would learn about request-level lists. The owner would be split, because the collection filter would still live elsewhere |
| An `Exclusions` value object holding the two lists | No rule of its own. It adds a public name and nested construction for every caller |
| A `Filter` protocol or a predicate pipeline | A generic filter engine is a non-goal, and one predicate has no variation to abstract |

## 9. Stage-2 decision (b): who owns "the order" now

**Decision.** `rank_feed` is still **the one owner of the feed order**. The order is a fixed composition of
three steps, each with one owner. The run limit cannot see or change a score, by construction. That it
arranges and never re-ranks is its contract, guarded by a test (below).

| Rule | Owner | What it cannot do |
|---|---|---|
| Eligibility | `FeedRequest.eligible_candidates()` (§8) | — |
| Rank order: score desc, then `item_id` asc by code point; exact equality | the sort key in `rank_feed`, `(score.copy_negate(), item_id)`: the stage-1 key, verbatim | — |
| At most 2 consecutive items per author; the best-ranked item that fits goes first; deferred items keep their order; the infeasible tail is omitted | `ranking._limit_author_runs`, with `_MAX_SAME_AUTHOR_RUN = 2` | read or change a score (by construction); re-rank or repeat an item (by contract, test-guarded) |
| Feed order = run limit ∘ rank order ∘ eligibility | `rank_feed` (the composition only) | — |

```python
_MAX_SAME_AUTHOR_RUN: Final = 2

def rank_feed(weights: Weights, request: FeedRequest) -> Feed:                  # illustrative
    eligible = request.eligible_candidates()                                   # the only read of candidates
    scores = {c.item_id: weights.score(c) for c in eligible}                   # once each; ids are unique
    ranked = sorted(eligible, key=lambda c: (scores[c.item_id].copy_negate(), c.item_id))   # stage-1 key
    shown = _limit_author_runs(ranked)
    return Feed(weights.version, tuple(RankedItem(c.item_id, scores[c.item_id]) for c in shown))

def _limit_author_runs(ranked: Sequence[Candidate]) -> tuple[Candidate, ...]:  # illustrative
    remaining, placed = list(ranked), []
    run_author, run_length = None, 0
    while remaining:
        barred = run_author if run_length == _MAX_SAME_AUTHOR_RUN else None
        i = next((i for i, c in enumerate(remaining) if c.author != barred), None)
        if i is None:
            break                                    # only the barred author is left: omitted, the feed ends
        c = remaining.pop(i)                         # pop from a rank-ordered list: deferred items keep order
        run_length = run_length + 1 if c.author == run_author else 1
        run_author = c.author
        placed.append(c)
    return tuple(placed)
```

**Contract of `_limit_author_runs`.**

- *Precondition.* `ranked` is in priority order: earlier means more preferred.
- *Postconditions.*
  1. The output is a sub-arrangement of the input, and each element appears at most once.
  2. No author appears more than `_MAX_SAME_AUTHOR_RUN` times in a row. Authors are compared by exact
     `str` equality, so `"A"` and `"a"` are different authors.
  3. Each position holds the earliest remaining input element that satisfies (2). So deferred elements
     keep their relative order, and two items by the same author always keep their rank order.
  4. It stops exactly when every remaining element is by the author of the last two placed elements.
     Those elements are omitted.
- *Consequences.*
  - It is the identity when the input has no author run longer than 2, because the head of `remaining`
    is always placeable.
  - An empty input gives `()`.
  - An omitted element is always by the author who ends the feed.

**What keeps the run limit from becoming a second owner of order or score.**

- *By construction.*
  - It cannot read a score. Its input is `Candidate`s, a `Candidate` carries no score, and the scores
    live only in `rank_feed`'s local map.
  - It cannot change a shown score. `rank_feed` looks up each returned candidate's score by `item_id` in
    that map, so a deferred item shows its own stage-1 score.
  - It cannot surface an item that is not eligible. Such an id has no entry in the map, so the lookup
    raises a `KeyError`: a defect that propagates (§5), never a shown item.
- *By contract, guarded by a test.* Its only use of the input is position (the precedence) and `author`,
  so "highest-ranked remaining" means "earliest in the input", and it returns each input element at most
  once. This is a convention: it receives whole `Candidate`s, so comparing ids or signals, or repeating an
  element, is expressible. The guard is the seeded property test in §14: each position holds the earliest
  placeable remaining input element, no element repeats, and any omitted elements are all by the author
  of the last two placed. Those checks fix the output from the input's positions and authors alone, so
  any use of ids or signals that changes a result fails them.

**Residual, stated.** Python cannot stop a future edit to `_limit_author_runs` from comparing `item_id`
or a signal. A narrower input (a generic `T` or a leaf module) was weighed and rejected (the `diversity.py`
row below), so the guard is behavioral. The invariant is recorded in `architecture.md`.

**The infeasible tail is not a special case.** It is the same step ("find the earliest placeable item")
finding none. There is no flag, no truncation parameter and no count.

**Traced examples** (goals.md):

| Input, in rank order | Feed |
|---|---|
| `a1 a2 a3 a4 b1 b2` | `a1 a2 b1 a3 a4 b2` |
| `a1 a2 a3 b1 c1` | `a1 a2 b1 a3 c1` |
| `a1 a2 a3` | `a1 a2` |
| `b1 a1 a2 a3` | `b1 a1 a2` (the stated consequence of the greedy reading) |

**Cost.** The worst case is O(n²), from scanning past deferred items. No performance requirement is
stated, and design-principles §13 is conditional, so the direct form reads as the rule. If a requirement
appears, a linear version fits behind the same private signature. It works because every deferred item
has the run author.

**Rejected.**

| Alternative | Why not |
|---|---|
| A score penalty for repeated authors | Concept cram: a sequence rule modelled as a score. It changes the shown score and doesn't guarantee the rule |
| Encode diversity in the sort key or a comparator | An item's placeability depends on what was placed before it. That is history, not a per-item key, and a stateful comparator breaks `sorted`'s contract |
| The run limit re-sorts by `(score, id)`, or receives `(Candidate, score)` pairs | A second owner of rank order, or an arrangement that can see what it must not use |
| `RankedItem` gains `author` so diversity can run on it | Changes the response shape (goals.md: unchanged) and leaks metadata out of the seam |
| A `diversity.py` leaf module with a function generic in `T` plus an `author_of` callable | The encapsulation Worker's proposal: its import barrier makes "cannot see scores" machine-checkable. Not taken, because `Candidate` already carries no score, so the barrier is already there in the type, and a module plus a callable parameter for one caller is a seam nobody crosses. See decisions/0002 |
| A generic `limit_runs(items, key, max_run)` | A different diversity key and a configurable limit are non-goals. Such parameters would be knobs no axis uses |
| Diversity in `FeedService` | Path D would miss it, and policy would sit in the shell |
| Append the infeasible tail | Breaks a hard constraint |
| Reject the request when the constraint can't be met | Fails a user's feed because of how the candidates happen to be distributed. The Guide chose omission (goals.md) |
| An arrangement that maximizes feed length, with lookahead or backtracking | The product preserves score order within the constraint. `b1 a1 a2` is the stated consequence |
| A `diversify: bool` flag or a `max_run` parameter on `rank_feed` | A flag argument. Diversity is unconditional product behavior |

## 10. Stage-2 decision (c): what items and requests carry, and who validates it

**Decision.** The stage-1 grain is kept:

- frozen value types, validated in their own constructor;
- `from_mapping` owns runtime key sets;
- per-item rules live on `Candidate`, and whole-request rules live on `FeedRequest`.

| New data | Carried by | Value rule owner | Presence ("missing" / "unknown") |
|---|---|---|---|
| author | `Candidate.author: str` | `Candidate.__init__` via `_require_id` | library: signature. Data: `Candidate.from_mapping` (a leading key) |
| topics | `Candidate.topics: frozenset[str]` | `Candidate.__init__` via `_require_id_set` | same as author |
| block list | `FeedRequest.blocked_authors: frozenset[str]` | `FeedRequest.__init__` via `_require_id_set` | library: signature. CLI: shape check |
| mute list | `FeedRequest.muted_topics: frozenset[str]` | `FeedRequest.__init__` via `_require_id_set` | same as the block list |

- **Sets, not tuples.** Eligibility needs membership only, and goals.md says repeats mean one entry. So the
  representation states the rule. Two candidates that differ only in topic order or repeats are equal.
- **Accept any iterable, except strings and mappings.** Topics and lists accept any `Iterable[str]` except
  `str`, `bytes` and `Mapping`, which are refused rather than guessed at. Every honest producer is covered:
  a JSON array, a list, tuple, set or generator.
- **Separate namespaces.** `blocked_authors` is compared only with `author`, and `muted_topics` only with
  `topics`. A muted topic `"x"` does not hide an item whose author is `"x"`.
- **Exactly one author** is structural: `author` is a single `str` field, so a list or `None` is rejected
  as "must be a non-empty string".

**Rejected.**

| Alternative | Why not |
|---|---|
| `AuthorId` / `TopicId` / `ItemMeta` value types | No rule beyond "non-empty str", which `_require_id` owns once. Stage 1 cut `ItemId` for the same reason, and the grain wins |
| `topics: tuple[str, ...]` | Keeps order and repeats that mean nothing, and every consumer would have to dedupe |
| Optional lists that default to `()` | The silent failure the product chose against |
| List entries validated in the CLI | The library path would go unvalidated, and a second owner would appear |
| A closed `IdCollection = list \| tuple \| set \| frozenset` alias | The clean-code Worker's proposal. It rejects a string and a mapping too, but it also rejects legitimate producers such as a generator, for no stated force. See decisions/0002 |
| `FeedRequest.from_mapping` owning the request's key set | The genericity Worker's proposal: "lists present" is a product rule, so it belongs in the core. Not taken now: stage 1 records the request's JSON shape as `cli`'s representation rule, and there is one data adapter. The force appears with a second adapter, and then it is the right move. See decisions/0002 |

## 11. Config file and CLI

**Config file** (TOML, UTF-8). Unchanged from stage 1: a flat table with exactly the three weights.

```toml
recency = 0.5
affinity = 0.3
popularity = 0.2
```

- TOML is stdlib (`tomllib`), easy for operators to edit, and rejects duplicate keys natively. JSON's
  `json` silently keeps the last duplicate.
- `load_weights_file` translates `OSError`, `UnicodeDecodeError` and `TOMLDecodeError` into
  `WeightConfigError(source=path)`. It delegates every weight rule to `Weights.from_mapping` and adds the
  path to any rejection.
- TOML `nan` and `inf` arrive as floats and are rejected by `exact_number`. An integer weight
  (`recency = 1`) is valid.

**CLI.** `python -m feed_ranking --weights PATH [REQUEST_FILE]`. The request is read from stdin when
`REQUEST_FILE` is omitted.

Request (stage 2), the worked example. The weights are the config file above (`0.5, 0.3, 0.2`).

```json
{"user": "u1",
 "blocked_authors": ["mallory"],
 "muted_topics": ["spoilers"],
 "candidates": [
   {"id": "x",  "author": "mallory", "topics": ["news"],             "recency": 1.0,  "affinity": 1.0, "popularity": 1.0},
   {"id": "m",  "author": "bob",     "topics": ["tech", "spoilers"], "recency": 0.95, "affinity": 0.9, "popularity": 0.9},
   {"id": "a1", "author": "alice",   "topics": ["cats"],             "recency": 0.9,  "affinity": 0.8, "popularity": 0.7},
   {"id": "a2", "author": "alice",   "topics": ["cats"],             "recency": 0.9,  "affinity": 0.6, "popularity": 0.5},
   {"id": "a3", "author": "alice",   "topics": [],                   "recency": 0.8,  "affinity": 0.5, "popularity": 0.5},
   {"id": "b1", "author": "bob",     "topics": ["tech"],             "recency": 0.6,  "affinity": 0.5, "popularity": 0.5},
   {"id": "a4", "author": "alice",   "topics": ["tech"],             "recency": 0.2,  "affinity": 0.9, "popularity": 0.8},
   {"id": "a5", "author": "alice",   "topics": [],                   "recency": 0.1,  "affinity": 0.2, "popularity": 0.3}
 ]}
```

| Step | Result |
|---|---|
| Scores (exact, §6) | x `1`, m `0.925`, a1 `0.83`, a2 `0.73`, a3 `0.65`, b1 `0.55`, a4 `0.53`, a5 `0.17` (e.g. a1 = 0.45 + 0.24 + 0.14) |
| Eligibility (§8) | x is blocked (`mallory`); m is muted (`spoilers`, one of its two topics). Both are absent, though they score highest, and m never counts toward bob's runs |
| Rank order | `a1 a2 a3 b1 a4 a5` |
| Run limit (§9) | a1, a2; alice is barred, so b1 goes next and a3 is deferred by one; a3, a4; only alice is left and she is barred, so a5 is omitted |

Expected: exit 0, stderr empty, and stdout is this one JSON line followed by a single newline (`\n`), as for every successful CLI run:

```json
{"weights_version": "w-d10d332756fa52f8", "items": [{"id": "a1", "score": "0.83"}, {"id": "a2", "score": "0.73"}, {"id": "b1", "score": "0.55"}, {"id": "a3", "score": "0.65"}, {"id": "a4", "score": "0.53"}]}
```

- Output (stdout), **unchanged**: `{"weights_version": "w-…", "items": [{"id": "a", "score": "0.58"}, ...]}`.
  - Scores are JSON strings in `canonical_text`, because a JSON number would be reparsed as a float and
    lose the exactness the tie rule depends on.
  - Authors and topics are never echoed, and there is no removed count.
- Order of work: parse arguments, start the service, read the request, decode it, rank it. Bad weights
  therefore win over a bad request, which is what "refuses to start" means. The request is read as bytes,
  from `REQUEST_FILE` or `sys.stdin.buffer`, and decoded as strict UTF-8 before `json.loads`.
- **Shape check** (a representation rule, the CLI's only request rule):
  - the top level is an object;
  - `user` is a string;
  - `candidates` is an array of objects;
  - **`blocked_authors` and `muted_topics` are present.**

  The CLI checks presence only. It passes the two decoded values to `FeedRequest` untouched, and
  `_require_id_set` judges them. So a JSON string, object, number or `null` in either key is rejected by
  the same owner, with the same message, as on the library path. Candidate objects go through
  `Candidate.from_mapping`, which owns the `author` and `topics` keys. Unknown top-level keys keep their
  stage-1 treatment: they are not checked.
- Every outcome has its own code. `cli.main` owns the mapping. It catches only `WeightConfigError`,
  `InvalidRequest` and an `OSError` from the request read. On any error, stdout is empty.

| Exit | Outcome | stderr | Message text owned by |
|---|---|---|---|
| 0 | Feed written (including an empty feed, when nothing is eligible) | — | — |
| 1 | *Never returned.* Python's status for an uncaught exception, meaning a defect such as a `decimal` trap (§5) | traceback | Python |
| 2 | Usage error | usage line | `argparse` |
| 3 | `WeightConfigError`: the service refused to start | `error: <path>: <problem>` | `WeightConfigError` (the raiser) |
| 4 | `InvalidRequest`: a rule violation, or a request that isn't UTF-8, isn't JSON or has the wrong shape | `error: <problem>` | `InvalidRequest` (the raiser; `cli` for the representation problems) |
| 5 | Request unreadable: an `OSError` opening or reading `REQUEST_FILE` or stdin (missing, a directory, no permission) | `error: cannot read request <path or stdin>: <strerror>` | `cli` |

- There is no reload subcommand. A one-shot process is a restart; the explicit reload is `FeedService.reload()`
  for a host that embeds the library.

## 12. Rule → owner → entry paths

Entry paths: **L** library `FeedService.rank`; **C** CLI; **S** startup (`FeedService(...)`, CLI
`--weights`); **R** `FeedService.reload`; **D** internal `ranking.rank_feed` (tests only; not public).
Rows marked **(S2)** are new or rewritten in stage 2.

| Rule | Owner (exactly one) | Paths |
|---|---|---|
| What a number is: int/float, finite, canonical decimal, `-0` → `0` | `numbers.exact_number` | via `Weights` (S, R) and `Candidate` (L, C, D) |
| How a number is written (version text, CLI scores) | `numbers.canonical_text` | via `Weights.version` (L, C, D); C output |
| Constructor arity: every keyword present, none unknown (**(S2)** now including `author`, `topics`, `blocked_authors`, `muted_topics`) | Python's signature (`TypeError`). A programming error, outside the product rule (§3) | direct `Weights(...)`, `Candidate(...)`, `FeedRequest(...)` in code |
| Weight names on data: exactly the three | `Weights.from_mapping` via `signals.read_signal_fields` | S, R (file), any mapping caller |
| Weight values: finite, ≥ 0; at least one > 0; never rescaled | `Weights.__init__` | S, R, and any direct `Weights(...)` |
| Config file readable, valid TOML, no duplicate keys | `config_file.load_weights_file` | S, R when the loader is the file loader; C |
| Invalid at startup → refuse to start | `FeedService.__init__` (doesn't catch) | S; the CLI maps it to exit 3 |
| Invalid on reload → keep last valid, report | `FeedService.reload` (build, then swap; raise) | R |
| One weight version per request, never partial | `FeedService.rank` (one read) + `Weights` immutability | L, C |
| Response carries the version used | `rank_feed` stamps it from the one `Weights` it scored with | L, C, D |
| Weight version identity | `Weights.version` (derived) | L, C, D |
| Change only on explicit reload | `FeedService`: the loader is called only in `__init__` and `reload` | S, R |
| score = w_r·r + w_a·a + w_p·p, exact, nothing else (**(S2)** no eligibility or diversity term; author and topics never read) | `Weights.score`, in `EXACT`; reads only the three signals | L, C, D via `rank_feed` |
| **(S2)** Candidate key set on data: exactly `id`, `author`, `topics` and the three signals (missing or unknown → rejected, naming the item) | `Candidate.from_mapping` via `read_signal_fields(leading=("id", "author", "topics"))` | C, any mapping caller |
| Signal values: finite, in [0, 1]; never clamped, filled or dropped | `Candidate.__init__` | L, C, D |
| **(S2)** What an id is: a non-empty `str`, never normalized, matched exactly (case-sensitive) | `request._require_id` | item id, author, topics, list entries (L, C, D) |
| **(S2)** What a collection of ids is: not a string or a mapping; repeats are one; may be empty | `request._require_id_set` | topics, both lists (L, C, D) |
| Item id: a non-empty str | `Candidate.__init__` via `_require_id` | L, C, D |
| **(S2)** Author: exactly one, a valid id | `Candidate.__init__` via `_require_id` | L, C, D |
| **(S2)** Topics: a required collection of valid ids | `Candidate.__init__` via `_require_id_set` | L, C, D |
| **(S2)** Block and mute lists: valid collections of ids | `FeedRequest.__init__` via `_require_id_set` | L, C, D |
| **(S2)** Block and mute lists: required | Library: the `FeedRequest` signature (no default). Data: the `cli` shape check | L, D / C |
| No duplicate ids (**(S2)** over all candidates, eligible or not) | `FeedRequest.__init__` | L, C, D |
| **(S2)** Validity before eligibility | Structural: eligibility is a method of an already constructed, hence valid, `FeedRequest` | L, C, D |
| **(S2)** Blocked author, or any muted topic → absent from the feed | `FeedRequest.eligible_candidates` | L, C, D (`rank_feed`'s only source of candidates) |
| **(S2)** Rank order: score desc, `item_id` asc by code point; exact equality (the stage-1 "Order" rule, narrowed to the rank order) | the sort key in `rank_feed`, `(score.copy_negate(), item_id)` | L, C, D |
| **(S2)** No more than 2 consecutive same-author items; earliest placeable item first; deferred items keep their order; the infeasible tail is omitted | `ranking._limit_author_runs` (`_MAX_SAME_AUTHOR_RUN`) | L, C, D |
| **(S2)** Feed order = run limit ∘ rank order ∘ eligibility | `rank_feed` (the composition only) | L, C, D |
| **(S2)** Shown score = the item's stage-1 score | `rank_feed` computes it once and attaches it after arranging; the run limit never sees scores | L, C, D |
| Empty candidates → empty feed; **(S2)** nothing eligible → empty feed | `rank_feed`, with no special case | L, C, D |
| `user` doesn't affect score, eligibility or order | Structural: neither `rank_feed` nor `eligible_candidates` reads `request.user`; `Weights.score` takes only a `Candidate` | L, C, D |
| Response shape: ordered items, each with its score, plus the version; nothing about removed items | `Feed` / `RankedItem` (unchanged) | L, C, D |
| Request JSON shape (**(S2)** including the two list keys being present) and UTF-8 | `cli` | C only. A representation rule, not a product rule |
| CLI outcome → exit code and stderr line | `cli.main` (§11 table) | C only |

The only stage-1 rule stage 2 rewrites is the order rule. Its sort key survives verbatim as the rank
order, and the run limit is a new owner beside it. Every other stage-1 row keeps its owner. Item-id
validity now delegates to `_require_id`, and that move preserves behavior.

## 13. Re-trace: every reader of a changed shape

- **`Weights.score(candidate)`** reads only the signals. The new fields don't reach it, so scores are
  unchanged.
- **The `FeedRequest` duplicate check** runs over all candidates, so an ineligible twin still collides.
- **`Candidate` equality and hash** now include `author` and `topics`. Both are hashable, since `topics`
  is a `frozenset`. The only consumer is the tests. Two candidates that differ only in topics are
  unequal, which is correct.
- **`rank_feed` → `Feed`.**
  - The shape is unchanged. The items are a subset of the eligible candidates, each with its own
    stage-1 score.
  - Permutation invariance still holds. Ids are unique, so the rank order is total, and the run limit is
    deterministic given that order.
- **The stage-1 test "many → descending"** holds only when no author has a run longer than 2. With a
  distinct author per item (the characterization fixture, §14) it holds unchanged.
- **The `cli` output** reads only `item_id` and `score`, so it is unchanged.
- **`FeedService`** passes the request through untouched. One weight version per request is unaffected,
  and no lock or state is added.

## 14. Test plan (test-first; `unittest`)

**Order of work** (add-feature: characterize, then refactor, then change). Stage 1 is designed but not
built, so:

- **Step 0: build stage 1 and characterize.** Build stage 1 exactly as specified in decisions/0001 and
  this document's unchanged sections, with the Step-0 suite (below) green. Every stage-1 test builds its
  inputs through one fixture helper per shape: a `Candidate`, a candidate mapping (for `from_mapping`), a
  `FeedRequest`, and a CLI request document. Pin as **golden data**:
  - the `(weights, request) → Feed` results for the goals.md scenario, the tie, trap and near-tie cases,
    and a seeded random set;
  - the exact CLI stdout **bytes** for the scenario, a tie set, the trap pair and an empty request.
- **Step 1: refactor, with no behavior change.** Route the item-id check through `_require_id`.
  Restructure `rank_feed` so it scores each candidate once into a local map keyed by `item_id`, sorts the
  candidates (not `RankedItem`s) by the stage-1 key, and then builds the `RankedItem`s from the map. That
  opens the seam, between the sort and the build, where Step 4 inserts `_limit_author_runs`. The whole
  stage-1 suite passes, unedited.
- **Step 2: metadata and lists, validation only.** In one edit, the fixture helpers supply
  `author=<item id>` (all distinct, so there are no runs), `topics=()` and empty lists, and the golden
  JSON inputs gain the same fields. **No expected value or golden output is edited**, and the golden
  stdout stays byte-identical. That proves "empty lists and no long runs → the stage-1 result".
- **Step 3: eligibility.**
- **Step 4: diversity.**

Each step is green before the next begins.

### 14.1 Step-0 suite: stage 1, per module

The stage-1 test obligations, which Steps 1 and 2 must pass unedited. Order of writing: `numbers` →
`signals` → `weights` → `request` → `ranking` → `config_file` → `service` → `cli`. Each module's tests
come before its code. Tests assert the public contract. `numbers` is tested directly because it owns §6,
and `ranking` is imported directly because `rank_feed` isn't public. The only change from the stage-1
plan is that every input is built through the fixture helpers (Step 0).

- **numbers**
  - `0.1` → `Decimal("0.1")`, not its binary expansion; `3` → `3`; `-0.0` → `0`.
  - `True`, `"0.5"`, `None`, `Decimal("0.5")` → not a number. NaN, ±inf, `10**400` → not finite.
  - `canonical_text`: `0.50` → `"0.5"`, `2` → `"2"`, `1e22` → `"10000000000000000000000"`, and it is
    unchanged under `getcontext().prec = 3`.
- **signals.** Exact key set → values. The first missing key, then the first unknown key, are reported
  in a fixed order. `leading` keys are required too.
- **weights**
  - The scenario `0.5/0.3/0.2` constructs.
  - Missing, unknown and empty mapping → errors naming the key. Negative, NaN, inf, string, bool →
    rejected naming the weight.
  - All zero → rejected; `0/0/5e-324` accepted. Sum 1.7 accepted and not rescaled: `(2, 0, 0)` with
    recency 0.5 scores exactly `1`.
  - Version: the two §7 examples as hard-coded strings; equal for `0.5` and `0.50`; different for any
    change.
  - Construction: `Weights(recency=0.5, affinity=0.3)` → `TypeError`, not `WeightConfigError`.
  - Formula: the scenario scores `0.58` and `0.55` exactly. **Trap**: x and y both score
    `Decimal("0.03")`. **Ambient context ignored**: with `getcontext().prec = 3`, a score needing 20
    digits is still exact.
- **request**
  - Empty id, non-str id → rejected; `" "` accepted.
  - For each signal: missing, unknown extra key, `-0.01`, `1.01`, NaN, inf, `"0.5"`, `None`, bool →
    rejected with `item_id` and `signal` set. Missing and unknown go through `from_mapping` (the mapping
    helper, minus or plus one key). A missing keyword on the constructor is a `TypeError`.
  - Exactly `0` and `1` accepted. `1.2` is rejected, not stored as `1`.
  - A duplicate id at any positions, including with different signals → rejected with `item_id`.
  - One bad item among many rejects the whole request.
- **ranking**
  - Empty → `Feed(v, ())`; one; many descending (from Step 2 the helper gives each item its own author, so this holds; §13).
  - Exact tie → id ascending, `"10"` before `"9"`, `"B"` before `"a"`.
  - The trap pair is ordered by id, and the same data as Python floats gives the same result.
  - A near-tie (scores differing in the 30th digit) keeps score order. This guards `copy_negate` and the
    exact context.
  - Permutation invariance over seeded shuffles. `user` independence. The version is stamped from the
    given weights.
- **config_file.** A valid file → `Weights` equal to one built in code. Missing file, directory, bad
  UTF-8, TOML syntax error, duplicate key, `nan`, string value, unknown key → `WeightConfigError` with
  `source` = the path and the problem named.
- **service** (in-memory loaders; no files)
  - A loader that raises → the constructor raises.
  - Reload valid → the next `rank` has the new version and scores. Reload invalid → raises, and the next
    `rank` still has the old version. A→B→invalid → B.
  - A non-domain `RuntimeError` from the loader → propagates, old weights kept.
  - The loader is called once at construction and once per `reload()`, never by `rank`.
  - **No mix under concurrency**: N threads rank a large request while one thread alternates reloads
    between V1 and V2. Every feed's scores equal `rank_feed(V_named, request)` for the version it names.
  - **Overlapping reloads**: with barriers, a slow load of A and a fast load of B. The final version is
    the last to finish under the lock, never a stale overwrite.
- **cli** (end to end)
  - The goals.md scenario → exit 0, items `a, b, c`, scores `"0.58", "0.55", "0.55"`.
  - Edit the file and rerun → new version.
  - Bad weights → exit 3, stderr names the problem, stdout empty. Bad weights and a bad request
    together → 3.
  - Bad signal → exit 4, naming item and signal.
  - Malformed JSON, missing `candidates`, non-UTF-8 bytes on stdin → exit 4.
  - `REQUEST_FILE` missing, or a directory → exit 5 naming the path.
  - Unknown flag → 2.
  - Empty `candidates` → `"items": []`.

### 14.2 Stage-2 tests (Steps 2–4)

**request: ids and metadata**

- The item-id message is `item id must be a non-empty string (<repr>)`, and the CLI prefixes
  `candidates[i]: ` (§3.1); both pinned. `" "` is accepted, and `"a"` ≠ `"A"`.
- **author**
  - A missing key goes through `from_mapping` → `InvalidRequest` with `item_id` set and `signal` `None`.
    A missing keyword on the constructor → `TypeError`.
  - `""`, `None`, `3` and `["A"]` are rejected, naming the item.
  - `"Alice"` is stored as `"Alice"`.
- **topics**
  - A missing key is rejected.
  - `"sports"` (a bare string: the trap), `{"t": 1}` (a mapping), `None` and `3` are rejected.
  - `["cats", ""]` and `["x", 3]` are rejected, naming `topics[i]`.
  - `[]`, a tuple, a set and a generator are accepted.
  - `["x", "x"]` builds a `Candidate` equal to one built with `["x"]`.
- **An unknown candidate key** (`"topic"`, `"authors"`) is rejected, as in stage 1:
  `item 'b': unknown 'topic'`, with `signal` = `'topic'` (§5). A missing `author` or `topics` has
  `signal` `None`; a missing signal has `signal` set.
- **First-problem order.** A bad author plus a bad signal reports the author.

**request: FeedRequest**

- **Lists**
  - A missing keyword → `TypeError`.
  - A bare string, a mapping, `None`, and an entry of `""` or `3` → `InvalidRequest` naming the list and
    the index.
  - Empty and repeated entries are accepted.
- **Validity first**
  - A blocked item with `recency=1.2` → rejected.
  - A duplicate id where one twin is muted and the other eligible → `duplicate item id`.
  - A muted item with an empty-string topic → rejected.
- **`eligible_candidates()`**
  - A blocked author is excluded.
  - An item with one muted topic among several unmuted ones is excluded.
  - Empty topics are never muted.
  - Blocking `"Alice"` does not exclude `"alice"`, and muting `"Cats"` does not hide `"cats"`.
  - A muted topic equal to an author id does not exclude that author, and vice versa: the namespaces are
    separate.
  - A muted topic no item has has no effect.
  - Repeated list entries act as one.
  - Submission order is preserved.
  - All ineligible → `()`.

**ranking** (path D). Weights `(1, 0, 0)` with descending recencies, so each test states the rank order
directly.

- **Characterization.** The golden `Feed`s are unchanged: ties, `"10"` before `"9"`, `"B"` before `"a"`,
  the trap pair, the near-tie that guards `copy_negate`, permutation invariance, `user` independence.
- **Eligibility.**
  - A blocked item with the **top** score is absent. The next item leads, and every other score is
    unchanged.
  - The same holds for an item with one muted topic.
  - All ineligible → `Feed(v, ())`.
- **Diversity.**
  - The four goals.md examples, verbatim.
  - Runs of 1 and 2 → identity; `A A B A A B` → identity.
  - A run of exactly 3 followed by another author: the third is deferred by one.
  - Interleaving: `a1 a2 a3 b1 b2 b3` → `a1 a2 b1 a3 b2 b3`.
  - Many authors: `A A A A B C D` → `a1 a2 b1 a3 a4 c1 d1`.
  - A single author with n = 0, 1, 2, 5 → 0, 1, 2 and 2 items.
  - An infeasible tail mid-feed: `a1 a2 b1 a3 a4 a5` → `a1 a2 b1 a3 a4`.
  - Case: authors `A a A` are not a run.
- **Filter before arrangement.** `a1[A] a2[A] x[X, blocked] a3[A]` → `a1 a2`.
- **Ties.**
  - Equal scores within one author → id order, including after a deferral.
  - Equal scores across authors → id order, and the earlier one counts toward its author's run.
  - A tie at a deferral point: the deferred item goes after the tied placeable one.
- **Scores unchanged.** Every `RankedItem.score == weights.score(candidate)` (`Decimal` equality). When
  diversity fires, the shown order is not score-descending. The stage-1 numeric guards (trap pair,
  30th-digit near-tie, `getcontext().prec = 3`) are rerun with authors that force a deferral.
- **Invariants.** Checked by a seeded random property test over 5 authors:
  - the output ⊆ the eligible candidates, with no repeats;
  - no author appears 3 times in a row;
  - same-author items keep rank order;
  - each position holds the earliest placeable remaining item;
  - any omitted items are all by the author of the last two placed (with "no repeats" and the line
    above, this is the guard for §9's convention that the run limit never compares ids or signals);
  - a permuted input gives the same feed.

**service.** The §14.1 service tests stay, unedited. Add:

- a request with a blocked item and a forced deferral through `FeedService.rank` (path L);
- the stage-1 concurrency test ("no mix under concurrency") rerun with that request shape.

**cli (end to end).**

- The §11 worked example (a blocked top-score item, a muted item, a deferral and an omitted tail) →
  exit 0, stderr empty, stdout exactly the line shown there.
- All ineligible → `"items": []`, exit 0.
- A missing `muted_topics` → exit 4, `request: 'muted_topics' is missing`, stdout empty.
- `"blocked_authors": "A"` → exit 4.
- `"topics": "x"` → exit 4.
- A candidate without `author` → exit 4, naming the item.
- Bad weights together with a bad list → exit 3 (weights still win).
- The goals.md scenario with distinct authors and empty lists → byte-identical to the golden output.
- Every §14.1 CLI case, through the Step-2 fixtures, keeps its exit code and message.

## 15. What was cut (subtractive pass) and concept fit

**Cut** (no present force behind any of these):

- **New types:**
  - a `WeightSource` Protocol (stage 1);
  - a `Scorer` strategy;
  - `Signals`, `ItemId`, `AuthorId`, `TopicId`, `ItemMeta`, `Score` and `WeightsVersion` types: none has
    a rule of its own;
  - an `Exclusions` or `Eligibility` value;
  - a `Filter` or `Rule` protocol or pipeline;
  - a `diversity.py` module;
  - `key=` or `max_run=` parameters on the arrangement.
- **Errors:**
  - a shared error base, or per-problem subclasses (`IneligibleItem`, `DiversityInfeasible`);
  - an `InvalidRequest.field` attribute.
- **Service and entry points:**
  - `FeedService.from_file`;
  - a `current_version` query, a `last_error` field, or a version returned from `reload`;
  - `rank_feed` on the public surface;
  - CLI `reload` and `validate` subcommands.
- **Response additions:**
  - `user` echoed in `Feed`;
  - `RankedItem.author`;
  - removed or omitted counts;
  - the pre-diversity order in `Feed`.
- **Flags and parameters:**
  - a `diversify` flag or a truncation parameter;
  - defaults of `()` on the new keywords;
  - sentinel defaults on constructors.
- **Alternative placements:**
  - filtering in `FeedService.__init__`, `FeedService.rank`, `cli`, or at `FeedRequest` construction;
  - `Candidate.is_eligible`;
  - `FeedRequest.from_mapping` (see §10);
  - the closed `IdCollection` alias.
- **Other:**
  - a lock on the request path;
  - file watching;
  - logging;
  - exact text-parsing hooks;
  - a linear-time arrangement.

**Kept, with the force behind each:**

- **Foundations.**
  - `numbers`: stage-1 decision §6, shared by weights and signals.
  - `signals`: which signals exist.
- **Stage-1 types.**
  - `Weights`: weight rules, the formula and version identity.
  - `Candidate`: the signal contract, the id rule, and now the item's author and topics.
- **The request.**
  - `FeedRequest`: duplicate ids, the lists, and eligibility, all of which concern the whole request.
  - `eligible_candidates()`: the one owner of the filter, and the funnel for every path.
- **The order.**
  - `rank_feed`: the order's composition. It is pure, so it can be tested without a service.
  - `_limit_author_runs`: the one owner of the sequence constraint. It is a different kind of rule from
    the key.
  - `_MAX_SAME_AUTHOR_RUN`: names the product's "2" once.
- **Id helpers.**
  - `_require_id` and `_require_id_set`: one meaning of "id" across five fields.
  - The refusal of strings and mappings: the stated "malformed → rejected" case.
- **The shell.**
  - `FeedService`: the one mutable state.
  - `WeightLoader`: the core must not know the source.
  - The reload lock: prevents a stale overwrite.
  - `config_file`: weights come from a file.
  - The CLI: the optional small CLI.

**Concept fit.**

- **Eligibility is a filter.** It is a subset query on a valid request, run before scoring. It is not a
  score, a sentinel, a flag on the item, or an error.
- **Diversity is a sequence constraint.** It maps a priority-ordered sequence to an arranged
  subsequence. It is not a key, a penalty or a comparator.
- **An omitted tail is absence.** There is no placeholder item.
- **The rank order is still a sort key**, unchanged.
- **`Weights` is a value**, not a config-file object, and the version is its derived identity.
- **A rejection is an exception**, never a sentinel score or a dropped item. (Filtering is not rejection:
  the request is valid and the item is simply not shown.)
- **`topics` and the lists are sets**, because repeats and order carry no meaning.
- **An empty feed is a `Feed` with no items.**
- **`user` is identity** carried on the request, not a ranking parameter.

## 16. Assumptions (choices the PO handed back; each a simple default)

Stage 1 (unchanged):

1. The weight config version id is a content hash of the weights (§7).
2. A number means the nearest IEEE-754 double, read as its shortest decimal (§6).
3. Unknown keys on a candidate object are rejected, the same as for weights, so a misspelled signal fails
   fast.
4. `user` must be a `str`; empty is allowed, since no rule was stated. It is not echoed in the response.
5. Overlapping reloads: the last to finish under the lock wins.
6. Each constructor reports its first problem, in a fixed order.
7. The config file format is TOML. The CLI request format is UTF-8 JSON, and CLI scores are decimal
   strings.
8. "Rejected, naming item and signal" applies to request *data*. A missing constructor keyword in the
   caller's own code is a programming error (`TypeError`), because the signature is the library contract.
9. CLI exit codes are 0/2/3/4/5 (§11). Code 1 is left to Python, so a crash is never mistaken for a
   rejection. An unreadable request file is its own outcome, distinct from a rejected request.

Stage 2 (the product decisions themselves are in goals.md "Stage 2"; these are the design-level defaults
under them):

10. The block and mute lists are required but may be empty. They are required keywords in the library and
    required keys in the JSON.
11. An infeasible diversity tail is omitted and the feed ends. The greedy reading keeps score order ahead
    of feed length: `b1 a1 a2 a3` → `b1 a1 a2`.
12. A bare string, `bytes` or a mapping passed where a collection of ids is expected is rejected, not
    iterated. Any other iterable of strings is accepted.
13. An entry is named by its index in iteration order, which is the JSON array index on the CLI. For a
    `set` passed by a library caller, which bad entry is named first is unspecified.
14. Ids (item, author, topic) are exact strings: no case folding, stripping or normalization. `" "` is
    valid. Author ids and topic ids are separate namespaces.
15. Unknown top-level JSON request keys keep their stage-1 treatment (not checked).
16. Diversity counts runs by exact author equality, on the filtered sequence.
