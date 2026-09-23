---
title: "BP1 — multi-stage build pilot: does aims' design trajectory beat no-method across a sequence?"
date: 2026-09-20
status: pre-registered before any arm ran
---

# Why (the claim design-only A/Bs cannot reach)

The paper's real edge is a **trajectory**: across successive unforeseen changes, aims' design improves while
no-method flattens and densifies — a single change hides this, only a sequence exposes it. Rounds 1–3 were
design-only/single-change and all null. BP1 runs an actual **3-stage build** with running code + hidden
tests, so the trajectory and cost are measurable.

# Product: in-memory inventory reservation service (`inventory.py`)
Three staged, unforeseen changes (`cards/stage-{1,2,3}.md`), each revealed only after both arms close the
prior stage; no card hints at a later stage:
1. reserve / release / available with a stock invariant.
2. reservation **expiry** (TTL, injected clock).
3. **confirm** (permanent) + **partial** reserve.

Each stage stresses the same core (the stock-invariant owner, the time seam, the reservation state).

# Arms (aims as-is vs no-method), faithful to PROTOCOL
- **aims arm:** builds stage 1 via the aims flow (design the objective, file co-located records), then each
  later stage is done by a **fresh session** given the code + the records + the new card (Q2 continuity).
- **plain arm:** one capable agent, "build it well", free to refactor; each later stage a fresh session
  given only the code + the new card.
Both get the identical cards; neither sees the hidden tests.

# Measurement (outcome-first, per the newly shipped decisions/0019)
Fixed before running:
- **Correctness gate (primary):** at each stage, the arm's `inventory.py` is run against the hidden
  `test_stage{N}.py` (all prior stages too). Pass = all green. A stage that ships a failing test is BLOCKED.
- **Trajectory / structure (rubric-free):** across the 3 stages, per arm — (a) **reopened-owner count**
  (how many times the stock-invariant / availability computation was reopened rather than extended at a
  seam), (b) **edit locality** (lines/functions changed per stage), (c) a **blind design judge** + a
  **disjoint-vocabulary judge** on the two final modules (which absorbed the changes with fewer edits / no
  reopened owner), method identity stripped.
- **Cost (recorder):** tokens / tool-calls / wall-clock per arm per stage.

# What counts
- If **both** arms stay correct at every stage (likely — strong models), the discriminator is the
  **trajectory**: does the plain arm's availability/expiry logic densify or scatter the invariant across
  stages while aims keeps one owner? A measured trajectory gap (fewer reopened owners / better final
  structure for aims, at a cost premium) is the paper's claim reproduced under test. A tie is a null and is
  reported as one. n=1 product → suggestive; the value is the measured trajectory, not a win tally.
