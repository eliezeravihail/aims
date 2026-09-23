# Design Y — stage 2



<!-- file: proposal.md -->

# Proposal

## Why

Stage 1 ranks purely on signals. Users now need control over what they see: authors they have blocked and
topics they have muted must never reach their feed. The feed must also not be dominated by one author in a
row. Both rules apply to the same ranking request, and the operator-tunable weighted scoring stays as it is.

## What Changes

- **BREAKING (request shape):** each candidate now requires an `author` (non-empty string) and a `topic` (one
  non-empty string). The request gains two optional lists, `blocked_authors` and `muted_topics` (non-empty
  strings, default empty). Stage-1 requests without `author`/`topic` are rejected.
- **Eligibility:** a candidate whose `author` is in `blocked_authors`, or whose `topic` is in `muted_topics`, is
  absent from the response, whatever its score. Matching is exact and case-sensitive. The response does not
  count excluded items or give a reason for them.
- **Diversity:** the returned order never contains more than 2 consecutive items from the same author. Within
  that hard limit, the order stays as close to stage-1 score order as possible. An item that would be the third
  in a row is deferred to the next position where it fits.
- **BREAKING (completeness):** when the remaining eligible items cannot all be placed without breaking the
  limit (one author outnumbers everyone else), the lowest-ranked surplus items of that author are omitted. The
  response is then shorter than the eligible set. Stage 1 promised "every candidate exactly once". Stage 2
  promises "each eligible candidate at most once, and only the unavoidable surplus of a single author is
  omitted".
- Excluded candidates are still validated: a malformed blocked or muted candidate still rejects the whole
  request.
- Unchanged: the weighted-sum formula, exact arithmetic, the `item_id` tie-break, weight configuration and
  reload, and the response entry shape (`item_id`, `score`).

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `feed-ranking`: the request contract gains `author`, `topic`, `blocked_authors` and `muted_topics`.
  Completeness weakens from "every candidate" to "eligible candidates, minus the unavoidable same-author
  surplus". Plain score ordering becomes score ordering under a max-2-in-a-row author constraint. Validation
  covers the new fields. New requirements cover eligibility exclusion, the diversity limit and the surplus
  omission rule.

`ranking-config` is not affected. Weights, their file, validation and reload behave exactly as before, and the
diversity limit is not operator-configurable.

## Impact

- The request model gains fields and validation. Two new pure pipeline stages (eligibility filter and
  diversity arrangement) sit around the unchanged scoring core. `FeedService` composes them. The CLI's input
  JSON gains the new fields, and its output format is unchanged.
- Callers must send `author` and `topic` on every candidate. That is a breaking input change, and there are no
  known consumers yet.
- Still standard library only, with no new dependencies. There is still no persisted state: block and mute
  lists arrive with each request.


<!-- file: specs/feed-ranking/spec.md -->

# Spec Delta

Notation in scenarios: "score order `a1, a2, b1`" means those candidates are eligible and their stage-1 order
(score descending, then `item_id` ascending) is as listed. Items named `aN` have author `A`, `bN` author `B`,
and so on.

## MODIFIED Requirements

### Requirement: Rank request contract
The service SHALL accept a rank request made of a `user` identifier, a list of candidate items, and optionally
the user's `blocked_authors` and `muted_topics`. Each is a list of strings and defaults to empty when absent.
Each candidate SHALL have a string `item_id`, a string `author`, a string `topic` and the numeric signals
`recency`, `affinity` and `popularity`. The service SHALL return each eligible candidate at most once, in ranked
order. Every eligible candidate SHALL be returned, except those omitted by the same-author surplus rule.
Ineligible candidates SHALL NOT be returned. Each returned entry SHALL carry the candidate's `item_id` and its
computed `score`.

#### Scenario: All candidates returned once
- **WHEN** a request contains candidates `a`, `b` and `c` with valid fields, three different authors, and no blocked authors or muted topics
- **THEN** the response contains exactly three entries, one each for `a`, `b` and `c`

