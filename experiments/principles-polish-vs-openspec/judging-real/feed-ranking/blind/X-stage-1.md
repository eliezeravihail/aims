# Design X — stage 1

# Feed Ranking Service — Stage 1 Architecture (FROZEN)

Produced by running the method method (plan phase + the one mandatory design review-and-revise round) on
the stage-1 product request. Design only — no implementation code. This document is frozen before any
stage-2 change is seen.

---

## 1. Objective (the design outcome, feature as its constraint)

**Kind: design.** Establish the ownership and boundaries of a feed-ranking service such that:

1. the **scoring rule** (weighted linear combination of the three signals) has exactly **one owner**;
2. the **signal weights** are an **operator-owned configuration input** reached only through a seam —
   retunable per deployment with **no code change**;
3. the returned order is a single **deterministic total order** (score descending, stable id tiebreak).

The feature behavior (combine recency/affinity/popularity under configurable weights; return candidates
ordered high-to-low; ties by stable id) is the *constraint the design must satisfy*, not the thing
optimized. A "build the feed endpoint" framing would collapse this into an inline sort with hardcoded
weights and no owned rules; the design objective exists to prevent exactly that.

## 2. Step-0 inventory (pinned from the spec, held fixed)

**Rules / invariants (R):**
- **R1** score = w_recency·recency + w_affinity·affinity + w_popularity·popularity (weighted linear combination).
- **R2** output ordered by score, highest first.
- **R3** ties (equal score) broken by a stable item id.
- **R4** weights are per-deployment configuration, operator-changeable with no code change.
- **R5** each signal is a normalized value in 0..1.

**Change axes (X):**
- **X1** the weight values (present, stated — the operator retunes per deployment).
- **X2** the scoring formula itself (foreseeable, *not* built for — localized by one-owner, no plug-in machinery).

**Acceptance / capability cases (C):**
- **C1** empty candidate list → empty result.
- **C2** one candidate → that candidate.
- **C3** many candidates → ordered by score descending.
- **C4** equal scores → ordered by item id ascending.
- **C5** operator changes weights (config only) → order changes accordingly, no code change.
- **C6** recency-heavy vs popularity-heavy weights → different order for the same candidate set.
- **Edges:** all-signals-equal; duplicate item id (→ reject at boundary); signal out of 0..1 or negative
  weight (→ reject at boundary); weights that do not sum to 1 (→ valid, not normalized).

## 3. Foundational substrate

- **Python 3 + standard library** — the only foundational layer (pervasiveness test: everything stands
  on it). Dataclasses/typing express the small value objects; `sorted(..., key=...)` gives a stable
  total order directly.
- **Confined (not foundational):** a transport framework (behind `TransportAdapter`) and a
  configuration source (behind `WeightsProvider`). The domain does not stand on either.
- *Gate note:* the substrate gate is normally an ask of the user; with no interactive channel the Guide
  chose it under the separated-phase fallback and recorded it (ADR 0001). Only language + stdlib cross a
  seam as-is.

## 4. Architecture — components, the rule each owns, seams

Functional core (pure scoring + ordering over immutable value objects) with thin adapters at the edges
(Ports & Adapters). The domain is independent of I/O and of where weights come from.

### 4.1 Value objects (the working currency; §0/§4)

| Type | Owns | Why it earns its place |
|---|---|---|
| `UnitInterval` | **R5** — a value in 0..1, validated at construction | one home for the range check, shared by all three signals; deleting it scatters the check |
| `SignalVector` | the shape "a candidate carries exactly recency, affinity, popularity" | groups the three named `UnitInterval`s immutably; prevents a loose triple of floats (§4 primitive obsession) |
| `ItemId` | a typed, totally-ordered identity | the tiebreak key and the request-uniqueness key are **one concept**, not a bare string |
| `Candidate` | `(ItemId, SignalVector)` | one immutable input item |
| `SignalWeights` | **R4 validity** — three coefficients, each ≥ 0, at least one > 0 | the operator-owned value; validated at construction; **not normalized** (ADR 0002) |
| `Score` | the seam currency scorer→orderer | a labeled result of the one formula, compared only for ordering; gives the scorer→orderer seam a published type (§0) |
| `ScoredCandidate` | `(Candidate, Score)` | the scorer's output / orderer's input |

