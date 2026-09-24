# Feed ranking — stage 2 architecture (eligibility and diversity)

Design only. This document changes [DESIGN.md](../../../DESIGN.md) (stage 1). Sections not listed here are
unchanged and are referenced by number: **§6** (exact numbers), **§7** (one weight version per request),
the config-file half of **§8**, and the stage-1 assumptions in **§12**. Every section that changes is written
out in full below. Product decisions are in `goals.md`, "Stage 2".

Axis pulled on: **correct genericity**. Each new element is made as generic as its consumers need (the floor)
and no more specific than every producer can honestly supply (the ceiling). The shape absorbs the change axes
stage 2 actually has, and it names the axes it deliberately doesn't absorb (§2).

---

## 0. The change in one paragraph

The change only adds new request data (two lists and two per-item fields) and two rules. So it lands on
three existing owners and adds no new module. It adds no new public type and changes neither `FeedService`,
`Weights`, `numbers`, `signals` nor `config_file`:

- **`Candidate`** also carries `author: str` and `topics: frozenset[str]`, validated in its constructor like
  every other item field.
- **`FeedRequest`** also carries `blocked_authors: frozenset[str]` and `muted_topics: frozenset[str]`. It
  validates them and owns eligibility as a query on an already-valid request: `eligible_candidates`.
  It also gains `from_mapping`, the one owner of the request's runtime key set. That key set now contains the
  required lists.
- **`rank_feed`** still owns "the order". It is now two private steps with a type boundary between them.
  The **rank order** is stage 1's key, unchanged. The **author-run limit** is a sequence constraint applied
  to that order. It is typed so that it *cannot* see a score or an id comparison.

The fact that `FeedService` doesn't change shows the stage-1 seam was calibrated correctly. `FeedRequest` was
the published type crossing the seam, and it absorbed new request data without the service knowing.

## 1. Shape (changed: module roles)

Core and shell as in stage 1. The only changes are the roles of `request.py`, `ranking.py` and `cli.py`.

```
feed_ranking/
  __init__.py      public re-exports (§3); no logic                                        [unchanged]
  __main__.py      raise SystemExit(cli.main())                                            [unchanged]
  numbers.py       Number, exact_number(), canonical_text(), EXACT                          [unchanged]
  signals.py       SIGNAL_NAMES, read_signal_fields()                                      [unchanged]
  weights.py       Weights, WeightConfigError                                              [unchanged]
  request.py       Candidate (+author, +topics), FeedRequest (+lists, +eligible_candidates,
                   +from_mapping), InvalidRequest; private _id(), _id_set()                [CHANGED] -> numbers, signals
  ranking.py       RankedItem, Feed, rank_feed(); private _limit_author_runs(),
                   MAX_SAME_AUTHOR_RUN                                                     [CHANGED] -> weights, request
  service.py       FeedService, WeightLoader                                               [unchanged]
  config_file.py   load_weights_file()                                                     [unchanged]
  cli.py           main(); shape check shrinks to "top level is an object"                 [CHANGED] -> service, config_file, request, numbers
```

The imports are the same as in stage 1, so the graph stays acyclic and the core never imports the shell. The
only dependency is still the standard library.

## 2. Change axes the shape absorbs, and those it deliberately doesn't (changed)

| Axis | Absorbed by | Cost of the change |
|---|---|---|
| Weight values; reload timing; weight source; entry path | Stage-1 seams (unchanged) | As in stage 1 |
| **A user's block and mute lists (they differ on every request)** | Request data: `FeedRequest.blocked_authors`, `.muted_topics` | None. The lists are values, and nothing is stored |
| **Which authors and topics each candidate has** | Request data: `Candidate.author`, `.topics` | None |
| **The rank order itself** (the formula, the tie rule) | `_limit_author_runs` takes the rank order only as a *sequence of `Candidate`s*. It never reads a score or compares ids | A change to the formula or the tie-break touches `Weights.score` or the sort key only. The diversity step stays untouched |
| **The rank order's owner** vs **the run limit's owner** | Two private steps in `ranking.py`, separated by the type `Sequence[Candidate]` | Each changes alone |
| *Not an axis:* the diversity key (author) | Hard-coded `candidate.author` in `_limit_author_runs` | Diversity by topic is a non-goal. It would change one function, with no seam to open |
| *Not an axis:* the limit 2 | Named constant `MAX_SAME_AUTHOR_RUN = 2`, not a parameter or a config value | "Configurable limit" is a non-goal. Changing it means changing one constant |
| *Not an axis:* the set of eligibility rules | Two fixed checks in `FeedRequest.eligible_candidates` | A generic filter engine is a non-goal. A third rule would add one field and one clause to one owner |
| *Not an axis:* more than one author per item | `author: str` | Goals say "exactly one". A multi-author item would change the diversity meaning itself, not just a type |

This is the genericity calibration for stage 2. The two axes that vary per request (list contents and item
metadata) are **data**, so they cost nothing. The axis the stage-2 rules could silently couple to (the rank
key) is **cut off by a type**. The four non-goals get **no** seam. Each would be a knob with no consumer, and
the falsifier in design-principles §7 finds no X-item that any of them serves.

