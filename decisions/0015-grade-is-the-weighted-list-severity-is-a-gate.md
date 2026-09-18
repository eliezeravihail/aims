---
title: "the grade is the weighted list; severity is a reported gate, not a global cap"
date: 2026-09-18
---

**Context.** The assessment form (`references/measurement.md`, `decisions/0012`/`0014`) aggregated two ways
at once: a **weighted average** over the whole chapter list (each chapter's severity setting its ceiling and
weight), *and* a **global graded cap** (`any S2 ⇒ ≤8.5 · any S3 ⇒ ≤7.5 · any S4 ⇒ ≤5.0`) applied on top by
taking the minimum. In practice the cap almost always bound: in the plant→mineral pilot the reported grades
were A `min(9.54, 8.5)=8.5` and B `min(6.63, 5.0)=5.0` — the elaborate whole-list weighting we built never
drove the number. Worse, one defect was counted three times (chapter ceiling → chapter weight → global cap),
contradicting the form's own "one defect, one item, never re-deduct". The visible effect: a single local,
easily-fixed correctness defect buried an otherwise-excellent design at a near-fail, and a comparison read
that as "40% worse design" when the real reading was "near-tie in design quality; one residual blocker."

**Decision.**
1. **The grade is the weighted list. Remove the global graded cap.** The reported grade is
   `Σ(chapter_score × weight) / Σ(weight)` and nothing overrides it. The weighting already carries severity
   (a severe chapter takes a low ceiling *and* an ×8 weight), so a serious defect still pulls the number
   down hard — it just no longer *caps* the whole design or double-counts itself.
2. **Severity becomes a reported gate beside the grade, not a cap on it.** `any S4 ⇒ BLOCKED` ("not
   shippable until this precondition item is fixed") is reported next to the grade, `worst_chapter`, and the
   `(#S3,#S4)` counts. A design can be strong (high grade) and blocked (one S4 to fix); the fix-list
   projection names exactly what to fix. The gate is a fact about **shippability**, not a verdict that the
   design is weak.

**Why.** A design score grades the design; an easily-fixable local bug is a fix-list item, not evidence of
a bad design. This supersedes the "graded caps" clause of `decisions/0012` (the two projections and the
one-instrument stance of `0012`/`0014` stand). It also sets up the further split the process needs — design
score vs. execution vs. adaptation — where a correctness/adaptation defect is scored on its own axis rather
than dragging the design-quality number (cf. `decisions/0009`).

**Consequence.** `references/measurement.md` Aggregation rewritten: grade = weighted list, gate reported
separately, no `min`. Under the corrected instrument the pilot reads A `9.54` (gate CLEAR, S2 only) vs
B `6.63` (gate BLOCKED, one S4 to fix) — a near-tie in design quality with one residual correctness blocker
on B, which is the honest reading.
