# Design X — stage 2

# Feed Ranking Service — Stage 2 Architecture (FROZEN)

Produced by running the method method again on the stage-2 change request, consulting the frozen stage-1
design and its co-located records (`goals.md`, `architecture.md`, ADRs 0001–0003). Design only — no
implementation code. Stage-1 weighted scoring and tunable weights are unchanged.

---

## 1. The change and the design objective

**Change:** on the same request, two new rules. **(1) Eligibility** — an item from a blocked author or
a muted topic must never appear (absent, not ranked low). **(2) Diversity** — no more than 2 items in a
row may share the same author; a would-be 3rd consecutive same-author item is deferred to the next
non-violating position, otherwise the score order is preserved.

**Kind: design.** Objective: localize each new rule as its **own single-rule owner** that slots into the
stage-1 pipeline **without reopening the scoring or ordering owners**, keeping stage-1 scoring/weights
working exactly as before. The naive "add block/mute and shuffle for variety" framing would inline both
rules into the sort and quietly corrupt the one place that owns the order.

## 2. Delta-discovery (new Step-0 items + open decisions)

**New rules (R):**
- **R6 (eligibility):** an item whose `Author` ∈ block list OR any of whose `Topic`s ∈ mute list must
  never appear in the output.
- **R7 (diversity):** no author appears in 3 consecutive output positions; a would-be 3rd is deferred to
  the earliest later non-violating slot, else order preserved.

**New change axes:** the block/mute lists vary **per request** (per-user data), distinct from the
per-deployment weights.

**New / changed cases (C):**
- all candidates blocked/muted → empty result;
- an item with several topics, one muted → absent;
- 3+ items by one author interleaved with others → the 3rd deferred behind a different author;
- the whole eligible set authored by one person → no 3-in-a-row is possible → emit in score order, drop
  nothing;
- eligibility + diversity together → diversity operates only on the eligible subset.

**Open product decisions surfaced (defaulted with rationale; would be asked in a live run — ADRs
0004/0005/0006):**
- Item topic cardinality → **a set of topics**; muted if any topic is muted.
- Where the block/mute lists come from → **supplied in the request** (per-user, per-request data), not a
  port; contrast weights, which stay a deployment-scoped port (ADR 0006).
- Diversity when unsatisfiable (all remaining one author) → **degrade to score order, never drop** (only
  eligibility removes items — ADR 0005).

## 3. Evolved architecture — the pipeline

Functional core as a **pipeline**, each stage a single-rule owner; `FeedRankingService` is the
imperative shell that composes them and owns no rule:

```
eligibility filter  →  score  →  order by score  →  diversify
 (R6, new)             (R1)       (R2+R3)            (R7, new)
```

New and changed components:

| Component | Status | Owns |
|---|---|---|
| `EligibilityPolicy` | **new** | **R6** — drop any candidate whose author is blocked or whose topic set meets the mute set; runs first, before scoring (INV6). |
| `DiversityPolicy` | **new** | **R7** — reorder the score-ordered list so no author runs 3-in-a-row; defer a would-be 3rd to the earliest admissible later slot; **reorder only, never drops** (INV7, INV8). |
| `Author` | **new** value object | author identity — used by both R6 (block membership) and R7 (adjacency); one concept, two rules. |
| `Topic` | **new** value object | topic identity — R6 mute membership. |
| `Candidate` | **extended** | gains `author: Author` + `topics: frozenset[Topic]`, additively; `FeedScorer` still reads only `signals`. |
| `RankRequest` | **extended** | gains `blocked_authors: frozenset[Author]`, `muted_topics: frozenset[Topic]`. |
| `TransportAdapter` | **extended** | now parses author/topics per candidate and the two lists; still owns boundary validation. |
| `FeedRankingService` | **extended** | orchestration gains the eligibility (first) and diversity (last) stages; still owns no rule. |

Unchanged stage-1 components: `UnitInterval`, `SignalVector`, `ItemId`, `SignalWeights`, `Score`,
`ScoredCandidate`, `FeedScorer`, `OrderingPolicy`, `WeightsProvider`.

