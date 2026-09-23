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