## 3. Public surface (changed sections complete)

Only `request.py`, `ranking.py` and `cli.py` change. `numbers`, `signals`, `weights`, `service` and
`config_file` keep the signatures in DESIGN.md §3 byte for byte.

```python
# request.py
class InvalidRequest(Exception):                     # unchanged type; new problems only (§5)
    problem: str
    item_id: str | None                              # the offending item when identifiable
    signal: str | None                               # set only when the problem is a signal (unchanged meaning)

@dataclass(frozen=True, slots=True, init=False)
class Candidate:
    item_id: str
    author: str                                      # NEW: exactly one author id, non-empty
    topics: frozenset[str]                           # NEW: zero or more topic ids, each non-empty; repeats = one
    recency: Decimal
    affinity: Decimal
    popularity: Decimal
    def __init__(self, item_id: str, *, author: str, topics: Iterable[str],
                 recency: Number, affinity: Number, popularity: Number) -> None: ...
        # order of checks: id, author, topics, then signals in SIGNAL_NAMES order
    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> "Candidate": ...
        # keys exactly {"id", "author", "topics", *SIGNAL_NAMES}
        # via signals.read_signal_fields(raw, leading=("id", "author", "topics"))

@dataclass(frozen=True, slots=True, init=False)
class FeedRequest:
    user: str
    candidates: tuple[Candidate, ...]                # ALL candidates as sent, eligible or not (unchanged meaning)
    blocked_authors: frozenset[str]                  # NEW
    muted_topics: frozenset[str]                     # NEW
    def __init__(self, user: str, candidates: Iterable[Candidate], *,
                 blocked_authors: Iterable[str], muted_topics: Iterable[str]) -> None: ...
        # order of checks: user is str; no duplicate item_id; blocked_authors; muted_topics
    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> "FeedRequest": ...      # NEW
        # keys exactly {"user", "candidates", "blocked_authors", "muted_topics"};
        # "candidates" a list of mappings, each via Candidate.from_mapping, located as candidates[i]
    @property
    def eligible_candidates(self) -> tuple[Candidate, ...]: ...                 # NEW
        # the candidates, in input order, whose author is not blocked and none of whose topics is muted

# private helpers in request.py (not exported): the one owner of what "an id" and "a set of ids" are here
def _id(value: object) -> str: ...                   # non-empty str, else ValueError
def _id_set(value: object) -> frozenset[str]: ...    # a non-str, non-Mapping iterable of _id; repeats fold;
                                                     # ValueError("[i] must be a non-empty string") /
                                                     # ValueError("must be a list of ids, not a string")

# ranking.py
@dataclass(frozen=True, slots=True)
class RankedItem:                                    # unchanged: the response shape is unchanged
    item_id: str
    score: Decimal

@dataclass(frozen=True, slots=True)
class Feed:
    weights_version: str
    items: tuple[RankedItem, ...]    # the eligible candidates in rank order (score desc, id asc), arranged so
                                     # that no author appears more than MAX_SAME_AUTHOR_RUN times in a row;
                                     # an unplaceable tail is omitted; () when nothing is eligible

def rank_feed(weights: Weights, request: FeedRequest) -> Feed: ...   # signature unchanged

MAX_SAME_AUTHOR_RUN: Final = 2                                         # private to ranking; the product's "2"
def _limit_author_runs(ranked: Sequence[Candidate]) -> list[Candidate]: ...
```

`rank_feed`'s body. This is illustrative, and it pins where each rule sits:

```python
def rank_feed(weights: Weights, request: FeedRequest) -> Feed:
    eligible = request.eligible_candidates                     # the only read of candidates
    scores = {c.item_id: weights.score(c) for c in eligible}   # ids unique: FeedRequest's invariant
    ranked = sorted(eligible, key=lambda c: (scores[c.item_id].copy_negate(), c.item_id))   # stage-1 key, verbatim
    shown = _limit_author_runs(ranked)
    return Feed(weights.version, tuple(RankedItem(c.item_id, scores[c.item_id]) for c in shown))

def _limit_author_runs(ranked: Sequence[Candidate]) -> list[Candidate]:
    remaining, placed = list(ranked), []
    while remaining:
        tail = placed[-MAX_SAME_AUTHOR_RUN:]
        full_run = len(tail) == MAX_SAME_AUTHOR_RUN and len({c.author for c in tail}) == 1
        barred = tail[0].author if full_run else None
        i = next((i for i, c in enumerate(remaining) if c.author != barred), None)
        if i is None:
            break                                  # only the barred author remains: omit the tail, feed ends
        placed.append(remaining.pop(i))            # pop keeps the deferred items in relative order
    return placed
```

Worst case is O(n²) in the candidate count, and no performance requirement is stated (design-principles §13
is conditional). A deque of deferred items would make it O(n) behind the same signature if one is ever
stated.

**`__init__` re-exports:** unchanged. There is no new public name. `FeedRequest.from_mapping` and
`eligible_candidates` are members of an already-public type.