### 3.1 Concrete signatures (delta only)

```
# domain/values.py  (stage 2 additions)
class Author:
    def __init__(self, raw: str) -> None: ...     # non-empty; __eq__, __hash__
class Topic:
    def __init__(self, raw: str) -> None: ...     # non-empty; __eq__, __hash__

@dataclass(frozen=True)
class Candidate:                                    # extended
    id: ItemId
    signals: SignalVector
    author: Author                                  # new
    topics: frozenset[Topic]                        # new (0+; muted if any is muted)

# domain/eligibility.py   — owns R6 (new)
class EligibilityPolicy:
    def filter(self, candidates: Sequence[Candidate],
               blocked_authors: frozenset[Author],
               muted_topics: frozenset[Topic]) -> list[Candidate]:
        # keep c iff c.author not in blocked_authors and c.topics.isdisjoint(muted_topics)

# domain/diversity.py     — owns R7 (new)
class DiversityPolicy:
    def arrange(self, ordered: Sequence[Candidate]) -> list[Candidate]:
        # walk `ordered` (already score desc / id asc). Emit greedily: at each slot pick the
        # highest-ranked not-yet-emitted item whose author != the last two emitted authors;
        # if the natural next item is blocked by a 2-in-a-row, defer and take the next admissible,
        # reconsidering deferred items (in rank order) at later slots. If none admissible
        # (all remaining share the streak author), emit the rest in rank order. Never drops.

# app.py  (extended)
@dataclass(frozen=True)
class RankRequest:                                  # extended
    user: str
    candidates: tuple[Candidate, ...]
    blocked_authors: frozenset[Author]              # new
    muted_topics: frozenset[Topic]                  # new

class FeedRankingService:                           # extended: two new stages, still rule-free
    def rank(self, request: RankRequest) -> list[Candidate]:
        eligible = self._eligibility.filter(
            request.candidates, request.blocked_authors, request.muted_topics)
        w = self._weights.current()
        scored  = [ScoredCandidate(c, self._scorer.score(c.signals, w)) for c in eligible]
        ordered = self._ordering.order(scored)      # unchanged
        return self._diversity.arrange(ordered)     # R7-respecting reorder
```

### 3.2 New / changed invariants

- **INV5' (supersedes INV5):** output is a permutation of the **eligible** subset (input minus
  blocked/muted). Only `EligibilityPolicy` removes.
- **INV6 (R6):** no blocked-author/muted-topic item ever appears — absent, not low.
- **INV7 (R7):** no author runs 3-in-a-row whenever satisfiable; degrades to score order (never drops)
  when the remaining items are all one author.
- **INV8:** diversity deviates from the score order only where R7 forces it (minimal constrained
  transform); `OrderingPolicy`'s order is otherwise preserved.
- INV1–INV4 (stage 1) hold **unchanged**.

## 4. SURVIVAL — the stage-1 design under the change

| Stage-1 element / seam | Verdict | How the new rules met it |
|---|---|---|
| `UnitInterval`, `SignalVector`, `ItemId`, `Score`, `ScoredCandidate` | **survived** | untouched — the new rules add fields/stages, not new signal or score semantics. |
| `SignalWeights`, `WeightsProvider` (R4 seam) | **survived** | untouched — weights stay deployment config through the port; per-user lists went to the request instead (ADR 0006), so this seam was not stretched. |
| `FeedScorer` (R1) | **survived** | untouched — "scoring keeps working exactly as before." Candidate grew, but the scorer still reads only `signals`. |
| `OrderingPolicy` (R2+R3) | **survived** | untouched — diversity is a **downstream** constrained transform, not a change to the sort. The stage-1 total order is the base order diversity preserves. |
| `Candidate` (transport→domain crossing type) | **extended** | additive: `author` + `topics`. Schema evolution absorbed in one value object + the adapter (§7 one-owner-of-representation). No existing consumer changed. |
| `RankRequest` | **extended** | additive: `blocked_authors`, `muted_topics`. |
| `TransportAdapter` (boundary validation) | **extended** | now parses/validates the new fields; still the single validation home. |
| `FeedRankingService` (imperative shell) | **extended** | gained two pipeline stages (first + last); still owns no rule. **This is the seam the new rules slotted into.** |
| `user` (opaque subject) | **survived (note superseded)** | stays an opaque id; the stage-1 "unused" note is superseded — the user's *supplied lists* are now consumed, but `user` itself is still not attribute-read. |
| **INV5 (permutation of all input)** | **reopened → superseded by INV5'** | the **one** deliberate reopening: eligibility must drop items, which INV5 forbade. Recorded as ADR 0004, not an accident. |

