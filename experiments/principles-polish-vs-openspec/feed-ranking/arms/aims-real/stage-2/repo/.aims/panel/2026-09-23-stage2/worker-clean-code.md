# Feed ranking: stage 2 architecture (eligibility and diversity)

Axis: **clean code**. This means the fewest moving parts, no smells and no new dependencies. Design only.
This document is the complete stage-2 architecture. A section marked *unchanged* holds as written in
[`DESIGN.md`](../../../DESIGN.md), and this document does not repeat it. Every changed section is given
here in full.

**The change in one paragraph.** `Candidate` gains `author` and `topics`. `FeedRequest` gains
`blocked_authors` and `muted_topics`, and the new query `eligible_candidates()`, which owns eligibility.
`rank_feed` stays the single owner of the feed order. It ranks exactly as in stage 1, but only the eligible
candidates, and then passes that ranked sequence through one private function,
`_limit_author_runs`, which owns diversity. No module, public type, error type or dependency is added.
`numbers`, `signals`, `weights`, `service` and `config_file` are untouched.

---

## 1. Shape (changed: two core modules gain one concept each)

The pure core and the thin shell are unchanged. `FeedService` is still the only mutable state.

```
feed_ranking/
  __init__.py      public re-exports; no logic                                          (unchanged list)
  __main__.py                                                                          (unchanged)
  numbers.py       Number, exact_number(), canonical_text(), EXACT                     (unchanged)
  signals.py       SIGNAL_NAMES, read_signal_fields()                                  (unchanged)
  weights.py       Weights, WeightConfigError                                          (unchanged)
  request.py       Candidate(+author, +topics), FeedRequest(+lists, +eligible_candidates()),
                   InvalidRequest, IdCollection                                        CHANGED  -> numbers, signals
  ranking.py       RankedItem, Feed, rank_feed(), _limit_author_runs()                 CHANGED  -> weights, request
  service.py       FeedService, WeightLoader                                           (unchanged)
  config_file.py   load_weights_file()                                                 (unchanged)
  cli.py           main()                                                              CHANGED (request shape)
```

- The import graph is unchanged and acyclic. The standard-library set is unchanged, with **no new
  import**: `frozenset`, `Mapping` and `Iterable` are already in use, and no `collections.deque`,
  `itertools` or anything else is needed.
- Each new rule lands next to the data it reads. Eligibility compares the request's lists with each
  candidate's metadata, so it goes on the request, which holds both. Diversity rearranges an order, so it
  goes with the owner of the order.

## 2. Change axes (changed rows only; the stage-1 rows stand)

| Axis | Absorbed by | Cost |
|---|---|---|
| Per-request block/mute lists (new) | Fields on `FeedRequest`; the predicate in `FeedRequest.eligible_candidates` | Stored lists (a non-goal) would be one more producer of the same two fields. Core untouched |
| *Not an axis:* diversity key (topic, …), run limit ≠ 2, configurable limit | One named constant `_MAX_SAME_AUTHOR_RUN = 2` and `Candidate.author` read in one function | A different key or limit reopens `_limit_author_runs` only. Accepted, since the PO fixed both |
| *Not an axis:* a rule/filter engine | Two concrete rules, each in its one owner | A third rule is a design change, not a plug-in. Accepted (non-goal) |

## 3. Public surface (changed parts complete; the rest as in DESIGN.md §3)