**Construction contract (extends DESIGN.md §3).** The same rule applies: arity is Python's rule and values
are the product's. `author`, `topics`, `blocked_authors` and `muted_topics` are **required keyword-only**
parameters with no default. So a stage-1 call such as `FeedRequest("u1", [...])` is now a `TypeError`. This
is deliberate. The PO chose "required" so that a caller who forgets the lists fails fast instead of silently
showing blocked content. A default of `()` would make the signature lie that the lists are optional, and it
would bring back exactly that silent failure. Every *value* is data, and the constructor rejects bad values
by name. That includes `None`, a bare string `"sports"` for `topics` (a `str` is an `Iterable[str]`, and
treating it as `{"s","p",…}` would be a silent cram), a mapping, and an empty or non-str entry. Data whose
key set is known only at run time goes through `from_mapping`, which is the one owner of "missing" and
"unknown".

Typical embedding:

```python
feed = service.rank(FeedRequest(
    "u1",
    [Candidate("a", author="alice", topics=["cats"], recency=0.9, affinity=0.1, popularity=0.5)],
    blocked_authors=["mallory"], muted_topics=[]))
```

### Genericity calibration of each new crossing type

| Element | Floor (what the consumer needs) | Ceiling (what every producer can supply) | Chosen |
|---|---|---|---|
| `Candidate.topics` | Eligibility needs membership or disjointness. Order and multiplicity carry no meaning ("repeats = one") | A JSON array, or any library iterable (list, tuple, set, generator) | **Accepts** `Iterable[str]` and **stores** `frozenset[str]`. A tuple would over-specify: two candidates that differ only in topic order or repeats would compare unequal and appear to carry information they don't. A bare `str` is refused, which is the one place `Iterable[str]` is too generic |
| `blocked_authors`, `muted_topics` | Membership | Same producers | Same as `topics`, for the same reasons |
| `Candidate.author` | Equality (both rules) | A non-empty string from every producer | `str`. There is no `AuthorId` type: its only rule, non-empty, is the same as the item id's, and stage 1 already cut `ItemId` on the same grounds |
| `FeedRequest.eligible_candidates` | `rank_feed` needs the collection of showable candidates | `FeedRequest` holds all it needs | A collection-level query, not a per-item `admits(c)` predicate: the only consumer wants the collection. It returns a tuple in input order, which is deterministic even though `rank_feed` re-sorts |
| `_limit_author_runs` input | A sequence whose order is the precedence, plus an author per element | `rank_feed` has exactly that | `Sequence[Candidate]` with no scores. It has **no `key` parameter** (diversity by another key is a non-goal) and **no `limit` parameter** (a configurable limit is a non-goal). Leaving out the score is the *ceiling* cut that stops the arrangement from ever becoming a second owner of order |
| `InvalidRequest` | The CLI prints the message and maps the type to exit 4. A library caller catches the type | — | Unchanged. There is **no** new `field` attribute: no consumer reads one structurally. `signal` keeps its exact stage-1 meaning instead of being widened to cover author and topics |

## 4. Seams and the types that cross them (changed rows marked)

| Seam | Crosses | Never crosses |
|---|---|---|
| caller → `FeedService.rank` | `FeedRequest` (now with both lists; items with author and topics) | dicts, raw JSON |
| `FeedService` → caller | `Feed` (`RankedItem`, `str` version, `Decimal`), unchanged | `Weights`, the loader, removed or omitted items, counts |
| loader → `FeedService` | unchanged | unchanged |
| `FeedService` → `rank_feed` | one `Weights`, one `FeedRequest`, unchanged | the service, the loader |
| **`FeedRequest` → `rank_feed`** (new, internal) | `eligible_candidates: tuple[Candidate, ...]` | the lists (`rank_feed` never reads them), `user` |
| **rank order → run limit** (new, private) | `Sequence[Candidate]` in rank order | scores, the sort key |
| `config_file` → core | unchanged | — |
| **`cli` → library** (changed) | public names. Decoded JSON (a top-level `dict`) goes into **`FeedRequest.from_mapping`**. `numbers.canonical_text` prints scores | `exact_number`, `EXACT`, `rank_feed`, `Candidate.from_mapping` (now called by `FeedRequest.from_mapping`) |

## 5. Error vocabulary (changed: new problems, no new types)

There are still **two public error types, one per distinct handling**. Every stage-2 input problem has the
same handling as a stage-1 one: the whole request is rejected and nothing is ranked (CLI exit 4). So each one
is an `InvalidRequest`. Eligibility and the infeasible tail are **not errors**: an absent item is a normal
outcome, and an all-ineligible request gives an empty feed.

| Error | Raised by | Handling | New messages (stage-1 messages unchanged) |
|---|---|---|---|
| `WeightConfigError` | unchanged | unchanged | — |
| `InvalidRequest` | `Candidate`, `FeedRequest`, `FeedRequest.from_mapping`, the CLI's representation check | Whole request rejected (exit 4) | `item 'b': author is missing` · `item 'b': unknown 'authors'` · `item 'b': author must be a non-empty string` · `item 'b': topics is missing` · `item 'b': topics must be a list of ids, not a string` · `item 'b': topics[1] must be a non-empty string` · `missing 'blocked_authors'` · `unknown 'blocked'` · `blocked_authors must be a list of ids, not a string` · `blocked_authors[2] must be a non-empty string` · `muted_topics[0] must be a non-empty string` · `candidates must be a list of objects` · `candidates[3]: item id must be a non-empty string` |

