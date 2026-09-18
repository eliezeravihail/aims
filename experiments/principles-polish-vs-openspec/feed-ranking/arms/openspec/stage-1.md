# Stage 1 — Ordered Feed Ranking (OpenSpec)

> Method: OpenSpec. Durable capability **specs** (Purpose + Requirements + Scenarios)
> are the behavioral contract; a **change bundle** (proposal.md / design.md / tasks.md)
> introduces the change. This file is the frozen stage-1 baseline.

---

# PART A — CAPABILITY SPECS (`openspec/specs/`)

Stage 1 defines two capabilities:

- `feed-ranking` — combine signals into a score and order candidates.
- `ranking-weights` — operator-tunable configuration for the signal weights.

---

## `openspec/specs/feed-ranking/spec.md`

### Purpose

Given a user and a list of candidate items — each carrying a `recency`, `affinity`, and
`popularity` signal in `[0, 1]` — produce a single ordered feed for that user, with the
most relevant item first. Relevance is a single scalar score computed by a weighted
combination of the three signals; the weights are supplied by the `ranking-weights`
capability. The ordering is deterministic and stable: equal-scoring items are ordered
by a stable item id so the same input always yields the same output.

This capability owns *scoring* and *ordering*. It does not own where weights come from
(that is `ranking-weights`), nor does it filter, remove, or re-arrange items for reasons
other than score (there are none in stage 1).

### Requirements

#### Requirement: Score is a weighted sum of the three signals

The system SHALL compute, for each candidate item, a scalar score equal to
`w_recency * recency + w_affinity * affinity + w_popularity * popularity`, where the
three weights are provided by the `ranking-weights` capability and each signal is the
value carried on that candidate.

##### Scenario: Signals combined with configured weights

- **Given** weights `recency=0.5, affinity=0.3, popularity=0.2`
- **And** a candidate with `recency=1.0, affinity=0.0, popularity=0.0`
- **When** the feed is ranked
- **Then** that candidate's score is `0.5`.

##### Scenario: All three signals contribute

- **Given** weights `recency=0.5, affinity=0.3, popularity=0.2`
- **And** a candidate with `recency=0.4, affinity=1.0, popularity=0.5`
- **When** the feed is ranked
- **Then** that candidate's score is `0.5*0.4 + 0.3*1.0 + 0.2*0.5 = 0.6`.

#### Requirement: Candidates returned in descending score order

The system SHALL return every input candidate exactly once, ordered by descending score
(highest score first). No candidate is added, dropped, or duplicated.

##### Scenario: Higher score ranks earlier

- **Given** candidate `A` scores `0.7` and candidate `B` scores `0.4`
- **When** the feed is ranked
- **Then** the returned order is `[A, B]`.

##### Scenario: Every input appears in the output

- **Given** an input of `N` candidates
- **When** the feed is ranked
- **Then** the output contains exactly those `N` candidates, none missing and none added.

#### Requirement: Ties break by stable item id

The system SHALL break ties between equal-scoring candidates by ascending item id,
using a total, stable ordering so that identical input always yields identical output.

##### Scenario: Equal scores ordered by id

- **Given** candidates `id=item-9` and `id=item-2` both score `0.5`
- **When** the feed is ranked
- **Then** the returned order places `item-2` before `item-9`.

##### Scenario: Determinism across runs

- **Given** the same user, candidates, and weights
- **When** the feed is ranked twice
- **Then** the two returned orderings are identical.

#### Requirement: Signals are treated as given, within `[0, 1]`

The system SHALL treat each incoming signal value as authoritative in the range
`[0, 1]`. A value outside `[0, 1]` is a malformed request and the system SHALL reject
the request rather than silently clamp or reweight.

##### Scenario: Out-of-range signal rejected

- **Given** a candidate with `affinity=1.4`
- **When** the feed is ranked
- **Then** the request is rejected as malformed and no partial ordering is returned.

#### Requirement: Empty candidate list yields an empty feed

The system SHALL return an empty ordered feed when given an empty candidate list,
without error.

##### Scenario: No candidates

- **Given** an empty candidate list
- **When** the feed is ranked
- **Then** the returned feed is empty and the request succeeds.

---

## `openspec/specs/ranking-weights/spec.md`

### Purpose

Provide the three signal weights (`recency`, `affinity`, `popularity`) that the
`feed-ranking` capability uses, as **per-deployment configuration** that an operator can
change without a code change. Weight changes take effect for subsequent requests.

### Requirements

#### Requirement: Weights are deployment configuration, not code

The system SHALL read the three signal weights from a deployment configuration source
(e.g. an environment/config value per deployment), such that an operator can change a
weight and have it take effect without modifying or redeploying application code.

##### Scenario: Operator changes a weight

- **Given** the deployment is configured with `recency=0.5, affinity=0.3, popularity=0.2`
- **When** an operator changes the configuration to `recency=0.2, affinity=0.3, popularity=0.5`
- **And** a new request is ranked
- **Then** the new request uses the updated weights, with no code change.

#### Requirement: Weight set is validated on load