### 4.2 Services and ports

| Component | Kind | Owns |
|---|---|---|
| `FeedScorer` | domain service | **R1** — the single home of the scoring formula |
| `OrderingPolicy` | domain service | **R2 + R3** — the single home of the total order (score desc, id asc) |
| `WeightsProvider` | **port** | **R4 sourcing** — supplies the active `SignalWeights` from deployment config; the only path to a weight value |
| `FeedRankingService` | application service (imperative shell) | orchestration only: fetch weights → score each → order → return. No rule of its own |
| `TransportAdapter` | confined adapter | parse wire request → `RankRequest`; serialize ordered result. **Boundary validation lives here** |
| `user` | request field | **nothing in stage 1** — carried because the request is per-user (grounded fact); not consumed by scoring/ordering; modeled as an opaque subject, not a rich type |

### 4.3 Seams (and the published type that crosses each)

- **Transport → domain:** `RankRequest = (user, tuple[Candidate, ...])` in; `list[Candidate]` (ranked)
  out. Validation (fail fast, §1) happens here: every signal in 0..1, every weight valid, ids unique.
  The core assumes valid inputs (defensive at the edge, trusting inside).
- **Configuration → domain:** `WeightsProvider.current() -> SignalWeights`. The seam that keeps weight
  *values* out of the *code* — this is R4 made structural (INV4).
- **Scorer → orderer:** `ScoredCandidate`. The orderer receives finished `Score`s; it never re-derives
  or mutates them.

### 4.4 Concrete signatures (Python — buildable skeleton)

```
# domain/values.py
class UnitInterval:
    def __init__(self, value: float) -> None: ...   # raises ValueError if not 0.0 <= value <= 1.0
    @property
    def value(self) -> float: ...

class ItemId:
    def __init__(self, raw: str) -> None: ...        # non-empty
    def __eq__, __hash__, __lt__                      # total order for the tiebreak

@dataclass(frozen=True)
class SignalVector:
    recency: UnitInterval
    affinity: UnitInterval
    popularity: UnitInterval

@dataclass(frozen=True)
class Candidate:
    id: ItemId
    signals: SignalVector

class SignalWeights:
    def __init__(self, recency: float, affinity: float, popularity: float) -> None: ...
    # raises if any < 0 or all == 0

@dataclass(frozen=True, order=False)
class Score:
    value: float

@dataclass(frozen=True)
class ScoredCandidate:
    candidate: Candidate
    score: Score

# domain/scoring.py         — owns R1
class FeedScorer:
    def score(self, signals: SignalVector, weights: SignalWeights) -> Score: ...
        # Score(w.recency*s.recency.value + w.affinity*s.affinity.value + w.popularity*s.popularity.value)

# domain/ordering.py        — owns R2 + R3
class OrderingPolicy:
    def order(self, scored: Sequence[ScoredCandidate]) -> list[Candidate]: ...
        # sorted by (-score.value, candidate.id)  -> total order, input-order-independent

# ports.py                  — owns R4 sourcing
class WeightsProvider(Protocol):
    def current(self) -> SignalWeights: ...

# app.py                    — orchestration only
@dataclass(frozen=True)
class RankRequest:
    user: str                                        # opaque subject; unused by ranking in stage 1
    candidates: tuple[Candidate, ...]

class FeedRankingService:
    def __init__(self, scorer: FeedScorer, ordering: OrderingPolicy, weights: WeightsProvider) -> None: ...
    def rank(self, request: RankRequest) -> list[Candidate]:
        w = self._weights.current()
        scored = [ScoredCandidate(c, self._scorer.score(c.signals, w)) for c in request.candidates]
        return self._ordering.order(scored)
```

