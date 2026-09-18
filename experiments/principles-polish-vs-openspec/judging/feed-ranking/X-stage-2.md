# Stage 2 — Eligibility + Diversity (the-method change)

> Builds on the **frozen** stage-1 baseline (`stage-1.md`): capabilities `feed-ranking`
> and `ranking-weights`, plus the `add-feed-ranking` change bundle. Stage 1 weighted
> scoring and tunable weights keep working exactly as before. This file adds the change
> the-method-style: updated/new capability specs, then a new change bundle.

---

# PART A — CAPABILITY SPECS (updated `the-method/the-spec-store/`)

The change introduces **two new capabilities** and leaves the two stage-1 capabilities'
existing requirements untouched (see SURVIVAL). The feed is now produced by a fixed
pipeline: **eligibility → scoring/ordering (stage 1) → diversity**.

- `feed-eligibility` — remove blocked authors / muted topics before ranking (NEW).
- `feed-diversity` — cap consecutive same-author items after ranking (NEW).
- `feed-ranking` — unchanged behavior; one clarifying requirement about its position in the pipeline.
- `ranking-weights` — unchanged.

---

## `the-method/the-spec-store/feed-eligibility/spec.md`  (NEW)

### Purpose

Enforce a hard eligibility gate before ranking: an item whose author is on the user's
**block list**, or whose topic is on the user's **mute list**, must never appear in the
feed — it is *absent*, not merely ranked low. Eligibility is independent of every signal
and every weight; no score can rescue an ineligible item, and no weight can suppress an
eligible one.

### Requirements

#### Requirement: Blocked authors are removed entirely

The system must remove, before scoring, every candidate whose author is on the
requesting user's block list. Such candidates never appear in the returned feed at any
position, regardless of their signals or score.

##### Scenario: Item from blocked author is absent

- **Given** the user's block list contains author `alice`
- **And** a candidate authored by `alice` with `recency=1.0, affinity=1.0, popularity=1.0`
- **When** the feed is produced
- **Then** that candidate does not appear anywhere in the feed.

##### Scenario: High score cannot rescue a blocked author

- **Given** the highest-scoring candidate is authored by a blocked author
- **When** the feed is produced
- **Then** the feed's first item is the highest-scoring *eligible* candidate, and the blocked one is absent.

#### Requirement: Muted topics are removed entirely

The system must remove, before scoring, every candidate whose topic is on the
requesting user's mute list. Such candidates never appear in the returned feed.

##### Scenario: Item on muted topic is absent

- **Given** the user's mute list contains topic `politics`
- **And** a candidate on topic `politics`
- **When** the feed is produced
- **Then** that candidate does not appear anywhere in the feed.

#### Requirement: Eligibility precedes scoring and is signal-independent

The system must apply eligibility filtering before any scoring or ordering, so that
ineligible items are excluded on identity (author/topic) alone and never enter the
ranked set.

##### Scenario: Removed before scoring

- **Given** a candidate that is both blocked and would score highest
- **When** the feed is produced
- **Then** it is excluded during eligibility, not ranked-then-hidden.

#### Requirement: Empty lists and no matches are no-ops

The system must leave the candidate set unchanged when the block and mute lists are
empty or match nothing; eligibility never removes an item that is neither blocked nor muted.

##### Scenario: No block/mute lists

- **Given** empty block and mute lists
- **When** the feed is produced
- **Then** every candidate is eligible and passes to ranking unchanged.

##### Scenario: All candidates ineligible

- **Given** every candidate is blocked or muted
- **When** the feed is produced
- **Then** the returned feed is empty and the request succeeds.

---

## `the-method/the-spec-store/feed-diversity/spec.md`  (NEW)

### Purpose

Prevent author monotony in the final order: **no more than 2 items in a row may share the
same author**. When a third consecutive same-author item would occur, it is **deferred to
the next non-violating position**, and order is otherwise preserved as much as possible.
Diversity operates on the ranked, eligible list; it reorders but never adds or drops items.

