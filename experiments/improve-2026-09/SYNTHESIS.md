---
title: "Synthesis — the 24h improvement run: two nulls, one adopted, the discipline held"
date: 2026-09-20
---

# What the run set out to do

Improve aims for **correctness in the result** — not for a higher score on its own rubric — and prove each
change **blind, on unseen products, with a rubric-free outcome metric fixed before the run** (`plan.md`).
Three candidates, each targeting a weakness the paper names.

# The three candidates and their measured outcomes

| # | candidate (targets) | test | outcome | shipped? |
|---|---|---|---|---|
| **I1** | a design-time **input-space table** — a mechanical §1 artifact (targets the plant→mineral correctness loss) | blind A/B on **2 unseen** design products (shipping-rate, discount-applicability); metric = hidden corner-probe representability | **null** — every arm, base and table, represented **6/6** probes on **both** products | **no** |
| **I2** | an **adversarial falsification review** — attack before item-check (targets "self-critique defends") | A/B on a seeded first-draft (fixed-window rate limiter); metric = does the review surface the seeded corner base misses | **null** — both reviews caught the seeded S4 with a concrete failing input; base caught **more** secondary corners | **no** |
| **I3** | **outcome-first comparison** + a **disjoint-vocabulary judge** (targets the rubric ceiling + vocabulary capture) | validated against the **recorded** Study-1 runs (no new blind run needed for a measurement-policy change) | **adopt** — the outcome reading retains resolution where the rubric ceiling'd (10/10/10 vs survival tie/win/tie) and is vocabulary-independent | **yes** (`decisions/0019`) |

# The meta-finding: the shipped method is already strong

Both I1 and I2 are nulls for the **same reason**, and it is a result worth stating plainly: the shipped
method already does the work the additions proposed to add.

- The shipped **§1 "trace the full input space (the procedure, not just the cases)"** plus the concept-fit
  pass already drove both *base* arms to the exact load-bearing types the corners require — an interval
  weight with `worst_case` (P1), a first-class boolean expression tree with a structured reason (P2),
  including the subtle empty-combination corner — with no mechanical table (I1 null).
- The same §1 pass already *is* a falsification step: on the seeded rate limiter the base review constructed
  the boundary-straddling burst and marked it BLOCKED, unprompted by any new attack wording (I2 null).

This is consistent with the earlier §7 null (`../plant-mineral-id/` → `../s7-yagni-stated-capability/`): the
plant→mineral loss was a **builder slip under adequate wording**, not a documented gap, and additions
inspired by it do not reproduce a base failure to beat. Two more weakness-prompted additions, tested
honestly, stayed out.

# The one change that survived makes aims look *less* flattering

I3 is the opposite of a reactive softening. It removes aims' perfect-score headline and leads a design
comparison with the harder, rubric-free reading (trap gate · reopened-owner count · edit locality), demoting
the vocabulary-captured rubric grade to second, and adds a judge that cannot be captured by a design that
recites the checklist. It is adopted because it is **more adversarial**, validated against the existing
record, and conservative (the rubric stays as the second reading).

# The discipline, stated as the result

Three candidates, one survivor. The value of the run is not the survivor alone but that **two plausible,
motivated additions were rejected by measurement** — the exact behavior the method preaches and the paper's
threats section demands. A method that only ever adopts its own proposals is gaming its rubric; this run
adopted the change that makes the instrument harder and rejected the two that would merely have added
surface. `arm-table-design-principles.md` and `arm-attack-review.md` remain as recorded negatives.

# Honest limits / future work

- I1's null tested **stated** change-axes. The sharper hypothesis — does a mechanical table catch a corner
  that is *implied but unstated*, where a prose trace might skip it? — is **not** settled here, and was
  deliberately **not** pursued by manufacturing an easier product to force a win.
- I2 is n=1 on one seed; a second seeded product could still surface value, but on the evidence it is a null.
- I3 changes measurement *policy* from the record; it is validated by discrimination, not by a fresh blind
  run, and keeps both readings so it is fully reversible.