- `_id` and `_id_set` raise an internal `ValueError`. Each caller translates it once and adds the location
  that only it knows: `Candidate` adds `item '<id>':` and the field name, and `FeedRequest` adds the list
  name. This is the stage-1 pattern for `numbers` and `signals`.
- `item_id` is set on every item-level problem. `signal` stays `None` for author and topics problems.
- **First problem, fixed order.** `Candidate` checks id, then author, then topics, then signals in
  `SIGNAL_NAMES` order. `FeedRequest` checks user, then duplicate ids, then `blocked_authors`, then
  `muted_topics`. `FeedRequest.from_mapping` checks the key set, then the `candidates` list shape, then each
  candidate in input order, then the constructor. The `candidates[i]:` prefix for an item whose id can't be
  read moves from `cli` into `FeedRequest.from_mapping`, and its text is unchanged.

## 6. Hard decision (a): where "an ineligible item never appears" lives

**Decision.** Eligibility is a **filter owned by `FeedRequest`**, exposed as the query
`FeedRequest.eligible_candidates`. `rank_feed` reads that query and only that query. It never reads
`request.candidates`. The rule:

```python
@property
def eligible_candidates(self) -> tuple[Candidate, ...]:
    return tuple(c for c in self.candidates
                 if c.author not in self.blocked_authors and c.topics.isdisjoint(self.muted_topics))
```

**Why here.**
- **Validity first holds by construction, not by ordering code.** A `FeedRequest` exists only if every
  candidate is valid (`Candidate.__init__`), the ids are unique across *all* candidates, and both lists are
  valid (`FeedRequest.__init__`). Eligibility is a query on an object that already exists, so it cannot run
  on an invalid request. An invalid item that would have been filtered out still rejects the request,
  because rejection happens before there is anything to filter.
- **Every entry path passes through it.** L (`FeedService.rank`), C (`cli` → `FeedRequest.from_mapping` →
  service) and D (`rank_feed` directly) all produce a `Feed` only through `rank_feed`, and `rank_feed`'s one
  read of candidates is `eligible_candidates`.
- **The rule's inputs all belong to the request.** It relates the request's own lists to the request's own
  candidates. It needs nothing from `Weights`, so putting it in `rank_feed` would make the order's owner also
  own the user's preferences.
- **It is the kind of thing it is.** Eligibility is a subset: it never touches a score, and nothing is
  shown low. It sits **before scoring**, so ineligible items are never scored, and no sentinel score can
  exist even in principle.

**Rejected.**

| Alternative | Why not |
|---|---|
| Score an ineligible item `-inf` or drop it by a sentinel | Concept cram: a filter modelled as a score. `Decimal('-Infinity')` would also trip the `EXACT` traps and break "scores shown unchanged" |
| Drop ineligible items inside `FeedRequest.__init__` and store only eligible ones | `request.candidates` would stop meaning "what was sent", and equality and repr would lose information. It would mix policy into the validity constructor. It also breaks down on the next change that needs "all candidates" |
| Filter in `FeedService.rank` | The CLI and D paths reach `rank_feed` without the service, so they would surface ineligible items. The shell would also own a domain rule |
| Filter in `cli` | L and D would bypass it |
| A separate `Exclusions(blocked_authors, muted_topics)` value with `excludes(c)` | It fails the subtractive pass. Its only consumer is `FeedRequest`, and it adds a public name and a nested constructor for every caller without absorbing any axis |
| A `Filter` protocol or a list of predicates passed to `rank_feed` | A generic filter engine is an explicit non-goal. With one consumer and two fixed rules it is speculative generality |
| A per-item `Candidate.is_eligible(blocked, muted)` | The rule is about the user's lists. The candidate would take both lists as parameters, and the lists' owner would be asking the item about the owner's own data |

## 7. Hard decision (b): who owns "the order" now

**Decision.** `rank_feed` remains the **one owner of the feed order**. It composes two private steps, and
each owns exactly one rule:

1. **Rank order.** Owner: the sort key in `rank_feed`, `(score.copy_negate(), item_id)`, copied from stage 1
   unchanged. It is the only place scores are compared and the only place ids break ties.
2. **Author-run limit.** Owner: `_limit_author_runs`. It is a **sequence constraint over the rank order**.
   It takes `Sequence[Candidate]` and nothing else, so it can use only **position** (the precedence) and
   **author**. It never reads a score and never compares ids. It cannot re-rank. It can only defer an item
   while the constraint forbids it, and omit a tail.

The score has one owner, `Weights.score`, and each item's `RankedItem.score` is that value unchanged. There
is no penalty term, no re-scoring and no second sort.

