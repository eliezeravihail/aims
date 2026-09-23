# aims Guide State

## Mode

auto

## Loop cursor

met:awaiting-next-change — O1 design met after panel + one revise round; DESIGN.md written. Next: an implementation objective conforming to DESIGN.md, when the operator allows implementation (currently design-only).

## Current objective

**Kind:** design

**Objective (O1):** A buildable stage-1 architecture for availability in which each product rule
(half-open overlap, clipping to working hours, gap-aligned stepping, input validity) has exactly one owner,
validation happens once at the public boundary, and the slot computation is a pure core over value types —
pinned to concrete Python 3.11 stdlib module skeleton and signatures.

**Why now:** New product; substrate fixed (decisions/0001); product rules decided (decisions/0002). Nothing
exists yet, so the shape is the highest-leverage uncertainty.

**Exit criteria:** see `.aims/panel/2026-09-23-availability/objective.md` (C1–C14, R1–R6)

**Preserve:**
- decisions/0001, decisions/0002; design only — no implementation code.

**Do not optimize for:**
- stage-2 features (booking creation, multi-resource, buffers, breaks, grid alignment, time zones).

## Worker handoff

`.aims/panel/2026-09-23-availability/objective.md` + one axis block per Worker.

## Open assumptions (unproven — carried, not filed)

- none. Feasibility is not in doubt.

## Open Guide TODO

- [x] Answers to Q1–Q4 filed (goals.md, decisions/0002)
- [x] O1: panel → merge → measure → revise round → re-measure (met)
- [x] Write DESIGN.md (+ architecture.md, decisions/0003)
- [ ] Owner confirmation of stated assumptions A1, A3, A5 (non-blocking)

## Last evaluated result

O1 revised: met. All R1–R6 single-owned; contracts stated; C1–C14 traced; residual S1 only (TimeRange public surface wider than caller floor — justified and pinned; A5 unbounded output — stated).
