---
title: "Scoring the design principles — the how-to-build and how-to-grade layer"
date: 2026-09-17
---

# Scoring the design principles

This file is **not a list of metrics.** The metrics a judge scores and a builder builds toward are the
principles in [`../../skills/aims-guide/references/design-principles.md`](../../skills/aims-guide/references/design-principles.md),
**§1–§18** — one metric per principle. Building and grading follow the **same** principles; only the *how*
differs, and that *how* is all this file adds:

- **building** — make each principle hold *by construction*, and self-verify before returning;
- **grading** — score each principle on **0–10, computed from a handful of binary structural sub-checks**,
  then combine by a severity-weighted rule.

Asking a builder for the principles and then measuring against a *different* list is the failure this
avoids — so there is deliberately no second canon here.

## Step 0 — the fixed inventory (before any scoring or building; identical for every side)

Pin three product-level lists **from the fixed spec, never from what a design says about itself**, and use
them unchanged for every judge and every design:

- **(R) the rules / invariants** the product declares;
- **(X) the change-axes** it implies, plus one plausible unstated variant;
- **(C) the acceptance cases** (inputs → required outputs).

Then, per design, enumerate that design's **seams and named elements**. Every sub-check below cites an R/X/C
item or a named seam. A design that **omits** a required rule (R) or fails a case (C) *fails* the relevant
sub-check — it is not N/A; silence is a miss. N/A is decided only by the spec (the product genuinely has no
such requirement). Worked inventories: [`checkout-spec-inventory.md`](checkout-spec-inventory.md),
[`marketplace-spec-inventory.md`](marketplace-spec-inventory.md).

## Scoring a principle — from binary sub-checks, not a holistic band

Do **not** eyeball a principle and pick a number. Decompose it into a handful of **concrete yes/no
structural sub-checks**, mark each pass/fail with a citation, and let the score *fall out* of them. This is
the change that makes the score both finer and steadier (see "Why this absorbs noise", below).

**Per principle:**

1. **Write the checklist.** From the principle's own "The question" in `design-principles.md` and the pinned
   R/X/C, state **3–8 binary structural checks** — each a property that is objectively present or absent in
   the design, each citing the inventory item or named seam it turns on, and each **tagged with the severity
   tier a *failure* of it carries** (S1–S4). The checks are *derived* from the principle every time against
   *this* product's inventory; they are not a frozen list (that would be the second canon this file
   refuses). Examples below.
2. **Mark each check.** A **passed** check quotes the single place the property holds by construction; a
   **failed** check quotes the defect **and** names the R/X/C or seam item it violates. A check the spec
   makes irrelevant is **N/A** and leaves the denominator. No citation → the check does not count as passed
   (this closes the "default everything to pass" gap).
3. **Base score = 10 × (passed / applicable)**, rounded to the nearest whole number.
4. **Severity = the tier of the worst *failed* check** (nothing failed → no severity). Severity sets the
   principle's **weight** and a **ceiling**; the reported `score_§` is `min(base score, ceiling)`.

| worst failed check on the principle | ceiling | weight |
|---|---|---|
| **none** — every check passes by construction | **10** | ×1 |
| **S1** cosmetic (a naming nit, formatting) | **8** | ×1 |
| **S2** moderate (primitive obsession, a local coupling, a dead abstraction, a data clump) | **7** | ×2 |
| **S3** high (mis-owned invariant, an implementation type leaked at a seam, a shotgun-surgery seam, a latent concept cram) | **5** | ×4 |
| **S4** severe / correctness (wrong or unproducible result; a stated rule unenforceable or bypassable; a security hole; data corruption) | **2** | ×8 |

A design's length and a checklist's length do not move the score in either direction — a principle met by
three sharp checks scores exactly like one met by eight; score only whether the principle holds, no more and
no less (`design-principles.md` §2).

### Worked checklists (illustrative — regenerate per product)

- **§13 functional correctness** — every check S4-tier, from C + implied probes:
  - `[S4]` each acceptance case `C_i` has a trace to its required output (cite the case);
  - `[S4]` each **implied probe** (a change-axis × a rule the cases don't spell out — e.g. a multi-line
    SOUTH cart with a cart-level discount forcing a per-line tax on the discounted amount) has a trace;
  - `[S4]` no required output is unproducible by the design's primitives.