### Requirements

#### Requirement: At most two consecutive items share an author

The system must ensure that in the returned order no three adjacent items have the same
author. A candidate that would become the third consecutive same-author item is deferred
past the run.

##### Scenario: Third consecutive same-author item is deferred

- **Given** the ranked order is `[A1, A2, A3, B1]` where `A*` share author `A` and `B1` is author `B`
- **When** diversity is applied
- **Then** the returned order is `[A1, A2, B1, A3]` — `A3` deferred to the next non-violating position.

##### Scenario: Two in a row is allowed

- **Given** the ranked order is `[A1, A2, B1]`
- **When** diversity is applied
- **Then** the order is unchanged: `[A1, A2, B1]` (two consecutive is within the cap).

#### Requirement: Deferral goes to the nearest non-violating position, order otherwise preserved

The system must move a deferred item to the earliest position at which placing it does
not create three-in-a-row, keeping the relative order of all other items and of same-author
items among themselves as much as possible (a stable, minimal reordering, not a reshuffle).

##### Scenario: Deferral is minimal

- **Given** the ranked order is `[A1, A2, A3, A4, B1]`
- **When** diversity is applied
- **Then** the order is `[A1, A2, B1, A3, A4]` — `A3` placed right after `B1`; `A4` follows since only two `A` now precede it at that point; relative `A` order and `B1`'s position are preserved as far as the cap allows.

##### Scenario: No eligible non-violating slot until the end

- **Given** the ranked order is `[A1, A2, A3]` with no other author present
- **When** diversity is applied
- **Then** the constraint cannot be satisfied; the system must place the surplus item(s) at the end in ranked order (`[A1, A2, A3]`), preserving completeness over the cap, and MAY surface that the cap could not be met.

#### Requirement: Diversity preserves the item set

The system must return exactly the items it received from ranking — none added, none
dropped, none duplicated — changing only their order.

##### Scenario: Set unchanged

- **Given** a ranked list of `N` eligible items
- **When** diversity is applied
- **Then** the output is a permutation of those same `N` items.

#### Requirement: Diversity runs after scoring/ordering and never changes scores

The system must apply diversity as the last pipeline stage, operating only on positions.
It must NOT recompute or alter any score, and must NOT reintroduce ineligible items.

##### Scenario: Scores untouched

- **Given** a ranked, eligible list
- **When** diversity is applied
- **Then** each item's score is identical to before; only ordering may differ.

---

## `the-method/the-spec-store/feed-ranking/spec.md`  (clarified, existing requirements survive)

### Purpose (amended note)

All stage-1 requirements stand. One clarifying requirement is **added** to pin
`feed-ranking`'s position in the now-three-stage pipeline. Nothing in stage-1 is rewritten.

#### Requirement: Ranking operates on the eligible set only

The system must score and order only the candidates that survive eligibility filtering,
and must hand its ordered result to the diversity stage. Ranking neither filters on
identity nor enforces author caps itself.

##### Scenario: Ranking sees only eligible items

- **Given** eligibility removed the blocked/muted candidates
- **When** ranking runs
- **Then** it scores and orders exactly the remaining eligible candidates by the stage-1 rules.

---

# PART B — CHANGE BUNDLE (`the-method/changes/add-eligibility-and-diversity/`)

## `a-design-doc`

### Why

Two user-protection and quality rules are now required on the **same** feed request:
users must never see content from authors they blocked or on topics they muted, and the
feed must not clump many items from one author together. Both must hold while stage-1
weighted scoring and operator-tunable weights keep working exactly as before.

### What changes

- **Add** capability `feed-eligibility`: hard pre-ranking removal of blocked-author /
  muted-topic items (absent, not low).
- **Add** capability `feed-diversity`: post-ranking cap of at most 2 consecutive
  same-author items, deferring the third to the next non-violating slot.
