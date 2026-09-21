---
title: "a design comparison leads with the §0–§14 rubric (code-grounded); tests are a floor, behavioral proxies are weak corroboration"
date: 2026-09-21
supersedes: 0019 (the 'lead with the outcome profile' primacy inversion)
---

**Context.** `decisions/0019` (I3), to escape a rubric that ceilinged at 10/10/10 and could be captured by a
design reciting its vocabulary, made a design *comparison* **lead with a rubric-free outcome profile** — a
correctness-trap gate (a test), a reopened-owner count, and edit locality — and **demoted the §0–§14 rubric
grade to secondary**. Re-evaluated against the correct measure (`experiments/improve-2026-09/REEVALUATION.md`),
that inversion is wrong, and this run's own later data disproves it:

1. **The lead signal is gameable.** `bp13-design-under-surprise/` part 1: a strong model absorbed an
   unforeseen change with a ~3-line seam edit and **0 reopened owners** while leaving a textbook `isinstance`
   type-switch in place — fewer edits and no reopen, *worse* design. The outcome profile ranked that build a
   winner.
2. **The demoted instrument is the one that works.** `bp14-design-rubric/`: two designs passing the
   **identical** test suite scored **43 vs 16** on the §0–§14 rubric, blind and code-grounded. Tests never
   separated them; the rubric did, decisively.

The point aims exists for is **design quality**, and design quality is scored against **§0–§14** — not by
tests (a floor; behavior is achievable by any design and can be gamed) and not by behavioral change-proxies
(reopened-owner / edit locality — gameable, per BP13).

**Decision.** For **comparing designs** (ranking arms; the in-loop fix-list is unchanged):
1. **Lead with the §0–§14 rubric grade, scored from the code** (the design's structure, never its
   self-description). The weighted-list grade + S-gate is the design measure and the lead.
2. **A correctness gate is a floor only:** a wrong number BLOCKS an arm; passing earns nothing and never
   substitutes for design quality.
3. **Behavioral facts (reopened-owner, edit locality) are weak corroboration, never the lead** — they are
   gameable; cite them only to support a rubric reading.
4. The two real risks I3 named are fixed **inside** the rubric, not by leaving it: **vocabulary capture** →
   the **disjoint-vocabulary judge**, re-pointed to score the **design against §0–§14 from code properties**
   (structure: type-dispatch vs polymorphism, one owner vs scattered, rich vs anemic, seam vs reopen), not
   the change-absorption behavior; **ceiling** → on a tie, apply the unforeseen change and **re-score the
   design on §0–§14** (a rigid design's §7/§8/§4 scores fall when a new variant is added — `bp13.../part2`:
   type-switch reopens the engine, polymorphic adds a class), rather than counting edits.

**What is kept from 0019.** The *disjoint-vocabulary judge* — the good idea in I3 — stays, re-pointed as
above; it is the rubric measured honestly (it produced the 43-vs-16 separation). The two-projection /
one-instrument stance of `0012`/`0014` and the weighted-list + gate of `0018` stand unchanged.

**Consequence.** `references/measurement.md` "Comparing designs" and the disjoint-vocabulary-judge section
rewritten to lead with the code-grounded rubric and demote tests to a floor. `0019` is marked superseded by
this ADR.
