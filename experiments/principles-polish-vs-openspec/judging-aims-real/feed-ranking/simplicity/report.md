# Judge report — feed ranking, designs X and Y (YAGNI / simplicity disposition)

**Instrument:** `rubric/assessment-form.md` rows §1–§17, with each row's items taken from `rubric/design-principles.md`. Every score comes from binary sub-checks: `score = round(10·passed/applicable)`, then capped at the severity ceiling (S1→8, S2→7, S3→5, S4→2). Weights are ×1 for none/S1, ×2 for S2, ×4 for S3 and ×8 for S4. Rows marked N/A are left out of every profile, and the same rows are N/A for both designs.

**Disposition, and how it was applied.** I looked hardest for unpaid machinery. For each piece I asked what stated requirement or R/X/C item pays for it. Findings of that kind are scored under §12, as the rubric directs: the §7 tie-break says "a seam no X-item would ever use is over-build … at most S1". My disposition decided where I searched. It did not change the weights.

## Step 0 — fixed inventory (from `product/stage-1.md`, `product/stage-2.md` and the oracle; identical for both designs)

- **R1**: score = w_r·recency + w_a·affinity + w_p·popularity, using the configured weights.
- **R2**: order by score, highest first.
- **R3**: equal scores are ordered by a stable item id.
- **R4**: weights are per-deployment configuration, and an operator changes them without a code change.
- **R5**: signals are in [0, 1].
- **R6** (stage 2): an item from a blocked author, or on a muted topic, never appears, "regardless of how high its signals are".
- **R7** (stage 2): no more than 2 consecutive items share an author; the third is deferred to the next valid position, and the relative order of everything else is otherwise preserved.
- **R8** (stage 2): the stage-1 scoring and weights keep working unchanged.
- **X1**: the operator edits the weights. **X2** (the plausible unstated variant): a per-request rule on the feed that is not a weight, such as a filter or an ordering constraint.
- **C1**: the example weights 0.5/0.3/0.2 order a set correctly.
- **C2**: mathematically equal scores tie and are ordered by id, including the binary-float noise trap. Unequal scores are never merged.
- **C3**: empty candidates give an empty feed.
- **C4**: a weight edit takes effect with no code change; each request uses one weight set.
- **C5**: invalid signals or weights are rejected.
- **C6**: a blocked top-scoring item is absent.
- **C7**: `a1 a2 a3 b1` → `a1 a2 b1 a3`.
- **C8**: a muted item neither separates nor extends a run.
- **C9**: when every item is ineligible, the feed is empty.

**N/A for every design:**
- **§15 Testability**: code-leaning, so N/A for a design-only document (`design-principles.md`: "Code-leaning (N/A on a pure design document): §12 (testability)").
- **§16 Performance**: no requirement is stated (oracle: "no performance requirement is stated").
- **§17 Security**: no trust boundary; this is an in-process library.

---

## 1. D1 — first-round design (stage 1)

