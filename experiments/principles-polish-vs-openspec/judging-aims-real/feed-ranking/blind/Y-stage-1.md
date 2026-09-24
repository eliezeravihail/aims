# Design Y — stage 1



<!-- file: proposal.md -->

# Proposal

## Why

A user's feed has to be ordered so that the most relevant candidate items appear first. Relevance comes from three
per-item signals (recency, affinity, popularity). How much each signal counts is a business decision that differs
between deployments and changes over time. Operators need to be able to retune it without a code change or release.

## What Changes

- New in-process ranking service. It takes a `user` and a list of candidate items (each with `item_id`, `recency`,
  `affinity` and `popularity` in [0.0, 1.0]) and returns the same candidates ordered by a combined score, highest
  first.
- The combined score is a weighted sum of the three signals. Equal scores are ordered by `item_id` ascending, so
  the result is deterministic.
- The weights are per-deployment configuration: a small JSON file whose path is given to the service. The file is
  validated when it is loaded, and an operator changes weights by editing it and reloading. No code change is
  needed.
- Invalid input is rejected with an explicit error and never silently "fixed". This covers out-of-range signals,
  duplicate item ids, invalid weights and unknown signal names.
- A small CLI wraps the library API for operators and for manual checks.

## Capabilities

### New Capabilities
- `feed-ranking`: scores candidate items from their signals and returns them in a deterministic order. Covers the
  request/response contract, the scoring rule, tie-breaking and input validation.
- `ranking-config`: per-deployment signal weights. Covers the file format, validation rules, how weights are
  loaded and reloaded, and the guarantee that a request is scored with one consistent set of weights.

### Modified Capabilities
<!-- none: no existing specs -->

## Impact

- Greenfield: no existing code or specs are affected.
- Python 3.11+ standard library only (`json`, `dataclasses`, `decimal` optional; see design). No new runtime
  dependencies.
- Public surface: a library function or class API plus a CLI entry point. Nothing is persisted. It runs as a
  single process.


<!-- file: specs/feed-ranking/spec.md -->

# Spec Delta

## Purpose

Takes a user's candidate items and returns them as an ordered feed, ranked by a weighted combination of each
item's recency, affinity and popularity signals, with a deterministic tie-break.

## ADDED Requirements

### Requirement: Rank request contract
The service SHALL accept a rank request made of a `user` identifier and a list of candidate items. Each candidate
SHALL have a string `item_id` and the numeric signals `recency`, `affinity` and `popularity`. The service SHALL
return every candidate exactly once, in ranked order. Each returned entry SHALL carry the candidate's `item_id` and
its computed `score`.

#### Scenario: All candidates returned once
- **WHEN** a request contains candidates `a`, `b` and `c` with valid signals
- **THEN** the response contains exactly three entries, one each for `a`, `b` and `c`

#### Scenario: Empty candidate list
- **WHEN** a request contains a valid `user` and no candidates
- **THEN** the service returns an empty ordered feed and no error

### Requirement: Weighted-sum score
The service SHALL compute each candidate's score as
`w_recency * recency + w_affinity * affinity + w_popularity * popularity`. The weights SHALL be the configured
weights in effect for that request. Scores SHALL be computed exactly, so two candidates whose weighted sums are
mathematically equal get equal scores and binary floating-point rounding cannot split them.

#### Scenario: Score from configured weights
- **WHEN** the weights are recency 0.5, affinity 0.3, popularity 0.2 and a candidate has recency 1.0, affinity 0.5, popularity 0.0
- **THEN** that candidate's score is 0.65

#### Scenario: Mathematically equal sums are equal scores
- **WHEN** the weights are recency 0.5, affinity 0.3, popularity 0.2, candidate `x` has signals (recency 0.0, affinity 0.0, popularity 0.4) and candidate `y` has signals (0.0, 0.2, 0.1)
- **THEN** both scores are exactly 0.08, the two are treated as a tie, and they are ordered by `item_id`

### Requirement: Order by score descending
The service SHALL order the returned entries by score, highest first.

#### Scenario: Higher score first
- **WHEN** candidate `a` scores 0.8 and candidate `b` scores 0.4
- **THEN** `a` appears before `b` in the response

### Requirement: Deterministic tie-break by item id
When two or more candidates have equal scores, the service SHALL order them by `item_id` in ascending order,
comparing ids as plain strings by code point. The same request with the same weights SHALL always produce the
same order, whatever order the candidates were submitted in.

#### Scenario: Tie broken by item id
- **WHEN** candidates `b` and `a` both score 0.5
- **THEN** `a` appears before `b`