**How they relate, stated as an invariant:** the feed is a **subsequence-with-deferrals** of the rank order.
Two items by the same author always keep their rank order. An item is placed out of rank order only because
it was deferred, and only an author's third consecutive item is deferred. Deferred items keep their relative
order.

**The infeasible tail.** When every remaining item is by the author of the last two placed items, the loop
ends and those items are omitted. This is not a special case: it is the same "find the highest-ranked
placeable item" step finding none. There is no flag, no truncation parameter, and no count.

**Why this split.**
- **The known change axes land in different places.** The formula or the tie rule changes step 1 only. The
  limit or the key would change step 2 only (both are non-goals, so neither gets a seam, §2). The type
  boundary `Sequence[Candidate]` is what makes step 2 independent of step 1's key: it is the genericity
  ceiling applied to a private function.
- **Characterization falls out of it.** When the rank order has no run longer than 2, the head of
  `remaining` is always placeable, so step 2 is the identity. With empty lists, `eligible_candidates ==
  candidates`. Together these give stage 1's feed byte for byte.

**Rejected.**

| Alternative | Why not |
|---|---|
| Put diversity into the sort key (for example a run-position penalty) | A sequence constraint can't be a key: whether an item is placeable depends on what was placed before it. It would also be a penalty in the order, a second owner of the score's meaning |
| `_limit_author_runs(scored: Sequence[tuple[Candidate, Decimal]])` | Too specific. The arrangement doesn't need the score, and seeing it invites it to compare scores and become a second owner of order |
| A generic `limit_runs(items: Sequence[T], key: Callable[[T], K], max_run: int)` | Speculative generality. Diversity by another key and a configurable limit are both non-goals, and a `key` or `max_run` parameter with one caller is a knob no axis uses |
| A `diversity.py` module | One private function with one caller. `ranking.py` is where "the order" lives, and splitting its two steps across modules would divide ownership of the order's composition |
| Keep the pre-diversity order in `Feed` as well, or report omitted items | Not in the response, and no consumer (non-goal) |
| Append the infeasible tail, or reject the request | Both are handed-back choices the Guide already made: appending breaks the hard constraint, and rejecting fails a feed because of how its candidates happen to be distributed |
| A `diversify: bool` parameter on `rank_feed` | A flag argument. Diversity is unconditional product behavior |

## 8. Hard decision (c): what each item and the request carry, and who validates it

**Decision.** This keeps stage 1's grain: frozen value types validated in their own constructor, and
`from_mapping` for runtime key sets.

| New data | Carried by | Value rule owner | Key-set owner ("missing" / "unknown") |
|---|---|---|---|
| author | `Candidate.author: str` | `Candidate.__init__` via `_id` | `Candidate.from_mapping` (leading key) |
| topics | `Candidate.topics: frozenset[str]` | `Candidate.__init__` via `_id_set` | `Candidate.from_mapping` (leading key) |
| block list | `FeedRequest.blocked_authors: frozenset[str]` | `FeedRequest.__init__` via `_id_set` | `FeedRequest.from_mapping` |
| mute list | `FeedRequest.muted_topics: frozenset[str]` | `FeedRequest.__init__` via `_id_set` | `FeedRequest.from_mapping` |

- **Per-item rules live on the item, and whole-request rules live on the request.** This is the stage-1
  split: the signal and id rules are on `Candidate`, and duplicate ids are on `FeedRequest`. The lists belong
  to the request, not to any item, so `FeedRequest` validates them.
- **`_id` and `_id_set` are one owner of one fact.** The goals state "a non-empty string" for author and
  topic ids and list entries, and they state "repeated entries … mean the same as one entry" jointly for
  lists and topics. That is the same knowledge in five places, so it gets one home. The item id also becomes
  an `_id` call: the rule is the same, and moving it is a behavior-preserving refactor whose messages are
  pinned by the stage-1 tests. The helpers stay **private**, because nothing outside `request.py` validates
  ids.
- **`FeedRequest.from_mapping` is added** because the lists are *required* on the data path too. "Lists
  present" is a product rule (fail fast on a forgotten list), not a JSON-representation rule, so it belongs
  in the core, not in `cli`. This matches how `Candidate.from_mapping` owns the item key set. The CLI
  therefore keeps only representation checks: UTF-8, valid JSON, top level is an object.
- **Exact, case-sensitive matching** is `str` equality and `frozenset` membership. Nothing folds case or
  strips whitespace. `" "` is a valid id, as `" "` is a valid item id in stage 1.
- **The two lists are separate namespaces.** `blocked_authors` is compared only with `author`, and
  `muted_topics` only with `topics`. A topic `"x"` in the mute list does not hide author `"x"`.

## 9. CLI (changed: request shape; the output and exit codes are unchanged)

Invocation, reading order, output shape and the exit-code table are exactly as in DESIGN.md §8.

**Request:**

```json
{
  "user": "u1",
  "blocked_authors": ["mallory"],
  "muted_topics": ["spoilers"],
  "candidates": [
    {"id": "a", "author": "alice", "topics": ["cats", "tech"], "recency": 0.9, "affinity": 0.1, "popularity": 0.5},
    {"id": "b", "author": "bob",   "topics": [],               "recency": 0.2, "affinity": 0.9, "popularity": 0.9}
  ]
}
```