```python
# request.py
IdCollection: TypeAlias = list[str] | tuple[str, ...] | set[str] | frozenset[str]
    # what a caller may hand in for topics or a list. The accepted kinds are a closed list, so a bare
    # str ("sports"), a dict or None is rejected, never iterated character- or key-wise.

class InvalidRequest(Exception):          # unchanged type and attributes
    problem: str
    item_id: str | None
    signal: str | None                    # still only set for a signal problem

@dataclass(frozen=True, slots=True, init=False)
class Candidate:
    item_id: str
    author: str                           # NEW: exactly one, non-empty
    topics: frozenset[str]                # NEW: zero or more, each non-empty; repeats collapse
    recency: Decimal
    affinity: Decimal
    popularity: Decimal
    def __init__(self, item_id: str, *, author: str, topics: IdCollection,
                 recency: Number, affinity: Number, popularity: Number) -> None: ...
        # first problem, in this order: id, author, topics, then signals in SIGNAL_NAMES order
    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> "Candidate": ...
        # keys exactly {"id", "author", "topics", *SIGNAL_NAMES}:
        # read_signal_fields(raw, leading=("id", "author", "topics")). The existing parameter; signals.py unchanged

@dataclass(frozen=True, slots=True, init=False)
class FeedRequest:
    user: str
    candidates: tuple[Candidate, ...]     # every candidate as given, eligible or not (validity first)
    blocked_authors: frozenset[str]       # NEW
    muted_topics: frozenset[str]          # NEW
    def __init__(self, user: str, candidates: Iterable[Candidate], *,
                 blocked_authors: IdCollection, muted_topics: IdCollection) -> None: ...
        # first problem, in this order: user, blocked_authors, muted_topics, duplicate item_id
    def eligible_candidates(self) -> tuple[Candidate, ...]: ...
        # NEW. The one owner of eligibility: candidates in input order whose author is not blocked
        # and whose topics are disjoint from the muted set

# ranking.py
@dataclass(frozen=True, slots=True)
class RankedItem:                         # unchanged
    item_id: str
    score: Decimal                        # the stage-1 score, untouched by eligibility or diversity

@dataclass(frozen=True, slots=True)
class Feed:                               # unchanged fields; the items contract is restated:
    weights_version: str
    items: tuple[RankedItem, ...]         # eligible items only, in rank order rearranged so that no
                                          # author appears 3 times in a row; () when nothing is eligible

def rank_feed(weights: Weights, request: FeedRequest) -> Feed: ...   # signature unchanged
_MAX_SAME_AUTHOR_RUN: Final = 2
def _limit_author_runs(ranked: Sequence[Candidate]) -> list[Candidate]: ...   # private
```

The `__init__` re-export list is unchanged. `IdCollection` is not re-exported. It is an annotation, and
callers pass a list.

**Construction contract.** The stage-1 contract is extended, not changed. `author`, `topics`,
`blocked_authors` and `muted_topics` are keyword-only and required. Omitting one in code is a
`TypeError`: arity is Python's rule. This matters here. A library caller who forgets the lists fails at
the call site and never silently shows blocked content, which is the reason the PO gave for "required"
(goals.md Q1). Every *value* is data, and a bad value is an `InvalidRequest`.

Typical embedding:

```python
feed = service.rank(FeedRequest(
    "u1",
    [Candidate("a", author="A", topics=["cats"], recency=0.9, affinity=0.1, popularity=0.5)],
    blocked_authors=[], muted_topics=["politics"]))
```

### 3.1 What "an id" means: one private owner inside `request.py`

Five values are now "an id": item id, author, each topic, each blocked author and each muted topic. They
share one meaning, a non-empty `str` compared exactly. That is real knowledge, not coincidental
duplication, so it has one home:

```python
def _require_id(value: object, what: str) -> str: ...
    # ValueError f"{what} must be a non-empty string (got {value!r})"
def _require_id_set(value: object, what: str, each: str) -> frozenset[str]: ...
    # not an IdCollection kind -> ValueError f"{what} must be a list of {each}s (got {value!r})"
    # else _require_id(entry, each) for each entry, in iteration order -> frozenset
```

This follows the stage-1 grain. The helpers raise `ValueError`, as `numbers` and `signals` do.
`Candidate.__init__` and `FeedRequest.__init__` each translate it once into `InvalidRequest`, adding the
`item_id` that only they know. The item-id check in `Candidate` moves onto `_require_id(item_id, "item
id")`. That change preserves behavior: the message text is identical, and a characterization test pins it.

**Matching is exact.** Comparison is `str` equality and set membership, so it is case-sensitive, with no
Unicode normalization and no stripping. `" "` is a valid id, as it is for item ids in stage 1.

## 4. Seams and the types that cross them (changed rows complete)

| Seam | Crosses | Never crosses |
|---|---|---|
| caller → `FeedService.rank` | `FeedRequest` (now with `blocked_authors`, `muted_topics`) | dicts, raw JSON, a pre-filtered list |
| `FeedService` → caller | `Feed` (`RankedItem`, `str`, `Decimal`). Unchanged | authors, topics, removal counts |
| `FeedService` → `rank_feed` | one `Weights`, one `FeedRequest`. Unchanged | the service, the loader |
| `rank_feed` → `request` | calls `request.eligible_candidates()`, and reads `Candidate.item_id` and `Candidate.author` | `request.candidates` (see §6a invariant), the lists themselves |
| `rank_feed` → `_limit_author_runs` | `Sequence[Candidate]` in rank order → `list[Candidate]` | scores, weights. Diversity cannot see or touch a score |
| `cli` → library | decoded JSON: candidate objects into `Candidate.from_mapping`, the two arrays into `FeedRequest(...)` | `_require_id*`, `rank_feed` |

