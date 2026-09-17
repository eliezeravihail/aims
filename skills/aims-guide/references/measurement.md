# The measurement instrument — one form, everywhere

**All measurement in aims is this one form.** The in-loop review (`SKILL.md` step 5), the standalone
`/aims-review`, and any comparison of designs use the **same** instrument — there is not a separate
"review" measurement and a separate "grading" measurement. The **metrics are
`references/design-principles.md` §1–§18**; this file is only the *how*: fill one row per principle, score
it from binary sub-checks, cite every deduction.

Having two measurement mechanisms is a recipe for divergence — so there is exactly one. What differs is not
the measurement but the **projection you show** (below).

## Step 0 — the fixed inventory (before any scoring)

Pin three lists **from the spec / the objective's exit criteria, never from what the design says about
itself**, and hold them fixed for the whole measurement:

- **(R)** the rules / invariants the product declares;
- **(X)** the change-axes it implies, plus one plausible unstated variant;
- **(C)** the acceptance cases (inputs → required outputs), or — when the product has no numeric cases —
  the end-to-end capability checks.

Every deduction cites an R/X/C item or a named seam. A design that **omits** a required rule or fails a
case *fails* the relevant sub-check — it is not N/A. N/A is decided only by the spec.

## Scoring a principle — from binary sub-checks, not a holistic guess

Decompose the principle (its "The question" in `design-principles.md`, against the pinned R/X/C) into
**3–8 binary structural sub-checks**, each a property objectively present or absent, each cited. Then:

- **score = round(10 × passed / applicable).**
- **severity = the tier of the worst *failed* check** (S1–S4). It sets the weight and a ceiling; the row
  score is `min(sub-check score, ceiling)`.

| worst failed check | ceiling | weight |
|---|---|---|
| none — holds by construction | 10 | ×1 |
| **S1** cosmetic (a naming nit) | 8 | ×1 |
| **S2** moderate (primitive obsession, a data clump, a dead abstraction) | 7 | ×2 |
| **S3** high (mis-owned invariant, a leaked type, a shotgun seam, a latent concept cram) | 5 | ×4 |
| **S4** severe / correctness (wrong or unproducible result; an unenforceable rule; a security hole) | 2 | ×8 |

**Every score needs a citation — including 10** (quote where the principle holds by construction). A score
below 10 also names the R/X/C or seam item it violates. **One defect, one principle** — the most specific;
other rows may reference it, never re-deduct. The score reflects how materially the design violates *that*
principle; cross-principle importance lives in the weight and the caps, never in the row score.

## Weighting a violation — the class comes from the source

Which principles apply, and how hard a failure bites, is **read from `design-principles.md`'s correctness
classes** — this tool does not redefine them:

- a **precondition** failing (§9, §13; §14 under concurrency; §17 with a trust boundary) is **S4** — the
  code is wrong, not merely less clean;
- a **quality** principle failing is **S1–S3** by pervasiveness (cosmetic → local → structural);
- a **conditional** (§16, §17) or **code-leaning** (§14, §15) principle is **N/A** where it does not apply
  (e.g. §14/§15 on a pure design document; §16/§17 with no stated requirement or boundary).

The **subtractive pass** and the **concept-fit pass** (`references/review.md`) are how you fill §12 and §2
respectively — passes *within* this form, not a separate measurement.

## Aggregation

```
weighted_average = Σ(score_§ × weight_§) / Σ(weight_§)
worst_principle  = min score_§
counts           = (#S3, #S4)
graded caps      = any S2 ⇒ ≤ 8.5 · any S3 ⇒ ≤ 7.5 · any S4 ⇒ ≤ 5.0
```

Report the capped grade beside `worst_principle` and the `(#S3,#S4)` counts — never a bare number.

## Two projections — the same filled form, shown two ways

- **Building / in-loop (the default).** Show only the rows **below 10**, sorted **most-severe-first** — a
  **fix-list**, each item its principle + citation + the direction to fix it. **Do not show the aggregate
  score.** This is a practical device, **not a principle**: during construction the Worker should fix
  *content*, and a visible number invites polishing the number instead. The scores still exist underneath;
  they are simply not the thing displayed.
- **Comparing designs.** Show the full scored form + the aggregate profile — for ranking arms or tracking a
  design across revisions, where a number is the point.

## Why sub-checks (not a holistic 0–10)

A principle's score is the mean of several independent binary checks, so a single misjudged check moves it
a fraction, not a whole band; across §1–§18 the errors cancel. Widening a *holistic* band (0–4 → 0–100)
does the opposite — a judge cannot place a design at 73 vs 76, so it is pure noise. The sub-checks, each a
sharp cited yes/no, are what make a re-run reproducible.

## Using the same form to build

The build side runs the **same** §1–§18, correctness first (an S4 caps the whole design): pin R/X/C, design
so every R has one owner (§9), every X is a localized extension not a reopen (§6/§2), and every C has a
trace (§13, over the full input space — not just the listed cases). Self-verify by filling this form before
returning, and never return a design carrying a failed S4 check, or an uncapped S3, without surfacing it.