#### Scenario: Input order does not affect output
- **WHEN** the same set of candidates is submitted twice in different orders with the same weights
- **THEN** both responses have the identical order

### Requirement: Candidate validation
The service SHALL reject the whole request with a validation error that names the offending item and field, and
SHALL NOT return a partial feed, when any of the following is true:
- a signal is missing, is not a real number (booleans, NaN and infinities count as not real), or is outside
  [0.0, 1.0];
- an `item_id` is missing or empty;
- two candidates share the same `item_id`.

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

### Requirement: User is carried but not scored
The service SHALL require a non-empty `user` identifier on every request. The `user` SHALL NOT affect scoring in
this stage, because per-user relevance already arrives in the `affinity` signal.

#### Scenario: Same candidates for different users
- **WHEN** two requests with different `user` values carry identical candidates under the same weights
- **THEN** both responses have the identical order and scores

#### Scenario: Missing user rejected
- **WHEN** a request has an empty or missing `user`
- **THEN** the request fails with a validation error


<!-- file: specs/ranking-config/spec.md -->

# Spec Delta

## Purpose

Lets an operator set the per-deployment weight of each ranking signal in a configuration file and change it
without a code change, while the service only ever scores with a valid, consistent set of weights.

## ADDED Requirements

### Requirement: Weights come from a deployment configuration file
The service SHALL read signal weights from a JSON configuration file whose location the deployment supplies. The
file SHALL contain a `weights` object with exactly one numeric entry for each signal: `recency`, `affinity` and
`popularity`. Weights SHALL NOT be hard-coded, and there SHALL be no built-in default weights.

#### Scenario: Weights loaded from file
- **WHEN** the configuration file contains `{"weights": {"recency": 0.5, "affinity": 0.3, "popularity": 0.2}}`
- **THEN** requests are scored with recency 0.5, affinity 0.3 and popularity 0.2

#### Scenario: No configuration supplied
- **WHEN** the service is started without a configuration file location, or the file does not exist
- **THEN** the service refuses to start and reports that configuration is required

### Requirement: Weight validation
The service SHALL accept a configuration only when every weight is a finite real number ≥ 0, at least one weight
is > 0, all three signals are present, and no unknown signal name appears. Weights SHALL NOT have to sum to 1. The
service SHALL use them as given and SHALL NOT normalize them. Any violation SHALL be reported with an error that
names the offending key.

#### Scenario: Negative weight rejected
- **WHEN** the configuration sets `affinity` to -0.1
- **THEN** the configuration is rejected with an error naming `affinity`

#### Scenario: Unknown signal rejected
- **WHEN** the configuration contains a `freshness` weight
- **THEN** the configuration is rejected with an error naming `freshness`

#### Scenario: Missing signal rejected
- **WHEN** the configuration omits `popularity`
- **THEN** the configuration is rejected with an error naming `popularity`

#### Scenario: All-zero weights rejected
- **WHEN** every weight is 0
- **THEN** the configuration is rejected

#### Scenario: Weights not summing to one accepted
- **WHEN** the weights are recency 5, affinity 3, popularity 2
- **THEN** the configuration is accepted and scores are the weighted sums with those exact values

### Requirement: Operator changes weights without a code change
An operator SHALL be able to change the weights by editing the configuration file and triggering a reload,
without modifying or redeploying code. A reload of a valid file SHALL take effect for every request that starts
after the reload completes.

#### Scenario: Reload applies new weights
- **WHEN** the operator changes `recency` from 0.5 to 0.1 in the file and triggers a reload
- **THEN** requests started after the reload are scored with recency 0.1

### Requirement: Invalid reload keeps last good weights
If a reload finds an invalid or unreadable configuration, the service SHALL keep scoring with the weights that
were last loaded successfully and SHALL report the reload failure to the caller that triggered it.

#### Scenario: Bad edit does not break ranking
- **WHEN** the operator saves a file with a negative weight and triggers a reload
- **THEN** the reload reports an error and subsequent requests keep using the previous valid weights

### Requirement: One weight set per request
Each rank request SHALL be scored entirely with a single weight set. A reload that happens while a request is
being processed SHALL NOT cause that request to mix old and new weights.

#### Scenario: Reload during a request
- **WHEN** a reload completes while a request is being scored
- **THEN** every candidate in that request is scored with the same weights, either all old or all new


<!-- file: design.md -->

# Design

## Context

