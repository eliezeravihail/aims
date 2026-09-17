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
- **grading** — score each principle 0–4 with evidence, then combine by a severity-weighted rule.

Asking a builder for the principles and then measuring against a *different* list is the failure this
avoids — so there is deliberately no second canon here.

## Step 0 — the fixed inventory (before any scoring or building; identical for every side)

Pin three product-level lists **from the fixed spec, never from what a design says about itself**, and use
them unchanged for every judge and every design:

- **(R) the rules / invariants** the product declares;
- **(X) the change-axes** it implies, plus one plausible unstated variant;
- **(C) the acceptance cases** (inputs → required outputs).

Then, per design, enumerate that design's **seams and named elements**. Every deduction cites an R/X/C item
or a named seam. A design that **omits** a required rule (R) or fails a case (C) is scored 0–1 on the
relevant principle, **not** N/A — silence is a miss. N/A is decided only by the spec (the product genuinely
has no such requirement). Worked inventories: [`checkout-spec-inventory.md`](checkout-spec-inventory.md),
[`marketplace-spec-inventory.md`](marketplace-spec-inventory.md).

## Scoring a principle — one judgment (severity), not two

Do **not** pick a 0–4 score and a severity independently. Find the **worst fault** on the principle, cite the
inventory item it violates, and tag its **severity**. Severity then fixes *both* the score ceiling and the
weight:

| worst fault on the principle | score | weight |
|---|---|---|
| **none** — holds *by construction* | **4** | ×1 |
| **S1** cosmetic (a naming nit, formatting) | **3** | ×1 |
| **S2** moderate (primitive obsession, a local coupling, a dead abstraction, a data clump) | **≤ 3** (2–3 by pervasiveness) | ×2 |
| **S3** high (mis-owned invariant, an implementation type leaked at a seam, a shotgun-surgery seam, a latent concept cram) | **≤ 2** (1–2) | ×4 |
| **S4** severe / correctness (wrong or unproducible result; a stated rule unenforceable or bypassable; a security hole; data corruption) | **≤ 1** (0–1) | ×8 |

**Every score needs a citation — including 4.** For a 4, quote *the single place the principle holds by
construction*; for a deduction, quote the defect **and** name the R/X/C or seam item it violates. No citation
→ the score is struck (this closes the "default everything to 4" gap). **Length is never a merit.**

## One defect, one principle

A single defect is deducted under **exactly one** principle — the most specific one — and the judge names it
there. Related principles may *reference* it, never re-deduct. (A Law-of-Demeter reach-through is scored
under §1/§6, not twice; an "anemic model with rules outside the owner" is scored once, under §5 *or* §9, and
the judge says which.)

## The metrics are the principles — applicability + severity ceiling

The table adds only what scoring needs on top of each principle's own "The question" in `design-principles.md`
(read that for *what* to measure). "Applies to" gates code-only checks off a pure design document.

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

Over the non-N/A principles:

```
weighted_average = Σ (score_§ × weight_§) / Σ (weight_§)      # weight from the severity table
worst_principle  = min score_§
counts           = (#S3 findings, #S4 findings)
```

Apply **graded caps** to the reported grade (one structural fault must not read as "Sound"):

| any finding at | grade capped at |
|---|---|
| S2 | ≤ 3.5 |
| S3 | ≤ 3.0 |
| S4 | ≤ 2.0 |

Report the **capped grade beside `worst_principle` and the (#S3,#S4) counts** — never a bare number. Rank by
capped grade, then `worst_principle`, then fewer S3/S4. So a single §-at-0/S3 among clean 4s does not average
to "Sound" (the S3 cap pins it ≤3.0 and `worst_principle=0` shows), while an S4 caps hardest. **No single
sub-S4 finding decides a ranking on its own** — a contested modeling call is S3 at most.

## Using the principles as build instructions (same principles, build-side how)

The build side runs the **same** §1–§18, in severity order (correctness first, because an S4 caps the whole
design). The re-grade is the proof this matters: a design placed last on an S4 (§13) because its build side
optimized change-locality (§6) and minimalism (§12) and never held §13 as a target.

1. **Step 0, before designing.** Pin R/X/C from the spec. Design so **every R has one owner** (§9), **every X
   is a localized extension, not a reopen** (§6/§2), and **every C has a trace** (§13). (Discovery's output,
   `references/discovery.md`, used as a build contract.)
2. **The §13 correctness trace is mandatory before "done".** Trace every C-case **and every implied probe**
   (a change-axis × a rule the cases don't spell out — e.g. a multi-line cart with a cart-level discount
   forcing a per-line figure). A design that cannot produce a required output carries an S4, however clean.
3. **Make each remaining principle hold by construction**, then self-verify with the same evidence rule the
   judge uses. **Never return a design carrying an S4, or an uncapped S3, without surfacing it.**

Where it plugs into aims: this is the **Worker's / merge agent's pre-return check** and the panel's return
gate (`references/panel-plan.md`, `references/worker-handoff.md`); in single-pass `/aims-plan` the one Worker
runs it before returning. It does not replace `design-principles.md` — it *is* how that file's principles are
applied on each side.

## Notes

- **Coverage anchor:** §1–§18 map onto ISO/IEC 25010 — maintainability (modularity → §1–§8; analysability →
  §11; modifiability → §6/§12; testability → §15), plus functional correctness (§13), reliability
  (§12/§14), performance (§16), security (§17) — so the principle set is checkably complete, not ad hoc.
- **This file is the scoring layer only.** If a principle is added, removed, or reworded, it changes in
  `design-principles.md`; this file only says how to score and build to it.
