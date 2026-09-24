# Feed ranking — stage 2 architecture (eligibility and diversity)

Axis: **correct encapsulation.** Each rule has one owner that cannot be bypassed, and no implementation type
crosses a public seam. This is a design-only document. It changes DESIGN.md (stage 1). Sections that are not
restated here are unchanged and still authoritative: §6 (exact decimals), §7 (one weight version per
request), the config-file half of §8, and §12 items 1–9. Every changed section is complete below.

**Kind of change:** add-feature. It is done as one behavior-preserving refactor step followed by three
behavior-changing steps (§11).

---

## 0. The change in one paragraph

The request now carries two lists, `blocked_authors` and `muted_topics`, and each candidate carries an
`author` and `topics`. All of them are validated in the constructors that already own request validity, so
**a `FeedRequest` that exists is fully valid.** Eligibility is a **filter owned by the valid request**:
`FeedRequest.eligible_candidates()`. `rank_feed` uses it as its only source of candidates. Diversity is a
**sequence constraint owned by a new core module, `diversity`**. That module imports nothing from the
package, and its function is generic in the item type, so it cannot read a score or an id. It can only
select and reorder by position and author. `rank_feed` still owns "the order". It composes three steps:
eligible candidates → stage-1 rank order (key unchanged) → author-run limit. `FeedService`, `Weights`,
`config_file`, `numbers`, `signals`, `Feed` and `RankedItem` are unchanged.

## 1. Shape (changed)

```
feed_ranking/
  __init__.py      public re-exports (§3); no logic                                       [unchanged list]
  __main__.py      raise SystemExit(cli.main())                                           [unchanged]
  numbers.py       Number, exact_number(), canonical_text(), EXACT                        [unchanged]
  signals.py       SIGNAL_NAMES, read_signal_fields()                                     [unchanged]
  diversity.py     MAX_AUTHOR_RUN, limit_author_runs()          [core foundation] NEW  -> nothing in package
  weights.py       Weights, WeightConfigError                                             [unchanged]
  request.py       Candidate (+author, +topics), FeedRequest (+lists, eligible_candidates()),
                   InvalidRequest, private _exact_id/_id_set    [core] CHANGED -> numbers, signals
  ranking.py       RankedItem, Feed, rank_feed(), private _Scored/_rank_key
                                                                [core] CHANGED -> weights, request, diversity
  service.py       FeedService, WeightLoader                                              [unchanged]
  config_file.py   load_weights_file()                                                    [unchanged]
  cli.py           main()                                       [shell] CHANGED (shape check: two keys)
```

Imports stay acyclic. `diversity` joins `numbers` and `signals` as a leaf that imports nothing from the
package. The core still never imports the shell.

## 2. Change axes (changed rows only; stage-1 rows stand)

| Axis | Absorbed by | Cost of the change |
|---|---|---|
| The user's block and mute lists vary per request | Carried on `FeedRequest`. Nothing is stored | None: a new value per request |
| Which items may be shown | `FeedRequest.eligible_candidates()` (one predicate) | A new exclusion rule edits one method |
| Feed arrangement beyond score | `diversity.limit_author_runs`, composed in `rank_feed` | Isolated. The rank key and the score are untouched |
| *Not an axis:* diversity key, run limit, a filter or rule engine, storing lists | `MAX_AUTHOR_RUN = 2`, author only, fixed composition | Accepted: goals.md stage-2 non-goals |

## 3. Public surface (changed parts complete; unchanged parts referenced)