- All four top-level keys are required, and unknown top-level keys are rejected (by
  `FeedRequest.from_mapping`, assumption S2-3). Candidate keys are exactly `id`, `author`, `topics` and the
  three signals.
- The CLI's own check shrinks to: bytes are strict UTF-8, the text is JSON, and the top level is an object.
  All three map to exit 4, with message text owned by `cli`. Everything else, including "`candidates` is an
  array of objects" and "`user` is a string", is owned by `FeedRequest.from_mapping` and the constructors.
  Both are still exit 4, with the same messages.
- **Output is unchanged:** `{"weights_version": "w-…", "items": [{"id": "a", "score": "0.58"}, ...]}`.
  Removed and omitted items are absent, and there are no counts.

## 10. Rule → owner → entry paths (all rules)

Entry paths: **L** library `FeedService.rank`; **C** CLI; **S** startup; **R** `FeedService.reload`;
**D** internal `ranking.rank_feed`. Rows marked **(S2)** are new or changed.

| Rule | Owner (exactly one) | Paths |
|---|---|---|
| What a number is | `numbers.exact_number` | via `Weights` (S, R) and `Candidate` (L, C, D) |
| How a number is written | `numbers.canonical_text` | via `Weights.version` (L, C, D); C output |
| Constructor arity (every keyword present, none unknown) | Python's signature (`TypeError`) | direct `Weights(...)`, `Candidate(...)`, **`FeedRequest(...)`** in code |
| Weight names on data | `Weights.from_mapping` via `read_signal_fields` | S, R, any mapping caller |
| Weight values | `Weights.__init__` | S, R, direct |
| Config file readable, TOML, no duplicate keys | `config_file.load_weights_file` | S, R (file loader); C |
| Invalid at startup → refuse to start | `FeedService.__init__` | S; C exit 3 |
| Invalid on reload → keep last valid, report | `FeedService.reload` | R |
| One weight version per request | `FeedService.rank` (one read) + `Weights` immutability | L, C |
| Response carries the version used | `rank_feed` | L, C, D |
| Weight version identity | `Weights.version` | L, C, D |
| Change only on explicit reload | `FeedService` | S, R |
| score = w_r·r + w_a·a + w_p·p, exact, nothing else | `Weights.score`, in `EXACT` | L, C, D via `rank_feed` |
| **(S2)** Author and topics never affect the score | Structural: `Weights.score` reads only the three signals | L, C, D |
| Signal names on data | `Candidate.from_mapping` via `read_signal_fields` | C, any mapping caller |
| Signal values in [0, 1], never clamped | `Candidate.__init__` | L, C, D |
| Item id: a non-empty str | `Candidate.__init__` via `_id` | L, C, D |
| **(S2)** Item key set on data: exactly id, author, topics and the signals | `Candidate.from_mapping` via `read_signal_fields(leading=("id","author","topics"))` | C, any mapping caller |
| **(S2)** Author: exactly one, a non-empty str | `Candidate.__init__` via `_id` | L, C, D |
| **(S2)** Topics: a collection (not a string) of non-empty strs; repeats = one | `Candidate.__init__` via `_id_set` | L, C, D |
| **(S2)** What "an id" and "a set of ids" are (non-empty str; repeats fold) | `request._id`, `request._id_set` | via `Candidate`, `FeedRequest` (L, C, D) |
| No duplicate ids, across **all** candidates, eligible or not | `FeedRequest.__init__` | L, C, D |
| **(S2)** Block and mute lists: present | Signature (L, D: keyword-only, no default) / `FeedRequest.from_mapping` (C, mapping callers) | L, C, D |
| **(S2)** Request key set on data: exactly user, candidates, blocked_authors, muted_topics | `FeedRequest.from_mapping` | C, any mapping caller |
| **(S2)** List entries: a collection (not a string) of non-empty strs; repeats = one; empty allowed | `FeedRequest.__init__` via `_id_set` | L, C, D |
| **(S2)** Validity before eligibility (an invalid ineligible item rejects) | Structural: eligibility is a query on an already constructed, hence valid, `FeedRequest` | L, C, D |
| **(S2)** Eligibility: blocked author OR any muted topic → absent; exact, case-sensitive | `FeedRequest.eligible_candidates` | L, C, D (the only candidate read in `rank_feed`) |
| **(S2)** Rank order: score desc, id asc by code point; exact equality | The sort key in `rank_feed`, `(score.copy_negate(), item_id)` (the stage-1 "Order" rule, narrowed to the rank order) | L, C, D |
| **(S2)** No more than 2 consecutive items by one author; highest-ranked placeable first; deferred keep order | `ranking._limit_author_runs` with `MAX_SAME_AUTHOR_RUN` | L, C, D |
| **(S2)** Infeasible tail omitted, the feed ends | `ranking._limit_author_runs` (no placeable item → stop) | L, C, D |
| **(S2)** Feed order = run limit applied to rank order over eligible items | `rank_feed` (composition only) | L, C, D |
| Empty candidates → empty feed; **(S2)** all ineligible → empty feed | `rank_feed`, with no special case | L, C, D |
| `user` doesn't affect the result | Structural: nothing reads `request.user` | L, C, D |
| Response shape: items with own stage-1 score + version; no counts | `Feed` / `RankedItem` (unchanged) | L, C, D |
| Request JSON representation (UTF-8, JSON, top-level object) | `cli` | C only |
| CLI outcome → exit code and stderr | `cli.main` | C only |