- **Clarify** `feed-ranking`: it operates on the eligible set and feeds the diversity stage.
- **No change** to `ranking-weights` or to any stage-1 scoring/ordering requirement.

### Impact

- Request contract gains per-user `block_list` (authors) and `mute_list` (topics), and
  each candidate must carry `author` and `topic` identifiers.
- Response is still an ordered list of the same shape; it may be shorter (eligibility) and
  differently ordered (diversity) than a pure stage-1 result.
- Pipeline becomes three stages: eligibility → ranking → diversity. Stateless still.

## `a-design-doc`

### Architecture decisions

1. **Three-stage pipeline, one direction.** `eligibility → ranking → diversity`. Each
   stage is a pure function; the composition is a pure function of
   `(candidates, block_list, mute_list, weights)`. This is the key structural choice: the
   two new rules are new *stages*, not edits to scoring.

2. **Eligibility is a filter, placed first.** Because blocked/muted items must be *absent*
   regardless of signals, the only correct place is *before* scoring — filtering on
   `author ∈ block_list` or `topic ∈ mute_list`. Putting it first also means ranking and
   diversity never have to reason about eligibility. Membership tests use set lookup.

3. **Diversity is a reordering, placed last.** The cap is a property of final adjacency, so
   it must run after the score order exists. It moves positions only; it cannot change
   scores or resurrect filtered items. Chosen algorithm: single left-to-right pass over the
   ranked list maintaining a small deferral queue —
   - keep a window of the last two placed authors;
   - if the next ranked item would make three-in-a-row, push it onto a per-author deferral
     buffer and instead emit the highest-ranked *buffered or upcoming* item whose author
     differs from the current run;
   - when no differing item exists, the run is unavoidable → append remaining items in
     ranked order and flag "cap not fully satisfiable".
   This yields a **stable, minimal** reordering: non-deferred items keep their relative
   order, and deferred items reinsert at the earliest legal slot in ranked order.