#### Scenario: Empty candidate list
- **WHEN** a request contains a valid `user` and no candidates
- **THEN** the service returns an empty ordered feed and no error

#### Scenario: Block and mute lists omitted
- **WHEN** a request has no `blocked_authors` and no `muted_topics`
- **THEN** every candidate is eligible

### Requirement: Order by score descending
The service SHALL order the returned entries by score, highest first, subject only to the same-author run limit.
Where the limit forces an item out of score order, every other item SHALL keep its score order.

#### Scenario: Higher score first
- **WHEN** candidate `a` scores 0.8 and candidate `b` scores 0.4, and they have different authors
- **THEN** `a` appears before `b` in the response

#### Scenario: Diversity does not reorder when not needed
- **WHEN** the score order is `a1, a2, b1, a3, b2`
- **THEN** the response order is `a1, a2, b1, a3, b2`

### Requirement: Candidate validation
The service SHALL reject the whole request with a validation error that names the offending item and field, and
SHALL NOT return a partial feed, when any of the following is true:
- a signal is missing, is not a real number (booleans, NaN and infinities count as not real), or is outside
  [0.0, 1.0];
- an `item_id` is missing or empty;
- two candidates share the same `item_id`;
- an `author` or `topic` is missing, is not a string, or is empty;
- `blocked_authors` or `muted_topics` is present but is not a list, or contains an entry that is not a non-empty
  string (the error names the field and the offending position).

Every candidate SHALL be validated, including those that the block or mute lists would exclude.

#### Scenario: Out-of-range signal rejected
- **WHEN** a candidate has `popularity` 1.2
- **THEN** the request fails with a validation error naming that candidate and `popularity`, and no feed is returned

#### Scenario: Missing signal rejected
- **WHEN** a candidate has no `affinity` value
- **THEN** the request fails with a validation error naming that candidate and `affinity`

#### Scenario: Duplicate item id rejected
- **WHEN** two candidates both have `item_id` `a`
- **THEN** the request fails with a validation error naming the duplicate id

#### Scenario: Boundary values accepted
- **WHEN** a candidate has signals exactly 0.0 and 1.0
- **THEN** the candidate is accepted and scored

#### Scenario: Missing author rejected
- **WHEN** a candidate has no `author`
- **THEN** the request fails with a validation error naming that candidate and `author`

#### Scenario: Topic list instead of string rejected
- **WHEN** a candidate has `topic` `["sports", "news"]`
- **THEN** the request fails with a validation error naming that candidate and `topic`

#### Scenario: Malformed excluded candidate still rejects the request
- **WHEN** a candidate by a blocked author has `recency` 1.5
- **THEN** the request fails with a validation error naming that candidate and `recency`

#### Scenario: Malformed block list rejected
- **WHEN** `blocked_authors` is `["alice", ""]`
- **THEN** the request fails with a validation error naming `blocked_authors`

## ADDED Requirements

### Requirement: Blocked authors and muted topics are excluded
A candidate SHALL be ineligible when its `author` exactly equals (case-sensitive) an entry of `blocked_authors`,
or its `topic` exactly equals (case-sensitive) an entry of `muted_topics`. An ineligible candidate SHALL NOT
appear anywhere in the response, whatever its score. The response SHALL NOT report ineligible candidates in any
form: no count, no placeholder and no reason. Ineligible candidates SHALL NOT take part in the same-author run
limit. They neither separate nor extend a run.

#### Scenario: Blocked author excluded despite top score
- **WHEN** candidate `x` has the highest score and its author is in `blocked_authors`
- **THEN** `x` does not appear in the response and the other candidates are returned in ranked order

#### Scenario: Muted topic excluded
- **WHEN** candidate `y` has topic `politics` and `muted_topics` is `["politics"]`
- **THEN** `y` does not appear in the response