No stage-1 rule changed owner, except the stage-1 "Order" row, which is deliberately split into rank order
(same owner, same key) and the run limit (new owner). The CLI's former checks of "`user` is a string" and
"`candidates` is an array of objects" duplicated rules that `FeedRequest` and its `from_mapping` own. They
now have that single owner.

## 11. Test plan (test-first; `unittest`)

**Order of work, as two moves (add-feature §0).** Stage 1 is not implemented yet, so the sequence is:
(0) build stage 1 exactly as in DESIGN.md with its §10 suite green. That suite is the characterization.
(1) Behavior-preserving refactor with the suite green and its expectations untouched: introduce `_id` for
the item id; add `FeedRequest.from_mapping` with the stage-1 key set and move the CLI's candidate-array
parsing into it, keeping the same messages; split `rank_feed` so the sort produces a `Sequence[Candidate]`
plus a score map. (2) The behavior change, test-first per module below.

**Characterization across the signature change.** Stage-1 tests build candidates and requests through one
fixture helper per type. In move (2) that helper alone gains `author=item_id` (all distinct, so no runs),
`topics=()` and empty lists. **No expected value is edited.** The stage-1 CLI scenario test gets the same
lift in its JSON fixture, and its stdout must stay byte-identical.

- **request / Candidate**
  - Author missing or unknown key (via `from_mapping`) → `item_id` set, `signal is None`.
  - Author `""`, `None`, `5` → rejected. Author `" "` accepted.
  - Topics `[]` accepted. `["a","a"]` equals `["a"]`, and the two Candidates compare equal.
  - Topics `"sports"` → rejected as a string, not split into letters. Topics `{"k": 1}`, `None`, `5`,
    `["", "x"]`, `["x", 3]` → rejected, naming `topics[i]`.
  - A generator of topics is accepted.
  - Missing keyword on the constructor → `TypeError`.
  - First-problem order: an item with a bad author and a bad signal reports the author.
- **request / FeedRequest**
  - Lists: empty accepted. Repeated entries fold. `"mallory"` as a bare string → rejected. Non-str or empty
    entry → `blocked_authors[i]` / `muted_topics[i]` named.
  - `FeedRequest("u1", cs)` without the lists → `TypeError`.
  - `from_mapping`: each of the four keys missing → rejected naming it. An unknown top-level key →
    rejected. `candidates` not a list → rejected. A candidate with no id → `candidates[i]:` prefix.
  - **Validity first:** a blocked item with `recency=1.2` → `InvalidRequest`. A muted item with a
    duplicate id of an eligible twin → `InvalidRequest` (duplicate id). A blocked item with a malformed
    topic → rejected.
  - **eligible_candidates:**
    - Blocked author → excluded.
    - One muted topic among several unmuted → excluded.
    - Empty topics → never muted.
    - `"Alice"` blocked does not exclude `"alice"`.
    - A topic id equal to a blocked author id does not exclude by topic, and vice versa (separate
      namespaces).
    - Input order is preserved.
    - All ineligible → `()`.
- **ranking** (the rank order is driven by weights `(1, 0, 0)` and descending recencies, so the tests
  state the rank order directly)
  - **Stage 1 (characterization):** the full §10 ranking suite still passes: ties, `"10"` before `"9"`,
    the trap pair, the near-tie that guards `copy_negate`, permutation invariance, `user` independence.
  - **Eligibility on path D:** the blocked item with the top score is absent, and the rest are in stage-1
    order with stage-1 scores. The same holds for an item with one muted topic.
  - **Diversity, the four goal examples:**
    - `a1 a2 a3 a4 b1 b2` → `a1 a2 b1 a3 a4 b2`
    - `a1 a2 a3 b1 c1` → `a1 a2 b1 a3 c1`
    - `a1 a2 a3` → `a1 a2`
    - `b1 a1 a2 a3` → `b1 a1 a2`
  - **Diversity, runs:**
    - A run of 1, and a run of exactly 2 → unchanged.
    - A run of exactly 3 followed by another author → the third is deferred by one.
    - Interleaving `a a b b a a b b` → unchanged.
    - Many authors: 5 authors with a random rank order (seeded) → the property holds (no three in a row;
      same-author pairs keep rank order; the output is rank order minus deferrals).
    - Single author with n=5 → the first two.
    - Single item → itself.
  - **Ties:**
    - Two items by *different* authors with equal scores keep id order.
    - Two items by the *same* author with equal scores keep id order after a deferral.
    - A tie across a deferral point: the deferred item goes after the tied placeable one, in id order.
  - **Filter before arrangement:** `a1[A] a2[A] x[B, blocked] a3[A]` → `a1 a2`. The blocked B does not
    break the run.
  - **Scores unchanged:** every `RankedItem.score` equals `weights.score(candidate)` and every item is an
    eligible candidate. The feed is a subsequence-with-deferrals of the rank order (the property check
    used on every diversity case).
  - **Characterization identity:** empty lists and distinct authors → `rank_feed` is equal to the stage-1
    expected `Feed` for the §10 cases.
