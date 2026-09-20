# Proposed addition to `references/measurement.md` (I3) — draft, applied in synthesis if adopted

Replace the "**Comparing designs**" bullet under *Two projections* with an outcome-first version, and add a
disjoint-vocabulary judge note. Draft text:

---

## Two projections — same filled form, shown two ways

- **Building / in-loop (default):** the **fix-list** — unchanged.
- **Comparing designs (ranking arms):** lead with the **outcome profile**, then the rubric grade second.
  - **Outcome profile (primary, rubric-free).** After the unforeseen change the comparison stresses:
    (1) **correctness-trap gate** — did the arm ship a wrong number on any hidden probe? (any fail ⇒ the
    arm is BLOCKED, and no rubric grade outranks a failed trap); (2) **reopened-owner count** — how many
    existing rule-owners the change forced open (lower is better); (3) **edit locality** — files/lines the
    arm needed to absorb the change. These are facts about what the design *did*, computable without the
    rubric's vocabulary.
  - **Rubric grade (secondary, vocabulary-dependent).** The weighted-list grade + gate as before — reported
    **beside** the outcome profile and explicitly labelled as scored against `design-principles.md`, whose
    vocabulary a rubric-sharing judge can be pulled toward. It never outranks the outcome gate.

  Why this order: the rubric grade **ceiling'd** (a perfect score on every arm loses the resolution to catch
  the next regression) and is **captured by vocabulary** (a design that recites the rubric scores well). The
  outcome profile did neither on the recorded runs (`experiments/improve-2026-09/i3-outcome-first/`), so it
  leads; the rubric grade stays, as the second reading.

## The disjoint-vocabulary judge (for a design comparison)

Alongside the two opposite-disposition rubric judges (`PROTOCOL.md` §6), run one **disjoint-vocabulary
judge** given only the two anonymized designs and the unforeseen change, and instructed to score **one
question**: *did this design absorb the change with fewer edits and no reopened rule-owner?* It is forbidden
from crediting rubric language ("subtractive pass", "concept-fit", "value object") — it may credit only an
observable edit/ownership fact. Its verdict is the tie-breaker when the rubric judges split, because it
cannot be captured by a design that recites the checklist.