This is a greenfield project. The substrate is fixed: Python 3.11+, standard library only, a single process, and no
network, database or persistence. Motivation is in `proposal.md`. Behavior is specified in
`specs/feed-ranking/spec.md` and `specs/ranking-config/spec.md`. This document covers only the structure that
delivers that behavior and why it is shaped this way.

## Goals / Non-Goals

**Goals:**
- Each rule has exactly one owner: the scoring formula, the tie-break, signal validity and weight validity.
- The ranking core is a pure function of (weights, candidates), so it is deterministic and testable without files
  or a clock.
- Configuration is a replaceable edge. The core never touches files, and the file loader never scores anything.

**Non-Goals:**
- Candidate retrieval, signal computation, pagination/truncation, diversity or dedup rules, per-user or
  per-segment weights, A/B weight experiments, and file watching or hot-reload daemons. None of these were asked
  for.
- Pluggable or non-linear scoring functions. The formula is a weighted sum, and there is no strategy registry
  until one is needed.

## Architecture

```
  CLI (adapter)            Library caller (adapter)
      |                           |
      +------------+--------------+
                   v
          +------------------+   snapshot()   +----------------------+
          |   FeedService    |--------------->|    WeightsProvider   |
          | (orchestration)  |                | holds current Weights|
          +--------+---------+                | load()/reload()      |
                   |                          +----------+-----------+
                   | parse_request()                     | parse_weights()
                   v                                     v
          +------------------+                +----------------------+
          |  request model   |                |   weights model      |
          | Candidate,       |                | Weights (validated,  |
          | RankRequest      |                | immutable)           |
          | (validation)     |                +----------+-----------+
          +--------+---------+                           |
                   |      +------------------------------+
                   v      v
          +------------------------+
          |   ranking core (pure)  |
          |  score(w, c) -> Decimal|
          |  rank(w, cs) -> list   |
          +------------------------+
                   |
                   v
             [RankedItem(item_id, score), ...]

  SIGNALS = ("recency", "affinity", "popularity")   <- one shared definition,
                                                       read by both models
```

### Components and the rules they own

| Component | Owns | Does not know about |
|---|---|---|
| `signals` | The canonical tuple of signal names, `SIGNALS`. Candidate fields and weight keys both come from it. | Values, weights, files |
| request model (`Candidate`, `RankRequest`) | Candidate validity: signals present, real, in [0,1]; non-empty unique `item_id`; non-empty `user`. It converts raw input into immutable, already-validated values. | Weights, scoring |
| weights model (`Weights`) | Weight validity: all signals present, no unknown keys, finite, ≥ 0, at least one > 0. It is an immutable value. | Where the weights came from |
| `WeightsProvider` | The configuration lifecycle: read the JSON file at a path, build `Weights`, hold the current snapshot, `reload()` with last-good retention, fail fast on the first load. | Candidates, scoring |
| ranking core (`score`, `rank`) | The scoring formula (weighted sum) and the ordering rule (score desc, then `item_id` asc). It is pure, does no I/O and does no validation. | Files, reloads, raw input |
| `FeedService` | Per-request orchestration: take one weights snapshot, parse the request, call `rank`, return the result. | Formula details, file format |
| CLI | Argument parsing, reading the request JSON (file or stdin), printing the ranked JSON, exit codes. | Everything else; it only calls `FeedService` |

Illustrative boundary signatures (not an implementation):

```python
SIGNALS: tuple[str, ...] = ("recency", "affinity", "popularity")

@dataclass(frozen=True)
class Candidate:      item_id: str; signals: Mapping[str, Decimal]
@dataclass(frozen=True)
class RankRequest:    user: str; candidates: tuple[Candidate, ...]
@dataclass(frozen=True)
class Weights:        values: Mapping[str, Decimal]
@dataclass(frozen=True)
class RankedItem:     item_id: str; score: Decimal

def parse_request(raw: Mapping) -> RankRequest            # raises ValidationError
def parse_weights(raw: Mapping) -> Weights                # raises ConfigError
def rank(weights: Weights, candidates: Sequence[Candidate]) -> list[RankedItem]

class WeightsProvider:
    def __init__(self, path: Path) -> None                # loads; raises ConfigError
    def snapshot(self) -> Weights
    def reload(self) -> None                              # raises ConfigError; keeps last good

class FeedService:
    def __init__(self, weights: WeightsProvider) -> None
    def rank(self, raw_request: Mapping) -> list[RankedItem]
```

Request flow: `FeedService.rank` calls `weights.snapshot()` once, then `parse_request(raw)`, then
`rank(snapshot, request.candidates)`.

