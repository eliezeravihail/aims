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
