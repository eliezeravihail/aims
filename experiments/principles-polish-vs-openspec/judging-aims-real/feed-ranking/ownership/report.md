# Blind design judgment: feed ranking, designs X and Y

**Judge disposition:** invariant ownership. This judge looks hardest for under-structure: a rule with more than one home, an invariant that can be bypassed, and a domain type that can hold illegal states.

**Method:** every row score is derived from binary sub-checks. Row score = min(round(10 × passed / applicable), severity ceiling). The ceilings are S1 → 8, S2 → 7, S3 → 5, S4 → 2, and the weights are ×1, ×1, ×2, ×4, ×8 (none, S1, S2, S3, S4).

**Profile:** grade = Σ(score × weight) / Σweight, with no global cap. It is reported with the worst chapter, the (#S3, #S4) counts and the gate (any S4 ⇒ BLOCKED).

**Evidence used:** only what each design specifies: types, owners, seams, rules and cases. Y's proposal, spec and tasks files are read only as evidence of what the design specifies (for example, the scenarios pin its behavior). Wording, length and principle vocabulary are not credited.

---

## Step 0: fixed inventory (from product/, identical for both designs)

**Rules (R)**
- **R1** score = w_r·recency + w_a·affinity + w_p·popularity.
- **R2** Order is by score, highest first.
- **R3** Ties break by a stable item id. The brief sharpens this: mathematically equal scores must tie exactly.
- **R4** Weights are per-deployment configuration, changed without a code change. Invalid weights are rejected, and the last good weights are kept on reload.
- **R5** One weight set per request, with no mixing during a reload.
- **R6** Signals are in [0, 1]. Invalid input is rejected, not "fixed".
- **R7** (stage 2) An item from a blocked author, or on a muted topic, never appears in the feed.
- **R8** (stage 2) No more than 2 consecutive items share an author. A third is deferred, and score order is otherwise preserved as much as possible.
- **R9** (stage 2) Scoring and weights keep working as before.

**Change axes (X)**
- **X1** Weight values change.
- **X2** The weight source changes. This is the plausible unstated variant.
- **X3** A new eligibility-style rule.
- **X4** A new ordering or sequence rule.
- **X5** A fourth signal. This is declared a non-axis by both designs.

**Acceptance cases (C)**
- **C1** Weights 0.5/0.3/0.2 give the expected scores and order.
- **C2** The exact-tie trap: mathematically equal sums tie and are ordered by id.
- **C3** Empty candidates give an empty feed.
- **C4** Invalid weights at start mean the service refuses to start. Invalid weights on reload mean the last good weights are kept and the failure is reported.
- **C5** A blocked item with the top score is absent.
- **C6** A muted item is absent and does not count toward a run.
- **C7** `a1 a2 a3 b1` gives `a1 a2 b1 a3`.
- **C8** All candidates ineligible gives an empty feed.

**Applicability (identical for all four forms)**
- Rows §1–§14 apply.
- §15 (testability) is N/A: it is code-leaning per design-principles, and these are pure design documents.
- §16 (performance) is N/A: the oracle says "no performance requirement is stated".
- §17 (security) is N/A: there is no trust boundary; it is a single-process library plus a local CLI.

### Sub-checks per row (shared by all four forms)

| § | Sub-checks |
|---|---|
| 1 | (a) orchestrators tell and do not query-then-decide; (b) no reach-through chains across a seam; (c) each component talks only to immediate collaborators |
| 2 | (a) injected dependencies are programmed to an owned abstraction; (b) crossing input types are calibrated, accepting every legitimate producer of the published type; (c) concept fit: each concept is modelled as its kind (tie as a sort key; stage 2: filter as a filter, run rule as a sequence step) |
| 3 | (a) injected dependencies are no wider than what is used; (b) the public surface has no method nobody uses |
| 4 | (a) each rule-bearing concept has a type; (b) illegal states are unrepresentable (fixed fields, validated construction); (c) no anonymous clumps at public seams; (d) ids and collections are typed to state their rule |
| 5 | (a) value types enforce their own invariants at construction; (b) behavior sits with the data it owns; (c) no "manager" holding logic over data bags |
| 6 | (a) dependencies are acyclic and point toward the stable side; (b) declared change axes are localized; (c) OCP: foreseeable axes extend at a seam; (d) no product rule is held in an adapter |
| 7 | (a) public seams speak domain types, not wire formats; (b) implementation exceptions are translated; (c) one error type per distinct handling |
| 8 | (a) each component has one reason to change; (b) no god object; (c) core/shell separation |
| 9 | One unbypassable owner, with all entry paths funnelling through it, for: (a) formula; (b) order and tie; (c) weight validity; (d) request and signal validity; (e) one weight set per request; stage 2 also (f) eligibility and (g) run limit |
| 10 | (a) the signal set has one home; (b) the meaning of "a number" has one home; (c) the id and validation rules have one home |
| 11 | (a) intention-revealing names; (b) errors name the item or field in the consumer's terms; (c) failure outcomes are distinguishable |
| 12 | (a) every type and layer answers to a present force; (b) no speculative config, source or format room; (c) no unrequested features |
| 13 | (a) C1; (b) C2; (c) C3; (d) C4; (e) R5 under concurrent reload; (f) exactness over the whole input space (host decimal context, long inputs, near-ties); stage 2 also (g) C5; (h) C6; (i) C7; (j) C8; (k) scores unchanged by stage 2 |
| 14 | (a) values are deeply immutable; (b) a single mutable reference is swapped only after full validation; (c) concurrent reloads are serialized; (d) functional core, imperative shell |

---

## 1. D1: first-round design

### X-stage-1

| § | Principle | Applies | Sub-checks | Score | Severity | Finding and citation |
|---|---|---|---|---|---|---|
| 1 | Tell-Don't-Ask / Law of Demeter | Y | a✓ b✓ c✓ | 10 | — | `FeedService.rank` passes one value down: "`weights = self._weights … return rank_feed(weights, request)`". The formula is told to the owner: `Weights.score(candidate)`. |
| 2 | Interface calibration and concept fit | Y | a✓ b✗ c✓ | 7 | S1 | **(b)** Constructors accept `Number: TypeAlias = int \| float` and list "`Decimal("0.5")` → not a number". The design also says "`Decimal` crosses seams freely… it is the published numeric representation". A caller holding the library's own output type cannot feed it back, so the input is calibrated below a legitimate producer. This is local. **(a)** holds: "`WeightLoader = Callable[[], Weights]` injected". **(c)** holds: "The tie-break is part of the sort key, never a perturbation of the score". |
| 3 | Interface Segregation | Y | a✓ b✓ | 10 | — | The injected dependency is a zero-argument callable. `rank_feed` is kept internal ("no consumer outside tests"). |
| 4 | Primitive obsession / illegal states | Y | a✓ b✓ c✓ d✓ | 10 | — | `Weights`, `Candidate`, `FeedRequest`, `RankedItem` and `Feed` are frozen, with named fields. "There is no other constructor, so a test fake or a future loader can't produce invalid weights either." `item_id: str` carries its one rule inside `Candidate.__init__`, so it cannot be bypassed. |
| 5 | Anemic domain model | Y | a✓ b✓ c✓ | 10 | — | "`Weights.__init__` … each exact_number, >= 0; at least one > 0". "`FeedRequest.__init__` … no duplicate item_id". The formula lives on `Weights.score`. |
| 6 | Cohesion, coupling, OCP | Y | a✓ b✓ c✓ d✓ | 10 | — | "Imports are acyclic and point toward `numbers` and `signals`". The weight source (X2) is absorbed by the injected loader. The CLI does only "JSON shape" checks. |
| 7 | Leaky abstractions / error vocabulary | Y | a✓ b✓ c✓ | 10 | — | Seam table: caller → service crosses "`FeedRequest`", never "dicts, raw JSON". The loader never lets through "`OSError`, `TOMLDecodeError`". There are two error types, "one per distinct handling". |
| 8 | Single Responsibility / god object | Y | a✓ b✓ c✓ | 10 | — | "`FeedService` holds the only mutable state". `config_file` parses and nothing else. `rank_feed` is pure. |
| 9 | One unforgeable owner | Y | a✓ b✓ c✓ d✓ e✓ | 10 | — | §9 table, "Owner (exactly one)": formula → `Weights.score`; order → `rank_feed`; weight values → `Weights.__init__`; signals → `Candidate.__init__`; one read → `FeedService.rank`. Library and CLI both reach `rank_feed` through `FeedService`. |
| 10 | DRY | Y | a✓ b✓ c✓ | 10 | — | `SIGNAL_NAMES` has one home. "What a number is" is owned by `numbers.exact_number` on every path ("One meaning of a number on every path"). |
| 11 | Naming and failure | Y | a✓ b✓ c✓ | 10 | — | Errors name the item and signal ("`item 'b': signal 'affinity' is outside [0, 1] (1.2)`"). Exit codes are distinct (0/2/3/4/5), and "Code 1 is left to Python". |
| 12 | YAGNI / subtractive | Y | a✓ b✓ c✓ | 10 | — | §11 cut list: the Protocol, the Scorer strategy, the id types and a `from_file`. What is kept is tied to a force. The version id rests on a stated rule ("Response carries the version used"). |
| 13 | Functional correctness | Y | a✓ b✓ c✓ d✓ e✓ f✓ | 10 | — | C1: "scores `0.58` and `0.55` exactly". C2: "Both score `0.03` exactly". C3: "`rank_feed`, with no special case". C4: "build, then swap; raise". (f) holds: "`EXACT.multiply` … never uses the ambient thread context" and "`copy_negate` is exact". |
| 14 | State and side effects | Y | a✓ b✓ c✓ d✓ | 10 | — | `Weights` is frozen with `Decimal` fields. "`fresh = self._load_weights()` … `self._weights = fresh`". The reload lock prevents "an older file's content last". The core is pure. |
| 15 | Testability | N/A | | | | Code-leaning; N/A on a design document. |
| 16 | Performance | N/A | | | | No stated requirement. |
| 17 | Security | N/A | | | | No trust boundary. |

**Profile X-stage-1:** grade = (13·10 + 7·1)/14 = **9.79**. worst = 7. (#S3, #S4) = (0, 0). Gate **CLEAR**.

### Y-stage-1

| § | Principle | Applies | Sub-checks | Score | Severity | Finding and citation |
|---|---|---|---|---|---|---|
| 1 | Tell-Don't-Ask / Law of Demeter | Y | a✓ b✓ c✓ | 10 | — | "`FeedService.rank` calls `weights.snapshot()` once, then `parse_request(raw)`, then `rank(snapshot, request.candidates)`". There are no reach-through chains. |
| 2 | Interface calibration and concept fit | Y | a✗ b✓ c✓ | 7 | S2 | **(a)** `FeedService.__init__(self, weights: WeightsProvider)` depends on the concrete file-backed class, whose constructor is `WeightsProvider.__init__(self, path: Path)`. The weight-source axis (X2) has no abstraction, so a non-file source must reopen `WeightsProvider` or `FeedService`. **(c)** holds: "sort key `(-score, item_id)`", the tie inside the key. |
| 3 | Interface Segregation | Y | a✓ b✓ | 10 | — | This is the same dependency as §2(a). It is referenced there and not deducted again. |
| 4 | Primitive obsession / illegal states | Y | a✓ b✗ c✓ d✓ | 7 | S2 | **(b)** `class Candidate: item_id: str; signals: Mapping[str, Decimal]` and `class Weights: values: Mapping[str, Decimal]`. The signal key set and value ranges are not in the type, so a `Candidate` with `{"recency": Decimal(5)}` and no affinity is representable. The rule survives only because the parser funnels input (see §5). This is confined to two types. |
| 5 | Anemic domain model | Y | a✗ b✓ c✓ | 7 | S2 | **(a)** "Raw input becomes a `RankRequest` or `Weights` only through `parse_request` or `parse_weights`. Those are the only places that reject bad data". The value types are unvalidated data bags, and their invariants live in free functions. The funnel exists, so this is not a §9 failure. |
| 6 | Cohesion, coupling, OCP | Y | a✓ b✓ c✓ d✓ | 10 | — | Components table: `signals` → models → core. The CLI "only calls `FeedService`". The X2 coupling is referenced from §2 and not deducted again. |
| 7 | Leaky abstractions / error vocabulary | Y | a✗ b✓ c✓ | 7 | S2 | **(a)** The public library seam is `def rank(self, raw_request: Mapping) -> list[RankedItem]`. The library API speaks the JSON-shaped dict, not a domain request type. **(b)** holds: "fail fast when the path is missing, invalid or unreadable" is translated to `ConfigError`. **(c)** holds: `ValidationError` and `ConfigError`. |
| 8 | Single Responsibility / god object | Y | a✗ b✓ c✓ | 7 | S1 | **(a)** `WeightsProvider` owns "read the JSON file at a path, build `Weights`, hold the current snapshot, `reload()` with last-good retention". It mixes the file format with the snapshot lifecycle, so it has two reasons to change. |
| 9 | One unforgeable owner | Y | a✓ b✓ c✓ d✓ e✓ | 10 | — | Formula: `score`. Order: `rank` "(score desc, then `item_id` asc)". Weights: `parse_weights`, whose only producer is `WeightsProvider`. Request: `parse_request`, which every library and CLI call reaches because `FeedService.rank` takes the raw input. One snapshot: "`FeedService` takes one `snapshot()` per request". |
| 10 | DRY | Y | a✓ b✗ c✓ | 7 | S1 | **(b)** "A number" is defined in two places: "Floats are converted via `Decimal(str(x))`" (parse boundary) and "JSON parsing uses `json.loads(..., parse_float=Decimal)`" (CLI and file readers). The same double means different numbers by path. The JSON text `0.1000000000000000055511151231257827` (the exact binary value of 0.1) is kept exact on the CLI path, while the float `0.1` from a library caller becomes `Decimal("0.1")`. |
| 11 | Naming and failure | Y | a✓ b✓ c✗ | 7 | S1 | **(c)** "It exits 0 on success, 2 on a request validation error and 3 on a config error". Exit 2 is also argparse's usage-error code. `feed-rank --confg w.json req.json` (a typo) and a valid invocation with `popularity: 1.2` both exit 2. The exit code for an unreadable request file is unspecified. |
| 12 | YAGNI / subtractive | Y | a✓ b✗ c✓ | 7 | S1 | **(b)** "An environment variable such as `FEED_RANKING_CONFIG` can supply the path as a fallback" and "The top-level object leaves room for later keys": a second configuration source and format headroom that no rule or axis asks for. |
| 13 | Functional correctness | Y | a✓ b✓ c✓ d✓ e✓ f✗ | **2** | **S4** | **(f)** The spec says "Scores SHALL be computed exactly, so two candidates whose weighted sums are mathematically equal get equal scores". The design computes `score(w, c) = sum(w[s] * c[s] for s in SIGNALS)` and sorts by `(-score, item_id)` in the ambient `decimal` context, which is 28 digits and host-mutable, with no precision bound on parsed inputs. Distinct scores are rounded into false ties. Reproducing inputs are in §3 (F1). |
| 14 | State and side effects | Y | a✗ b✓ c✓ d✓ | 8 | S1 | **(a)** "`Weights` is frozen" but holds `values: Mapping[str, Decimal]` (and `Candidate.signals` likewise), so the freeze is shallow if a `dict` is stored. **(b)** and **(c)** hold: "validates it into a new `Weights`, and only then replaces the reference" and "A lock around `reload()` serializes concurrent reloaders". |
| 15–17 | Testability, performance, security | N/A | | | | As above. |

**Profile Y-stage-1:** Σweight = 25. grade = 148/25 = **5.92**. worst = 2. (#S3, #S4) = (0, 1). Gate **BLOCKED**.

If the §13 defect is removed (it has a one-line local fix: a module-owned exact context), the grade is 142/18 = 7.89 and the gate is CLEAR. The verdict below does not depend on the S4.

**D1 winner: X.** X leads under both readings (9.79 against 5.92, or 7.89 with Y's S4 fixed).

The gap is structural, and it is exactly where this judge looks hardest:
- **X:** every invariant is owned by the value type's own constructor, which is its only constructor. The weight source is behind an injected abstraction. Exactness is owned by one context.
- **Y:** the invariants are owned by parser functions over open `Mapping` bags. The service depends on a concrete file provider. The library seam speaks raw dicts. Exactness is claimed but not owned.

---

## 2. D2: change absorption

**Classification rule:**
- **survived:** untouched.
- **extended:** additions only; existing responsibility and boundary are kept.
- **reopened:** the responsibility or boundary changed. This includes a breaking signature, a changed return type, or a restructured body taking on a new job.
- **discarded:** gone.

### X: stage 1 → stage 2

| Component or seam | Class | Evidence |
|---|---|---|
| `numbers`, `signals` | survived | "[core foundation, unchanged]". `read_signal_fields(…, leading=…)` is reused as it was. |
| `Weights`, `WeightConfigError`, `Weights.score` | survived | "`weights.py — UNCHANGED`"; "reads only the three signals". |
| `config_file` | survived | "`config_file.py — UNCHANGED`" |
| `FeedService`, `WeightLoader` | survived | "`service.py — UNCHANGED`"; "`FeedService` passes the request through untouched". |
| `RankedItem` | survived | "`score: Decimal # the item's own stage-1 score`" |
| `__init__` public surface | survived | "re-exports the same ten names as in stage 1" |
| `InvalidRequest` | extended | "unchanged type and attributes; new messages only" |
| `cli` | extended | "signature UNCHANGED; the request JSON grows" |
| **`Candidate`** | **reopened** | Its constructor boundary gains required keywords: "`def __init__(self, item_id: str, *, author: str, topics: Iterable[str], …)`". The stage-1 id check moves ("The stage-1 item-id check moves behind `_require_id`"). |
| **`FeedRequest`** | **reopened** | "Stage-1 calls stop working, deliberately. A call like `FeedRequest("u1", [...])` is now a `TypeError`." It also takes on a new responsibility: "the query `eligible_candidates()`, which is the one owner of eligibility". |
| **`rank_feed`** | **reopened** | "Restructure `rank_feed` so it scores each candidate once into a local map … That opens the seam, between the sort and the build". Also: "The only stage-1 rule stage 2 rewrites is the order rule." Its job changed from sorting to composing filter, sort and run limit. |
| **`Feed` (items contract)** | **reopened** | Stage 1: "`score desc, then item_id asc`". Stage 2: "arranged so that no author has more than 2 consecutive items; items that cannot be placed are omitted … NOT strictly score-descending". This is forced by the requirement; Y has the symmetric case. |
| Seams caller→service (extended), loader→service (survived), service→`rank_feed` (survived), config→core (survived), cli→library (extended) | — | §4 seam table, stage 1 against stage 2. |
| New | — | `_require_id`, `_require_id_set`, `_limit_author_runs`, `_MAX_SAME_AUTHOR_RUN`, `eligible_candidates()`. |

**X: reopened + discarded = 4 + 0 = 4.** The instances are `Candidate`, `FeedRequest`, `rank_feed` and the `Feed` contract.

### Y: stage 1 → stage 2

| Component or seam | Class | Evidence |
|---|---|---|
| `signals` | survived | Unchanged (not named in stage-2 changes) |
| `Weights`, `parse_weights`, `ConfigError`, `WeightsProvider` | survived | "`ranking-config` is not affected. Weights, their file, validation and reload behave exactly as before". |
| `score` (formula) and the sort key | survived | "Scoring and the score-order sort stay byte-for-byte the stage-1 rules". |
| `RankedItem` | survived | "the response entry shape (`item_id`, `score`)" is unchanged. Its construction moves into `FeedService`. |
| `RankRequest` | extended | "`RankRequest(+exclusions: Exclusions)`". The lists are optional ("default empty"), so stage-1 request bodies keep this shape. |
| `parse_request` / request model validation | extended | New rules are added to the same owner: "**plus `author`/`topic` non-empty strings**; **`Exclusions` validity**". |
| `FeedService` | extended | Its stage-1 role was "Per-request orchestration". In stage 2 it is "Composition order: parse, then filter, then rank, then arrange, then project". The role is unchanged and the pipeline gains stages. |
| CLI | extended | "Same command and exit codes. The input JSON gains `author` and `topic`". |
| **`rank` (ranking core)** | **reopened** | Its return type changes from stage-1 `rank(...) -> list[RankedItem]` to stage-2 `rank(...) -> list[Scored]`: "**The only change is that it returns `Scored(candidate, score)` so later stages can still see `author`**". |
| **`Candidate`** | **reopened** | "**BREAKING (request shape):** each candidate now requires an `author` … and a `topic` … Stage-1 requests without `author`/`topic` are rejected." |
| **Response contract** | **reopened** | "**BREAKING (completeness):** … Stage 1 promised 'every candidate exactly once'". The spec has "MODIFIED Requirements … Order by score descending". This is forced by the requirement; X has the symmetric case. |
| Seams FeedService→WeightsProvider (survived), FeedService→parse_request (extended), FeedService→rank (reopened; this is the same instance as `rank`), CLI→FeedService (extended) | — | Stage-1 and stage-2 architecture diagrams |
| New | — | `Exclusions`, `Scored`, `eligibility.is_eligible` / `filter_eligible`, `diversity.arrange`, `MAX_SAME_AUTHOR_RUN`. |

**Y: reopened + discarded = 3 + 0 = 3.** The instances are `rank`'s return type, `Candidate`, and the response contract.

**Survival reading against the oracle.** The oracle says a design "extends if eligibility and diversity slot in as new stages of an already-seamed pipeline … with scoring untouched", and "reopens if … there was no pipeline seam and the order was produced inline".

- **Y:** its two rules arrive as new modules composed by a pre-existing orchestrator. Its one core reopen is a widened return type; the formula and the key are untouched.
- **X:** its formula and key are also untouched (`Weights.score` and the sort key "verbatim"). But `rank_feed` had to be restructured to open the sort-to-build seam, which is X's own admission. Both new rules landed inside existing owners: a new method on `FeedRequest`, and a private step inside `rank_feed`.

X's placements are cohesive and funnel every path, but they are placements in reopened owners, not at a pre-existing seam.

**D2 winner on survival: Y, narrowly** (3 against 4, and the oracle's "extends" profile). Per measurement.md, this behavioral count is corroboration only and does not outrank the form.

### X-stage-2 form

| § | Principle | Applies | Sub-checks | Score | Severity | Finding and citation |
|---|---|---|---|---|---|---|
| 1 | Tell-Don't-Ask / Law of Demeter | Y | a✓ b✓ c✓ | 10 | — | `rank_feed` tells: "`eligible = request.eligible_candidates()` # the only read of candidates". `_limit_author_runs` reads only `c.author`. |
| 2 | Interface calibration and concept fit | Y | a✓ b✗ c✓ | 7 | S1 | **(b)** The stage-1 `Decimal` rejection persists: "`True`, `"0.5"`, `None`, `Decimal("0.5")` → not a number" (§14.1). **(c)** holds: "Eligibility is a **filter** … It is not a score, a sentinel". "Diversity is a sequence constraint. … It is not a key, a penalty or a comparator." |
| 3 | Interface Segregation | Y | a✓ b✓ | 10 | — | The run limit receives "`Sequence[Candidate]` in rank order" and never scores; the public surface is unchanged. |
| 4 | Primitive obsession / illegal states | Y | a✓ b✓ c✓ d✓ | 10 | — | "`topics: frozenset[str]`" and "`blocked_authors: frozenset[str]`": "the representation states the rule itself, since repeats mean one entry and matching is membership". "Exactly one author is structural". |
| 5 | Anemic domain model | Y | a✓ b✓ c✓ | 10 | — | "validated in its own constructor". Eligibility is a behavior of the request that owns both lists ("only the request holds both"). |
| 6 | Cohesion, coupling, OCP | Y | a✓ b✓ c✓ d✗ | 8 | S1 | **(d)** The rule that the lists are required lives in the adapter on the data path: "Block and mute lists: required \| Library: the `FeedRequest` signature (no default). Data: the `cli` shape check". The design concedes this: "'lists present' is a product rule, so it belongs in the core. Not taken now". A second data adapter would have to re-implement it. **(c)** holds for the declared stage-2 axes: "A third rule adds one field and one clause to that one owner". |
| 7 | Leaky abstractions / error vocabulary | Y | a✓ b✓ c✓ | 10 | — | `FeedService` → caller "never crosses … authors, topics, anything about removed items". "Stage 2 adds no error type." "Absence is never an error." |
| 8 | Single Responsibility / god object | Y | a✓ b✓ c✓ | 10 | — | §9 table: each step has one owner, and `rank_feed` is "(the composition only)". |
| 9 | One unforgeable owner | Y | a✓ b✓ c✓ d✓ e✓ f✓ g✓ | 10 | — | (f) "`rank_feed` gets its candidates only from `request.eligible_candidates()` … so no path sits beneath the filter". It holds on paths L, C and D. (g) "`ranking._limit_author_runs` … read or change a score (by construction)" is listed as something it cannot do. Validity precedes eligibility structurally ("filtering a request that failed validation cannot be expressed"). The residual bypass risk (the public `candidates` field) is stated and guarded by a test, and it is not an open path. |
| 10 | DRY | Y | a✓ b✓ c✓ | 10 | — | "What an id is … one home: two private functions in `request.py`" (five fields). |
| 11 | Naming and failure | Y | a✓ b✓ c✓ | 10 | — | "`item 'b': topics must be a collection of ids, not a string`". The exit codes are unchanged and distinct. |
| 12 | YAGNI / subtractive | Y | a✓ b✓ c✓ | 10 | — | No new module, type or error. `_MAX_SAME_AUTHOR_RUN` is a private constant, and `key=` / `max_run=` knobs were cut. |
| 13 | Functional correctness | Y | a–f✓ g✓ h✓ i✓ j✓ k✓ | 10 | — | (g) "A blocked item with the top score is absent". (h) "`a1[A] a2[A] x[X, blocked] a3[A]` → `a1 a2`". (i) "`a1 a2 a3 b1 c1` → `a1 a2 b1 a3 c1`". (j) "All ineligible → `Feed(v, ())`". (k) "Every `RankedItem.score == weights.score(candidate)`". The worked CLI example checks out: the scores and `a1 a2 b1 a3 a4` are correct. |
| 14 | State and side effects | Y | a✓ b✓ c✓ d✓ | 10 | — | New fields are `frozenset`. "no lock or state is added". |
| 15–17 | | N/A | | | | |

**Profile X-stage-2:** grade = (12·10 + 7 + 8)/14 = **9.64**. worst = 7. (#S3, #S4) = (0, 0). Gate **CLEAR**.

### Y-stage-2 form

| § | Principle | Applies | Sub-checks | Score | Severity | Finding and citation |
|---|---|---|---|---|---|---|
| 1 | Tell-Don't-Ask / Law of Demeter | Y | a✓ b✗ c✓ | 7 | S1 | **(b)** The orchestrator reaches through the pair type: "`[RankedItem(s.candidate.item_id, s.score) for s in arrange(ordered, lambda s: s.candidate.author)]`". This is cosmetic. |
| 2 | Interface calibration and concept fit | Y | a✗ b✓ c✓ | 7 | S2 | **(a)** Unchanged from stage 1: `FeedService` still depends on the concrete `WeightsProvider(path)`. **(b)** holds: "`arrange(ordered: Sequence[T], author_of: Callable[[T], str])`" is well calibrated. **(c)** holds: D1 rejects "a score of −∞", and D3 rejects folding diversity "into the sort key". |
| 3 | Interface Segregation | Y | a✓ b✓ | 10 | — | `arrange` sees only order and a key ("It knows nothing about scores or weights"). |
| 4 | Primitive obsession / illegal states | Y | a✓ b✗ c✓ d✓ | 7 | S2 | **(b)** persists: "`class Candidate: item_id: str; author: str; topic: str; signals: Mapping[str, Decimal]`". **(d)** holds: "`Exclusions: blocked_authors: frozenset[str]; muted_topics: frozenset[str]`", and `Scored` is a named pair. |
| 5 | Anemic domain model | Y | a✗ b✓ c✓ | 7 | S2 | **(a)** persists: new invariants are also parser-owned ("request model: … **`Exclusions` validity**"). The dataclasses remain unvalidated. |
| 6 | Cohesion, coupling, OCP | Y | a✓ b✓ c✓ d✓ | 10 | — | New rules sit in their own modules. "When more policies arrive … they join the predicate and do not touch scoring." |
| 7 | Leaky abstractions / error vocabulary | Y | a✗ b✓ c✓ | 7 | S2 | **(a)** persists: `FeedService.rank(raw)` still takes a raw `Mapping`. |
| 8 | Single Responsibility / god object | Y | a✗ b✓ c✓ | 7 | S1 | **(a)** persists (`WeightsProvider` unchanged). The new modules are single-purpose. |
| 9 | One unforgeable owner | Y | a–e✓ f✓ g✓ | 10 | — | (f) "The eligibility predicate is owned by one pure function". (g) "`diversity` … The run limit (`MAX_SAME_AUTHOR_RUN = 2`), the placement rule … the surplus-omission policy". Both are enforced on the single public path `FeedService.rank`. (The internal `rank` could be called on an unfiltered list, but it is not an intended entry path.) |
| 10 | DRY | Y | a✓ b✗ c✓ | 7 | S1 | **(b)** The two number conversions persist (the stage-1 finding). |
| 11 | Naming and failure | Y | a✓ b✓ c✗ | 7 | S1 | **(c)** "Same command and exit codes … A request error … exits with 2": it still collides with argparse. |
| 12 | YAGNI / subtractive | Y | a✓ b✗ c✓ | 7 | S1 | **(b)** The env-var fallback persists (ranking-config is "unchanged"). The new parts each answer a force; `Scored` exists "so later stages can still see `author`". |
| 13 | Functional correctness | Y | a–e✓ f✗ g✓ h✓ i✓ j✓ k✓ | **2** | **S4** | (g), (h), (i) and (j) hold: "Blocked author excluded despite top score", "`a1, a2, m1, a3, b1` → `a1, a2, b1, a3`", "`a1, a2, a3, b1` → `a1, a2, b1, a3`", "All candidates excluded → empty". **(f)** The inexact ambient-context scoring is carried unchanged ("Unchanged: the weighted-sum formula, exact arithmetic"). See §3 (F1). |
| 14 | State and side effects | Y | a✗ b✓ c✓ d✓ | 8 | S1 | **(a)** A shallow freeze on the `Mapping` fields persists. "The pipeline stays a composition of pure functions". |
| 15–17 | | N/A | | | | |

**Profile Y-stage-2:** Σweight = 25. grade = 145/25 = **5.80**. worst = 2. (#S3, #S4) = (0, 1). Gate **BLOCKED**.

With the §13 defect fixed, the grade is 139/18 = 7.72 and the gate is CLEAR.

**D2 winner on the stage-2 form: X** (9.64 against 5.80, or 7.72 with the S4 fixed). The stage-2 additions are sound in both designs:
- **Y's** new modules are clean and well seamed.
- **X's** additions are equally well owned, and more of X's invariants are held by types.

The gap is the stage-1 structure Y carries forward: parser-owned invariants over `Mapping` bags, a raw-dict library seam, a concrete provider dependency, and inexact scoring.

**Summary of D2:** Y absorbed the change with slightly fewer reopens. X's stage-2 design is the better design.

---

## 3. Correctness traps (from spec-and-oracle.md)

| Trap | X | Y |
|---|---|---|
| **1. Blocked-as-weight cram** | **Avoided.** "Eligibility is a **filter**. Its one owner is the query `FeedRequest.eligible_candidates()`… Ineligible items are never scored, so no sentinel score can exist". The design rejects "Score an ineligible item `-inf`, or add a penalty term". | **Avoided.** "D1. Filter before scoring, as a separate pure stage … ineligible items never enter the ordering". The design rejects "(a) a score of −∞ or 0 for excluded items … they would still be present". |
| **2. Diversity-as-penalty cram** | **Avoided.** "`_limit_author_runs` … a private sequence constraint that never sees a score". The design rejects "A score penalty for repeated authors … doesn't guarantee the rule". | **Avoided.** "D3. Diversity is a post-order rearrangement over an opaque key". The design rejects "fold diversity into the sort key … no per-item key can express it". |
| **3. Pipeline ownership (filter → score/sort → diversify)** | **Avoided.** "Feed order = run limit ∘ rank order ∘ eligibility": three owners, and scoring is unchanged. X had to reopen `rank_feed` to open the sort-to-build seam (see D2), but the resulting pipeline is correct and every path goes through it. | **Avoided.** "`ordered = rank(w, filter_eligible(req.candidates, req.exclusions))` … `arrange(ordered, …)`": three owners in separate modules, and scoring is unchanged. |
| Oracle: "Is a muted item counted for diversity? → No" | Correct: "`a1[A] a2[A] x[X, blocked] a3[A]` → `a1 a2`" | Correct: "`a1, a2, m1, a3, b1` … → `a1, a2, b1, a3`" |

Neither design falls into any hidden-spec trap.

### Reported correctness failures, with reproducing inputs

**F1: Y (stage 1 and stage 2), §13(f), S4. Scores are not exact, although Y's spec requires it.**

Y specifies `score(w, c) = sum(w[s] * c[s] for s in SIGNALS)` and the sort key `(-score, item_id)` with no module-owned context. Both follow the host's ambient `decimal` context, and `parse_float=Decimal` accepts inputs of any length. The two cases below were run against those exact expressions (Python `decimal`).

- **Case A (library path, host changed the decimal context).**
  - Setup: the weights file is `{"weights": {"recency": 0.5, "affinity": 0.3, "popularity": 0.2}}`. The embedding host has run `decimal.getcontext().prec = 6`.
  - Call: `FeedService.rank({"user": "u", "candidates": [{"item_id": "a", "recency": 0.1234567, "affinity": 0.0, "popularity": 0.0}, {"item_id": "b", "recency": 0.1234568, "affinity": 0.0, "popularity": 0.0}]})`
  - **Y outputs** `[a (0.0617284), b (0.0617284)]`. The scores are falsely tied and broken by id, and a's shown score is wrong.
  - **Correct:** `[b (0.0617284), a (0.06172835)]`.
  - X on the same inputs gives the correct answer ("`Weights.score` calls `EXACT.multiply` and `EXACT.add` explicitly … a host that sets `getcontext().prec = 6` would otherwise round scores").
- **Case B (CLI path, default precision 28).**
  - Setup: weights `{"weights": {"recency": 1, "affinity": 0, "popularity": 0}}`.
  - Request candidates: `{"item_id":"a","recency":0.1,…0,0}` and `{"item_id":"b","recency":0.1000000000000000000000000000001,…0,0}`. Both are valid signals in [0, 1].
  - **Y outputs** `[a, b]`, with b's score rounded to `0.1000000000000000000000000000`.
  - **Correct under Y's own "computed exactly" contract:** `[b, a]`.
  - X reads b as its nearest double and also returns `[a, b]`. That is X's documented meaning of a number ("A number written with more than about 17 significant digits is read as its nearest double"), so for X this is a stated input domain, not a broken contract. Case A is the case that separates the designs.

The fix is local: one module-owned exact context plus `copy_negate`. Per measurement.md, it is reported as a gate and not a cap. Neither the D1 nor the D2 form verdict depends on it (see the profiles).

**No correctness failure found in X.** I traced X's C1–C8, the trap pair, and the stage-2 worked example: scores 0.83/0.73/0.65/0.55/0.53 and output `a1 a2 b1 a3 a4`. All are right.

### Different readings of an unspecified case (not scored as failures)

Neither the card nor the oracle decides what happens when the run limit cannot place every item. Both designs state their choice, and I simulated both rules.

- **Input `b1 a1 a2 a3`:** X gives `b1 a1 a2` (a3 omitted; score order kept). Y gives `a1 b1 a2 a3` (all kept; the top-ranked b1 is moved second).
- **Input `a1 b1 a2 a3 a4`:** X gives `a1 b1 a2 a3`. Y gives `a1 a2 b1 a3 a4`.

The card says only a would-be third item is "deferred" and that "the relative order of everything else is otherwise preserved". Read literally, that favors X's reading, while Y's lookahead maximizes completeness. The oracle ("The constraint is hard; within it, preserve score order as much as possible") does not settle which choice is right, so neither is scored.

---

## 4. Residual tells, and how I controlled for them

- **The method guess.** In GUESS.md I guessed X = aims, which shares the rubric's vocabulary. X uses that vocabulary heavily: "subtractive pass", "concept fit", "one owner", and "design-principles §13" by name. This is the capture risk measurement.md warns about. Controls:
  - I credited no row on wording. Every pass cites a structural fact: a constructor that is the only constructor, an injected `Callable`, `frozenset` fields, `EXACT.multiply`, or a funnel ("`rank_feed` gets its candidates only from…").
  - I scored X's recited "Kept"/"Cut" lists as nothing. §12 passes only because I found no unpaid element in the signatures.
  - I hunted X for the same classes of fault as Y, and two findings survived:
    - the `Decimal` input rejection (§2);
    - the "lists required" rule sitting in the CLI (§6), which X itself concedes.
- **Format and length.** Y's spec, proposal and tasks structure reads as process rather than architecture, and X is about 2.5× longer. I scored only the architecture content of each. Y's spec scenarios were used only where they pin behavior (for example, the diversity outputs).
  - Length cut both ways: X's greater detail exposed more surface to fault-finding, not less.
- **References to documents I cannot see.** X cites `goals.md` and `decisions/` records, which are unavailable to me. I credited no claim that rests only on them. Where a rule was attributed to goals.md (the version in the response, the "greedy" reading), I judged it by the stage cards and the oracle.
- **The S4 dominates Y's grade.** A single ×8 row moves Y by about 2 points. Following "a removable local blemish must not flip a verdict", I reported each Y grade with and without it. Every verdict (D1: X; D2 stage-2 form: X) holds either way.
- **Survival count granularity.** Counting is sensitive to how components are split. I counted per named type or function in both designs. I charged both designs the requirement-forced response-contract change symmetrically. I did not count Y's `parse_request` separately from its request model, mirroring X, whose validation lives inside `Candidate`/`FeedRequest`.
  - Y's narrow survival win (3 against 4) should be read as corroboration, as measurement.md directs, not as a lead signal.
- **My disposition.** Weighting invariant ownership heavily favors X's validating constructors over Y's parser-owned invariants. That preference is the disposition I was assigned, and it is visible in the §4 and §5 rows. A judge with a minimalist disposition might score Y's §4 and §5 findings as S1 rather than S2, which would narrow the gap but not reverse it.