- **service:** unchanged tests. Add one: a request with blocked items through `FeedService.rank` → absent
  (path L). The concurrency test runs with the stage-2 request shape.
- **cli (end to end):**
  - The JSON example of §9 → exit 0.
  - A blocked top-score item → absent from stdout.
  - Missing `muted_topics` → exit 4 naming it, stdout empty.
  - `topics: "x"` → exit 4.
  - Bad weights together with a bad list → exit 3 (weights still win).
  - All ineligible → `"items": []`, exit 0.
  - The infeasible-tail example → two items.
  - The goals.md stage-1 scenario lifted with distinct authors and empty lists → byte-identical stdout.

## 12. What was cut (subtractive pass) and concept fit

**Cut, each with no present force behind it:**
- **An `Exclusions` or `Eligibility` value type.** Its only consumer is `FeedRequest`, and it adds a public
  name and nested construction.
- **A `Filter` or `Rule` protocol, a list of predicates, a `Filter` passed to `rank_feed`.** A generic
  filter engine is a non-goal.
- **`key=` and `max_run=` parameters on the arrangement.** Diversity by another key and a configurable limit
  are non-goals.
- **A `diversity.py` module.** One private function, and its caller is the owner of the order.
- **`AuthorId` and `TopicId` types.** They have no rule beyond "non-empty str", which `_id` owns.
- **An `InvalidRequest.field` attribute, or widening `signal`.** No structural consumer.
- **New error types** (`IneligibleItem`, `DiversityInfeasible`). Absence is not an error, and there is no
  distinct handling.
- **`RankedItem.author`, removed or omitted counts, the pre-diversity order in `Feed`.** The response shape
  is unchanged, and reporting removals is a non-goal.
- **A `diversify` flag, a truncation parameter.** Flag arguments.
- **Defaults of `()` for the lists or for `topics`.** They would lie about "required" and restore the silent
  failure the PO chose against.
- **Eligibility in `FeedService` or `cli`.** It would be bypassed on other paths.
- **`FeedRequest` dropping ineligible candidates at construction.** See §6.
- **A per-item `admits(c)` predicate.** No consumer.
- **A deque-based O(n) arrangement.** No stated performance need. It can be added behind the same private
  signature.

**Kept, with the force behind each:**
- `Candidate.author` and `.topics`: the new rules read them.
- `FeedRequest.blocked_authors` and `.muted_topics`: the lists travel with the request, and nothing is
  stored.
- `FeedRequest.eligible_candidates`: the one owner of eligibility, reached by every path through
  `rank_feed`.
- `FeedRequest.from_mapping`: "lists required" on the data path is a product rule, and runtime key sets
  live in `from_mapping` (stage-1 grain).
- `_id` and `_id_set`: one home for "id" and "set of ids", stated jointly by the goals for five fields.
- `_limit_author_runs`: the one owner of the sequence constraint. Its `Sequence[Candidate]` type keeps it
  from becoming a second owner of order.
- `MAX_SAME_AUTHOR_RUN`: names the product's 2, and it is used in exactly one place.
- The str and Mapping refusal in `_id_set`: without it, `topics="sports"` would be silently read as six
  one-letter topics. That is a present, stated case ("malformed topics → rejected").

**Concept fit:**
- **Eligibility is a filter.** It is a subset query on the request that runs before scoring. Nothing is
  scored `-inf`, and there is no placeholder item.
- **Diversity is a sequence constraint.** It arranges an ordered sequence by position and author, and it
  leaves scores and the sort key alone. There is no penalty term.
- **The infeasible tail** is the constraint's own "nothing placeable" outcome, not a truncation rule.
- **`topics` and the lists are sets** because repeats and order carry no meaning.
- **An empty feed** is still a `Feed` with no items.

## 13. Assumptions added in stage 2 (each a simple default)

- **S2-1.** `topics` and the lists accept any iterable except a string or a mapping, which are refused
  rather than guessed at. They are stored as `frozenset`, so two candidates that differ only in topic order
  or repeats are equal.
- **S2-2.** Index-located messages (`topics[i]`, `blocked_authors[i]`) use the position in the input as
  iterated, which is the JSON array index on the CLI.
- **S2-3.** Unknown top-level request keys are rejected. This is consistent with unknown candidate keys
  (stage-1 assumption 3), and it fails fast on a misspelled `blocked_author`.
- **S2-4.** `FeedRequest` reports the first problem in field order: user, duplicate ids, `blocked_authors`,
  `muted_topics`.
- **S2-5.** The arrangement is quadratic in the worst case. No performance requirement is stated.