`FeedService`, `load_weights_file`, the loader seam and `config_file → core` are unchanged.

## 5. Error vocabulary (changed: messages only, no new type)

There is still no new error type. Every stage-2 rejection is handled the way a stage-1 rejection is: the
whole request is rejected, nothing is ranked, and the CLI exits with 4. A second type would have no
different handler. Eligibility and diversity produce **no errors**. A removed item is an absence, not a
failure.

| Error | New raisers | New messages (examples) |
|---|---|---|
| `InvalidRequest` | `Candidate` (author, topics), `Candidate.from_mapping` (keys), `FeedRequest` (lists), `cli` (missing top-level key) | `item 'b': author must be a non-empty string (got None)` · `item 'b': topics must be a list of topic ids (got 'sports')` · `item 'b': topic id must be a non-empty string (got '')` · `item 'b': 'author' is missing` · `blocked_authors must be a list of author ids (got None)` · `muted_topics: topic id must be a non-empty string (got 7)` · `request: 'blocked_authors' is missing` |

- `item_id` is set on every candidate-level problem, and `None` on a list-level one. `signal` stays
  `None` unless the problem is a signal. That includes a missing `author` or `topics` key:
  `from_mapping` sets `signal` only when the key is in `SIGNAL_NAMES`.
- First-problem order: within a candidate, id → author → topics → signals. Within a request, user →
  `blocked_authors` → `muted_topics` → duplicate id. On the CLI, candidates are built in input order before
  the `FeedRequest`, so a bad candidate is reported before a bad list.
- A `set` passed by a library caller has no stable iteration order. With two bad entries, which one is
  named first is unspecified. A list, which is all JSON can produce, is deterministic.
- `WeightConfigError`, the `decimal`-trap-is-a-defect rule and every exit code are unchanged.

## 6. Hard decisions

### (a) Where "an ineligible item never appears" lives

**Decision.** The owner is `FeedRequest.eligible_candidates()`. Its predicate is one expression:
`c.author not in self.blocked_authors and c.topics.isdisjoint(self.muted_topics)`. `rank_feed` reads its
candidates **only** through this method. `rank_feed` is the only producer of a `Feed`, so every entry
path (L, C, D) passes through the filter. There is no second path to a `Feed`.

**Position relative to validation and scoring.** Validity is first *by construction*, not by the order
of statements. `eligible_candidates()` is a method of a `FeedRequest`, and a `FeedRequest` exists only
once every candidate, including a future-ineligible one, has passed `Candidate.__init__`, and the
whole set has passed the duplicate-id check. So an invalid-but-ineligible item rejects the request
before eligibility can even be asked. Eligibility comes **before** scoring and ranking: an ineligible
item is never scored, never sorted and never seen by diversity. That last point is required: a blocked
item between two runs must not break a run.

**Invariant to record in architecture.md.** `ranking` never reads `request.candidates`. Reading it would
reintroduce blocked items, and only the eligibility tests would catch that. It is the stage-2 counterpart
of "read `_weights` once".

**Rejected.**

| Alternative | Why not |
|---|---|
| Filter inside `FeedRequest.__init__`, storing only eligible candidates | A surprising side effect. The value would no longer be the request that was sent (`candidates` ≠ the argument), and eq and repr would lie. It is marginally shorter, but it hides data instead of owning a rule |
| Filter in `FeedService.rank` or `cli` | The D path (and L, for a CLI filter) would bypass it: a second place a filter must be remembered |
| `-inf` / sentinel score, or a penalty term | A filter modelled as a score (concept-fit failure). The item would still exist and could surface via a tie or diversity |
| Filter after diversity | A blocked item would break a same-author run. The spec says diversity runs on the filtered sequence |
| `Candidate.is_visible(blocked, muted)` | The rule would be split across two types, and `Candidate` would learn about request-level lists |
| An `Eligibility`/`Audience` value type or a filter `Protocol` | No second implementation and no rule beyond the one expression. A generic filter engine is a non-goal |