**Did the new rules slot in at existing seams, or force an owner open?** Both new rules slotted in at
the **existing pipeline-shell seam** (`FeedRankingService`) and the transport boundary, each as a new
single-rule owner (`EligibilityPolicy` first, `DiversityPolicy` last). **No stage-1 rule owner was
forced open** — scoring, ordering, weighting, and validation are byte-for-byte intact. The only
invariant reopened (INV5 → INV5') was reopened *on purpose* because the eligibility rule contradicts it;
that is the honest cost of the change, isolated to one ADR. The value objects grew additively. This is
the payoff of stage-1's one-owner-per-rule + imperative-shell pipeline: a new rule becomes a new stage,
not a surgery on an old one.

## 5. Mandatory design review-and-revise round (one round)

The stage-2 design was not read as met on its first pass; one measure → return-findings → revise round
ran. Findings folded in:

- **F1 (edge/correctness — first pass unspecified):** diversity when all remaining eligible items share
  the last-two author → no non-violating slot exists. **Revised:** `DiversityPolicy` never drops; it
  degrades to score order (ADR 0005, INV7). Only eligibility removes.
- **F2 (concept-fit):** eligibility is a *filter over a set* (removal); diversity is a *permutation of a
  sequence* (reordering). Modeling diversity as a drop would conflate the two kinds and silently break
  INV5'. **Revised:** distinct owners, distinct signatures (`filter -> subset`, `arrange ->
  permutation`); removal lives only in eligibility.
- **F3 (open product decisions):** item topic cardinality → set (muted if any); eligibility data source →
  in-request vs deployment port → in-request (ADR 0006). Filed with rationale.
- **F4 (subtractive pass):** `Author`/`Topic` earn their place (Author owns one identity used by *two*
  rules; distinct from `ItemId`). `BlockList`/`MuteList` wrapper types **cut** — they would own nothing
  beyond set membership; kept as `frozenset[Author]`/`frozenset[Topic]` on the request, with the rule in
  `EligibilityPolicy`. No rule-plugin framework, no UserPreferences port (YAGNI — only two rules
  received).
- **F5 (interaction R6×R7):** verified — diversity operates only on the eligible subset; a blocked item
  is never a diversity neighbor and is never resurrected.

Re-measured after revision: all exit criteria met; INV1–INV4 intact, INV5' / INV6 / INV7 / INV8 owned;
no substantial finding open. Design frozen.

## 6. Cost

- **Stage 1:** design passes run = **1**; mandatory revise rounds run = **1** (findings F1–F4 in
  stage-1 §7). Approx word count of `stage-1.md` ≈ **1,710 words** (plus the filed records: goals,
  base-dependencies, dependencies, architecture, ADRs 0001–0003).
- **Stage 2:** design passes run = **1**; mandatory revise rounds run = **1** (findings F1–F5 above).
  Approx word count of `stage-2.md` ≈ **1,700 words** (plus record deltas: goals/architecture edits,
  ADRs 0004–0006, state.md).
- **Total across both stages:** 2 design passes, 2 revise rounds (one mandated round each, no extra
  iteration). No spike/MVP round (feasibility was obvious — a stateless scoring+sort service). The
  stage-2 change reused the stage-1 owners without a single reopening of a rule owner, so its design
  cost was additive (two new stages) rather than a rewrite.
