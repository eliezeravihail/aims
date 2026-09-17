---
title: "Single-pass re-runs under the assessment form — anchored, then neutral"
date: 2026-09-17
---

# Single-pass re-runs under the assessment form

The aims arm rebuilt **single-pass** (one designer, not the panel) under the current method — the single
source ([`../../skills/aims-guide/references/design-principles.md`](../../skills/aims-guide/references/design-principles.md)),
the sub-check build discipline ([`../judging-rubric/quality-metrics.md`](../judging-rubric/quality-metrics.md)),
the §13 correctness trace over the full input space, and the one mandatory self-review-and-revise round
(`decisions/0011`) — then every arm graded **blind** on the 0–10 assessment form
([`../judging-rubric/assessment-form.md`](../judging-rubric/assessment-form.md)), one judge per product,
labels shuffled. Reference arms (OpenSpec, plain) are the existing frozen designs, re-graded on the form.
Two runs were done; the second corrects a measurement flaw in the first.

## Run 2 — neutral prompts, current method (the reading to trust)

The build prompts carried the **raw product spec only** (no pointing at any hard corner), and the judge
prompts carried the rubric + the frozen Step-0 inventory with **no "look here" hint from the operator**.
This is the de-anchored run.

| product | aims single-pass (new) | OpenSpec | plain |
|---|---|---|---|
| **checkout** | **8.5** — worst 7, (0,0); §13 S2 (non-stackable winner compared on pre-clamp face) | 8.5 — §4 S2 + §13 S1 | 8.5 — §4 S2 |
| **marketplace** | **9.9** — worst 8, (0,0); §2 S1 (a read-model facet cram) | 7.5 — §6 S3 (reopen) | 7.5 — §6 S3 (reopen) |
| **ledger** | capsule-aware **10.0**; blind **8.5** (§4 S2) | — | — |

- **Checkout is a three-way tie at the 8.5 cap, no S3/S4 in any arm.** aims is **no longer last** here. Its
  build's own §13 full-space trace caught the cart-discount→line allocation and the clamp interaction (its
  self-review listed "per-line allocation of cart discounts" and "clamp-as-effective-cap"); the residual is
  a narrow §13 S2 (it selects the non-stackable winner on the pre-clamp face magnitude, mis-attributing the
  superseding code only when both codes exceed the remaining base — no acceptance case reaches it).
- **Marketplace: aims first**, by absorbing the car category with zero core edits where both others reopen
  fulfillment/order (§6 S3).

## Run 1 — earlier, operator-anchored (superseded on checkout)

The first run's prompts were **contaminated by the operator**: the build prompt ordered "you MUST test the
multi-line SOUTH allocation" and the judge prompt said "pay special attention to whether each design
allocates a cart discount." Both sides were pointed at the same corner, so a finding there is not
independent evidence.

| product | aims single-pass | OpenSpec | plain |
|---|---|---|---|
| checkout | 7.5 — §13 **S3** (clamp re-allocated in SOUTH) | 8.5 | 8.5 |
| marketplace | 9.9 | 7.5 | 7.5 |

The checkout **S3 did not reproduce** once the anchoring was removed (run 2: 8.5, S2). Two things changed
between the runs and **both plausibly contributed** — the de-anchoring, and the §2 method rebalance
(`decisions/0013`: dropped the "second-implementation" criterion, disease-ranking toward structure); at
n = 1 they cannot be cleanly separated. What is established: **the earlier "aims is last on checkout" did
not survive either correction.**

## Confounds — do not over-read any single grade

- **Judge ±0.5.** One judge per product; a 0.5 gap is inside the instrument's precision. Checkout's three
  8.5s are a genuine tie.
- **Maturity / N/A asymmetry (marketplace).** The new aims arm is a full typed design; the reference arms
  are ~5KB sketches, and the judge scored §14/§15 for aims but marked them `N/A(code)` for the sketches —
  which inflates aims' marketplace margin. Read 9.9 vs 7.5 as "won the §6 extension axis," not a 2.4-point
  quality gulf.
- **n = 1** per product, one judge, one build each. The value is the recurring shape, not any number.

## Reading

Under neutral measurement and the rebalanced method, aims **ties checkout and leads marketplace** — a
better showing than any prior run, and the specific "aims below plain on checkout" result is retracted as a
measurement artifact of operator anchoring. It remains n = 1, LLM-judged, product-dependent; no single grade
is a verdict on the method.
