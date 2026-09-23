# Questions for the product owner — feed ranking stage 2

Context: stage 1 returns every candidate exactly once, ordered by weighted score, then by `item_id`. Stage 2
adds eligibility (block/mute) and diversity (no more than 2 same-author items in a row). The diversity rule is
read as: walk the score order, and at each position take the highest-ranked remaining item that does not make a
third consecutive same-author item. Anything skipped keeps its place in the queue.

## Q1 (blocking): what happens when the diversity rule cannot be met?

Sometimes no valid position is left for a deferred item. For example, after eligibility filtering the
candidates are `A1, A2, A3` (all from author A), or `A1, A2, A3, A4, B1` (in any valid order, one A item still
ends up third in a row). The two rules then conflict:

- "no more than 2 items in a row may share the same author" (a hard limit), and
- "it is deferred to the next available position" (the item is postponed, not removed; unlike muted items,
  nothing says it disappears).

Which should win?

- **(a) Best effort, keep everything:** place items with the rule as long as any valid choice exists. After
  that, add the leftover same-author items at the end in score order, so the tail breaks the rule.
  The feed stays complete (the stage-1 promise that every eligible item appears exactly once still holds).
- **(b) Strict, drop the leftovers:** items that cannot be placed without breaking the rule are left out, so
  the returned feed can be shorter than the eligible set.
- **(c) Something else**, for example returning the leftovers separately or reporting them as an error.

Recommended default if you have no preference: **(a)**, because it drops no content, and a violation can only
happen at the tail, when one author is all that is left.

## Q2 (minor, a default is assumed unless you say otherwise): shape of the new inputs

- Assumption: each candidate gains a required `author` (string) and a required `topic` (a single string). The
  request carries the user's `blocked_authors` and `muted_topics` as optional lists of strings (default
  empty), since the service keeps no stored state.
- Matching is an exact, case-sensitive string match.
- Is that right? In particular, **can an item have more than one topic?** If it can, it would be excluded when
  *any* of its topics is muted.

## Q3 (minor, a default is assumed): what does the caller see about excluded items?

- Assumption: blocked or muted items are simply absent from the response, with no count and no reason given.
  They are still validated like any other candidate (a malformed blocked item still rejects the request), so
  that a bad upstream payload never goes unnoticed.
