---
title: "the grade is the weighted list; severity is a reported gate, not a global cap"
date: 2026-09-18
---

**Context.** The assessment form (`references/measurement.md`, `decisions/0012`/`0014`) aggregated two ways
at once: a **weighted average** over the whole chapter list (each chapter's severity setting its ceiling and
weight), *and* a **global graded cap** (`any S2 ⇒ ≤8.5 · any S3 ⇒ ≤7.5 · any S4 ⇒ ≤5.0`) applied on top by
`min`. The cap almost always bound and **double-counted one defect three times** (chapter ceiling → chapter
weight → global cap), contradicting the form's own "one defect, one item, never re-deduct".

**Provenance and a warning about it.** This change was first made on `claude/aimes-redesign-clean-q6ljk9`
**in the same round the aims arm lost** the plant→mineral pilot, and its softening effect on that loss
(capped 5.0 → uncapped 6.63) is exactly the kind of reactive instrument-change that destroys a measurement's
credibility even when the change is correct (raised in review by Pavel). It is adopted here **only** on its
standalone merit (the double-count is a real defect of the old rule), and **only together with two
guardrails that remove the softening**: (1) it is applied **retroactively to every prior experiment**, not
just the one where it helped (`experiments/grade-rule-regrade.md`), so no comparison is left cross-rule; and
(2) both readings (capped and uncapped+gate) are kept side by side. Under the retroactive gate the aims
plant→mineral arm is the **only BLOCKED arm across the whole set** — so the corrected rule makes that loss
*starker*, not softer.

**Decision.**
1. **The grade is the weighted list. Remove the global graded cap.** Reported grade =
   `Σ(chapter_score × weight) / Σ(weight)`, nothing overrides it. The weighting already carries severity (a
   severe chapter takes a low ceiling *and* an ×8 weight), so a serious defect still pulls the number down
   hard — it just no longer *caps* the whole design or double-counts itself.
2. **Severity is a reported gate beside the grade, not a cap on it.** `any S4 ⇒ BLOCKED` ("not shippable
   until this precondition is fixed") is reported next to the grade, `worst_chapter`, and `(#S3,#S4)`.

**What this does NOT license — a correction to the original rationale.** The first write of this decision
called the plant→mineral result "a near-tie in design quality; one easily-fixed local bug." That framing is
**wrong and is not adopted.** aims read 6.63 (BLOCKED) vs OpenSpec 9.54 (CLEAR) — a ~3-point gap **and** a
blocking S4, which is a clear loss, not a near-tie. And the S4 is not a trivial local bug: a type model
(`Term | Quantity`, a single point) that **cannot represent a value the spec names** ("6.5–7") is a §4
(domain-modeling) / §1 (correctness) **design** defect, not an execution slip. The grade rule change is
about not *double-counting* that defect; it is **not** a claim that the defect is minor. Removing the cap
lifts the number; the **gate keeps the loss visible**, and the design-quality reading stays honest about the
§4 root cause.

**Consequence.** `references/measurement.md` Aggregation rewritten (grade = weighted list, gate separate, no
`min`). Supersedes the "graded caps" clause of `decisions/0012` only; the two projections and one-instrument
stance of `0012`/`0014` stand. Renumbered from the `0015` used on the origin branch (which now collides with
the merged `0015` refactoring/add-feature ADR).