```python
# request.py
class InvalidRequest(Exception):          # UNCHANGED type; new messages only (§5)
    problem: str
    item_id: str | None
    signal: str | None                    # None for author/topics/list problems

@dataclass(frozen=True, slots=True, init=False)
class Candidate:
    item_id: str
    author: str                           # NEW  exactly one; non-empty str; stored as given (no case folding, no strip)
    topics: frozenset[str]                # NEW  zero or more; each non-empty str; repeats collapse
    recency: Decimal
    affinity: Decimal
    popularity: Decimal
    def __init__(self, item_id: str, *, author: str, topics: Iterable[str],
                 recency: Number, affinity: Number, popularity: Number) -> None: ...
        # first problem in fixed order: id, author, topics, then signals in SIGNAL_NAMES order
    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> "Candidate": ...
        # keys exactly {"id", "author", "topics", *SIGNAL_NAMES}
        # via read_signal_fields(raw, leading=("id", "author", "topics"))

@dataclass(frozen=True, slots=True, init=False)
class FeedRequest:
    user: str
    candidates: tuple[Candidate, ...]     # the request as submitted: every valid candidate, eligible or not
    blocked_authors: frozenset[str]       # NEW
    muted_topics: frozenset[str]          # NEW
    def __init__(self, user: str, candidates: Iterable[Candidate], *,
                 blocked_authors: Iterable[str], muted_topics: Iterable[str]) -> None: ...
        # first problem in fixed order: user is str, blocked_authors, muted_topics, then no duplicate item_id
    def eligible_candidates(self) -> tuple[Candidate, ...]: ...
        # NEW  submission order; a candidate is excluded iff its author is blocked or any of its topics is muted

# diversity.py  (internal; not re-exported)
T = TypeVar("T")
MAX_AUTHOR_RUN: Final = 2
def limit_author_runs(ranked: Iterable[T], author_of: Callable[[T], str]) -> tuple[T, ...]: ...

# ranking.py
RankedItem                                # UNCHANGED (item_id, score)
Feed                                      # UNCHANGED fields; the items contract is restated in §8(b)
def rank_feed(weights: Weights, request: FeedRequest) -> Feed: ...   # UNCHANGED signature

# service.py, weights.py, config_file.py, numbers.py, signals.py: UNCHANGED
# cli.py: def main(argv: Sequence[str] | None = None) -> int   UNCHANGED signature
```

`__init__` re-exports the same ten names. `diversity`, like `numbers` and `signals`, stays internal. Tests
import it directly.

**Construction contract (extends DESIGN §3).** `author`, `topics`, `blocked_authors` and `muted_topics`
are keyword-only and have **no default**. Leaving one out in library code is a `TypeError`, the same as a
missing signal keyword. This is how "required" holds on the library path. A default of `()` would be the
silent failure goals.md names: a caller who forgets the lists would be shown blocked content. Every
**value** is data, and a bad value is an `InvalidRequest`. That includes `None`, a bare `str` passed as a
collection, a `Mapping`, and an empty string entry.

Typical embedding:

```python
feed = service.rank(FeedRequest(
    "u1",
    [Candidate("a", author="alice", topics=["cats"], recency=0.9, affinity=0.1, popularity=0.5)],
    blocked_authors=["mallory"], muted_topics=[],
))
```

### What an id is: one owner, private to `request.py`

Every identifier in the request follows the same rule: a non-empty `str`, matched exactly. That covers
the item id, the author id, each topic id, and each list entry. One pair of private functions in
`request.py` owns the rule. It follows the `numbers` pattern: raise a local `ValueError`, and let the
caller translate it once, adding the name that only the caller knows.

```python
def _exact_id(x: object) -> str: ...
    # ValueError "must be a non-empty string (<repr>)"; returns x unchanged: no strip, no casefold
def _id_set(x: object) -> frozenset[str]: ...
    # ValueError "must be a collection of ids, not a string" for str/bytes/bytearray;
    #            "must be a collection of ids" for a Mapping or a non-iterable (a dict would silently yield its keys);
    #            "[i] must be a non-empty string (<repr>)" for the first bad entry, i in iteration order.
    # Repeats collapse by construction (frozenset). Matching is set membership: exact and case-sensitive.
```

These are private functions, not a module. Their only users (`Candidate` and `FeedRequest`) both live in
`request.py`, so a module would publish a seam that nobody crosses (§12). The stage-1 item-id rule moves
behind `_exact_id` as a behavior-preserving refactor: the same acceptance set (`" "` is still accepted)
and the same message text. After the move, "what an id is" has one owner instead of five.

## 4. Seams and the types that cross them (complete)

| Seam | Crosses | Never crosses |
|---|---|---|
| caller → `FeedService.rank` | `FeedRequest` | dicts, raw JSON, unvalidated lists |
| `FeedService` → caller | `Feed` (`RankedItem`, `str` version, `Decimal`) | `Weights`, the loader, authors, topics, anything about removed items |
| loader → `FeedService` | `Weights`, or `WeightConfigError` | paths, TOML, `OSError`, `TOMLDecodeError` |
| `FeedService` → `rank_feed` | one `Weights` value, one `FeedRequest` | the service, the loader |
| `rank_feed` → `FeedRequest` | the query `eligible_candidates()` → `tuple[Candidate, ...]` | the lists; ranking never evaluates eligibility itself |
| `rank_feed` → `diversity` | a rank-ordered sequence of private `_Scored` values plus an `author_of` function | `Weights`, `FeedRequest`; `diversity` sees `T` and a `str` author, never a score or an id |
| `config_file` → core | a `Mapping` into `Weights.from_mapping` | — |
| `cli` → library | public names; decoded JSON objects into `Candidate.from_mapping`; the two decoded list values passed **as-is** into `FeedRequest`; `numbers.canonical_text` | `exact_number`, `EXACT`, `rank_feed`, `_id_set`; the CLI never validates an id |

