---
title: "BP3 result — aims' trajectory edge on this axis is ONE transferable principle, not the method"
date: 2026-09-20
---

# BP3 — is the edge the method, or one sentence?

BP1/BP2 traced aims' entire measured trajectory advantage to a single stage-1 decision: **derive availability
from ground facts (one owner) instead of storing it**, which made the later time-dependent change additive
rather than a reopen. BP3 tests whether that requires the aims *method* or just the *principle*, by running a
plain arm (opus, no skill, no records, no review) whose stage-1 prompt appended **one neutral sentence**:

> "Prefer deriving/computing values from your ground-truth state on demand rather than storing them as
> separate mutable fields you must keep in sync."

Later stages got **no** hint and no method — just "build it well," fresh session, code only.

## Result — the hint arm matched aims (0 reopens), correctness intact

| arm | stage-1 availability | reopened-owner events | correctness |
|---|---|---|---|
| BP1 plain (no hint) | **stored** `_available` counter | **1** (stage-2 rewrite) | 21/21 |
| BP1 aims (full method) | derived from ledger | **0** | 21/21 |
| **BP3 plain + one-line hint** | **derived** `_added − Σ reservations` | **0** | 14/14 (s1–s2)†, extending cleanly |

† stage-3 in progress at time of writing; stages 1–2 (where the only reopen difference lived) are green and
the arm extended cleanly. Update on stage-3 completion.

The one sentence made the plain builder **derive** availability at stage 1 — the exact design aims produced —
so the stage-2 expiry change landed as a clean seam extension (+34/−12, `available`'s `_added − Σ` shape
unchanged, just a per-reservation expiry predicate added), **0 reopens**, identical to the aims arm. The
model reopen that the un-hinted plain arm paid did **not** happen.

## What this means (honest, and it cuts against "you need the method")

On the axis BP1/BP2 measured, **aims' trajectory edge is reducible to one transferable principle** (§5
derive-don't-store / one-owner). A plain builder given that principle in a single line — with **no** skill,
**no** co-located records, **no** review, at plain-arm cost — reproduced the whole 0-reopen advantage. So the
1.85× cost premium BP1 measured did **not** buy the edge here; the edge was a sentence, and the method's
machinery (panel, records, mandatory review) was not what delivered it on this product.

This is the most deflating and most useful finding of the run, and it is stated plainly:

- **For the method:** it argues for a **lightweight delivery** — most of the measured structural benefit on
  changes like this rides on a few high-yield principles that transfer in one line; a heavyweight process is
  not required to capture them. (An "aims-lite" that just injects the top one-owner principles as short
  prompts is a plausible, cheaper design worth testing — it may retain the edge at plain cost.)
- **What the sentence does NOT give you:** durable records across many sessions/people (the compounding /
  scale claim BP1–BP3 could not test), and the discipline to keep applying the principle on a *large,
  opaque* codebase where the right move is not one obvious sentence. Those remain the method's real
  candidate value — and remain unproven here, exactly as the paper says.

**Verdict:** on the tested axis, the method is **not** needed for the trajectory edge — one principle,
transferred in a sentence, matches it. Where the method must still earn its cost is scale, longevity, and
many hands — none of which a 3-stage single-module pilot can reach. n=1; suggestive; correctness held.