### (b) Who owns "the order" now

**Decision.** `rank_feed` remains the **single owner of the feed order**. The order is now a composition
of two sub-rules, each with one home, in one fixed pipeline inside that owner:

1. **Rank order**, unchanged and still owned by the sort key in `rank_feed`:
   `(score.copy_negate(), item_id)`, with scores from `Weights.score` in `EXACT`.
2. **Diversity**, owned by `_limit_author_runs`: a *sequence constraint* applied to the ranked
   sequence. It takes `Candidate`s in rank order and returns the arranged prefix. It never sees a score, so
   it cannot become a second owner of the score. It only rearranges, so it cannot become a second owner of
   rank order: every decision it makes is "the highest-ranked remaining item that is allowed", and rank is
   read from the order it was handed.

```python
def rank_feed(weights, request):                                   # illustrative
    eligible = request.eligible_candidates()
    scores = {c: weights.score(c) for c in eligible}               # score computed once, by its owner
    ranked = sorted(eligible, key=lambda c: (scores[c].copy_negate(), c.item_id))
    return Feed(weights.version,
                tuple(RankedItem(c.item_id, scores[c]) for c in _limit_author_runs(ranked)))

def _limit_author_runs(ranked):                                    # illustrative; the rule, verbatim
    remaining, placed = list(ranked), []
    while remaining:
        nxt = next((c for c in remaining if not _would_exceed_run(placed, c.author)), None)
        if nxt is None:
            break                                                  # infeasible tail: omitted; the feed ends
        remaining.remove(nxt)
        placed.append(nxt)
    return placed
# _would_exceed_run: the last _MAX_SAME_AUTHOR_RUN placed items all have this author
```

- **Infeasible tail.** When no remaining item may be placed, the loop ends and the rest are omitted.
  This can only happen when every remaining item is by the run author, because any other author would
  be allowed. That is exactly goals.md's rule. No error is raised, and nothing is appended.
- **Deferred items keep relative order.** `remaining` stays a rank-ordered list, and the scan is always
  from its head.
- **Stage-1 identity.** If the ranked sequence has no author run longer than 2, the head of `remaining` is
  always allowed, so the output equals the input. With empty lists, `eligible_candidates()` is every
  candidate in input order. Together they give exactly the stage-1 `Feed`.
- **Decimal traps preserved.** The key is unchanged (`copy_negate`, exact scores). `Candidate` is
  hashable because it is frozen and every field is hashable, `frozenset` included, and ids are unique, so the score dict is exact
  and collision-free.
- **Cost.** The worst case is O(n²), from scanning past deferred items and `list.remove`. No performance
  requirement is stated (design-principles §13 is conditional), and the direct form reads as the rule.

**Rejected.**

| Alternative | Why not |
|---|---|
| Encode diversity in the sort key | Impossible: an item's position depends on what was placed before it, which is history, not a key |
| Diversity penalty in the score | A sequence rule modelled as a score. It would change the reported score and be a second owner of it |
| Linear algorithm with a single-author deferred queue | Correct (all deferred items share the run author), but clever. Its correctness needs a proof the reader must redo, and nothing requires the speed |
| A separate public `diversify` stage, or a `diversity.py` module | One private function with one caller. A module would be a lazy class, and public surface nobody consumes |
| Operating on `RankedItem` (adding `author` to it) | That changes the response shape and leaks metadata the response must not carry |
| `max_run` parameter, or a `diversify: bool` flag on `rank_feed` | A configurable limit is a non-goal. A flag argument switches behaviour. The constant is named only so that `2` has a name |
| Append the unplaceable tail, or reject the request | Appending breaks a hard constraint. Rejecting fails a feed because of how candidates happen to be distributed (goals.md) |

### (c) What items and the request carry, and who validates it

**Decision.** This follows the stage-1 pattern exactly.

- **Per-item metadata** (`author`, `topics`) is part of the candidate contract, validated in
  `Candidate.__init__` (values) and `Candidate.from_mapping` (key set via the existing
  `read_signal_fields(leading=...)`). `topics` is stored as `frozenset[str]`, so "repeats mean one" and
  "order is irrelevant" hold by representation, not by a rule someone must remember. An empty
  `topics` is valid. Such an item can never be muted.
