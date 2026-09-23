---
title: "BP7 — does the trajectory edge generalize off the derive-don't-store axis, and does aims-lite capture it?"
date: 2026-09-20
status: pre-registered before any arm ran
---

# Two questions in one build

Everything measured so far (BP1/BP2/BP5/BP6) lives on **one** structural axis: derive-vs-store availability.
Two open questions the campaign has NOT answered:

1. **Generalization.** Does aims' trajectory edge appear on a *different* structural axis — **concept-fit**
   (model the concept as a first-class thing vs cram cases into branches)? If the edge is really about the
   review catching under-modeled shortcuts, it should show on this axis too. If it only ever appears on
   derive-don't-store, the edge is narrower than claimed.
2. **aims-lite (the improvement candidate).** BP3 showed the derive-don't-store edge transfers via one
   sentence. Does a **small principle-injection** ("aims-lite" — a short prompt of the 3 highest-yield aims
   principles, no skill/records/review) capture the concept-fit edge too, at plain cost? If yes, aims-lite is
   a real, cheaper delivery worth proposing.

# Product (fresh, not seen before): a promotional pricing engine

A 2-stage build where the natural shortcut is **case branching**, not a stored counter:
- **Stage 1**: three promo rule kinds (percent-off-category, amount-off-over-threshold, buy-x-get-y) +
  an engine that applies them. Shortcut: an `if rule_type == ...` chain inside `total()`. Concept-fit design:
  each rule is a first-class object that computes its own discount.
- **Stage 2** (the break): a **stacking policy** — rules gain `priority` (apply in order) and `exclusive`
  (an exclusive rule that fires blocks all lower-priority rules). This threads ordering + short-circuit
  through the discount computation.

**Trajectory hypothesis:** the case-branch arm must **reopen** `total()` to sort by priority and short-circuit
across the type branches; the first-class-rule arm **extends** by sorting the rule list and adding a break —
its per-rule discount computation is already encapsulated. If concept-fit modeling avoids the reopen, the edge
generalizes.

# Arms (all opus; stage 2 by a FRESH session per arm)

- **plain** — "build it well," code only. No skill, records, review, or hints.
- **lite** — plain + a short principle block appended to the stage-1 AND stage-2 prompt (no skill/records/
  review): concept-fit ("model each distinct concept as its own first-class type with a uniform interface,
  rather than branching on a type tag"), one-owner ("each rule/fact has exactly one place that computes it"),
  full-input-space ("trace the whole procedure, not just the given examples"), subtractive ("remove anything
  the requirement doesn't force").
- **aims** — the full method (skill invoked, co-located records, mandatory review).

# Metrics (fixed now, outcome-first per decisions/0019)

- **Correctness gate:** hidden pytest per stage (validated against a reference impl: stage-1 12 tests,
  stage-2 7 tests, 19 total). Recorded as pass/total; a wrong number is a correctness loss.
- **Trajectory (primary):** reopened-owner count at stage 2 — did `total()` (or the rule dispatch) get
  **rewritten** (reopen) or **extended** at a seam? Measured from the stage-1→stage-2 diff, blind-checkable
  from the snapshots.
- **Cost:** tokens + wall per arm.

# Pre-registered predictions (so nulls are honest)

- plain: ~50/50 whether it reaches for first-class rules or a type-branch chain at stage 1 (concept-fit is a
  softer pull than derive-don't-store; a capable model often objects first anyway). If it branches, expect a
  stage-2 reopen.
- lite: the concept-fit sentence should push it to first-class rules → 0 reopens, plain cost.
- aims: first-class rules via the concept-fit pass → 0 reopens, at the ~1.85× premium.
- **Most likely honest outcome given BP1–BP6:** correctness ties; the interesting result is whether *any* arm
  reopens. If none do (all three model rules as objects), that is a **null that says concept-fit is an easy
  pull for opus on this card** — informative, and recorded as such, not padded.

Nulls recorded as nulls. n=1 product. No arm sees the hidden tests or this plan.
