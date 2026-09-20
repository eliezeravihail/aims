---
title: "I3 validation — outcome-first comparison discriminates where the rubric ceiling'd"
date: 2026-09-20
---

# I3 — make the rubric-free OUTCOME the primary comparison reading (validated against the record)

**Claim under test (pre-registered).** A design *comparison* should lead with the **rubric-free outcome**
(correctness traps passed → a gate; reopened-owner count; edit locality) and treat the rubric grade as
secondary — because the rubric grade **ceiling'd** (aims scored a perfect first-round grade on all three
Study-1 products) and is **captured by vocabulary** (all three judges flagged the aims designs reciting the
rubric). I3 is adopted only if the outcome reading (a) is computable from the record, (b) **retains
resolution where the rubric lost it**, and (c) is independent of the rubric's vocabulary.

## Evidence, entirely from already-recorded runs (no new run)

Study 1 (`../../principles-polish-vs-openspec/results.md`), aims vs OpenSpec, three products:

| product | rubric D1 (aims) | rubric-free survival (aims / OS) | correctness trap |
|---|---|---|---|
| feed-ranking | **10** | tie — 0 / 0 | both passed |
| booking-availability | **10** | **aims better** — ≈1 / ≈2 | both passed |
| entitlements | **10** | tie — ≈2 / ≈2 | both passed |

And the loss (`../../plant-mineral-id/results.md`): rubric aims 6.63, **but the deciding fact is a correctness
trap FAILED → gate BLOCKED**.

**(a) Computable.** Every outcome number above is already in the record: survival counts, trap pass/fail, and
(in the add-feature experiments) edit locality (e.g. boltons 31 vs 53 lines).

**(b) Resolution retained where the rubric lost it.** The rubric D1 is **10 / 10 / 10** — a flat ceiling:
it cannot tell the three aims designs apart and, worse, could not register a regression in any of them
(the paper's ceiling threat). The rubric-free survival reads **tie / better / tie** — it *keeps* the
booking win visible while honestly calling feed and entitlements ties. The outcome reading did **not**
ceiling. On plant→mineral the outcome reading (gate) is what makes the loss stark, independent of the 6.63.

**(c) Vocabulary-independent.** All three Study-1 judges flagged that the aims designs speak the rubric's own
vocabulary ("subtractive pass", "§7 falsifier", concept-fit), which a rubric-sharing judge is pulled toward.
The survival count and the trap gate need **none** of that vocabulary — they are facts about what the design
did to an unforeseen change, not about whether it recites the checklist.

## Verdict

**Adopt** — as a *measurement-policy* change, conservative and honesty-increasing:
1. For **comparing designs**, lead with the **outcome profile** (trap gate · reopened-owner count · edit
   locality) and show the rubric grade **second**, explicitly labelled as vocabulary-dependent.
2. Add a **disjoint-vocabulary judge** to the protocol: a second design judge instructed to score *only*
   "did the design absorb the unforeseen change with fewer edits and no reopened owner?", forbidden from
   crediting rubric vocabulary — run alongside the two opposite-disposition rubric judges.

This makes aims look **less** flattering (it removes the perfect-score headline), which is the point: it is
the anti-ceiling, anti-capture direction the paper's own threats section asks for. It changes *which reading
leads a comparison*; it does not touch how a design is built, and it keeps the rubric grade in the record.
Because it alters the instrument, it is applied with both readings kept side by side and is validated here
against the existing record rather than by a fresh self-confirming run.
