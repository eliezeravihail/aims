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