- **Lists** are request-level facts, validated in `FeedRequest.__init__` (values) and stored as
  `frozenset[str]` (repeats collapse). *Required* is Python arity for the library and the CLI shape check for JSON, the
  same split stage 1 uses for `candidates`.
- **One meaning of "id"**: `_require_id` / `_require_id_set` (§3.1).
- **Exactly one author** is structural: `author` is a `str` field, so a list or `None` is rejected as
  "not a non-empty string".

**Rejected.** `AuthorId`/`TopicId` value types (no rule beyond non-empty `str`, which the helpers own
once; stage 1 cut `ItemId` for the same reason). Topics as a `tuple` (it keeps meaningless order and
repeats, and every consumer would dedupe). Optional lists that default to empty (the PO chose required
precisely to fail fast). A `FeedRequest.from_mapping` (the CLI's three-line top-level check is its only
consumer; stage 1 keeps request shape in `cli`). Accepting any `Iterable` for topics (a `str` or a `dict`
iterates silently, which is fail-slow).

### Unchanged decisions

DESIGN.md §6 (exact decimals) and §7 (one weight version per request) are unchanged and still in force.

## 7. Config file and CLI (CLI changed; the config file is unchanged)

Request (UTF-8 JSON):

```json
{"user": "u1",
 "blocked_authors": ["spammer"],
 "muted_topics": ["politics"],
 "candidates": [{"id": "a", "author": "A", "topics": ["cats"],
                 "recency": 0.9, "affinity": 0.1, "popularity": 0.5}]}
```

- The CLI shape check grows by one clause. `blocked_authors` and `muted_topics` must be present. A missing
  one is exit 4, `request: 'blocked_authors' is missing`. The values are passed **as decoded** to
  `FeedRequest`, which owns "a list of non-empty strings". The CLI does not re-check entries, so it does
  not become a second owner. Candidate objects go through `Candidate.from_mapping`, which owns the
  `author`/`topics` keys.
- Output is **unchanged**: `{"weights_version": "w-…", "items": [{"id": "a", "score": "0.58"}, …]}`.
  There is no author, no topics and no count.
- Exit codes 0/1/2/3/4/5 and their order (weights before request) are unchanged.

## 8. Rule → owner → entry paths (all rules)

Paths: **L** `FeedService.rank`, **C** CLI, **S** startup, **R** reload, **D** `ranking.rank_feed` (tests).

