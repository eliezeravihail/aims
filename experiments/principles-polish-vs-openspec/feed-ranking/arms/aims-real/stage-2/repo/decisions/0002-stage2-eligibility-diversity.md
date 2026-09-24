---
title: "Stage 2: eligibility as a filter owned by the valid request, diversity as a run limit inside the order's owner"
date: 2026-09-23
---
**Context.** This is the opening design round of the stage-2 product change: block and mute lists, and at
most 2 same-author items in a row (goals.md "Stage 2"). Three independent axis Workers (clean code,
encapsulation, genericity) worked one shared objective. The Guide merged the three, measured the merge,
and ran the mandatory revise round. The full architecture is in DESIGN.md.

**Decision.**
- **Eligibility is a filter.** Its one owner is `FeedRequest.eligible_candidates()`.
  - Validity comes first by construction: the method exists only on a valid `FeedRequest`, and that
    validity covers every candidate, including ones that will be filtered out.
  - `rank_feed` reads candidates only through this method. So the library, CLI and internal paths all
    filter, and ineligible items are never scored.
- **`rank_feed` still owns the order**, now as run limit ∘ rank order ∘ eligibility.
  - The stage-1 sort key survives verbatim as the rank order.
  - The run limit (`ranking._limit_author_runs`) is a private sequence constraint over `Candidate`s,
    which carry no score. It places greedily, keeps deferred items in their relative order, and omits the
    infeasible tail.
- **New data follows the stage-1 grain.**
  - `Candidate.author: str` and `topics: frozenset[str]`.
  - `FeedRequest.blocked_authors` and `muted_topics: frozenset[str]`, all required and keyword-only.
  - One private owner of "what an id is" (`_require_id`, `_require_id_set`). It refuses a bare string or a
    mapping where a collection is expected.
- **No new module, public type, error type or dependency.** This **supersedes** only the stage-1 "Order"
  row of decisions/0001 and DESIGN.md §9 (stage 1): the order is no longer the sort key alone.

**Strengths harvested per axis.**
- *Clean code.*
  - Proved the change needs no new module, type, error or import.
  - Put the run limit next to the owner of the order, as one private function.
  - Supplied the smell check: feature envy on `eligible_candidates` is answered by where the rule's data
    lives.
  - Supplied the invariant "ranking never reads `request.candidates`" as the stage-2 counterpart of "read
    `_weights` once".
  - Noted that a `set` has no stable iteration order, so which bad entry an error names first is
    unspecified for set input.
- *Encapsulation.*
  - Surfaced the traps that would silently iterate: a bare string, or a `dict` used as a collection of
    ids.
  - Stated the residual honestly: Python cannot stop `ranking.py` from reading `request.candidates`, so a
    three-path behavioral test guards it.
  - Contributed the formal contract of the run limit (postconditions 1–4).
  - Proposed rerunning the stage-1 numeric guards with a forced deferral, to show exactness survives the
    arrangement.
  - Placed list presence on the library path in the signature: no default, because a default of `()` is
    the silent failure the product ruled out.
- *Genericity.*
  - Calibrated each new type from both ends. Topics and lists **accept** any iterable of strings and
    **store** a `frozenset`, because repeats mean one and matching is membership.
  - Showed the run limit needs no score, so its input type *is* the barrier: `Sequence[Candidate]`, not
    `(Candidate, score)` pairs.
  - Named what gets no seam (the diversity key, the limit, a filter engine, storing lists).
  - Separated the author and topic namespaces.
  - Showed that `FeedService` not changing is evidence the stage-1 seam was calibrated right.

**Axis splits and how each was resolved.**
- *Where the run limit lives.* Encapsulation wanted a leaf `diversity.py` module, generic in `T` with an
  `author_of` callable, so that "cannot see scores" is machine-checkable by the import graph. Clean code
  and genericity wanted a private function in `ranking.py`. **Chose the private function over the
  module.**
  - `Candidate` carries no score, so the score barrier already holds in the input type.
  - A module plus a callable parameter for one caller is a seam nobody crosses.
  - The part the module would have added (no re-ranking by id or signals) is stated in DESIGN.md §9 as a
    convention, guarded by the "earliest placeable remaining item" property test.
- *Who owns "the lists are present" on the data path.* Genericity wanted a new `FeedRequest.from_mapping`
  owning the request key set, because "required" is a product rule. Clean code and encapsulation wanted
  the stage-1 `cli` shape check to gain the two keys. **Chose the CLI shape check over `from_mapping`.**
  - decisions/0001 places the request's JSON shape in `cli`, and there is one data adapter.
  - The force for `from_mapping` arrives with a second adapter. That is when to move it, and the move is
    local.
  - Unknown top-level keys keep their stage-1 treatment.
- *What a collection of ids accepts.* Clean code proposed a closed alias
  `IdCollection = list | tuple | set | frozenset`. Encapsulation and genericity proposed "any iterable
  except `str`, `bytes` or a mapping". **Harmonized.** Both pulls aim at the same thing: refuse the silent
  character-wise or key-wise iteration. The refusal list does that and still accepts every honest producer
  (a generator, dict views), so the clean axis gets its fail-fast and the genericity axis its ceiling.
- *Query vs property.* Genericity had `eligible_candidates` as a property; the other two had a method.
  **Chose the method**, because it computes a filtered collection, not an attribute.
- *First-problem order in `FeedRequest`.* The drafts differed on whether duplicate ids or the lists come
  first. **Chose user → lists → duplicate ids** (two of three). Either order is fine; one had to be fixed.
- *Score carrier.* Encapsulation used a private `_Scored` pair, genericity a score map keyed by id, and
  clean code a map keyed by `Candidate`. **Chose the map keyed by `item_id`.** Ids are unique by the
  `FeedRequest` invariant, and the map lets the run limit receive plain `Candidate`s, which is what keeps
  scores out of its reach.

**Product choices the PO handed back (Guide's, recorded in goals.md).**
- The lists are required on each request, and an empty list is allowed.
- Validity comes first.
- An infeasible tail is omitted rather than appended or rejected. The stated consequence is
  `b1 a1 a2 a3` → `b1 a1 a2`.

**Rejected** (details in DESIGN.md §8–§10):
- a `-inf` or penalty score;
- diversity in the sort key;
- filtering in the service, in the CLI, at construction, or after diversity;
- `Candidate.is_eligible`;
- `Exclusions`, `AuthorId` and `TopicId` types;
- a filter protocol;
- a length-maximizing arrangement;
- `max_run` or `key` parameters, or a `diversify` flag;
- defaults on the new keywords;
- new error types.

**Consequences.**
- Stage-1 library calls without the new keywords become `TypeError`s. This is deliberate.
- The feed is no longer strictly score-descending.
- An eligible item can be missing from the feed because of diversity. The response never says so.
- The run limit is O(n²) in the worst case, because no performance requirement is stated.