## Decisions

### D1. The weighted sum lives in one pure function; ordering is one sort key
`rank` computes each score with `score(w, c) = sum(w[s] * c[s] for s in SIGNALS)`. It then sorts with the key
`(-score, item_id)`. Because this key is total and uses the unique id as its last element, sort stability and
input order cannot affect the output. That satisfies the "input order does not affect output" requirement without
relying on how Python's sort behaves.
*Alternative:* sort by score, then rely on a stable sort over pre-sorted ids. Rejected because it is correct only
if two separate steps stay in sync.

### D2. Exact arithmetic with `decimal.Decimal`
Signals and weights are converted to `Decimal` at the parse boundary. Floats are converted via `Decimal(str(x))`,
so `0.1` becomes exactly `0.1`. With `float`, weights 0.5/0.3/0.2 give 0.08000000000000002 for (0, 0, 0.4) and
0.08 for (0, 0.2, 0.1). Two mathematically equal scores would then be ordered by float noise instead of by
`item_id`, which breaks the tie-break contract. With `Decimal`, those ties are real ties. The request size is a
user's candidate list (hundreds to low thousands), so the cost is negligible. JSON parsing uses
`json.loads(..., parse_float=Decimal)` so values are never floats in the first place.
*Alternative:* round float scores to N places before comparing. Rejected because the choice of N is arbitrary and
rounding creates artificial ties near the cut-off boundary.

### D3. Validation at the edges; the core trusts its inputs
Raw input becomes a `RankRequest` or `Weights` only through `parse_request` or `parse_weights`. Those are the only
places that reject bad data, and each error names the offending item and field or key. `rank` receives
already-validated values and contains no defensive checks. Invalid candidates reject the whole request (spec). We
do not silently drop or clamp values, because a malformed signal usually means an upstream bug that should
surface.
*Alternative:* clamp out-of-range signals to [0,1]. Rejected: it hides upstream defects and is a product decision
nobody made.

### D4. One definition of the signal set
Both `Candidate` and `Weights` validate against the same `SIGNALS` tuple. This keeps the "unknown signal" check in
the config and the "missing signal" check in the request consistent. It is a single constant, not a plugin
mechanism.

### D5. Configuration: a JSON file, an explicit reload, and immutable snapshots
- **Format:** JSON (`json` is in the standard library, whereas TOML via `tomllib` would also work). Shape:
  `{"weights": {"recency": 0.5, "affinity": 0.3, "popularity": 0.2}}`. The top-level object leaves room for later
  keys without a format break. Unknown *top-level* keys are rejected too, so a typo such as `"weigths"` fails
  loudly.
- **Location:** a path passed explicitly to `WeightsProvider` (CLI: `--config PATH`). An environment variable
  such as `FEED_RANKING_CONFIG` can supply the path as a fallback. There are no default weights and no
  hard-coded path. A missing config is a startup error.
- **Reload:** `WeightsProvider.reload()` re-reads the file, validates it into a new `Weights`, and only then
  replaces the reference. On failure it raises and keeps the old snapshot. For the CLI, each invocation is a fresh
  process that loads the file, so "edit the file" is the whole operator workflow. A long-lived library host calls
  `reload()` on whatever trigger it has (a signal handler, an admin call). The trigger is the host's job.
- **Consistency:** `Weights` is frozen. `FeedService` takes one `snapshot()` per request and passes that object
  down, so a concurrent reload cannot produce mixed weights. Swapping a single attribute reference is atomic in
  CPython, so no lock is needed for readers. A lock around `reload()` serializes concurrent reloaders.

*Alternatives:* file watching with mtime polling or inotify. Rejected: it is not asked for, and in the standard
library alone it needs a background thread. Weights passed as CLI flags: rejected as the primary mechanism,
because deployment configuration belongs in a deployment artifact and not in call sites.

### D6. Weights are used as given, not normalized
Positive scaling of all weights does not change the order, so a sum-to-1 rule would only reject valid intent
(e.g. 5/3/2). Normalizing would change the returned `score` values the operator sees. Negative weights are
rejected. That is a product assumption (see below).

### D7. Output carries the score
Each `RankedItem` has `item_id` and `score`. The request asks for ordered candidates, and returning the score as
well costs nothing. It makes the ordering explainable to operators tuning weights and makes the spec testable.
The CLI prints `score` as a JSON string, e.g. `"0.65"`, to keep it exact.