| Rule | Owner (exactly one) | Paths |
|---|---|---|
| What a number is | `numbers.exact_number` | S, R via `Weights`; L, C, D via `Candidate` |
| How a number is written | `numbers.canonical_text` | L, C, D (version); C (scores) |
| Constructor arity (incl. new `author`, `topics`, `blocked_authors`, `muted_topics`) | Python's signature (`TypeError`) | code calling constructors |
| Weight names on data | `Weights.from_mapping` via `read_signal_fields` | S, R |
| Weight values; at least one > 0; never rescaled | `Weights.__init__` | S, R, direct |
| Config file readable, TOML, no duplicate keys | `config_file.load_weights_file` | S, R, C |
| Invalid at startup → refuse | `FeedService.__init__` | S (CLI exit 3) |
| Invalid on reload → keep last valid, report | `FeedService.reload` | R |
| One weight version per request | `FeedService.rank` + `Weights` immutability | L, C |
| Response carries the version used | `rank_feed` | L, C, D |
| Weight version identity | `Weights.version` | L, C, D |
| Change only on explicit reload | `FeedService` | S, R |
| score = w·s, exact, nothing else (no eligibility or diversity term) | `Weights.score` in `EXACT` | L, C, D |
| Candidate key set on data: exactly `id`, `author`, `topics` + the three signals | `Candidate.from_mapping` via `read_signal_fields(leading=…)` | C, mapping callers |
| Signal values in [0, 1], never clamped | `Candidate.__init__` | L, C, D |
| **What an id is** (non-empty `str`, exact match): item id, author, topic, list entry | `request._require_id` (and `_require_id_set` for collections) | L, C, D via the two constructors |
| Item id valid | `Candidate.__init__` → `_require_id` | L, C, D |
| **Exactly one author per item** | `Candidate.__init__` (a `str` field) → `_require_id` | L, C, D |
| **Topics: a collection of ids; repeats = one; may be empty** | `Candidate.__init__` → `_require_id_set`, stored `frozenset` | L, C, D |
| No duplicate ids (eligible or not) | `FeedRequest.__init__` | L, C, D |
| `user` is a str; doesn't affect the result | `FeedRequest.__init__`; structurally unread by `rank_feed` | L, C, D |
| **Block and mute lists: required; entries are ids; repeats = one; empty allowed** | `FeedRequest.__init__` → `_require_id_set` (values); arity or `cli` (presence) | L, C, D |
| **Validity before eligibility** | Structural: `eligible_candidates` is a method of an already-valid `FeedRequest` | L, C, D |
| **Ineligible (blocked author OR any muted topic) → absent** | `FeedRequest.eligible_candidates` | L, C, D (rank_feed's only source of candidates) |
| **Feed order** (composition below) | `rank_feed` | L, C, D |
| Rank order: score desc, id asc by code point, exact | `rank_feed`'s sort key `(score.copy_negate(), item_id)` | L, C, D |
| **Diversity: ≤ 2 consecutive same author, greedy, deferred keep order** | `ranking._limit_author_runs` | L, C, D |
| **Infeasible tail omitted; feed ends** | `ranking._limit_author_runs` (loop exit) | L, C, D |
| Empty or all-ineligible → empty feed | `rank_feed`, with no special case | L, C, D |
| Response shape: items with own stage-1 score + version, no counts | `Feed` / `RankedItem` (unchanged) | L, C, D |
| Request JSON shape (incl. the two new keys present) and UTF-8 | `cli` | C only |
| CLI outcome → exit code | `cli.main` | C only |

## 9. Test plan (test-first; `unittest`; no new test dependency)

**Step 0: characterization (before any stage-2 edit).** Stage 1 is designed but not built, so it is built
first with its full DESIGN.md §10 suite. Two additions are pinned as **golden data**:

- `(weights, request) → Feed` for the goals.md scenario, the ties/trap/near-tie cases and a seeded random
  set;
- the exact CLI stdout bytes for the scenario.

Stage 2 then changes the input contract on purpose: `author`, `topics` and the lists become required, so
stage-1 inputs no longer construct. The stage-1 tests migrate **mechanically through one test helper**.
The helper adds `author=<item id>` (all authors distinct, so no runs), `topics=()`, `blocked_authors=()`
and `muted_topics=()`, and the JSON fixtures gain the same fields. **Expected outputs and golden files are
not edited.** That is the proof of "empty lists and no long runs → byte-identical stage-1 output".

**Steps, each green.** (1) The migration of the stage-1 tests plus the metadata and list validation in
`request.py` and `cli`. `rank_feed` is untouched, and the golden data passes. (2) Eligibility:
`eligible_candidates` and the one-line change in `rank_feed`. (3) Diversity: `_limit_author_runs`.

| Module | Tests |
|---|---|
| request: ids | item-id message unchanged after moving to `_require_id` (pinned). `" "` accepted; `"a"` ≠ `"A"` |
| request: author | missing key (from_mapping, `item_id` set, `signal` None); `None`, `""`, `3`, `["A"]` → rejected naming the item; missing keyword → `TypeError` |
| request: topics | missing key; `None`, `"sports"`, `{"t": 1}`, `[""]`, `[3]` → rejected naming the item; `[]` accepted; `["x","x"]` constructs a `Candidate` equal to `["x"]`; tuple/set/frozenset accepted |
| request: lists | missing keyword → `TypeError`; `None`, `"A"`, `[""]`, `[1]` → `InvalidRequest`, `item_id` None; `[]` accepted; repeats accepted |
| request: validity first | a blocked item with signal `1.2` → rejected (it cannot even be constructed; via CLI → exit 4); a duplicate id where one twin is blocked and the other eligible → rejected; a muted item with an empty-string topic → rejected |
| request: eligibility | blocked author out; the `"a"` vs `"A"` case not blocked; an item with one muted topic among three → out; an item with `topics=()` never muted; a muted topic no item has → no effect; repeated list entries = one; input order preserved; all ineligible → `()` |
| ranking: characterization | the golden `Feed`s, unchanged, via the helper |
| ranking: eligibility | a blocked item with the **top** score absent; the next item leads; scores of the others unchanged; all ineligible → `Feed(v, ())` |
| ranking: diversity | the four goals.md examples verbatim; runs of 1, 2 and exactly 3; interleaving `a1 a2 a3 b1 b2 b3` → `a1 a2 b1 a3 b2 b3`; many authors (no run > 2 → identity); single author n = 1, 2, 5 → first min(n, 2); mid-feed infeasible tail `a1 a2 b1 a3 a4 a5` → `a1 a2 b1 a3 a4`; ties inside an author (equal scores → id order within the run); ties across authors (`a1`, `b1` equal → `a1` first, and it counts toward A's run); a blocked `x1` ranked between `a1 a2` and `a3` → `a1 a2` (the filtered run is not broken); each `RankedItem.score == weights.score(candidate)` (shown unchanged) |
| ranking: invariants (seeded random) | output ⊆ eligible; no 3 consecutive same author; order among same-author items is rank order; if items were omitted, all of them are by the author of the last two placed; permutation of input → the same feed; near-tie ordering and ambient-`prec` tests still pass |
| service | one test: `rank` applies eligibility and diversity (the L path); everything else unchanged |
| cli | new request shape → exit 0, output bytes unchanged in shape; missing `blocked_authors` or `muted_topics` → 4; `"blocked_authors": "A"` → 4; a candidate without `author` → 4 naming the item; a blocked item absent end to end; scenario golden bytes with empty lists |

## 10. Subtractive pass: what was cut, and what stays

**Cut** (no present force): `AuthorId`/`TopicId` value types; an `Eligibility`/`Audience` type; a
`FeedRule`/filter `Protocol` or pipeline; a `diversity.py` module; a public `diversify`; a `max_run`
parameter; any flag argument on `rank_feed`; `author` on `RankedItem`; removed/omitted counts; a new
error type or an `InvalidRequest.field` attribute (no consumer); `FeedRequest.from_mapping`;
`Candidate.is_visible`; eager filtering in `FeedRequest.__init__`; the linear deque algorithm; sentinel or
`-inf` scores; default-empty lists; any new stdlib import.

**Kept, with the force behind each:**

- `author` / `topics` fields: the PO's item metadata.
- `blocked_authors` / `muted_topics`: the PO's request lists.
- `eligible_candidates()`: the single owner of eligibility, and the only door `rank_feed` uses.
- `_limit_author_runs`: the single owner of the sequence constraint, a separate step because it is a
  different *kind* of rule from the key.
- `_MAX_SAME_AUTHOR_RUN`: names the PO's number once.
- `_require_id` / `_require_id_set`: five call sites share one meaning of "id". Without the helpers, that
  meaning would be duplicated five times.
- `IdCollection`: makes the signature true about what is accepted.

**Concept fit.**

- Eligibility is a **filter**, a query returning a subset. It never touches a score or a position.
- Diversity is a **sequence constraint**, a function from a sequence to a sequence. It never touches a score.
- An omitted tail is an **absence**: the loop ends. It is not a synthetic or placeholder item, and not
  an error.
- An all-ineligible request is a `Feed` with no items.
- Topics and lists are **sets**, because repeats and order carry no meaning.
- The score is still exactly the stage-1 formula and the only number shown.

**Smell check.**

- *Feature envy*: `eligible_candidates` reads `Candidate.author`/`topics`, but the rule belongs to
  the request's lists, and moving it to `Candidate` would split it.
- *Shotgun surgery*: a stage-3 run limit or diversity key touches one function.
- *Duplication*: the id rule is in one place.
- *Size*: `request.py` grows by two fields, one method and two helpers; `ranking.py` by one function and
  one constant.

## 11. Assumptions (new; stage-1 assumptions stand)

1. The accepted collection kinds for topics and lists are `list`, `tuple`, `set` and `frozenset`. JSON
   arrays arrive as `list`.
2. Validation order for first-problem reporting is as in §5.
3. No Unicode normalization or case folding. "Exact" is `str` equality.
4. `" "` is a valid author or topic id, consistent with item ids.

## 12. Records to update when this lands

- architecture.md: add the invariant "`ranking` reads candidates only via `eligible_candidates()`", and
  restate the order as rank key + `_limit_author_runs`.
- A new `decisions/0002-stage2-eligibility-diversity.md` that **supersedes** the DESIGN.md §9 "Order" row
  in place.
- DESIGN.md §3/§4/§5/§8/§9/§10 replaced by the corresponding sections above.