#### Scenario: Matching is case-sensitive
- **WHEN** candidate `z` has author `Alice` and `blocked_authors` is `["alice"]`
- **THEN** `z` is eligible and appears in the response

#### Scenario: All candidates excluded
- **WHEN** every candidate is from a blocked author or on a muted topic
- **THEN** the service returns an empty ordered feed and no error

#### Scenario: Excluded item does not separate a run
- **WHEN** the candidates in score order are `a1, a2, m1, a3, b1`, and `m1` is on a muted topic
- **THEN** the response order is `a1, a2, b1, a3`

### Requirement: No more than two consecutive items from the same author
In the returned order, no three consecutive entries SHALL share the same `author`. The service SHALL build the
order position by position. At each position it SHALL place the highest-ranked remaining eligible item that
satisfies both conditions:
- placing it does not make three consecutive entries from the same author; and
- the items still remaining can then be placed without breaking the limit.

A skipped item keeps its place in the queue and is reconsidered at the next position. The result is
deterministic for a given request and weights.

#### Scenario: Third consecutive item deferred
- **WHEN** the score order is `a1, a2, a3, b1`
- **THEN** the response order is `a1, a2, b1, a3`

#### Scenario: Deferred item placed at the next valid position
- **WHEN** the score order is `a1, a2, a3, a4, b1, b2`
- **THEN** the response order is `a1, a2, b1, a3, a4, b2`

#### Scenario: Other author deferred to keep the feed complete
- **WHEN** the score order is `a1, b1, a2, a3, a4`
- **THEN** the response order is `a1, a2, b1, a3, a4`, because placing `b1` second would leave `a2, a3, a4` impossible to place

#### Scenario: Input order still does not affect output
- **WHEN** the same set of candidates, including several by the same author, is submitted twice in different orders with the same weights
- **THEN** both responses have the identical order

### Requirement: Unplaceable same-author surplus is omitted
The same-author run limit is hard and SHALL never be broken. When one author's eligible items outnumber what
the limit allows, the service SHALL omit that author's lowest-ranked surplus items and return the rest. The
limit allows at most `2 × (k + 1)` items from one author, where `k` is the number of eligible items from all
other authors. The service SHALL omit only that surplus. It SHALL NOT omit any other eligible item, and it SHALL
NOT report the omission.

#### Scenario: Single author only
- **WHEN** the score order is `a1, a2, a3`
- **THEN** the response order is `a1, a2`

#### Scenario: One author outnumbers the rest
- **WHEN** the score order is `a1, a2, a3, a4, a5, b1`
- **THEN** the response order is `a1, a2, b1, a3, a4`, and `a5` is omitted

#### Scenario: Surplus limit reached exactly
- **WHEN** the score order is `a1, a2, a3, a4, b1`
- **THEN** the response order is `a1, a2, b1, a3, a4`, and nothing is omitted


<!-- file: design.md -->

# Design

## Context

Stage 1 (archived as `2026-09-23-add-feed-ranking`) established this pipeline: the edges validate raw input into
immutable values, a pure core scores and sorts, `FeedService` takes one weights snapshot per request and
orchestrates, and the CLI is a thin adapter. Weight configuration is a separate edge (`WeightsProvider`). See
`proposal.md` for why stage 2 exists, and `specs/feed-ranking/spec.md` for the exact behavior. The substrate is
unchanged: Python 3.11+, standard library only, single process, no persistence.

The stage-1 core ends at `rank(weights, candidates) -> list[RankedItem]`, and its output is the final feed.
Stage 2 adds one step before that ordering (drop ineligible items) and one step after it (rearrange for author
diversity, possibly omitting a surplus). The question is where those two rules live so that each keeps a single
owner, and so that the stage-1 scoring rules stay untouched.

## Goals / Non-Goals

**Goals:**
- Each new rule has exactly one owner. The eligibility predicate is owned by one pure function, and the run
  limit with its surplus policy by another.