`frozenset[str]` crosses the public seam as the stored type of the lists and of `topics`. It is stdlib,
immutable, and it states the rule itself: repeats mean one, and matching is exact membership. It is a
published representation, not an implementation detail. The same holds for `Decimal`.

`_Scored` never leaves `ranking.py`. `diversity` receives it only as an opaque `T`.

## 5. Error vocabulary (additions)

**No new error type.** Every new rejection is handled like the stage-1 ones: the whole request is
rejected, nothing is ranked, and the CLI exits with 4. A new type would be a subtype that no handler
catches differently (design-principles §5). `WeightConfigError` is untouched.

| Raised by | Condition | `problem` text (CLI stderr `error: <problem>`) | `item_id` / `signal` |
|---|---|---|---|
| `Candidate.from_mapping` | `author` / `topics` key absent | `item 'b': author is missing`, `item 'b': topics is missing` | `'b'` / `None` |
| `Candidate.__init__` | bad author | `item 'b': author must be a non-empty string (None)` | `'b'` / `None` |
| `Candidate.__init__` | topics a string, mapping or non-iterable | `item 'b': topics must be a collection of topic ids, not a string` | `'b'` / `None` |
| `Candidate.__init__` | bad topic entry | `item 'b': topics[1] must be a non-empty string ('')` | `'b'` / `None` |
| `FeedRequest.__init__` | bad list | `blocked_authors must be a collection of author ids, not a string` | `None` / `None` |
| `FeedRequest.__init__` | bad list entry | `muted_topics[0] must be a non-empty string (3)` | `None` / `None` |
| `cli` (shape) | top-level key absent | `request: 'blocked_authors' is missing`, `request: 'muted_topics' is missing` | `None` / `None` |

- When the item id itself is invalid there is no `item_id`, so the CLI names the item by input index, as
  in stage 1 (`candidates[2]: …`).
- A `TypeError` from a missing keyword in library code is Python's, not the product's (DESIGN §3,
  assumption 8, extended to the four new keywords).
- The fixed first-problem order becomes: CLI shape → candidates in input order (each one: id, author,
  topics, signals) → `FeedRequest` (user, blocked_authors, muted_topics, duplicate ids). A request with a
  bad candidate *and* a bad list reports the candidate.
- Ineligibility is **never** an error. An ineligible item is simply absent from the feed. An empty feed
  is `Feed(version, ())`.

## 6. Unchanged: exact decimals (DESIGN §6) and one weight version per request (DESIGN §7)

Neither decision is touched. Each eligible item's score is computed **once**, by `Weights.score`, inside
`EXACT`. It is carried unchanged to `RankedItem.score`. The rank key is still
`(score.copy_negate(), item_id)`. The diversity step never does arithmetic.

## 7. Config file and CLI (§8; config file unchanged, CLI changed)

**Request JSON.**

```json
{"user": "u1",
 "blocked_authors": ["mallory"],
 "muted_topics": ["spoilers"],
 "candidates": [
   {"id": "a", "author": "alice", "topics": ["cats", "cats"], "recency": 0.9, "affinity": 0.1, "popularity": 0.5}
 ]}
```

**Output:** unchanged, byte for byte in form: `{"weights_version": "w-…", "items": [{"id": "a", "score":
"0.58"}, …]}`. Authors and topics are never echoed, and there is no removed-count.