- **§9 one unforgeable owner** — from R:
  - `[S3]` each rule `R_i` has exactly one owner component (cite it);
  - `[S4]` no owned rule is bypassable through another path (cite the path, or the funnel that closes it);
  - `[S3]` no rule is enforced in two places (no shotgun seam).
- **§4 primitive obsession** — from the seams:
  - `[S2]` each domain quantity crossing a public seam is a value object, not a bare primitive (cite the seam);
  - `[S1]` no bare tuple/dict stands in for a named record at a seam.

## One defect, one principle

A single defect fails a sub-check under **exactly one** principle — the most specific one. Related
principles may *reference* it, never re-fail on it. (A Law-of-Demeter reach-through fails a check under
§1/§6, not twice; an "anemic model with rules outside the owner" fails once, under §5 *or* §9, and the judge
says which.) This keeps the many sub-checks genuinely independent, which is what the averaging below relies
on.

## The metrics are the principles — applicability + severity ceiling

The table adds only what scoring needs on top of each principle's own "The question" in `design-principles.md`
(read that for *what* to measure). "Applies to" gates code-only checks off a pure design document; the
**severity ceiling** is the worst tier a failed check on that principle may carry.

| § | principle (short) | applies to | severity ceiling |
|---|---|---|---|
| §1 | Tell-Don't-Ask / Law of Demeter | Both | S3 |
| §2 | Program to an interface + generic calibration + concept-fit / family altitude (LSP) | Both | S3 |
| §3 | Interface Segregation | Both | S2 |
| §4 | Primitive obsession | Both | S2 |
| §5 | Anemic domain model | Both | S2 |
| §6 | Cohesion/coupling — Feature Envy, Shotgun Surgery (OCP, acyclic deps) | Both | S3 |
| §7 | Leaky abstractions — boundary vocabulary, error types | Both | S3 |
| §8 | Single Responsibility / God Object | Both | S3 |
| §9 | Where a stated rule is enforced — one unforgeable owner | Both | **S4** |
| §10 | Duplication vs the wrong abstraction (DRY) | Both | S2 |
| §11 | Naming and failure (least astonishment) | Both | S2 |
| §12 | Size as a forcing question (YAGNI / subtractive) | Both | S2 |
| §13 | **Functional correctness** — every case + every implied interaction | Both | **S4** |
| §14 | State & side-effect discipline (immutability, purity) | Code-leaning | S3 (S4 on a race / corruption) |
| §15 | Testability — verifiable by construction | Code-leaning | S3 |
| §16 | Performance & resource use — on its own terms, never a proxy | Both | requirement-dependent; **N/A if unstated** |
| §17 | Security & trust boundaries | Both | S4 where a boundary exists; else **N/A** |
| §18 | (names OCP/LSP/ADP/DRY/least-astonishment/YAGNI — folded into the above, **not scored separately**) | — | — |

**§9 and §13 are the two that can reach S4** (an unenforceable rule; a wrong or unproducible result) and so
cap the grade — the reason correctness is built and checked *first*. Code-leaning principles (§14, §15) are
`N/A (code)` on a pure design document unless its text gives a basis.

## Aggregation — report a profile, not a single number

Over the non-N/A principles, on the **0–10** scale:

```
weighted_average = Σ (score_§ × weight_§) / Σ (weight_§)      # weight from the severity table
worst_principle  = min score_§
counts           = (#S3 findings, #S4 findings)
```

Apply **graded caps** to the reported grade (one structural fault must not read as "Sound"):

| worst finding at | grade capped at |
|---|---|
| S2 | ≤ 8.5 |
| S3 | ≤ 7.5 |
| S4 | ≤ 5.0 |