- Scoring and the score-order sort stay byte-for-byte the stage-1 rules. Diversity consumes score order and does
  not redefine it.
- The pipeline stays a composition of pure functions, testable without files, weights providers or a clock.

**Non-Goals:**
- Stored or server-side user preferences. The block and mute lists arrive in the request, because the substrate
  has no persistence.
- Operator-configurable run length, per-topic diversity, or diversity on any key other than author. None of
  these were asked for, so `MAX_SAME_AUTHOR_RUN = 2` is a constant, not config.
- Reporting excluded or omitted items. The product owner said they "do not exist" in the output.
- Case folding, Unicode normalization, author aliasing and topic hierarchies.

## Architecture

```
  CLI (adapter)            Library caller (adapter)
      |                           |
      +------------+--------------+
                   v
          +------------------+   snapshot()   +----------------------+
          |   FeedService    |--------------->|   WeightsProvider    |  (unchanged)
          | (orchestration)  |                +----------------------+
          +--------+---------+
                   | parse_request(raw)
                   v
          +---------------------------+
          | request model             |  Candidate(+author, +topic)
          | (validation, all items)   |  RankRequest(+exclusions: Exclusions)
          +------------+--------------+
                       |
    ================== | ============ pure pipeline ==========================
                       v
          +---------------------------+
      1.  | eligibility               |  is_eligible(c, excl) -> bool
          | filter_eligible(cs, excl) |  owns: block/mute predicate
          +------------+--------------+
                       v  eligible candidates
          +---------------------------+
      2.  | ranking core (unchanged)  |  score(w, c); order key (-score, item_id)
          | rank(w, cs)               |  owns: formula + tie-break
          +------------+--------------+
                       v  list[Scored] in score order
          +---------------------------+
      3.  | diversity                 |  arrange(seq, author_of) -> list
          | arrange(...)              |  owns: max-2 run limit, lookahead,
          +------------+--------------+        surplus omission
                       v
             [RankedItem(item_id, score), ...]
```

### Components and the rules they own

| Component | Owns (new/changed in bold) | Does not know about |
|---|---|---|
| request model | Candidate validity, **plus `author`/`topic` non-empty strings**; **`Exclusions` validity (lists of non-empty strings, default empty)**; unique ids across *all* candidates | Which items will be excluded, scoring, order |
| `eligibility` (**new**) | **The exclusion predicate: author in blocked set, or topic in muted set, compared exactly** | Scores, order, authors' adjacency |
| ranking core | Weighted-sum formula; order `(-score, item_id)`. **The only change is that it returns `Scored(candidate, score)` so later stages can still see `author`** | Eligibility, diversity |
| `diversity` (**new**) | **The run limit (`MAX_SAME_AUTHOR_RUN = 2`), the placement rule (highest-ranked feasible item), the feasibility test, the surplus-omission policy** | Scores, weights, what "author" means beyond an opaque key |
| `FeedService` | Composition order: parse, then filter, then rank, then arrange, then project to `RankedItem` | The rules inside each stage |
| CLI | Reads the extended request JSON, prints the unchanged output | Everything else |

Illustrative boundary signatures (not an implementation):

```python
@dataclass(frozen=True)
class Candidate:   item_id: str; author: str; topic: str; signals: Mapping[str, Decimal]
@dataclass(frozen=True)
class Exclusions:  blocked_authors: frozenset[str]; muted_topics: frozenset[str]
@dataclass(frozen=True)
class RankRequest: user: str; candidates: tuple[Candidate, ...]; exclusions: Exclusions
@dataclass(frozen=True)
class Scored:      candidate: Candidate; score: Decimal

# eligibility.py
def is_eligible(c: Candidate, ex: Exclusions) -> bool
def filter_eligible(cs: Sequence[Candidate], ex: Exclusions) -> list[Candidate]

# ranking core
def rank(weights: Weights, cs: Sequence[Candidate]) -> list[Scored]   # score order

# diversity.py
MAX_SAME_AUTHOR_RUN = 2
def arrange(ordered: Sequence[T], author_of: Callable[[T], str]) -> list[T]

# FeedService.rank(raw) ==
#   w = provider.snapshot(); req = parse_request(raw)
#   ordered = rank(w, filter_eligible(req.candidates, req.exclusions))
#   return [RankedItem(s.candidate.item_id, s.score)
#           for s in arrange(ordered, lambda s: s.candidate.author)]
```