### X-stage-1

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 10 | — | The formula sits with the data it combines: `def score(self, candidate: "Candidate") -> Decimal: ... # THE formula`. `rank_feed` tells `Weights` to score and reaches through no object chains. |
| 2 | Interface calibration + concept fit | Y | 10 | — | The seams carry domain types (`caller → FeedService.rank` crosses `FeedRequest`, and "Never crosses: dicts, raw JSON"). The loader seam is the most generic type that is still complete: `WeightLoader = Callable[[], Weights]`. `Weights` is a value, and the version is derived from it. |
| 3 | Interface segregation | Y | 10 | — | `FeedService` has two methods, `rank` and `reload`, and each client uses what it depends on. |
| 4 | Primitive obsession | Y | 10 | — | Signals are named `Decimal` fields on `Candidate` and `Weights`. The id rule is owned by `Candidate.__init__` ("id non-empty str"). The published results are `RankedItem` and `Feed`. |
| 5 | Anemic model | Y | 10 | — | `Weights` validates and scores, `Candidate` validates its own signals, and `FeedRequest` owns "no duplicate item_id". |
| 6 | Cohesion / coupling / OCP | Y | 10 | — | "Imports are acyclic and point toward `numbers` and `signals`". X1 is absorbed with "Edit the file and reload; no code". Producing a score (`Weights.score`) and producing the order (`rank_feed`) are separate owners, so X2 has a seam. |
| 7 | Leaky abstractions / errors | Y | 10 | — | `load_weights_file translates OSError, UnicodeDecodeError and TOMLDecodeError into WeightConfigError`. There is "one per distinct handling", and internal `ValueError` is "translate[d] once". |
| 8 | SRP / god object | Y | 10 | — | Each module has one reason to change. `FeedService` "holds the only mutable state". |
| 9 | One owner per rule | Y | 10 | — | The §9 table gives exactly one owner per rule, and all paths go through it ("Only valid weights exist. Owner: `Weights.__init__`. There is no other constructor"). |
| 10 | DRY | Y | 10 | — | The signal set lives only in `SIGNAL_NAMES`, used by both `Weights` and `Candidate`. Number meaning lives only in `exact_number`, and number printing only in `canonical_text`. |
| 11 | Naming & failure | Y | 10 | — | Errors name the item and signal (`item 'b': signal 'affinity' is outside [0, 1] (1.2)`), and names reveal intent. |
| 12 | Size / YAGNI | Y | **6** | S1 | Sub-checks: (a) every type owns a rule ✔; (b) no seam without an X-item ✔ (the `WeightLoader` alias is one line, used by the in-memory loaders the reload tests need); (c) nothing beyond stated needs ✘; (d) no format generality for unstated futures ✔; (e) edge machinery proportional ✘ → 3/5. **(c):** the response gains a derived version id that no card asks for: `version … "w-" + sha256(canonical text)[:16]`, stamped into `Feed.weights_version`. That value is the only reason `Feed` exists as a wrapper type. **(e):** "Every outcome has its own code": five exit codes, including a separate `5 \| Request unreadable`. Both can be removed locally → S1. |
| 13 | Functional correctness | Y | 10 | — | C1: "scenario scores `0.58` and `0.55` exactly". C2: "Weights.score calls EXACT.multiply and EXACT.add explicitly … sort key is `(score.copy_negate(), item_id)`", so no false ties or splits. C3: "`Feed(v, ())`". C4: "one snapshot read per request; swap only after a full load". C5: constructors reject bad values. The hidden-case interactions I traced (for example, a host setting `getcontext().prec = 6`) hold. |
| 14 | State & side effects | Y | 10 | — | The values are `frozen=True`. There is a single reference store, and `rank` takes no lock. "The reload lock exists for one reason: two overlapping reloads could otherwise finish out of order". |
| 15–17 | — | N/A | — | — | see Step 0 |

