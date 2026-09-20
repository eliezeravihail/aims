---
title: "comparing designs leads with the rubric-free outcome; a disjoint-vocabulary judge breaks ties"
date: 2026-09-20
---

**Context.** The measurement instrument (`references/measurement.md`, `decisions/0012`/`0014`/`0018`) scored
a *design comparison* by leading with the rubric grade. Two recorded facts make that primacy unsound as a
comparison lead:

1. **Ceiling.** In the three-product Study 1 (`experiments/principles-polish-vs-openspec/`) the aims arm
   scored a **perfect first-round rubric grade on all three** (10/10/10). An instrument that returns its
   maximum for an arm on every product has lost the resolution to register that arm's next regression — the
   single most valuable thing a comparison instrument does.
2. **Vocabulary capture.** All three blind judges independently flagged that the aims designs **speak the
   rubric's own vocabulary** ("subtractive pass", "§7 falsifier", concept-fit); a judge sharing the rubric
   is pulled toward a design that recites it.

The rubric-free **survival count** on the same runs read **tie / win / tie** — materially weaker than the
grade, and *without* the ceiling and *without* the vocabulary dependence. The honest reading of a comparison
was already leaning on the outcome, ad hoc.

**Decision.** For **comparing designs** (ranking arms; not the in-loop fix-list, which is unchanged):
1. **Lead with the rubric-free outcome profile** — a correctness-trap **gate** (any wrong number ⇒ that arm
   BLOCKED, outranking any grade), the **reopened-owner count**, and **edit locality** — then report the
   rubric grade **second**, labelled as vocabulary-dependent. The outcome gate never loses to the grade.
2. **Add a disjoint-vocabulary judge** to a design comparison: it scores only "did this design absorb the
   change with fewer edits and no reopened owner?", is forbidden from crediting rubric language, and breaks
   ties when the two opposite-disposition rubric judges split.

**Why this is adopted, and why it is not a reactive softening.** Unlike a grade change that would *flatter*
the home method, this makes aims look **less** flattering — it removes the perfect-score headline and leads
with the harder, rubric-free reading (which was tie/win/tie, not a sweep). It is validated **against the
existing record** (`experiments/improve-2026-09/i3-outcome-first/validation.md`), where the outcome profile
retained resolution exactly where the rubric ceiling'd and caught the plant→mineral loss by the gate,
independent of vocabulary — not by a fresh self-confirming run. It is conservative: the rubric grade stays,
as the second reading; only its *primacy in a comparison* changes.

**Provenance.** Produced in the 24-hour autonomous improvement run (`experiments/improve-2026-09/`) whose two
other candidates — a §1 input-space table (I1) and a falsification review pass (I2) — were **A/B-tested on
unseen products and both came back null**, so only this measurement-honesty change was adopted. The
discipline held: a change enters the method only on evidence, and the null candidates stayed out.

**Consequence.** `references/measurement.md` "Two projections" rewritten (comparison leads with the outcome
profile; disjoint-vocabulary judge added). `experiments/PROTOCOL.md` §6 notes the disjoint-vocabulary judge.
The two projections and one-instrument stance of `0012`/`0014`, and the weighted-list + gate of `0018`,
stand.