**Shape check (the CLI's only request rule; still a representation rule).** A top-level object. `user` a
string. `candidates` an array of objects. `blocked_authors` and `muted_topics` **present**. The CLI
checks presence only. It hands the two values to `FeedRequest` untouched, and `_id_set` decides whether
each is an acceptable collection. So a JSON string, object, number or `null` in either key is rejected
by the same owner as on the library path, with the same message. Order of work, exit codes and stderr
format are unchanged (DESIGN §8 table).

## 8. Hard decisions

### (a) Where "an ineligible item never appears" lives

**Decision.** The rule's owner is `FeedRequest.eligible_candidates()`. It is placed after validation by
construction, and before scoring by construction.

```python
def eligible_candidates(self) -> tuple[Candidate, ...]:
    return tuple(c for c in self.candidates
                 if c.author not in self.blocked_authors and self.muted_topics.isdisjoint(c.topics))
```

Three properties make it unforgeable in the intended paths.

1. **Validity comes first, structurally.** `eligible_candidates` is a method of a `FeedRequest`, and a
   `FeedRequest` exists only if every candidate (eligible or not), both lists, `user` and id uniqueness
   are valid. No ordering check is needed: filtering a request that failed validation cannot be
   expressed. The duplicate-id check runs over `self.candidates`, which still holds the ineligible twin.
   An invalid-but-ineligible item therefore still rejects the request. The `Candidate` behind an
   ineligible item was itself built by the validating constructor, so a bad signal on it rejects the
   request before `FeedRequest` is even reached.
2. **One funnel on every entry path.** L (`FeedService.rank`), C (`cli` → `FeedService.rank`) and D
   (`rank_feed`) all produce a `Feed` only through `rank_feed`. `rank_feed`'s **only** source of
   candidates is `request.eligible_candidates()`. It never reads `request.candidates` or the lists. D is
   the lowest path, and it filters too, so no path sits beneath the filter.
3. **It precedes scoring and arrangement.** Ineligible items are never scored. That means no sentinel
   score, and no "shown low". They never enter the diversity pass, so an ineligible item between two runs
   of one author does not break the run (`a1 a2 x a3`, with x blocked, gives `a1 a2`).

`Weights.score` still reads only the three signals, so no eligibility term can enter the score.

**The residual, stated.** Python cannot stop a future edit to `ranking.py` from reading
`request.candidates`. The guard is behavioral: a blocked top-score item is asserted absent on D, L and C
(§11). `candidates` stays public because it is the request as submitted. It is a stage-1 public field,
and removing or filtering it would be a breaking and surprising change (see "rejected").

**Why FeedRequest, not Candidate.** The rule relates two things: the user's lists and the item's metadata.
The lists belong to the request, and only the request holds both. This is the same argument that put
duplicate ids on `FeedRequest` in stage 1 ("the rule is about the request as a whole"). `FeedRequest`
reads `Candidate`'s public fields inside its own module, where they are its working currency. No other
module decides eligibility.

**Rejected.**

| Alternative | Why not |
|---|---|
| Score an ineligible item `-inf`, or add a penalty term | Concept cram (a filter modelled as a score). It would also still be shown, just low |
| Filter in `FeedService.rank` | Path D would surface ineligible items. Policy would sit in the shell |
| Filter in `cli` | Library path unprotected: a second owner the day it is copied |
| Drop ineligible items in `FeedRequest.__init__` (store only eligible) | The request would no longer equal what was submitted, and `candidates` would silently change meaning. It would also blur "validated" with "filtered" |
| Filter after diversity | Wrong result: blocked items would shape the runs (`a1 a2 x a3` would allow `a3`) |
| Filter before validation (skip validating ineligible items) | Violates "validity first" (goals.md) |
| `Candidate.is_eligible(blocked, muted)` | The candidate would own a rule about the user's lists. It is a split owner, because the filter would still live elsewhere |
| An `Exclusions` value object holding the two lists | A lazy class. `FeedRequest` already holds the lists and is the natural owner. It adds a public type and a constructor for no rule of its own |
| A generic `Filter` protocol or pipeline | goals.md non-goal. One predicate has no variation to abstract |
| A separate `ValidatedRequest` type | `FeedRequest` is already valid by construction. It would be a second type for the same fact |

### (b) Who owns "the order" now

**Decision.** `rank_feed` still owns the feed order. That order is now a **composition of three
single-owner steps**, and neither of the other two steps can reach into the rank order or the score.

```python
class _Scored(NamedTuple):                 # private; exists so each score is computed exactly once
    candidate: Candidate
    score: Decimal

def _rank_key(s: _Scored) -> tuple[Decimal, str]:
    return (s.score.copy_negate(), s.candidate.item_id)      # the stage-1 rule, verbatim

def rank_feed(weights: Weights, request: FeedRequest) -> Feed:
    scored = [_Scored(c, weights.score(c)) for c in request.eligible_candidates()]
    shown = limit_author_runs(sorted(scored, key=_rank_key), author_of=lambda s: s.candidate.author)
    return Feed(weights.version, tuple(RankedItem(s.candidate.item_id, s.score) for s in shown))
```

| Rule | Owner | What it cannot do |
|---|---|---|
| Rank order: score desc, id asc, exact | `ranking._rank_key` (unchanged key) | — |
| At most 2 consecutive items per author; greedy; deferred items keep order; infeasible tail omitted | `diversity.limit_author_runs` | Read a score or an id, re-sort, or append |
| Feed order = diversity(rank order(eligible)) | `rank_feed` (the composition) | — |

**Why diversity cannot become a second owner of order or score.** `limit_author_runs` is generic in `T`,
and its module imports nothing from the package. Its only information about an item is its **position**
in the input and its **author string**. A type checker rejects any body that reads `.score` or
`.item_id` from a `T`. The import graph rejects any `Decimal` comparison against a `Candidate`. So its
"highest-ranked remaining item" can only mean "earliest in the input", and the rank order stays owned by
the one sort key. The same parametricity guarantees that the score shown is the stage-1 score: diversity
hands back the very `_Scored` values it received.

**Contract of `limit_author_runs`.**

- *Precondition:* `ranked` is in priority order (earliest = most preferred).
- *Postconditions:* (1) the output is a sub-arrangement of the input, and each element appears at most
  once. (2) No author appears more than `MAX_AUTHOR_RUN` times consecutively. (3) Each position holds the
  earliest remaining input element that satisfies (2), so deferred elements keep their relative order.
  (4) It stops exactly when every remaining element is by the author of the last `MAX_AUTHOR_RUN` placed
  elements. Those elements are omitted.
- *Consequences:* it is the identity when no author has a run longer than 2 in the input. An empty input
  gives `()`.

```python
def limit_author_runs(ranked, author_of):
    remaining, placed = list(ranked), []
    run_author, run_length = None, 0
    while remaining:
        pick = next((i for i, x in enumerate(remaining)
                     if not (author_of(x) == run_author and run_length == MAX_AUTHOR_RUN)), None)
        if pick is None:
            break                                            # only the capped author is left: omitted
        x = remaining.pop(pick)
        run_length = run_length + 1 if author_of(x) == run_author else 1
        run_author = author_of(x)
        placed.append(x)
    return tuple(placed)
```

Illustrative only. It is O(n²) in the worst case (two long single-author blocks). No performance
requirement is stated (design-principles §13 is conditional). If one appears, a rank-ordered deque plus
a pointer to the first element by a different author makes it O(n) behind the same signature.

**`Feed.items` contract (restated).** "The eligible candidates in rank order (score desc, item_id asc by
code point, exact), arranged so that no author has more than two consecutive items; items that cannot be
placed without breaking that are omitted. Not strictly score-descending. `()` when nothing is eligible."
The type is unchanged.

