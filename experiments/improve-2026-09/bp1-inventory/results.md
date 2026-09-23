---
title: "BP1 result — the trajectory edge is real but modest and non-compounding; correctness a tie; ~1.85x cost"
date: 2026-09-20
---

# BP1 — multi-stage build pilot (inventory reservation service): the trajectory, measured

A real 3-stage build (reserve → expiry → confirm+partial), running Python + hidden pytest per stage, two
arms (aims add-feature with co-located records vs a no-method "build it well"), later stages by **fresh
sessions**. Scored outcome-first per `decisions/0019`. Full protocol: `plan.md`; per-stage detail:
`stage-log.md`.

## The numbers

| | correctness (all 3 stages) | reopened-owner events | module lines s1/s2/s3 | tokens Σ | wall Σ |
|---|---|---|---|---|---|
| **aims** | **21/21** ✓ | **0** | 100 / 137 / 178 | ~258k | ~11 min |
| **plain** | **21/21** ✓ | **1** (stage-2 model rewrite) | 60 / 89 / 125 | ~140k | ~3 min |

**Blind judge** (blind to which arm used a method; sealed mapping X=plain, Y=aims — `snapshots/`) independently
reported: reopened-owner count **X=1, Y=0**; final design a **near-tie with aims marginally ahead** (aims
funnels both reserve paths through one `_record` write-seam, uses a named-tuple reservation, and guards id
collisions). It judged code structure and diffs, not method vocabulary, and still picked the aims arm.

## What actually happened (the mechanism)

- **Correctness is a tie.** Both arms passed every hidden test at every stage; neither shipped a wrong number.
- **The trajectory edge is real, and it traces to one stage-1 decision.** The aims arm made availability
  **derived, never stored** (`available = added − reserved`) at stage 1 — its review *explicitly rejected*
  a stored per-sku counter as "a second copy of the availability fact (drift risk) with no stage-1 force"
  (§5 one-owner). That choice made both later changes **additive**: expiry became one predicate inside the
  existing owner; confirm reused `expiry is None`. The plain arm stored availability at stage 1 (fine in
  isolation), which **forced a core rewrite** the moment time-dependent expiry arrived — one reopened owner.
- **But it did NOT compound.** After its stage-2 reopen, the plain arm had converged to the same derived
  model and absorbed stage 3 cleanly (0 further reopens). The paper's caveat holds: **a strong model
  refactors deeply**, so rot did not accumulate — the plain arm reached an equally-good (marginally worse)
  endpoint, having paid **one** reopen along the way.
- **Q2 continuity — a positive signal (n=1).** The fresh aims stage-2 session read the co-located record,
  which named the extension seam explicitly, and extended exactly there. The record steered a historyless
  session to the right seam — the outcome the earlier continuity experiment could not show at re-derivable
  scale. (Caveat: the derived design is also visible in the code, so the record confirmed more than it
  uniquely caused.)
- **Cost.** aims ≈**1.85× tokens**, ≈**3.7× wall-clock**, ~1.4× larger module — in the paper's 2.5–3×
  ballpark (a little lower here). The premium bought **one avoided reopen** and durable records, not a
  correctness win.

## Honest verdict

BP1 reproduces the paper's core claim **in the direction predicted but at modest magnitude on this product**:
the method's §5 one-owner / derive-don't-store discipline at stage 1 bought a cleaner trajectory (0 vs 1
reopened owner, blind-confirmed), and its records steered a fresh session — but the edge was a **single
avoided reopen**, not compounding rot, because a capable no-method model refactored to parity. This is
**not** a correctness advantage (there was none) and **not** a large structural gap; it is a real, small,
measured trajectory benefit at a real cost premium — exactly the honest shape the paper argues for, now
observed under a running-code test rather than asserted. n=1 product → suggestive.

**Where the edge should be larger (the next test, BP2):** under a **weaker executor** that does *not*
refactor deeply, the plain arm's early shortcut should accumulate instead of being rewritten to parity —
that is the condition (mixed-tier: cheap Worker, strong review) under which the paper predicts the gap
widens. BP2 runs the same sequence on a cheaper model to test it.
