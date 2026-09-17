---
title: "Pilot result — feature-based identification (plants → minerals), aims vs OpenSpec"
date: 2026-09-17
---

# Result: aims vs OpenSpec on the plant→mineral identifier

Run per [`plan.md`](plan.md): two arms designed the same product across two staged reveals (stage 1
plants, stage 2 add minerals with a disjoint feature schema), each built by fresh builders with no
cross-leak, then judged **blind** (labels shuffled, method names and the aims arm's self-review stripped)
on `design-principles.md` §0–§14 against the frozen [`inventory.md`](inventory.md). n = 1.

## Outcome — the home method lost this round

| | graded | worst chapter | (#S3,#S4) | weighted |
|---|---|---|---|---|
| OpenSpec arm | **8.5** | §4 (S2) | (0,0) | 9.54 |
| **aims arm** | **5.0** | **§1 (S4)** | (0,1) | 6.63 |

The **aims arm lost, decisively, on the check this product is built around** — and it is worth recording
plainly rather than explaining away.

- **Check 1 — the stage-2 reopen (R7/R8/R9, X1): a near tie.** Both arms absorbed the mineral domain as an
  **extension at a seam** — plant identification frozen, the match/rank/explain core reused not copied, a
  third domain (birds) slotting in via one adapter + one registration. The aims arm's reopen footprint was
  if anything *slightly cleaner* (it left `input` and `identification` literally unchanged and reopened only
  `FeatureId`/`Unit` enum→value-object plus a `SpeciesRecord`→`ReferenceRecord` rename), and its foundational
  value objects (§0/§4) were a touch more elegant. On the axis the pilot was designed to stress, the method
  held up well.

- **Check 2 — the numeric-range feature (X4/C6): the aims arm was clean-but-wrong.** It modeled an
  observation as `Term | Quantity` — a single point. An observed Mohs hardness of "6.5–7" (which the stage-2
  card names explicitly) is therefore **unrepresentable**: the parser reports it `MALFORMED_QUANTITY`, and
  the `QuantityRange.overlaps` method it did define is **dead code on the match path** (matching uses
  `span.contains(point)`). The OpenSpec arm got this right: observed value is `float | NumericRange`, match
  is inclusive overlap, a single figure is the degenerate interval `[x,x]` for which overlap ≡ the stage-1
  `contains(x)` — so it added the range case *and* preserved stage-1 plant behaviour exactly. That is a §1
  functional-correctness failure (precondition → S4), and it caps the aims arm at 5.0.

## What this pilot actually shows

1. **The instrument works and is not a home-team referee.** Judged blind, on the single form, the
   measurement caught a real S4 correctness defect in the *aims* arm and ranked the competitor above it.
   A biased or coarse instrument would have flattered the home method; this one did the opposite, which is
   the strongest available evidence that §0–§14 grades the design and not the pedigree.

2. **A single build pass — even with the mandatory self-review — can rationalize a required capability
   away under YAGNI.** The aims arm's own self-review explicitly *cut* range-valued observations calling it
   YAGNI. But an observed range is a **stated present force** here (the card and X4 name it), not speculative
   generality — so the subtractive cut was misapplied. The guard the method already carries (§1 "trace the
   full input space", and the §7 YAGNI tie-break, which resolves *by the change-axes*: X4 names the very
   feature) points the other way; the builder simply did not run §1 over X4 hard enough to notice that the
   type model could not represent a case the spec requires.

3. **The reopen axis was the wrong thing to fear.** The pilot was built to stress domain-extension seams,
   and *both* methods handled that cleanly. The defect that decided the contest was ordinary
   functional-correctness on an input-space corner — the failure mode §1 exists for. That is a useful
   recalibration: structure-vs-YAGNI got the attention; tracing the full input space is where the round was
   won and lost.

## A candidate refinement (for the iteration round, not applied here)

The honest reading is that this was a **builder** miss, not a hole in the document — §1 and the §7 tie-break
already cover it. The one wording question worth putting to the iteration round: whether §7 (YAGNI /
subtractive) should state outright that **a capability named by an R/X/C item is by definition a present
force, so it is never a YAGNI cut** — making explicit the precedence of §1 correctness over the subtractive
discipline that the aims builder here got backwards. Recorded as a candidate; not folded into the central
document unilaterally.

Artifacts (blind judge report and both arms' stage-1/stage-2 designs) are in the run scratchpad; this file
is the durable reading.