## 5. Invariants

- **INV1 (R5):** every signal is in 0..1 — `UnitInterval` at construction; malformed values rejected at
  the boundary.
- **INV2 (R1):** exactly one owner of the scoring formula (`FeedScorer`).
- **INV3 (R2+R3):** the returned order is the unique total order (score desc, id asc); deterministic and
  independent of input order, because id is a unique total tiebreak.
- **INV4 (R4):** weights are external config reached only through `WeightsProvider`; retuning is a config
  change, never a code change; no weight literal in the domain.
- **INV5 (permutation):** ranking reorders, never filters — output is a permutation of the input
  candidates.

## 6. Key design reasoning

- **One owner per rule (§5).** R1 → `FeedScorer`, R2+R3 → `OrderingPolicy`, R4 validity → `SignalWeights`,
  R4 sourcing → `WeightsProvider`, R5 → `UnitInterval`. Each rule has exactly one home and one path all
  callers use. The naive framing would inline all of these into one sort call.
- **Weights are configuration, structurally (R4/INV4).** The domain can only obtain weights through the
  port; there is no literal to edit and redeploy. This is the difference between "an operator can retune"
  as a *claim* and as a *guarantee by construction*.
- **The order is a property of the design, not of the input.** A unique total order (score desc, id asc)
  plus unique ids means determinism does not depend on candidates arriving pre-sorted.
- **Deliberate non-generality (§7 YAGNI).** No Strategy interface for the formula (X2 is localized by
  one-owner alone), no weight normalization (ADR 0002), no rich `UserId` (nothing reads it in stage 1).
  Each omission answers to the absence of a present force.

## 7. Mandatory design review-and-revise round (one round, as the method prescribes)

The design was **not** read as met on its first pass. One measure → return-findings → revise round was
run (subtractive pass, concept-fit pass, exit-criteria + edge pass). Findings returned and folded in:

- **F1 (concept-fit — value-correct cram, caught in design so cheap to fix).** The sum-to-1 example
  tempted modeling `SignalWeights` as a decomposition (shares of a total). That is a decomposition forced
  onto independent coefficients; its tell is a normalization step that reorders nothing. **Revised:**
  weights are independent non-negative coefficients, not normalized (ADR 0002). *This is the finding the
  concept-fit pass exists for.*
- **F2 (correctness/edge — first pass left it unspecified).** Duplicate item ids break the "unique total
  order" guarantee (equal id + equal score → nondeterministic). **Revised:** ids are unique per request;
  a duplicate is rejected at the boundary (ADR 0003, INV3).
- **F3 (subtractive pass).** `Score` and `ItemId` are thin. Verdict: **kept, minimally** — `Score` is the
  scorer→orderer seam currency (§0 published-type-across-seam); `ItemId` unifies the tiebreak key and the
  uniqueness key into one concept. Each owns a stated rule/seam, so neither is unpaid machinery. Recorded
  that if either later owns no rule it should collapse to a primitive.
- **F4 (subtractive pass).** `user` is unused by stage-1 ranking. Verdict: **kept as an opaque subject,
  not built into a rich type** — it is a stated part of the per-user request (a requirement, not
  machinery), so the pass does not cut it, but no behavior is modeled around it.
- No Strategy/plug-in machinery was introduced for X2; one-owner already localizes a formula change.

Re-measured after revision: all exit criteria met; no substantial finding open. Design frozen.

## 8. Filed records (co-located design record in the project tree)

`goals.md`, `base-dependencies.md`, `dependencies.md`, `architecture.md`, and ADRs
`decisions/0001-foundational-substrate.md`, `0002-weights-are-independent-coefficients-owned-by-config.md`,
`0003-total-order-and-unique-id-tiebreak.md`. Loop status in `.method/state.md`. (No source files exist
yet — a design objective ships no code — so there are no companions to anchor; system records take no
anchor.)