Report the **capped grade beside `worst_principle` and the (#S3,#S4) counts** — never a bare number. Rank by
capped grade, then `worst_principle`, then fewer S3/S4. A single §-with-a-failed-S3-check among clean 10s
does not average to "Sound" (the S3 cap pins it ≤7.5 and `worst_principle` shows), while an S4 caps hardest.
**No single sub-S4 finding decides a ranking on its own** — a contested modeling call is S3 at most.

## Why this absorbs noise (the point of the sub-checks, not the scale's maximum)

The instrument's precision is limited by **judge calibration noise** — the same design has scored 0.5 apart
(on the old 0–4 band) from two judges with no qualitative disagreement. The fix is **not a bigger number**:

- **Widening a *holistic* band from 0–4 to 0–100 does not help.** A judge cannot reliably place a design at
  73 vs 76, so the extra resolution is pure noise — a ±0.5 wobble on 0–4 simply becomes ±12 on 0–100, the
  *same ~10%*. The scale's maximum is a red herring.
- **What absorbs noise is decomposition into many independent, well-defined checks that are then averaged.**
  A principle's score is now the mean of *k* binary checks, so a single misjudged check moves it by ~`10/k`,
  not a whole band. Across §1–§18 that is dozens of near-deterministic 0/1 measurements; independent errors
  cancel, and the aggregate's noise shrinks by roughly `√N`. Each check is sharp enough ("does rule R have
  one owner — cite it") that two judges agree on it far more often than on a holistic 0–4, which is where the
  determinism actually comes from.

So 0–10 is used not because 10 > 4 but because a score built from ~5–8 binary checks *lands* on tenths
meaningfully; the checks, not the ceiling, are the mechanism.

**The one deliberate step function stays: the severity cap.** A single failed S4 check (a wrong result, an
unownable rule) still pins the grade low rather than being smoothed into an average — because a correctness
bug *should* dominate. Its determinism comes from the cap being triggered by **one named binary check with a
citation**, not a holistic "how severe did that feel" judgment. Smoothing the cap away would trade
faithfulness for stability; the sub-checks buy stability everywhere the cap does not fire.

## Using the principles as build instructions (same principles, build-side how)

The build side runs the **same** §1–§18, in severity order (correctness first, because an S4 caps the whole
design). The re-grade is the proof this matters: a design placed last on an S4 (§13) because its build side
optimized change-locality (§6) and minimalism (§12) and never held §13 as a target.

1. **Step 0, before designing.** Pin R/X/C from the spec. Design so **every R has one owner** (§9), **every X
   is a localized extension, not a reopen** (§6/§2), and **every C has a trace** (§13). (Discovery's output,
   `references/discovery.md`, used as a build contract.)
2. **The §13 correctness trace is mandatory before "done".** Trace every C-case **and every implied probe**
   (a change-axis × a rule the cases don't spell out — e.g. a multi-line cart with a cart-level discount
   forcing a per-line figure). A design that cannot produce a required output fails a §13 S4 check, however
   clean.
3. **Make each remaining principle pass its checks by construction**, then self-verify with the same sub-check
   evidence rule the judge uses. **Never return a design carrying a failed S4 check, or an uncapped S3,
   without surfacing it.**

Where it plugs into aims: this is the **Worker's / merge agent's pre-return check** and the panel's return
gate (`references/panel-plan.md`, `references/worker-handoff.md`); in single-pass `/aims-plan` the one Worker
runs it before returning. It does not replace `design-principles.md` — it *is* how that file's principles are
applied on each side.

## Notes

- **Scale change:** grades recorded in the experiment records under the earlier rubric are on the **0–4
  band** scale (e.g. `regrade-results.md`, `cross-experiment-regrade.md` report 3.94 / 3.0 / 2.0); those are
  read on that scale and are not retroactively rescaled. The **0–10 sub-check scale here is the current
  instrument** for any new reading. To compare an old 0–4 grade to a new 0–10 one, multiply the old by 2.5 as
  a rough guide only — the sub-check decomposition, not a linear rescale, is the real difference.
- **Coverage anchor:** §1–§18 map onto ISO/IEC 25010 — maintainability (modularity → §1–§8; analysability →
  §11; modifiability → §6/§12; testability → §15), plus functional correctness (§13), reliability
  (§12/§14), performance (§16), security (§17) — so the principle set is checkably complete, not ad hoc.
- **This file is the scoring layer only.** If a principle is added, removed, or reworded, it changes in
  `design-principles.md`; this file only says how to score and build to it.
- **The fillable instrument** is [`assessment-form.md`](assessment-form.md): one row per principle, the
  0–10 score, severity, and a cited finding for any score below 10. It is *how* this procedure is recorded;
  its two projections (the scored form for judging; the worst-first, score-less sub-10 findings for the
  operational review) are in `decisions/0012`.