### D8. Entry points
The library API (`FeedService`) is primary. The CLI is a thin adapter:
`feed-rank --config weights.json [REQUEST_FILE|-]` prints `[{"item_id": ..., "score": ...}, ...]`. It exits 0 on
success, 2 on a request validation error and 3 on a config error, with the message on stderr.

## Assumptions (product questions answered with a simple default)

- `item_id` is a string, and "stable item id" means ascending code-point order on that string.
- `user` is required but does not influence the score in this stage, since personalization arrives via `affinity`.
- Weights must be ≥ 0 and not all zero. They do not have to sum to 1, and they are not normalized.
- Signals outside [0,1], non-numeric signals and duplicate ids reject the whole request. Nothing is clamped or
  dropped.
- An empty candidate list returns an empty feed.
- There is no truncation or limit. Every candidate is returned.
- "Without a code change" is satisfied by editing a file plus a reload or a new process, not by live file
  watching.

## Risks / Trade-offs

- [Decimal is slower than float] → Candidate lists are small per request, and the correctness of ties is part of
  the contract. If profiling ever shows a problem, the change is local to the parse boundary and `score`.
- [An operator edits the file, but a long-lived host never calls `reload()`] → This is documented as the host's
  responsibility. `reload()` reports success or failure explicitly. The CLI path always reads fresh.
- [A bad config at startup takes the service down] → This is intentional (fail fast). There is no silent fallback
  to invented default weights.
- [An upstream sends slightly out-of-range values, e.g. 1.0000001] → They are rejected loudly. If that turns out to
  be common, a tolerance is a product decision to add explicitly later.

## Migration Plan

Not applicable: this is a new service with no existing consumers. Rollback is removing the package.


<!-- file: tasks.md -->

# Tasks

## 1. Scaffolding

- [ ] 1.1 Create the `feed_ranking` package (stdlib only, Python 3.11+) with a `unittest` test directory, and verify `python -m unittest` runs with zero tests and no errors

## 2. Signals and weights model

- [ ] 2.1 Define the shared `SIGNALS` tuple and verify with a unit test that it is exactly `("recency", "affinity", "popularity")`
- [ ] 2.2 Implement the frozen `Weights` value and `parse_weights` (all signals present, no unknown keys, finite, ≥ 0, at least one > 0, Decimal values, no normalization; unknown top-level keys rejected), and verify tests covering each `ranking-config` "Weight validation" scenario pass

## 3. Request model

- [ ] 3.1 Implement the frozen `Candidate` and `RankRequest` and `parse_request` (non-empty user; non-empty, unique string `item_id`; each signal present, real, not bool/NaN/inf, in [0,1]; converted to Decimal via `str`), and verify tests for every `feed-ranking` "Candidate validation" and "User is carried but not scored" scenario pass, including errors that name the item and field

## 4. Ranking core

- [ ] 4.1 Implement pure `score` (weighted sum over `SIGNALS`) and `rank` (sort key `(-score, item_id)`, returning `RankedItem` values), and verify tests pass for the 0.65 example, the exact 0.08 tie, tie-by-id, score descending, empty input, and permuted input giving identical output

## 5. Configuration lifecycle

- [ ] 5.1 Implement `WeightsProvider` (load JSON from an explicit path with an env-var fallback, parse with `parse_float=Decimal`, fail fast when the path is missing, invalid or unreadable, and `snapshot()`), and verify tests using temp files for the load and "No configuration supplied" scenarios
- [ ] 5.2 Implement `reload()` (validate first, then swap the reference; keep the last good weights and raise on failure; serialize reloaders with a lock), and verify tests for "Reload applies new weights" and "Bad edit does not break ranking"

## 6. Service facade

- [ ] 6.1 Implement `FeedService.rank` (one `snapshot()` per request, then `parse_request`, then `rank`), and verify with a test using a provider stub that swaps weights mid-request that all candidates in one request use one weight set
- [ ] 6.2 Document the library API and the config file format (including the operator workflow: edit the file, then reload or re-run) in the package README, and verify the README examples match the tested behavior

## 7. CLI adapter

- [ ] 7.1 Implement the `feed-rank --config PATH [REQUEST_FILE|-]` CLI that prints ranked JSON with string scores and exits 0 on success, 2 on a request error and 3 on a config error, and verify subprocess tests for each exit code
- [ ] 7.2 Add CLI usage to the README and verify the documented command runs as written against a sample config and request

## 8. Integration check

- [ ] 8.1 End to end: run the CLI with weights 0.5/0.3/0.2, edit the file to change the weights, re-run, and verify the order changes as predicted with no code change
