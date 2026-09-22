# The judge's prompt — frozen before Phase 0

The disjoint-vocabulary judge (`experiments/PROTOCOL.md` §6; `skills/aims-guide/references/measurement.md`).
It scores each design against §0–§14 **from the code**, and may not credit anything a design says about
itself. It is not told what the scores are for, nor how many designs are expected to have problems.

---

You are judging four implementations of the same feature in the mkdocs codebase. They are labelled with
letters; you do not know who wrote them or how, and you should not speculate.

**Inputs**

- The specification all four implement: `/tmp/claude-0/phase0/judge/SPEC.md`.
- The unmodified codebase, for context: `/tmp/claude-0/phase0/judge/pristine/`.
- Each design: `/tmp/claude-0/phase0/judge/design-<L>/` — the full tree after the change, and
  `/tmp/claude-0/phase0/judge/design-<L>.patch` — the change as a diff against the unmodified codebase.
  Any prose notes the author left have been removed; judge the code.

**The standard.** Read these two files in full first:
`/home/user/aims/skills/aims-guide/references/design-principles.md` (what good design is, chapters §0–§14,
each item with its correctness class) and `/home/user/aims/skills/aims-guide/references/measurement.md` (how
the form is filled and scored). Read nothing else under `/home/user/aims`.

**Step 0 — before you open any design.** From `SPEC.md` alone, write down and hold fixed: the rules and
invariants (R), the likely change axes plus one plausible variant the spec does not state (X), and the
acceptance cases (C). The same inventory applies to all four designs.

**Then, for each design, fill the form.**

- Score **what the change introduced or altered**. Pre-existing code counts only where the change interacts
  with it — for example, by bending an existing seam or duplicating an existing responsibility.
- For each applicable chapter: the items that apply, each passing or failing, with a citation — a `file:line`
  from the design, and for a failure the R/X/C item or seam it violates. No citation, not counted.
- A failed item's severity follows its correctness class: a precondition failing is S4; otherwise S1–S3 by how
  far the defect spreads.
- **Score from code properties only** — where a rule lives, whether one concept has one owner, whether a new
  variant would be one addition or a reopened owner, whether a dimension is modelled or threaded through
  everything. **Do not credit** naming, docstrings or comments that *describe* good design; credit only
  structure that *is* good design.
- One defect, one item; other items may reference it but not re-deduct it.

**Report, per design:** the chapter scores; every failed item with its severity and citation; the grade
(the weighted list), the worst chapter, the counts (#S3, #S4), and the gate (any S4 ⇒ BLOCKED). Then one
paragraph comparing the four on the structural choices that separate them.

Do not modify any file.
