---
title: "one measurement instrument — the assessment form; no-score-in-loop is a device, not a principle"
date: 2026-09-17
---

**Context.** aims had grown **two** measurement mechanisms: the operational review
(`references/review.md` / `references/review-panel.md`, which told the judge to *formulate a fresh
quality-requirements list per design* and produce "reproduced readings, never a score") and the scored
assessment form (`experiments/judging-rubric/`, 0–10 sub-checks). Two mechanisms measuring the same thing is
a recipe for divergence — and the review panel's ad-hoc per-design list is exactly the free-association the
fixed form exists to prevent. Separately, "never a score" had hardened into a stated principle, when its
real job is narrow and practical.

**Decision.**
1. **One measurement instrument: the assessment form.** It now ships with the method as
   `references/measurement.md` (one row per principle §1–§18, sub-check-derived 0–10, severity table,
   aggregation). The in-loop review, `/aims-review`, and any comparison of designs **all fill the same
   form**. The subtractive and concept-fit passes are how §12 and §2 are filled — passes *within* the form,
   not a separate measurement. `review.md` / `review-panel.md` no longer formulate a per-design list; they
   fill this form.
2. **"No score in the loop" is a device, not a principle.** During building, show the form's **fix-list**
   (the sub-10 rows, most-severe-first, each cited) and **not the aggregate score** — so the Worker fixes
   *content* rather than polishing a number. The per-principle scores exist in the filled form; they are
   simply not displayed in the loop. When the point is to *compare* designs (ranking arms, tracking a design
   across revisions), the full scored profile is shown.

**Consequences.**
- `references/measurement.md` added (the shipped instrument). `experiments/judging-rubric/quality-metrics.md`
  becomes a pointer to it; `assessment-form.md` keeps the fillable layout + worked example and points to it.
- `review.md`, `review-panel.md`, `SKILL.md` step 5, the `/aims-review` command, and `design-principles.md`
  all reference the one instrument and the fix-list projection; the blanket "never a score" wording is
  replaced by the device framing.
- Supersedes the framing of `decisions/0012` ("one instrument, two projections") by making the instrument a
  shipped surface used by the operational review, not a measurement-layer artifact separate from the panel.

**Alternatives.**
- *Keep the panel's per-design list and the form as two mechanisms* — rejected: that is the divergence this
  removes.
- *Enshrine "never a score"* — rejected: the scores are real (they are the measurement); what must not
  happen is the loop displaying a grade the Worker then games. That is a projection choice, not a ban on
  measuring.
