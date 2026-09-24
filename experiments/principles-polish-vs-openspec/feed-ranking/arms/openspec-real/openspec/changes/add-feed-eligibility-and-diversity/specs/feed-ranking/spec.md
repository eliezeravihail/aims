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