**Traced examples (goals.md):** `a1 a2 a3 a4 b1 b2` → `a1 a2 b1 a3 a4 b2`. `a1 a2 a3 b1 c1` →
`a1 a2 b1 a3 c1`. `a1 a2 a3` → `a1 a2`. `b1 a1 a2 a3` → `b1 a1 a2`.

**Rejected.**

| Alternative | Why not |
|---|---|
| A score penalty for repeated authors | Concept cram, and it changes the shown score |
| Encode diversity in the sort key or comparator | Diversity depends on what was placed before, so it cannot be a per-item key. A stateful comparator breaks `sorted`'s contract |
| Diversity re-sorts its input by `(score, id)` | A second owner of rank order |
| `RankedItem` gains `author` so diversity can run on it | Changes the response shape (goals.md: unchanged) and leaks metadata out of the seam |
| Diversity takes `list[RankedItem]` plus an `{item_id: author}` map | Diversity could then read score and id. It is a weaker barrier than a generic `T` |
| Diversity inside `FeedService` | Path D would miss it, and policy would sit in the shell |
| Append the infeasible tail | Breaks a hard constraint |
| Reject the request when infeasible | The product chose omission (goals.md) |
| Optimal or backtracking arrangement | The product chose the greedy reading (`b1 a1 a2` is the stated consequence) |
| `max_run` parameter or a key function for "topic" | goals.md non-goal. One named constant owns the limit |
| Private function inside `ranking.py` | Works, but loses the import barrier. The rule would sit next to `Weights` and `Candidate` and could quietly start reading them. A leaf module makes "cannot see scores" checkable |

### (c) What items and requests carry, and where each new validation rule lives

**Decision.** The metadata sits on `Candidate` (`author: str`, `topics: frozenset[str]`), and the lists
sit on `FeedRequest` (`frozenset[str]` each). Each rule lands where the matching stage-1 rule already
lives.

| New rule | Owner | Why there (the stage-1 analogue) |
|---|---|---|
| What an id is: non-empty `str`, never normalized | `request._exact_id` | Like `numbers.exact_number` for "what a number is" |
| What an id collection is: not str/bytes/Mapping; repeats = one | `request._id_set` | Same |
| An item has exactly one valid author and a valid topic collection | `Candidate.__init__` | Where the item's signals and id are validated |
| Metadata keys present on data; unknown keys rejected | `Candidate.from_mapping` via `read_signal_fields(leading=("id","author","topics"))` | The existing one owner of "missing" and "unknown" |
| The lists are valid | `FeedRequest.__init__` | Request-wide, like user and duplicate ids |
| The lists are required | Library: `FeedRequest` signature (no default). CLI: shape check (presence) | Exactly how stage 1 makes `user` and `candidates` required |

