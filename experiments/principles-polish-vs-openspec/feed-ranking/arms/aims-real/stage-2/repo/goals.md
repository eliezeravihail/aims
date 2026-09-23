---
title: "goals"
date: 2026-09-23
---
## Goal
A service that takes a `user` and a list of candidate items and returns those candidates as an **ordered
feed**: highest combined score first. The combination weights are deployment configuration an operator
changes without touching code.

## Core scenario (start → useful result)
An operator deploys with weights `recency 0.5, affinity 0.3, popularity 0.2`. A caller asks for user `u1`
with candidates `a (0.9, 0.1, 0.5)`, `b (0.2, 0.9, 0.9)`, `c (0.2, 0.9, 0.9)`. Scores: a = 0.58,
b = c = 0.55. The feed comes back `a, b, c` (b before c by id), each with its score and the id of the
weight config that produced it. The operator edits the weights and reloads; the next request is ranked
with the new weights, and no request is ranked with a mix of the two.

## Product decisions (grounded — PO answers of 2026-09-23; "choose" answers were handed back to the Guide)
- **Score** = weighted linear sum `w_r·recency + w_a·affinity + w_p·popularity`. Nothing else enters it.
  *(PO, Q1)*
- **Weights**: exactly the three named signals; each a finite number ≥ 0; at least one > 0. Not required
  to sum to 1 and never rescaled. *(handed back, Q2)*
- **Invalid config**: rejected with an error naming the problem. At startup the service does not start;
  on a reload the service keeps the last valid weights and reports the rejection. No request ever ranks
  with partial or invalid weights. *(handed back, Q3)*
- **Change timing**: weights come from a config file; a change takes effect after an explicit reload
  (restart or a reload call). No file watching. Each request is ranked entirely by one weight version.
  *(handed back, Q4)*
- **Signals**: the PO states all three are present and in [0, 1]. This is the input contract; a request
  that breaks it is rejected whole, naming the item and signal — never clamped, zero-filled or dropped.
  *(PO, Q5; rejection behaviour handed back)*
- **Item id / ties**: a non-empty string; equal scores (exact, no epsilon) order by id ascending, plain
  code-point string order (`"10"` before `"9"`). *(handed back, Q6)*
- **Duplicate id in one request**: the request is rejected. *(handed back, Q7)*
- **Response**: the ordered candidates, each with its score, plus the id of the weight config used.
  Empty candidates → empty feed, not an error. *(handed back, Q8)*
- **`user`**: carried for identity only in stage 1; does not affect score or order. *(handed back, Q9)*

## Non-goals (stage 1)
Per-user or per-segment weights; learned or non-linear ranking; decay; diversity/filtering rules;
pagination/truncation; file watching; persistence; network serving; computing the signals.

## Stage 2 — eligibility and diversity (received 2026-09-23)
**The change.** (1) *Eligibility.* An item by a blocked author, or on a muted topic, never appears in the
feed, however high its signals. It is absent, not shown low. (2) *Diversity.* In the returned order, no more
than 2 consecutive items share an author. Stage-1 scoring and operator-tunable weights keep working as before.

**Product decisions** (PO answers of 2026-09-23. Q1–Q3 were handed back ("choose a simple sensible
approach"), so the Guide adopted the default offered in QUESTIONS.md. Q4/Q5 were answered, and the
infeasible case was handed back.)
- **Where the lists come from.** Each request carries the user's block list (author ids) and mute list
  (topic ids) next to `user` and the candidates. Both are required parts of the request, and an empty
  list is allowed. The service stores nothing, and `user` still does not affect the result. *(handed
  back, Q1. "Required, may be empty" was chosen so that a caller who forgets the lists fails fast instead of
  silently showing blocked content.)*
- **Item metadata.** Each candidate has exactly one required author id, a non-empty string. It also has a
  required set of zero or more topic ids, each a non-empty string. An item is muted if **any** of its topics
  is muted. A missing or malformed author, topics or list entry rejects the whole request, naming the item
  where there is one. Matching is exact and case-sensitive. Repeated entries in a list, or in an item's
  topics, are allowed and mean the same as one entry. *(handed back, Q2)*
- **Validity comes first.** The stage-1 input contract applies to every candidate, including ones that will
  be filtered out. A blocked or muted item with a bad signal or a duplicate id still rejects the request.
  Eligibility applies only to a valid request. *(handed back, Q3)*
- **Diversity is a hard constraint.** Within it, preserve score order as much as possible. *(PO, Q4/Q5)*
  Reading adopted: build the feed position by position from the eligible items in stage-1 rank order
  (score desc, id asc). At each position, place the highest-ranked remaining item that would not make a
  third consecutive item by the same author. Deferred items keep their relative order. Examples:
  `a1[A] a2[A] a3[A] a4[A] b1[B] b2[B]` → `a1 a2 b1 a3 a4 b2`; `a1[A] a2[A] a3[A] b1[B] c1[C]` →
  `a1 a2 b1 a3 c1`.
- **When the constraint cannot be met, the unplaceable items are omitted.** *(the PO handed this back; Guide's
  choice.)* When every remaining item is by the author of the last two placed items, those items are left out
  and the feed ends. Example: `a1[A] a2[A] a3[A]` → `a1 a2`. The constraint is hard, so appending would
  break it. Rejecting the request would make the user's feed fail because of how the candidates happened to
  be distributed. Consequence, stated: the greedy reading favors score order over feed length.
  `b1[B] a1[A] a2[A] a3[A]` → `b1 a1 a2`. `a3` is omitted even though `a1 a2 b1 a3` would keep all four,
  because that order demotes the higher-ranked `b1`.
- **Response.** The shape is unchanged: ordered items, each with its own stage-1 score, plus the weights
  version. Filtered and omitted items are simply absent, and nothing reports how many were removed. The feed
  is no longer strictly score-descending. *(handed back, Q5)*

**Non-goals (stage 2).** Storing the lists; per-user weights; diversity by topic or any other key; a limit
of more than 2 or a configurable limit; reporting removed items; pagination; a generic rule or filter engine.
