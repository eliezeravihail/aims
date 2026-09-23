---
title: "BP2 result — the trajectory edge reproduces on a cheaper model (n=2); mixed-tier rot did NOT compound"
date: 2026-09-20
---

# BP2 — the same 3-stage build on a weaker executor (haiku)

Identical product, cards, and hidden tests as BP1; the only change is **both arms run on a cheaper model
(haiku)**. Hypothesis (`plan.md`): under a weaker executor the plain arm would *not* refactor its early
shortcut to parity, so rot (extra reopens or a correctness break) would accumulate and aims' edge would
widen.

## The numbers

| | correctness (all 3 stages) | reopened-owner events | module lines s1/s2/s3 | s2 edit | s3 edit |
|---|---|---|---|---|---|
| **aims (haiku)** | **21/21** ✓ | **0** | 114 / 122 / 179 | +24/−16 (extend) | +57/−0 (extend) |
| **plain (haiku)** | **21/21** ✓ | **1** (stage-2 `available` reopen) | 99 / 121 / 171 | +33/−11 (reopen) | +50/−0 (extend) |

## What happened

- **Correctness is a tie — and the weak executor did NOT break.** Both haiku arms passed every hidden test
  at every stage, including the hardest (stage 3: confirm-past-expiry + partial). No wrong number shipped by
  either arm; the cheaper model handled the whole sequence correctly.
- **The trajectory pattern reproduced (n=2).** aims (haiku), guided by its records + one-owner review,
  derived availability from a reservation ledger at stage 1 and **extended at the seam** for both later
  changes (0 reopens). plain (haiku) kept a stored `_reserved` total at stage 1 and **reopened** the
  availability computation when expiry arrived (1 reopen), then extended stage 3 cleanly — exactly BP1's
  shape, now on a different model tier.
- **The mixed-tier hypothesis did NOT reproduce here.** The predicted compounding — a weak executor letting
  rot accumulate across stages — did **not** happen: haiku stayed correct and even the plain arm reopened
  cleanly (not messily) and then extended. On this tractable product, a cheaper model was still capable
  enough that its one reopen was clean and its correctness held. So the edge is the **same single avoided
  reopen** as BP1, not a widened gap.

## Honest verdict (BP1 + BP2 together, n=2)

The trajectory edge is **real, small, and stable across two model tiers**: aims' §5 one-owner /
derive-don't-store discipline (and its records steering fresh sessions) reliably **avoids one model reopen**
that the no-method arm pays when the time-dependent change arrives — while correctness stays tied. It is
**not** a correctness advantage and **not** (on these products) a compounding one, because capable models —
even the cheaper one — refactor their reopen cleanly rather than accumulating rot.

**What would be needed to see compounding** (the paper's real frontier, still not reached here): a product
where the early shortcut is *stickier* (cannot be cleanly rewritten), a *longer* sequence (5+ interacting
changes), or a genuinely weaker or constrained executor that does not refactor at all. Two 3-stage
products on two model tiers both show the modest, non-compounding shape. That is the honest current state of
aims' trajectory claim under running-code test: directionally confirmed, magnitude modest, compounding
unproven.
