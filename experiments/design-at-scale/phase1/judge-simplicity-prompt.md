# Phase 1 judge — simplicity

Frozen before Phase 1. One of three judges on the same six designs (`PROTOCOL-NOTES.md`). Not told what the scores decide.

---

You are judging six implementations of the same feature in the mkdocs codebase. They are labelled with
letters; you do not know who wrote them or how, and you should not speculate.

**Inputs**

- The specification all six implement: `/tmp/claude-0/phase1/judge/SPEC.md`.
- The unmodified codebase, for context: `/tmp/claude-0/phase1/judge/pristine/`.
- Each design: `/tmp/claude-0/phase1/judge/design-<L>/` — the full tree after the change, and
  `/tmp/claude-0/phase1/judge/design-<L>.patch` — the change as a diff against the unmodified codebase.
  Prose notes the authors left have been removed; judge the code.

**The standard.** Read these two files in full first:
`/home/user/aims/skills/aims-guide/references/design-principles.md` (what good design is, chapters §0–§14,
each item with its correctness class) and `/home/user/aims/skills/aims-guide/references/measurement.md` (how
the form is filled and scored). Read nothing else under `/home/user/aims`.

**Your disposition.** You weigh **simplicity** above all. Every abstraction, indirection, layer and extension point
must pay for itself in what this specification needs now; structure built for a variation nobody asked for is
the defect you look hardest for (§12, size as a forcing question). But **small is not unearned**: a private field
with no setter, or a one-line funnel that makes a rule impossible to bypass, is small *and* load-bearing — never
count it as ceremony. Apply the same form and severities as any judge — your disposition decides where you look
first, not how an item is scored.

**Step 0 — before you open any design.** From `SPEC.md` alone, write down and hold fixed: the rules and
invariants (R), the likely change axes plus one plausible variant the spec does not state (X), and the
acceptance cases (C). The same inventory applies to all six designs.

**Then, for each design, fill the form.**

- Score **what the change introduced or altered**. Pre-existing code counts only where the change interacts
  with it — for example, by bending an existing seam or duplicating an existing responsibility.
- For each applicable chapter: the items that apply, each passing or failing, with a citation — a `file:line`
  from the design, and for a failure the R/X/C item or seam it violates. No citation, not counted.
- A failed item's severity follows its correctness class: a precondition failing is S4; otherwise S1–S3 by how
  far the defect spreads.
- **Score from code properties**, never from what naming, docstrings or comments say about the design.
- One defect, one item; other items may reference it but not re-deduct it.

**Report, per design:** the chapter scores; every failed item with its severity and citation; the grade
(the weighted list), the worst chapter, the counts (#S3, #S4), and the gate (any S4 ⇒ BLOCKED). Then one
paragraph comparing the six on the structural choices that separate them.

Do not modify any file.
