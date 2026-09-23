---
title: "Pre-registration — improving aims for correctness in the result (blind, outcome-measured)"
date: 2026-09-20
status: pre-registered before any arm ran
---

# Goal (the *correct* goal)

Improve aims so that **following it yields a more correct design** — not so that it scores higher on its own
rubric. Every claim here is judged by a **rubric-free outcome metric fixed in this document before any arm
runs**, on a **product the improvement has not seen**, using aims **as-is** (arms invoke the real
`aims-guide` skill from the repo; the operator does not hand-direct them). A candidate enters the shipped
method **only** if it beats base on the pre-registered outcome; a null is recorded as a null. This is the
discipline the paper's threats section and the plant→mineral loss demand: no reactive instrument change, no
teaching-to-the-rubric.

Method commit under test: `git rev-parse HEAD` recorded per experiment in its own `run.md`.

# Weaknesses being targeted (from the paper's own honest findings)

- **W1 — a real correctness loss on record.** plant→mineral: the aims arm shipped a type (`Term | Quantity`)
  that could not represent a stated value ("6.5–7"), an S4 on the full-input-space trap. The method's own
  §1 exists to catch this and did not, at design time. → **I1**.
- **W2 — self-critique defends.** The mandatory review checks items; the paper argues a model conditioned on
  an interface it wrote rationalizes rather than revises. → **I2**.
- **W3 — ceiling effect + vocabulary capture.** aims scored a perfect first-round grade on all three Study-1
  products (the instrument lost resolution), and all three judges noted the designs recite the rubric's own
  vocabulary. The rubric-free survival count was materially weaker (tie/win/tie). → **I3**.

# Candidates and their pre-registered outcome metrics

## I1 — a design-time input-space table (mechanical, a gate)
**Change.** §1 gains a required artifact the design must carry and the review must check: a table with **one
row per (change-axis X × rule R) corner** it implies, each row naming the **concrete extreme/corner value**
and a column **"the chosen type can represent this value: yes + the constructor / no"**. A design with any
`no` or blank row cannot pass review. It is not new prose — it is an enumeration the builder must *fill*, so
an unrepresentable value is visible before code.

**Outcome metric (rubric-free, binary, fixed now).** For each product a **hidden probe set** of corner
values is frozen before the run (boundary-inclusive edges, empty/one/many, a spanning/interval value, a
zero/negative). Score = **# of hidden probes the delivered type model can represent** (a yes/no fact about
the types, judged blind, not a rubric grade). **I1 wins iff the table arm represents strictly more hidden
probes than base**, on ≥2 unseen products. A tie (both represent all, or both miss the same) is a **null** →
not folded in (exactly the plant→mineral §7 discipline).

## I2 — adversarial falsification review (attack, not tick)
**Change.** The mandatory review-and-revise round's task becomes: **construct a concrete input/scenario the
current design mishandles** (an actual failing case with the value and the wrong output), and only then
revise. Ticking items is demoted to a checklist *after* the attack. Rationale: an attack conditions the
model on "find the break," not on "defend what I wrote."

**Outcome metric (rubric-free, fixed now).** On a fresh product **seeded with one subtle corner defect a
first-draft design is likely to carry**, score = **did the review surface a reproducible failing case for
the seeded corner before code (yes/no)**, plus # of *other* real corners it surfaced. **I2 wins iff the
falsification arm surfaces the seeded corner where the base review misses it.** Both catching, or both
missing, is a null.

## I3 — outcome-first measurement + disjoint-vocabulary judge
**Change.** In `measurement.md` / `PROTOCOL.md`: the **primary** reading of a design comparison is the
**rubric-free outcome** after an unforeseen change — (a) correctness traps passed [gate], (b) reopened-owner
count, (c) edit locality (files/lines to absorb the change) — and the rubric grade is **secondary**. Add a
**disjoint-vocabulary judge**: instructed to score only "does the design *absorb* the change with fewer
edits and no reopened owner," never "does it use value objects / name the subtractive pass."

**Outcome metric (fixed now).** This is a *measurement* improvement, so it is validated by **discrimination,
not by a win**: on the recorded runs where the rubric **ceiling'd** (aims perfect on all three Study-1
products), does the outcome-first reading **still separate arms**? I3 is adopted iff the outcome-first
reading is (a) computable from the record and (b) **at least as discriminating** as the rubric while being
**independent of the rubric's vocabulary** — i.e. it does not simply reproduce the ceiling. If outcome-first
also ceilings, it is not an improvement and is recorded as such.

# Protocol (same for every I)

- Freeze the product package (`starter` implicit — design-only; `cards/`, `hidden/` probes, step-0
  inventory) **before** any arm runs; the two arms differ **only** in the one candidate change.
- Arms invoke the real skill (read `skills/aims-guide/SKILL.md` + references from the pinned commit); the
  only difference is the swapped candidate doc for the treatment arm. No hand-direction.
- Judge/score **blind**: arms relabelled X/Y, method identity stripped; the outcome metric is a fact about
  the artifact (representable? failing case? edits?), not a taste grade.
- **n ≥ 2** unseen products for any wording change adopted into the skill (PROTOCOL §3). n=1 is suggestive.
- Keep **both** numbers (base and treatment) and record the exact hidden probe set used.

# What "done" means

Each I ends in its own `results.md` with the pre-registered metric filled, and a one-line verdict:
**adopt** (beat base on ≥2 unseen products) or **null / not adopted**. Only adopted changes touch
`skills/`; everything else stays in this experiments folder as a recorded negative. A running `LOG.md`
tracks progress across the 24-hour window.