## Decisions

### D1. Filter before scoring, as a separate pure stage
Eligibility is a yes/no predicate on one candidate and the request's exclusions, and it does not depend on
scores or neighbors. Running it first means ineligible items never enter the ordering, which gives these
properties by construction:
- they can't be "shown low" (spec: absent, not demoted);
- they can't separate or extend a same-author run (spec scenario "Excluded item does not separate a run");
- they can't count toward the surplus limit `k`.

It lives in its own module, not in `rank`, because `rank` owns relevance and eligibility is a user policy. When
more policies arrive (for example, age gating), they join the predicate and do not touch scoring.
*Alternatives:* (a) a score of −∞ or 0 for excluded items. Rejected: they would still be present, which violates
"never appear". (b) Filter at parse time inside `parse_request`. Rejected: that would mix validation with
policy, and would make the rule "validate excluded items too" depend on the order of statements in one
function.

### D2. Validate every candidate, including those that will be excluded
The product owner left this open. We validate all candidates (whole request rejected on any error, as in stage
1) because:
- validation stays a single pass with a single owner and no dependency on the exclusion lists;
- duplicate-`item_id` detection covers the whole payload, so an eligible item can never silently shadow an
  excluded one;
- a malformed upstream payload surfaces even when the user happens to block its author.

The cost is that a user can get a validation error "caused by" an item they would never see. That is an upstream
defect, and stage 1 already chose loud over silent (stage-1 D3).

### D3. Diversity is a post-order rearrangement over an opaque key
`arrange` receives the list already in score order and a key function. It knows nothing about scores or
weights. It only knows "earlier in the input means preferred". That keeps two owners separate: the ranking core
defines *preference* (score, then `item_id`), and diversity defines *admissibility* of a sequence. Because
`arrange` is deterministic and its input order is already total and independent of input order (stage-1 D1),
the "input order does not affect output" guarantee carries through unchanged. It is generic over `T` and a key,
so it is testable with plain strings like `"a1"`.
*Alternative:* fold diversity into the sort key. Rejected: a run limit depends on neighbors, so no per-item key
can express it.

### D4. Placement rule: greedy by rank, with a feasibility lookahead
At each position, `arrange` takes the highest-ranked remaining item whose placement (i) does not create a third
consecutive same-author item and (ii) leaves the remaining items still arrangeable. The feasibility test (ii) is
a pure counting check. With `R` the remaining items, `L` the author at the end of the output so far and `r` the
length of its current run (0, 1 or 2), the remaining items are arrangeable iff for every author `X`:

```
count_R(X)  <=  2 * (|R| - count_R(X)) + 2 - (r if X == L else 0)
```

(Each of X's runs is at most 2 long and runs are separated by other items. That gives `|R|-count+1` slots, and
the first slot is shortened when X continues the current run.) The condition was checked against exhaustive
enumeration for all sequences of up to 7 items over 3 authors. Task 3.2 turns this into a permanent test.

Why the lookahead and not the plain "skip the third, take the next" greedy:
- Plain greedy can strand items that a different valid order would have kept. With score order
  `a1, b1, a2, a3, a4`, plain greedy produces `a1, b1, a2, a3` and then cannot place `a4`. Because the limit is
  hard (product owner Q1), `a4` would have to be dropped. With lookahead, `b1` is deferred once, and all five
  are returned: `a1, a2, b1, a3, a4`.