**Profile X-stage-1:** grade = (13×10 + 6)/14 = **9.71**, worst = **6**, (#S3,#S4) = **(0,0)**, gate **CLEAR**.

### Y-stage-1

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 10 | — | There are no object chains; `FeedService` "calls `weights.snapshot()` once". The pull-and-decide style is scored once, under §5. |
| 2 | Interface calibration + concept fit | Y | 10 | — | `FeedService(weights: WeightsProvider)` depends on one collaborator, and the tests use a "provider stub". The concepts fit (weights are a value; `WeightsProvider` owns the lifecycle). |
| 3 | Interface segregation | Y | 10 | — | `WeightsProvider` has `snapshot`/`reload`; `FeedService` has `rank`. |
| 4 | Primitive obsession | Y | **5** | S2 | Sub-checks: (a) domain concepts are typed ✔; (b) the fixed signal set is structural ✘; (c) the public library seam is typed ✘; (d) the id rule is owned ✔ → 2/4. **(b):** `class Candidate: item_id: str; signals: Mapping[str, Decimal]` and `class Weights: values: Mapping[str, Decimal]`. These are string-keyed bags for a fixed set of three, and the type allows any keys. **(c):** the public library API is `def rank(self, raw_request: Mapping) -> list[RankedItem]`, so a library caller must hand over an untyped dict. Both clumps are local → S2. |
| 5 | Anemic model | Y | **5** | S2 | Sub-checks: (a) value types enforce their own invariants ✘; (b) behavior sits with its data ✘; (c) `WeightsProvider` owns its lifecycle ✔; (d) `FeedService` only orchestrates ✔ → 2/4. **(a):** "Raw input becomes a `RankRequest` or `Weights` only through `parse_request` or `parse_weights`", while `Candidate`/`Weights` are plain frozen dataclasses that anyone can build unvalidated. **(b):** the formula is a free function over two bags, `score(w, c) = sum(w[s] * c[s] for s in SIGNALS)`. The rules are still in one place (the parsers), so → S2, not S3. |
| 6 | Cohesion / coupling / OCP | Y | 10 | — | "The core never touches files, and the file loader never scores anything". `score` and `rank` are separate functions, which gives X2 a seam. |
| 7 | Leaky abstractions / errors | Y | 10 | — | `parse_weights … # raises ConfigError`, `parse_request … # raises ValidationError`. An unreadable file is reported as a config error ("fail fast when the path is missing, invalid or unreadable"). |
| 8 | SRP | Y | 10 | — | The components table gives one rule set per component. |
| 9 | One owner per rule | Y | 10 | — | "Each rule has exactly one owner". The one public path, `FeedService.rank(raw)`, always goes through `parse_request`, so the parser's ownership holds by intent. |
| 10 | DRY | Y | 10 | — | "Both `Candidate` and `Weights` validate against the same `SIGNALS` tuple." |
| 11 | Naming & failure | Y | 10 | — | "each error names the offending item and field or key". |
| 12 | Size / YAGNI | Y | **6** | S1 | Same five sub-checks as X → 3/5. **(c):** an unrequested second config source: "An environment variable such as `FEED_RANKING_CONFIG` can supply the path as a fallback". It also contradicts the signature `WeightsProvider.__init__(self, path: Path)`. **(d):** speculative format room: `{"weights": {...}}` because "The top-level object leaves room for later keys without a format break". Both are local → S1. |
| 13 | Functional correctness | Y | **2** | **S4** | Sub-checks: C1 ✔, C2 (float-noise trap) ✔, C3 ✔, C4 ✔, C5 ✔, C2 (unequal scores never merged) ✘ → 5/6 = 8, capped at 2. D2 says "Exact arithmetic with `decimal.Decimal`", and the spec says "Scores SHALL be computed exactly", but the design never sets a context. `json.loads(..., parse_float=Decimal)` plus `sum(w[s] * c[s] …)` and the key `(-score, item_id)` therefore run in the default 28-digit context, which rounds. **Reproduction (checked in Python):** weights file `{"weights": {"recency": 1, "affinity": 1e-17, "popularity": 0}}`; candidates `{"item_id":"b","recency":0.5,"affinity":0.00000000000001,"popularity":0}` and `{"item_id":"a","recency":0.5,"affinity":0,"popularity":0}`. Every input is valid, in range and exactly representable as a double. **Design output:** `[a, b]`, because b's score 0.5 + 1e-31 is rounded to `0.5000000000000000000000000000`, a false tie, broken by id. **Correct output:** `[b, a]` (0.5000000000000000000000000000001 > 0.5). This fails R2. It is a one-line fix (a local high-precision context plus `copy_negate`), but §1 items are preconditions, so the gate is BLOCKED. |
| 14 | State & side effects | Y | **8** | S1 | Sub-checks: (a) immutable values ✘; (b) atomic single-reference swap ✔; (c) reloaders serialized ✔; (d) functional core ✔ → 3/4. **(a):** "`Weights` is frozen", but its field is `values: Mapping[str, Decimal]`, and nothing makes the mapping read-only. A `snapshot().values[...] = …` would mutate the shared live weights, and the no-mixing argument relies on immutability. It is local → S1. |
| 15–17 | — | N/A | — | — | see Step 0 |

**Profile Y-stage-1:** grade = (9×10 + 5×2 + 5×2 + 6 + 2×8 + 8)/23 = 140/23 = **6.09**, worst = **2**, (#S3,#S4) = **(0,1)**, gate **BLOCKED** (§13).

**Robustness check.** If the §13 defect is treated as a removable local blemish and set to 10, Y-stage-1 = 134/16 = **8.38**. That is still below X.

**D1 winner: X.** The verdict does not depend on the S4. On YAGNI the two designs tie: §12 is 6 vs 6, each with two S1 over-builds. X's unrequested version hash and exit-code taxonomy weigh about the same as Y's env-var fallback and "room for later keys". X's extra length is spent on specifying rules (exact context, owner table), not on extra types or layers. Y loses on string-keyed bags at the public seam and on rules held outside the values (§4, §5), and separately on an exactness hole.

---

## 2. D2 — change absorption

"Reopened" means the element's responsibility or boundary changed. "Discarded" means it is gone.

### X: stage-1 → stage-2

| Element | Class | Evidence |
|---|---|---|
| `numbers` (`exact_number`, `canonical_text`, `EXACT`) | survived | "[core foundation, unchanged]" |
| `signals` (`SIGNAL_NAMES`, `read_signal_fields`) | survived | "[core foundation, unchanged]"; the existing `leading` parameter now carries `("id","author","topics")` |
| `Weights` / `Weights.score` / `version` | survived | "weights.py — UNCHANGED"; "reads only the three signals" |
| `WeightConfigError`, `config_file` | survived | "UNCHANGED" |
| `FeedService`, `WeightLoader` | survived | "service.py — UNCHANGED" |
| `InvalidRequest` | survived | "unchanged type and attributes; new messages only" |
| `RankedItem` | survived | fields unchanged |
| `Candidate` | extended | "gains `author` and `topics`. They are validated in its constructor like every other item field"; the item-id check moves behind `_require_id`, described as a "Behavior-preserving move" |
| `FeedRequest` | extended | "gains `blocked_authors` and `muted_topics` … also gains the query `eligible_candidates()`". Its stage-1 duties (validity, duplicate ids) are unchanged |
| `cli` | extended | "CHANGED: request shape"; the shape check adds list presence |
| seam caller → `FeedService.rank` | extended | still `FeedRequest`, now "(with both lists; items with author and topics)" |
| seams loader → service, service → `rank_feed`, config_file → core | survived | unchanged rows in §4 |
| **`rank_feed`** | **reopened** | "Restructure `rank_feed` so it scores each candidate once into a local map keyed by `item_id`, sorts the candidates (not `RankedItem`s) … That opens the seam"; "The only stage-1 rule stage 2 rewrites is the order rule" |
| **`Feed.items` contract** (published output) | **reopened** | "the Feed.items contract is restated … NOT strictly score-descending … items that cannot be placed are omitted" |

**X reopened + discarded = 2** (`rank_feed`; `Feed.items` contract). Nothing was discarded. The new elements are `_limit_author_runs`, `_MAX_SAME_AUTHOR_RUN`, `_require_id` and `_require_id_set`, all private.

### Y: stage-1 → stage-2

| Element | Class | Evidence |
|---|---|---|
| `signals` / `SIGNALS` | survived | unchanged |
| `Weights`, `parse_weights`, `WeightsProvider` | survived | "`ranking-config` is not affected"; the diagram marks WeightsProvider "(unchanged)" |
| `score(w, c)` | survived | "Scoring and the score-order sort stay byte-for-byte the stage-1 rules" |
| `Candidate` | extended | "`Candidate(+author, +topic)`" |
| `RankRequest`, `parse_request` | extended | "`RankRequest(+exclusions: Exclusions)`"; validation covers the new fields |
| `FeedService` | extended | still orchestration; "Composition order: parse, then filter, then rank, then arrange, then project to `RankedItem`" |
| `RankedItem` | survived | "the response entry shape (`item_id`, `score`)" unchanged |
| CLI | extended | "The input JSON gains `author` and `topic` … Same command and exit codes" |
| seam `FeedService` → `WeightsProvider.snapshot()` | survived | "one weights snapshot per request, as before" |
| **`rank(w, cs)`** and its seam to `FeedService` | **reopened** | "The only change is that it returns `Scored(candidate, score)`"; task 3.1: "verify all stage-1 ranking tests still pass after adapting them to the new return type". The signature changes from `-> list[RankedItem]` to `-> list[Scored]` |
| **output contract** | **reopened** | "Completeness weakens from 'every candidate' to 'eligible candidates, minus the unavoidable same-author surplus'" |

**Y reopened + discarded = 2** (`rank`'s return boundary; the output contract). Nothing was discarded. The new elements are the `eligibility` module, the `diversity` module, `Exclusions` and `Scored`.

**Survival verdict: no clear advantage (2 vs 2).** The output-contract reopen is forced by the card in both designs. The reopens that remain differ in kind:
- **Y** widens a return type, and scoring and sorting are untouched.
- **X** restructures the body of the order owner. Its public signature is unchanged, and `Weights.score` is untouched.

Under the oracle's rule ("reopens if the scoring component has to change"), neither design's scoring component reopens. This is weak corroboration only.

### X-stage-2 form

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 10 | — | The request answers its own question: `request.eligible_candidates()`. `rank_feed` "never evaluates eligibility itself". |
| 2 | Interface calibration + concept fit | Y | 10 | — | "Eligibility is a **filter**"; "Diversity is a sequence constraint … not a key, a penalty or a comparator". The run limit gets `Candidate`s, which carry no score. It is a private function inside one module, so a generic `T` is not needed ("a module plus a callable parameter for one caller is a seam nobody crosses"). |
| 3 | Interface segregation | Y | 10 | — | The public surface is still "the same ten names as in stage 1". |
| 4 | Primitive obsession | Y | 10 | — | author, topics and the lists are `str`/`frozenset[str]`, and their one rule is owned once by `_require_id`/`_require_id_set`. "`AuthorId` / `TopicId` … No rule beyond 'non-empty str'". |
| 5 | Anemic model | Y | 10 | — | `FeedRequest` owns eligibility over its own data. `Candidate` validates its new fields. |
| 6 | Cohesion / coupling / OCP | Y | 10 | — | "Changing the formula or the tie-break touches `Weights.score` or the sort key only; the run limit is untouched". A further eligibility rule "adds one field and one clause to that one owner". |
| 7 | Leaky abstractions / errors | Y | 10 | — | "Stage 2 adds no error type"; "Absence is never an error". |
| 8 | SRP | Y | 10 | — | `rank_feed` handles "the composition only"; each step has its own owner (§9 table). |
| 9 | One owner per rule | Y | 10 | — | The only read of candidates is `eligible = request.eligible_candidates()`, and the rule is "rank_feed's only source of candidates" on paths L, C and D. The run limit's single owner is `ranking._limit_author_runs`. |
| 10 | DRY | Y | 10 | — | There is one meaning of "id" across five fields, and "2" is named once as `_MAX_SAME_AUTHOR_RUN`. |
| 11 | Naming & failure | Y | 10 | — | The names say what they do (`eligible_candidates`, `_limit_author_runs`), and messages name the field and index. |
| 12 | Size / YAGNI | Y | **4** | S1 | Sub-checks: (a) every element owns a rule ✔ (no new module or type); (b) no seam without an X-item ✔; (c) nothing beyond stated needs ✘ (carried: the `weights_version` hash); (d) no data-model generality beyond the cards ✘; (e) edge machinery proportional ✘ → 2/5. **(d):** the cards give each item a topic ("on a muted topic"), yet X models `topics: frozenset[str] # zero or more topic ids`, which needs set validation. It cites goals.md, which I cannot see. **(e):** the input-refusal machinery has grown: "`str` / `bytes` / `bytearray` → … Mapping, or not iterable → …", "a generator [is] accepted", "Which entry is named can vary for a `set`", plus a 13-row message catalog and the carried five exit codes. Each can be removed locally → S1. |
| 13 | Functional correctness | Y | 10 | — | C6: "A blocked item with the **top** score is absent". C7: the traced example `a1 a2 a3 b1 c1 → a1 a2 b1 a3 c1`. C8: "`a1[A] a2[A] x[X, blocked] a3[A]` → `a1 a2`". C9: "All ineligible → `Feed(v, ())`". R8: "`Weights.score` reads only the three signals". I ran the illustrative `_limit_author_runs` over all 29,523 sequences of up to 9 items from 3 authors and found no run of 3. Stage-1 exactness is unchanged. |
| 14 | State & side effects | Y | 10 | — | No state is added ("no lock or state is added"). `topics` and the lists are frozensets. |
| 15–17 | — | N/A | — | — | |

**Profile X-stage-2:** grade = (13×10 + 4)/14 = **9.57**, worst = **4**, (#S3,#S4) = **(0,0)**, gate **CLEAR**.

### Y-stage-2 form

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 10 | — | No chains. The free-function style is scored once, under §5. |
| 2 | Interface calibration + concept fit | Y | 10 | — | "Filter before scoring, as a separate pure stage"; "Diversity is a post-order rearrangement". It rejects "a score of −∞ or 0 for excluded items". |
| 3 | Interface segregation | Y | 10 | — | `is_eligible`/`filter_eligible` and `arrange` are narrow functions. |
| 4 | Primitive obsession | Y | **5** | S2 | Carried from stage 1 and not re-deducted elsewhere: `signals: Mapping[str, Decimal]` and `FeedService.rank(raw)` over an untyped `Mapping`. `Exclusions` and `Scored` are typed ✔, and the id rules are owned ✔ → 2/4. |
| 5 | Anemic model | Y | **5** | S2 | Carried: the value types are unvalidated bags, and the rules live in free functions. The new predicate follows the same pattern: `def is_eligible(c: Candidate, ex: Exclusions) -> bool` pulls fields out of two bags → 2/4. |
| 6 | Cohesion / coupling / OCP | Y | 10 | — | "Two new pure pipeline stages … sit around the unchanged scoring core"; "When more policies arrive … they join the predicate and do not touch scoring". |
| 7 | Leaky abstractions / errors | Y | 10 | — | New-field errors go through the existing validation error: "A request error (including new-field errors) exits with 2". |
| 8 | SRP | Y | 10 | — | `FeedService` does composition only; each stage owns one rule. |
| 9 | One owner per rule | Y | 10 | — | "The eligibility predicate is owned by one pure function, and the run limit with its surplus policy by another." |
| 10 | DRY | Y | **7** | S1 | Sub-checks: signal set ✔, validation single pass ✔, run limit held once ✘ → 2/3. `MAX_SAME_AUTHOR_RUN = 2` is named, but the rule's feasibility check and trim restate the 2 as a literal: `count_R(X) <= 2 * (|R| - count_R(X)) + 2 - …` and "at most `2 × (k + 1)`". If the constant changes, the formulas do not. It is local → S1. |
| 11 | Naming & failure | Y | 10 | — | `arrange`, `Scored` and `Exclusions` are clear, and errors name the field and position. |
| 12 | Size / YAGNI | Y | **2** | S1 | Same five sub-checks → 1/5. **(a):** `Exclusions` owns no rule: its validity is enforced in `parse_request`, and deleting it (`is_eligible(c, blocked, muted)`) harms no ownership. **(b):** `arrange(ordered: Sequence[T], author_of: Callable[[T], str])` is generic over `T` plus a key callable for one caller, although "diversity on any key other than author" is a declared non-goal, so no X-item uses it. **(c):** a completeness-maximizing policy the cards do not ask for: the "feasibility lookahead" counting predicate, the pre-trim of the "minimal surplus", and a brute-force verification task. The card's rule is "deferred to the next available position". Also carried: the env-var fallback. **(d):** carried: `{"weights": …}` "room for later keys". (e) ✔. Every item is removable → S1. |
| 13 | Functional correctness | Y | **2** | **S4** | Stage-2 cases all pass: C6 "`x` does not appear", C7 "`a1, a2, a3, b1` → `a1, a2, b1, a3`", C8 "`a1, a2, m1, a3, b1` → `a1, a2, b1, a3`", C9 "empty ordered feed", R8 "`ranking-config` is not affected". I ran Y's feasibility rule plus trim over all 29,523 sequences of up to 9 items from 3 authors: no run of 3, and never more than the minimal drop. **Fail, carried unchanged:** the stage-1 default-context rounding, since "Unchanged: … exact arithmetic". Same reproduction as §13 of Y-stage-1, now with `"author"`/`"topic"` added to each candidate (for example author `"p"`/`"q"`, topic `"t"`, empty lists). Design output `[a, b]`; correct `[b, a]`. → 7/8 = 9, capped at 2. |
| 14 | State & side effects | Y | **8** | S1 | Carried: `Weights.values: Mapping` is not guaranteed read-only. `Exclusions` uses `frozenset` ✔. |
| 15–17 | — | N/A | — | — | |

**Profile Y-stage-2:** grade = (8×10 + 5×2 + 5×2 + 7 + 2 + 2×8 + 8)/23 = 133/23 = **5.78**, worst = **2**, (#S3,#S4) = **(0,1)**, gate **BLOCKED** (§13, carried from stage 1).

**Robustness check.** With the one-line §13 fix, Y-stage-2 = 127/16 = **7.94**, still below X-stage-2 at 9.57.

**D2 winners:**
- **Survival: no clear advantage** (2 vs 2 reopened + discarded).
- **Stage-2 form: X.** X absorbed stage 2 with no new module, type, error type or public name. Y added four elements, and two of them (`Exclusions` and the generic `T`/`author_of` parameters) fail the subtractive test. Y also added a lookahead/trim policy that the card does not ask for.
- **Where X loses points:** mainly on edge machinery (input-type refusals, the error catalog, exit codes) and on the multi-topic model.

---

## 3. Correctness traps (`product/spec-and-oracle.md`)

| Trap | X | Y |
|---|---|---|
| **1. Blocked-as-weight cram** | **Avoided.** "Eligibility is a **filter**. Its one owner is the query `FeedRequest.eligible_candidates()` … before scoring by construction"; it rejects "Score an ineligible item `-inf`, or add a penalty term — Concept cram". | **Avoided.** "Filter before scoring, as a separate pure stage … ineligible items never enter the ordering"; it rejects "a score of −∞ or 0 for excluded items … they would still be present". |
| **2. Diversity-as-penalty cram** | **Avoided.** "`_limit_author_runs` … a private sequence constraint that never sees a score"; it rejects "A score penalty for repeated authors … doesn't guarantee the rule". | **Avoided.** "Diversity is a post-order rearrangement over an opaque key"; it rejects "fold diversity into the sort key … no per-item key can express it". |
| **3. Pipeline ownership (filter → score/sort → diversify, three owners)** | **Avoided.** "Feed order = run limit ∘ rank order ∘ eligibility — `rank_feed` (the composition only)", with each step owned once. The stage-1 `rank_feed` needed an internal restructure to open the sort → build seam (D2). | **Avoided.** "`ordered = rank(w, filter_eligible(req.candidates, req.exclusions))` … `arrange(ordered, …)`", with the three owners in separate modules. The stage-1 `rank` had to change its return type (D2). |

**Other correctness findings (every failure has a reproducing input):**

1. **Y, stage 1 and stage 2 (§13, S4): unequal scores are merged by default-context rounding.**
   - **Inputs:** weights `recency=1, affinity=1e-17, popularity=0`. Candidate `b`: `recency=0.5, affinity=1e-14, popularity=0`. Candidate `a`: `recency=0.5, affinity=0, popularity=0`.
   - **Y as written:** b's score becomes `0.5000000000000000000000000000`, a false tie ordered by id, so the output is **`[a, b]`**.
   - **Correct:** **`[b, a]`**.
   - **X on the same input:** `[b, a]`. X uses `EXACT` with traps and `copy_negate`, and all six inputs are shortest-repr doubles, so X's canonicalization changes nothing.
   - I checked this with Python's `decimal` and `json` modules.

2. **Not a failure, but a divergence to report.** When the plain "defer the third" rule leaves items with nowhere to go, the two designs read the card differently. Both keep the hard limit (checked exhaustively, as above).
   - **X keeps score order and drops the tail:** `b1 a1 a2 a3` → `b1 a1 a2`, and `a1 b1 a2 a3 a4` → `a1 b1 a2 a3`. X states this as a PO-sanctioned assumption: "The greedy reading keeps score order ahead of feed length".
   - **Y keeps the most items and may move a non-third item:** `a1 b1 a2 a3 a4` → `a1 a2 b1 a3 a4`.
   - The card only says "deferred to the next available position … preserved as much as possible", and the oracle says "within it, preserve score order". Both readings fit.
   - X drops more items than the minimum on 3,474 of the 29,523 sequences I enumerated. Given its stated assumption, this is not counted against it.

X has no correctness failure that I could reproduce. Its one arguable number semantic is that 18+-digit inputs are read as their nearest double, but that is stated explicitly as an assumption ("A number means the nearest IEEE-754 double"), so it is not a defect.

---

## 4. Residual tells, and how I controlled for them

- **My method guess.** In GUESS.md I put X = aims and Y = OpenSpec at 97%. The rubric is aims' own, and X uses its vocabulary heavily: "subtractive pass", "concept fit", "Owner (exactly one)", and even "design-principles §13 is conditional". That last one suggests X was built against this very rubric. **Control:** I gave no credit for self-description. Every pass cites a structural element (a signature, an owner, a sort key, an import direction). X's own "Cut / Kept" lists were never read as evidence. I checked each item against my own subtractive question.
- **Documentation style and length.** X's stage-2 file is about 2.5× Y's, and Y is in OpenSpec's proposal/spec/tasks format. **Control:** Y's spec scenarios and tasks were read only as statements of behavior. Length earned nothing, and X's length was checked for over-build instead (§12 = 6 and 4). Y's terse "illustrative signatures" were read literally. That is where the §4, §5 and §14 findings come from (`Mapping` fields, an unset `Decimal` context). I did not fill those gaps charitably, but I also did not invent defects the text does not state. I withdrew a suspected exit-code clash for Y's CLI because the design never names `argparse`.
- **Invisible PO material.** X cites `goals.md` for several choices (the version id, multi-topic items, required lists, greedy omission). Y cites "product owner Q1". Neither document was provided. **Control:** each such choice was treated as a stated assumption. Where it adds unrequested structure (the version hash, multi-topic sets) I still scored it as an S1 over-build under §12. I did not penalize either design's interpretation of the unspecified infeasible-tail case.
- **The rubric's tilt against my disposition.** The rubric favors rich domain objects (§4/§5, "the graver risk is too little structure"). My YAGNI disposition would, on its own, rate Y's "frozen dataclasses plus pure functions" as the leaner style. **Control:** I scored §4/§5 as the rubric defines them, capped at S2 because the rules still have single owners. I also report that the D1 and D2 verdicts hold even if the §13 S4 is removed (8.38 and 7.94 vs 9.71 and 9.57). On §12 alone, the dimension my disposition weights most, the designs tie at stage 1 (6 vs 6) and X is leaner at stage 2 (4 vs 2).
- **The S4 gate.** Y's BLOCKED comes from one missing line (a local exact context). It is reported beside the grade and does not decide either winner.
