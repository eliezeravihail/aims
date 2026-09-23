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