- Whenever plain greedy would place every item, the lookahead makes exactly the same choices. It was verified
  exhaustively up to 8 items over 3 authors, and it holds by construction: plain greedy's choice has a valid
  completion, so it is feasible, so it is also the highest-ranked feasible choice. In the common case, the
  behavior is literally the spec's "defer to the next available position".

Complexity: each position scans the queue until it finds a feasible item. The check is O(1) with maintained
per-author counts plus the current maximum, so the worst case is O(n²) and typically near O(n). At hundreds to
low thousands of candidates this is negligible. No index structures are needed.

### D5. Unsatisfiable input: omit the minimal surplus, lowest-ranked first
The product owner made the limit hard and left the unsatisfiable case to us. Rules:
- Before placement, `arrange` checks the whole eligible set with the same condition (`r = 0`). At most one author
  can violate it. If author `X` has `m` items and the others have `k` in total with `m > 2(k+1)`, `X`'s items
  ranked below the first `2(k+1)` are dropped. The remaining set is then feasible, so the D4 loop never gets
  stuck and never drops anything else.
- It drops the *lowest-ranked* surplus because that keeps "score order as much as possible".
- The number of dropped items is the minimum possible: condition (ii) is necessary, so no arrangement keeps more.
- The omission is silent (proposal: omitted items do not exist in the output), which is consistent with how the
  product owner treats excluded items.

*Alternatives:* (a) append the leftovers at the tail, breaking the rule. Rejected: the product owner called the
limit hard. (b) Reject the request with an error. Rejected: a user who follows only one author would get no
feed at all, which is a worse outcome than a short feed. (c) Plain greedy and drop whatever gets stranded.
Rejected in D4: it drops more than necessary, including items that could have been kept.

### D6. Input shape and matching
- `author` and `topic` are required, non-empty strings on every candidate. There is a single topic, not a list:
  a list is a data-model choice nobody asked for, and a single string keeps the predicate trivially clear. If
  multi-topic items appear later, `is_eligible` becomes "any topic muted", and that change stays local to the
  eligibility module and the request model.
- `blocked_authors` and `muted_topics` are optional request fields, default empty, held as `frozenset` in
  `Exclusions`. Duplicate entries are harmless. Entries must be non-empty strings, and anything else is rejected
  with an error naming the field and position.
- Matching is exact string equality: case-sensitive, with no trimming and no normalization. Upstream owns
  canonical ids. Folding case would be a silent product decision (for example, `Alice` versus `alice` could be
  different accounts).
- `user` is still carried and not used. Exclusions travel with the request, not keyed by `user`, because there is
  no store.

### D7. The response shape is unchanged
Entries remain `{item_id, score}`. After a diversity deferral, scores in the response are no longer monotonic.
This is expected and visible (for example, `b1` with a lower score appears before `a3`). We do not add `author`,
`position reason` or omission counts: nobody asked for them, and the caller already knows each item's author.

### D8. CLI
Same command and exit codes. The input JSON gains `author` and `topic` per candidate and the optional top-level
lists. A request error (including new-field errors) exits with 2. No new flags.

## Assumptions (stated where the product owner said "choose")

- An unsatisfiable run limit omits the minimal lowest-ranked surplus of the single dominant author, silently (D5).
- Each candidate has exactly one `topic`. Matching is exact and case-sensitive (D6).
- Excluded candidates are validated like all others (D2).
- The run limit applies to eligible items only. Excluded items do not separate runs (D1).
- The run limit is fixed at 2 and is not operator-tunable.

## Risks / Trade-offs

- [The lookahead makes the order less obvious than "skip the third": a non-dominant item can move later] → This
  happens only when plain greedy would otherwise drop content. The behavior is identical in every case where
  plain greedy succeeds (D4). Spec scenario "Other author deferred to keep the feed complete" documents it.
