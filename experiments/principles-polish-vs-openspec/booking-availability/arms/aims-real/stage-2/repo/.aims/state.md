# aims Guide State

## Mode

auto

## Loop cursor

awaiting-human — O2 met; DESIGN.md (stage 2) written with architecture.md and decisions/0005. Design only:
no implementation objective until the next product change or an explicit build request.

## Current objective

**Kind:** design (adapts the agreed-but-unbuilt stage-1 design; reviewed also with the add-feature lens)

**Objective (O2):** Adapt the stage-1 architecture so buffer, minimum notice and granularity are each
absorbed at exactly one owner, every stage-1 rule keeps its single owner, and stage-1 behaviour is exact
under default settings — pinned to concrete Python 3.11 stdlib skeleton and signatures.

**Why now:** Stage-2 product change received; owner answers filed (decisions/0004). Design is unbuilt, so
the change is cheapest here.

**Exit criteria:** `.aims/panel/2026-09-23-stage2/objective.md` — H1–H4 resolved with reasons; S1–S16
traced; rule→owner table covers R1–R6, B1–B3, G1, N1–N2, V1, M1.

**Preserve:**
- decisions/0001–0004; stage-1 outputs under default settings; design only — no implementation code.

**Do not optimize for:**
- multi-resource, breaks, zones, booking storage, output caps; a Strategy hierarchy for its own sake.

## Worker handoff

`.aims/panel/2026-09-23-stage2/objective.md` + one axis block per Worker.

## Open assumptions (unproven — carried, not filed)

- none. Feasibility is not in doubt.

## Open Guide TODO

- [x] Answers to Q1–Q4 filed (goals.md, decisions/0002)
- [x] O1: panel → merge → measure → revise round → re-measure (met)
- [x] Write DESIGN.md (+ architecture.md, decisions/0003)
- [ ] Owner confirmation of stated assumptions A1, A3, A5 (non-blocking; A5 granularity now touched by Q3)
- [x] Stage 2: answers to Q1–Q4 filed (decisions/0004, goals.md)
- [x] Stage 2 O2 (met — panel → merge → measure → revise → re-measure): buffer absorbed in the one occupancy owner (not a trailing filter, not a synthetic booking); grid replaces/coexists with R1 at its one owner; notice cutoff at one owner; time model gains date/now

## Last evaluated result

O2 revised: met. First measurement of the merge: no S3/S4; six S1–S2 findings (false A5 cost claim, I2′
load-bearing but unpinned, dual naive-time check unexplained, vague R1 wording, oracle anchor undefined,
missing crossings). The revise round resolved all six and fixed two more (R2 row wording, date.max trace).
Re-measured by hand: B23–B28 and the corrected traces hold. Residual: A12/A14 stated for owner confirmation.