The system SHALL validate the configured weights on load: all three MUST be present and
non-negative, and at least one MUST be positive. An invalid weight set is rejected at
load time so a request never runs against unusable configuration.

##### Scenario: Missing weight rejected

- **Given** configuration providing only `recency` and `affinity`
- **When** the configuration is loaded
- **Then** loading fails with a clear error, and the previous valid configuration (if any) stays in effect.

##### Scenario: All-zero weights rejected

- **Given** configuration `recency=0, affinity=0, popularity=0`
- **When** the configuration is loaded
- **Then** loading fails with a clear error.

#### Requirement: Weights need not sum to one

The system SHALL accept any valid non-negative weight set regardless of sum; ordering
depends only on relative weights, so normalization is not required for correctness.

##### Scenario: Un-normalized weights still order correctly

- **Given** weights `recency=5, affinity=3, popularity=2`
- **When** the feed is ranked
- **Then** the resulting order is identical to weights `0.5, 0.3, 0.2` (same relative proportions).

---

# PART B — CHANGE BUNDLE (`openspec/changes/add-feed-ranking/`)

## `proposal.md`

### Why

Users need a single ordered feed rather than a raw candidate list. Product wants the
mix of freshness, author closeness, and popularity to be **tunable per deployment** by
operators (different markets/surfaces weight signals differently) without shipping code.

### What changes

- **Add** capability `feed-ranking`: score each candidate by a weighted sum of its
  `recency`, `affinity`, `popularity` signals and return candidates in descending score
  order, ties broken by stable item id.
- **Add** capability `ranking-weights`: the three weights as validated per-deployment
  configuration, changeable by an operator without a code change.

### Impact

- New request/response contract: `(user, [candidate{id, recency, affinity, popularity}])`
  → `[candidate]` ordered.
- New deployment config surface: three weight values, validated on load.
- No data migration; stateless request-scoped computation.

## `design.md`

### Architecture decisions

1. **Pure, stateless ranking function.** Ranking is a pure function of
   `(candidates, weights)`. No per-user state, no persistence, no cross-request memory.
   This makes it trivially testable and deterministic.

2. **Weights injected, not read inside the scorer.** The scorer receives a resolved
   `Weights` value; it does not know about config files or environment. This keeps
   `feed-ranking` and `ranking-weights` cleanly separated — the seam that lets stage-2
   rules slot in without touching scoring.

3. **Score = linear weighted sum.** `score = Σ wᵢ · sᵢ`. Chosen because it is the exact
   product requirement, is monotonic per signal, and needs no normalization for ordering.

4. **Total order via (–score, id).** Sort key is `(-score, item_id)`: descending score,
   then ascending id. `item_id` is assumed unique per request, giving a total order and
   thus determinism. Ascending id is the tie-break rule.

5. **Validation at the boundaries.** Signal-range validation happens on request ingress;
   weight validation happens on config load. Neither the scorer nor the sorter carries
   defensive checks — invalid data cannot reach them.

### Component structure

```
Request ingress
  └─ validate signals in [0,1]  ──(reject if not)
Weights provider  (ranking-weights)
  └─ load + validate config once; expose resolved Weights
Scorer            (feed-ranking)
  └─ score(candidate, weights) -> float
Orderer           (feed-ranking)
  └─ sort by (-score, id) -> ordered feed
Response
```

- **Weights provider** — owns config read + validation; hands a resolved `Weights` to
  each request. Single source of the three numbers.
- **Scorer** — the pure weighted-sum function, one candidate at a time.
- **Orderer** — applies the scorer across candidates and produces the total order.

### Data shapes (conceptual)

- `Candidate { id, recency, affinity, popularity }` — signals in `[0,1]`.
- `Weights { recency, affinity, popularity }` — non-negative, not all zero.
- `RankedFeed = [Candidate]` — descending score, id tie-break.

### Non-goals (stage 1)

Filtering/removal, per-author or per-topic rules, re-arrangement beyond score order,
pagination, and personalization of weights. Explicitly out of scope; the seams above
are chosen so such rules could be added later without rewriting scoring.

## `tasks.md`

- [ ] Define the request/response contract: `(user, candidates[])` → ordered `candidates[]`.
- [ ] Define `Candidate` and `Weights` shapes.
- [ ] Implement request-ingress validation: each signal in `[0,1]`, else reject as malformed.
- [ ] Implement the weights provider: load three weights from deployment config.
- [ ] Implement weight validation on load: all present, non-negative, at least one positive.
- [ ] Implement `score(candidate, weights)` as the weighted sum.
- [ ] Implement the orderer: sort by `(-score, id)`.
- [ ] Wire ingress → weights provider → scorer → orderer → response.
- [ ] Tests: weighted-sum values, descending order, id tie-break, determinism across runs.
- [ ] Tests: empty candidate list → empty feed; out-of-range signal → rejected.
- [ ] Tests: operator weight change takes effect without code change; invalid weight sets rejected on load.
- [ ] Tests: un-normalized weights order identically to their normalized proportions.

---

**STATUS: FROZEN.** Stage-1 specs (`feed-ranking`, `ranking-weights`) and the
`add-feed-ranking` change bundle are the baseline. Stage 2 builds on this file without
editing it.