- [The feasibility condition is subtle, and a wrong derivation would drop or strand items] → Task 3.2 checks it
  against brute-force enumeration, and `arrange` asserts that it never gets stuck after trimming.
- [Existing stage-1 callers break (new required fields)] → No known consumers. The break is declared in the
  proposal. Making the fields optional would silently disable blocking and diversity for such callers, which is
  worse.
- [A short feed can surprise a caller that expects `len(out) == len(eligible)`] → The spec now states the only
  case where this happens (single-author surplus).
- [An upstream sends inconsistent casing for authors, so a block fails to apply] → Exact match is documented.
  Normalization is an explicit future decision, not a hidden one.

## Migration Plan

Additive code, but a breaking request contract. Callers must send `author` and `topic`. There is no data
migration and no config change (`ranking-config` is untouched). Rollback is reverting the change. Stage-1 weight
files remain valid in both directions.


<!-- file: tasks.md -->

# Tasks

## 1. Request model

- [ ] 1.1 Add required `author` and `topic` (non-empty strings) to `Candidate` and its parsing, and verify tests for "Missing author rejected", "Topic list instead of string rejected", and that errors name the item and field
- [ ] 1.2 Add the frozen `Exclusions` value (`blocked_authors`, `muted_topics` as `frozenset[str]`, default empty) to `RankRequest` and `parse_request`, rejecting non-list values and entries that are not non-empty strings, and verify tests for "Block and mute lists omitted" and "Malformed block list rejected"
- [ ] 1.3 Confirm validation covers every candidate regardless of exclusions, and verify the "Malformed excluded candidate still rejects the request" test and a test that duplicate ids across an excluded and an eligible item are rejected

## 2. Eligibility

- [ ] 2.1 Implement pure `is_eligible` / `filter_eligible` in a new eligibility module (exact, case-sensitive author/topic membership), and verify tests for "Blocked author excluded despite top score", "Muted topic excluded", "Matching is case-sensitive" and "All candidates excluded"

## 3. Diversity

- [ ] 3.1 Change `rank` to return `Scored(candidate, score)` in score order without changing the formula or sort key, and verify all stage-1 ranking tests still pass after adapting them to the new return type
- [ ] 3.2 Implement the feasibility predicate from design D4 as a standalone function, and verify with a test comparing it to brute-force permutation search over all author multisets of up to 7 items, 3 authors and every tail state
- [ ] 3.3 Implement `arrange(ordered, author_of)` with `MAX_SAME_AUTHOR_RUN = 2`: minimal lowest-ranked surplus trim (D5), then greedy placement with lookahead (D4). Verify tests for every scenario in "No more than two consecutive items from the same author" and "Unplaceable same-author surplus is omitted", plus a property test over random sequences that the output never has 3 in a row, is a subsequence-preserving permutation of the kept items, drops only the minimal surplus, and equals plain skip-the-third greedy whenever that greedy places everything

## 4. Service and CLI

- [ ] 4.1 Compose `FeedService.rank` as parse, filter, rank, arrange, then project to `RankedItem` (one weights snapshot per request, as before), and verify tests for "Excluded item does not separate a run", "Diversity does not reorder when not needed", "All candidates returned once" and "Input order still does not affect output" with same-author candidates
- [ ] 4.2 Extend the CLI input handling to the new fields (output and exit codes unchanged), and verify subprocess tests: a blocked item is absent, a same-author triple is deferred, and a missing `author` exits 2
- [ ] 4.3 Update the README request format (new fields, exact matching, the run limit, the surplus-omission rule), and verify its example request runs through the CLI and produces the documented output

## 5. Integration check

- [ ] 5.1 End to end with weights 0.5/0.3/0.2: run the CLI on a request mixing blocked, muted and same-author items, and verify the output matches a hand-computed expectation; then edit the weights file, re-run, and verify the order changes as predicted and diversity and eligibility still hold