**Rejected.** An `ItemMeta` or `Author`/`TopicId` value type: stage 1 cut `ItemId` for having no rule of
its own, the grain wins, and keyword-only names already prevent swaps. `topics: tuple[str, ...]`: it
would keep repeats and order that mean nothing, so the set is the rule. Optional lists defaulting to
`()`: the silent failure goals.md rules out. List-entry validation in the CLI: the library path would go
unvalidated, giving a second owner later. `FeedRequest.from_mapping`: it would move the stage-1 CLI shape
rule into the core. That rewrites a recorded decision with no present force, since there is only one
adapter. The force appears with a second adapter, and then it is the right move. A shared `ids` module:
both users are in `request.py`.

## 9. Rule → owner → entry paths (complete: stage 1 and stage 2)

Paths: **L** `FeedService.rank`. **C** CLI. **S** startup. **R** `FeedService.reload`. **D**
`ranking.rank_feed` (internal; tests).

| Rule | Owner (exactly one) | Paths |
|---|---|---|
| What a number is | `numbers.exact_number` | via `Weights` (S, R), `Candidate` (L, C, D) |
| How a number is written | `numbers.canonical_text` | `Weights.version` (L, C, D); C output |
| Constructor arity (all keywords present, none unknown), now including author, topics and the two lists | Python's signature (`TypeError`; programming error) | direct `Weights(...)`, `Candidate(...)`, `FeedRequest(...)` |
| Weight names on data | `Weights.from_mapping` via `read_signal_fields` | S, R |
| Weight values: finite, ≥ 0, at least one > 0, never rescaled | `Weights.__init__` | S, R, direct |
| Config file readable, TOML, no duplicate keys | `config_file.load_weights_file` | S, R; C |
| Invalid at startup → refuse to start | `FeedService.__init__` | S; C exit 3 |
| Invalid on reload → keep last valid, report | `FeedService.reload` | R |
| One weight version per request | `FeedService.rank` (one read) + `Weights` immutability | L, C |
| Response carries the version used | `rank_feed` | L, C, D |
| Weight version identity | `Weights.version` | L, C, D |
| Change only on explicit reload | `FeedService` | S, R |
| score = w·signals, exact, nothing else (no eligibility or diversity term) | `Weights.score` in `EXACT`; reads only signals | L, C, D |
| Candidate keys on data: exactly id, author, topics, signals | `Candidate.from_mapping` via `read_signal_fields` | C, mapping callers |
| Signal values in [0, 1], never clamped | `Candidate.__init__` | L, C, D |
| **What an id is: non-empty `str`, matched exactly (case-sensitive, no normalization)** | `request._exact_id` | item id, author, topics, list entries (L, C, D) |
| **What an id collection is; repeats = one** | `request._id_set` | topics, both lists (L, C, D) |
| Item id valid | `Candidate.__init__` via `_exact_id` | L, C, D |
| **Author: exactly one, valid** | `Candidate.__init__` via `_exact_id` | L, C, D |
| **Topics: required collection of valid ids** | `Candidate.__init__` via `_id_set` | L, C, D |
| **Lists valid** | `FeedRequest.__init__` via `_id_set` | L, C, D |
| **Lists required** | Library: `FeedRequest` signature. Data: `cli` shape check | L, D / C |
| No duplicate ids (eligible or not) | `FeedRequest.__init__` over all `candidates` | L, C, D |
| **Validity before eligibility** | Structural: eligibility is a method of a constructed (valid) `FeedRequest` | L, C, D |
| **Blocked author or any muted topic → absent** | `FeedRequest.eligible_candidates` | L, C, D (`rank_feed`'s only candidate source) |
| **Rank order: score desc, id asc, exact** | `ranking._rank_key` `(score.copy_negate(), item_id)` | L, C, D |
| **≤ 2 consecutive same author; greedy; deferred keep order; infeasible tail omitted** | `diversity.limit_author_runs` (`MAX_AUTHOR_RUN`) | L, C, D |
| **Feed order = diversity ∘ rank order ∘ eligibility** | `rank_feed` (composition) | L, C, D |
| **Shown score = the stage-1 score** | `rank_feed` (computes once, carries it); `diversity` is parametric | L, C, D |
| Empty candidates, or none eligible → empty feed | `rank_feed`, no special case | L, C, D |
| `user` affects nothing | Structural: neither `rank_feed` nor `eligible_candidates` reads `user` | L, C, D |
| Request JSON shape (now including the lists' presence) and UTF-8 | `cli` | C (representation rule) |
| CLI outcome → exit code | `cli.main` (DESIGN §8 table, unchanged) | C |

Bold rows are new or rewritten. The only stage-1 rule rewritten is the order rule: its key survives
verbatim in `_rank_key`. Every other stage-1 row keeps its owner. The only change is that item-id
validity now delegates to `_exact_id`, and that is a refactor.

## 10. Re-trace (add-feature §6): every reader of a changed shape

- `Weights.score(candidate)` reads only signals. New fields don't reach it, so scores are unchanged.
- `FeedRequest` duplicate check: over all candidates, so an ineligible twin still collides.
- `Candidate` equality and hash now include author and topics. The only consumer is the tests. Two
  candidates with equal signals and different topics are not equal, which is correct.
- `rank_feed` → `Feed`: the shape is unchanged, and items are a subset of eligible candidates.
  Permutation invariance still holds: ids are unique, so the rank order is total, and the diversity step
  is deterministic.
- `cli` output: reads only `item_id` and `score`, so it is unchanged.
- `FeedService`: passes the request through, untouched. One weight version per request is unaffected.
- Stage-1 test "many → descending" still holds whenever no author runs longer than 2 (see characterization).

## 11. Test plan (test-first, `unittest`)

**Step 0: characterize (before any change).** The stage-1 suite (DESIGN §10) is green against stage-1
code. It builds requests through one test helper, `stage1_request(user, candidates)`. Record golden CLI
stdout **bytes** for the goals.md scenario, a tie set, the trap pair, and an empty request.

**Step 1: refactor (no behavior change).** Route the item-id check through `_exact_id`, and extract
`_rank_key`. The whole stage-1 suite passes unedited.

**Step 2: metadata and lists (validation only).** In one edit, `stage1_request` supplies
`author=f"author-{id}"`, `topics=()`, `blocked_authors=()` and `muted_topics=()`. The golden CLI inputs
gain the same neutral fields. **No stage-1 assertion is edited.** Golden stdout stays byte-identical.
This is the "empty lists, no long runs → stage-1 output" characterization. New tests:

- author: missing (`from_mapping` → `InvalidRequest`; constructor → `TypeError`), `""`, `None`, `3`,
  a list → rejected with `item_id`. `" "` accepted. `"Alice"` is stored as `"Alice"`.
- topics: missing; `"cats"` (bare string, the trap) rejected; `{"cats": 1}` (mapping) rejected; `None`,
  `3` rejected; `["cats", ""]` rejected, naming `topics[1]`. `[]` accepted. `["x", "x"]` → `frozenset({"x"})`.
  A generator is accepted.
- lists: absent keyword → `TypeError`. CLI key absent → exit 4 `request: 'blocked_authors' is missing`.
  A bare string, a mapping, `null`, or an entry `""`/`3` → `InvalidRequest` naming the list and index.
  Repeated entries accepted. Empty accepted.
- Unknown candidate key (`"topic"`) rejected (stage-1 behavior).
- First-problem order: a bad candidate plus a bad list → the candidate is reported.

**Step 3: eligibility.** `FeedRequest` tests plus `rank_feed` (D), `FeedService.rank` (L) and CLI (C)
tests. The key cases run on **all three paths**.

- A blocked item with the top score → absent. The others are in stage-1 order with the same scores.
- An item with topics `{"ok", "muted"}` and `muted_topics=["muted"]` → absent. `{"ok"}` → present.
- Case: block `"Alice"`, item author `"alice"` → present. Mute `"Cats"`, topic `"cats"` → present.
- Empty topics with a non-empty mute list → present.
- Repeated list entries behave as one.
- All candidates ineligible → `Feed(v, ())`, CLI `"items": []`, exit 0.
- **Validity first:** a blocked item with signal `1.2` → `InvalidRequest` (it never gets to be filtered).
  A duplicate id where one twin is muted → `InvalidRequest duplicate item id`. A muted item with author
  `""` → rejected.
- `user` independence with non-empty lists.
- A blocked item between two runs does not break the run: `a1[A] a2[A] x[X blocked] a3[A]` → `a1 a2`.

**Step 4: diversity.** `diversity` is tested directly on bare strings, with
`author_of=lambda s: s[0].upper()`, so no weights are needed.

- The four goals.md examples, exactly.
- Runs of 1 and 2 → identity. Exactly 3 → the third is deferred or omitted. `A A B A A B` → identity.
- Interleaving: `A A A B B B` → `a1 a2 b1 a3 b2 b3`. Many authors: `A A A A B C D` → `a1 a2 b1 a3 a4 c1 d1`.
- Single author, n = 0, 1, 2, 5 → `()`, 1, 2, 2 items.
- Infeasible tail after a mix: `B A A A A` → `b1 a1 a2`.
- Deferred elements keep relative order (property check over seeded random author sequences). The
  output never has three consecutive authors equal. Each output position is the earliest admissible
  remaining input element. The output is a sub-arrangement with no repeats.
- Then through `rank_feed`: a tie inside an author (`a2` and `a1` with equal scores → `a1` first). A tie
  across authors (by id). A deferred item keeps its **stage-1 score** in the feed (`Decimal` equality with
  `weights.score`). The shown order is not score-descending when diversity fires. Stage-1 numeric guards
  (the trap pair, the 30th-digit near-tie, `getcontext().prec = 3`) are rerun with authors that force a
  deferral, to prove exactness survives the arrangement.
- One structural check (the construction guarantee of §8(b)): `feed_ranking.diversity` imports no
  `feed_ranking` module.

**Service and CLI (end to end).** The goals.md scenario with the lists empty → byte-identical to golden.
A reload between two requests still gives one version per feed, now with non-empty lists (the stage-1
concurrency test, rerun with a blocked item and a forced deferral). A CLI bad-author request → exit 4 with
the message. Bad weights and a bad list together → exit 3 (the startup order is unchanged).

## 12. Subtractive pass and concept fit

**Kept, with the present force behind each.**

- `Candidate.author` and `Candidate.topics`: item metadata the rules read.
- `FeedRequest` lists: the user's preferences, per request, not stored.
- `eligible_candidates()`: the one owner of the filter, and the funnel for every path.
- `_exact_id` and `_id_set`: one rule used in five places (item id, author, topic entries, two lists).
  `_id_set` also owns the bare-string and mapping traps.
- `diversity` module: owner of the sequence constraint. The import barrier makes "cannot read scores"
  checkable, and it can be tested on bare sequences.
- `MAX_AUTHOR_RUN`: names the product's "2" once.
- `_Scored`: each score is computed once and travels with its candidate, so diversity can read the
  author and the output can show the same score.
- `_rank_key`: names the stage-1 order rule separately from the composition, so its owner survives
  verbatim.

**Cut.**

- A shared `ids` module: one consumer module.
- An `Exclusions` value, `ItemMeta`, `AuthorId`/`TopicId`: no rule of their own, against the grain.
- A `Filter`/`Rule` protocol or pipeline: a non-goal.
- `ValidatedRequest`: `FeedRequest` already is one.
- `FeedRequest.from_mapping`: one adapter; stage-1 decision kept.
- `RankedItem.author`: response shape.
- A removed-items count: a non-goal.
- A `max_run` or `key` parameter on diversity: a non-goal.
- A new `IneligibleItem`/`MetadataError` exception: same handling as `InvalidRequest`.
- Defaults on the new keywords: they would defeat "required".
- A deque-based O(n) arranger: no stated performance need.
- Storing eligibility on `Candidate`: it depends on the request, not the item.

**Concept fit.**

- Eligibility is a **filter**: a predicate choosing a subsequence of the valid request. It is not a
  score, not a sentinel, not a flag on the item, and not an error.
- Diversity is a **sequence constraint**: a function from a priority-ordered sequence to an arranged
  subsequence. It is not a key, not a penalty, and not a comparator.
- An omitted tail is simply absence: there is no placeholder item.
- The rank order is still a **sort key**, unchanged.
- `topics` and the lists are **sets**, because repeats mean one and membership is the matching.
- There are no flag arguments, no `-inf`, and no synthetic items.

## 13. Assumptions (new; each a simple default within goals.md)

10. A bare string passed where a collection of ids is expected is rejected, not iterated per character.
    A mapping is rejected, not iterated over its keys.
11. An id entry is reported by its index in iteration order (for JSON, the array index).
12. The CLI checks only that the two list keys are present. Their values are judged by `FeedRequest`.
13. Unknown top-level JSON keys keep their stage-1 treatment (the shape check does not name them).
14. Validation reports the first problem in the order given in §5.

## 14. Records to update at merge (for the Guide)

- DESIGN.md: §1, §3, §4, §5, §8 (CLI), §9 and §10 as above. §2 gains the new rows.
- architecture.md: add to the invariants that hold by construction:
  - "a `FeedRequest` that exists is valid, and eligibility is its method";
  - "`rank_feed` reads candidates only through `eligible_candidates()`";
  - "`diversity` imports nothing from the package".

  Note the residual: reading `request.candidates` in `ranking.py` silently resurrects blocked items.
- New decision `decisions/0002-stage2-eligibility-diversity.md`. It supersedes only the order row of
  0001/DESIGN §9 and records the three hard decisions.