4. **Scoring seam reused unchanged.** Because stage 1 injected `Weights` into a pure scorer
   (its stage-1 design decision #2), scoring needs no modification — eligibility hands it a
   subset, diversity consumes its output. The weights config surface is untouched.

5. **Determinism preserved end to end.** Eligibility filtering is order-preserving; ranking
   keeps its `(-score, id)` total order; diversity's pass is deterministic given that order.
   Same input → same output still holds.

### Component structure

```
Request ingress
  ├─ validate signals in [0,1]                (stage 1, unchanged)
  └─ read block_list (authors), mute_list (topics)   (NEW input)

Eligibility filter        (feed-eligibility, NEW)
  └─ drop candidate if author ∈ block_list OR topic ∈ mute_list
        -> eligible[]

Weights provider          (ranking-weights, unchanged)
Scorer + Orderer          (feed-ranking, unchanged logic)
  └─ score(eligible, weights); sort by (-score, id)
        -> ranked[]

Diversity reorderer       (feed-diversity, NEW)
  └─ single pass; cap = 2 consecutive same author; defer 3rd to next legal slot
        -> feed[]

Response
```

- **Eligibility filter** — owns identity-based removal; the only stage that shortens the list.
- **Scorer + Orderer** — untouched stage-1 components.
- **Diversity reorderer** — owns adjacency; the only stage that permutes without filtering.

### Data shapes (delta from stage 1)

- `Candidate` gains `author` and `topic` identifiers (signals unchanged).
- Request gains `block_list: [author]` and `mute_list: [topic]`.
- Intermediate `eligible[]` and `ranked[]` are the same `Candidate` shape; `feed[]` is the
  final permutation.

### Edge cases

- All items ineligible → empty feed (eligibility req).
- Fewer than 3 items, or all distinct authors → diversity is a no-op.
- A single author dominates so the cap cannot be met → completeness wins; surplus appended
  in ranked order, optionally flagged (diversity req).

## `a-design-doc`

- [ ] Extend request contract with `block_list` (authors) and `mute_list` (topics).
- [ ] Extend `Candidate` with `author` and `topic` identifiers.
- [ ] Implement `feed-eligibility` filter: drop `author ∈ block_list OR topic ∈ mute_list`, before scoring.
- [ ] Insert eligibility as the first pipeline stage; confirm ranking receives only eligible items.
- [ ] Keep `feed-ranking` scorer/orderer unchanged; wire it to consume `eligible[]`.
- [ ] Implement `feed-diversity` reorderer: single pass, cap 2 consecutive same author, defer 3rd to next legal slot.
- [ ] Handle the unsatisfiable case: append surplus in ranked order, flag "cap not met".
- [ ] Wire pipeline: ingress → eligibility → ranking → diversity → response.
- [ ] Tests (eligibility): blocked author absent even at top score; muted topic absent; empty lists no-op; all-ineligible → empty feed.
- [ ] Tests (diversity): two-in-a-row allowed; third deferred to next non-violating slot; deferral is minimal and order-preserving; set is a permutation; scores unchanged.
- [ ] Regression tests: all stage-1 scenarios (weighted sum, descending order, id tie-break, determinism, un-normalized weights, operator weight change) still pass.
- [ ] Integration test: eligibility + diversity on one request together, stage-1 scoring intact.

---

# PART C — SURVIVAL

Per stage-1 spec/component: **survived** (unchanged), **extended** (kept, added to),
**reopened** (existing requirement re-examined/rewritten), **discarded**.

| Stage-1 item | Verdict | Note |
|---|---|---|
| Spec `feed-ranking` — weighted-sum score | **survived** | Untouched; scoring identical. |
| Spec `feed-ranking` — descending order | **survived** | Still the ordering rule within the ranked set. |
| Spec `feed-ranking` — id tie-break / determinism | **survived** | Still applies; diversity is deterministic on top of it. |
| Spec `feed-ranking` — signal range validation | **survived** | Unchanged ingress rule. |
| Spec `feed-ranking` — empty list → empty feed | **survived** | Still holds (also reachable via all-ineligible). |
| Spec `feed-ranking` — pipeline position | **extended** | One clarifying requirement added: ranking runs on the eligible set and feeds diversity. No stage-1 wording rewritten. |
| Spec `ranking-weights` (all requirements) | **survived** | Weights config, validation, non-normalization all unchanged. |
| Component: pure Scorer (weights injected) | **survived** | Reused verbatim; the stage-1 injection seam is exactly why no rewrite was needed. |
| Component: Orderer `(-score, id)` | **survived** | Reused as-is; diversity consumes its output. |
| Component: Weights provider | **survived** | Untouched. |
| Request/response contract | **extended** | Added `block_list`, `mute_list`, and candidate `author`/`topic`; existing fields unchanged. |
| Pipeline shape | **extended** | One-stage (rank) → three-stage (eligibility → rank → diversity). Additive framing, not a redesign of the middle stage. |
| — | **reopened**: none | No stage-1 requirement was reinterpreted or rewritten. |
| — | **discarded**: none | Nothing removed. |

**Additive or rewrite?** The new rules were **additive**. Both new capabilities attach at
pre-existing seams — eligibility as a filter *before* the injected-weights scorer,
diversity as a reordering *after* the total-order sort — so no stage-1 requirement or
component was rewritten. The stage-1 decision to make the scorer a pure function with
weights injected (rather than a monolith reading config and filtering inline) is what kept
this purely additive: the two rules bracket the ranking stage instead of cutting into it.

---

## Cost

- **Passes:** 2 design passes total — one for stage 1 (specs + change bundle, frozen), one
  for stage 2 (new/updated specs + change bundle + survival). No rework pass on stage 1 was
  needed; the seams held.
- **Approximate word counts:**
  - Stage 1 design (`stage-1.md`): ~1,050 words.
  - Stage 2 design (`stage-2.md`, this file, incl. survival + cost): ~1,300 words.
