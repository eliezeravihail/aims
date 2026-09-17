---
title: "Single-pass re-run under the assessment-form instrument — three products, 0–10"
date: 2026-09-17
---

# Single-pass re-run under the assessment form

The aims arm rebuilt **single-pass** (one designer, not the panel) under the **current** method — the single
source ([`../../skills/aims-guide/references/design-principles.md`](../../skills/aims-guide/references/design-principles.md)
§1–§18), the sub-check build discipline in
[`../judging-rubric/quality-metrics.md`](../judging-rubric/quality-metrics.md), the §13 correctness trace
**over the full input space**, and the **one mandatory self-review-and-revise round** (`decisions/0011`) —
then every arm graded **blind** with the new **assessment form** ([`../judging-rubric/assessment-form.md`](../judging-rubric/assessment-form.md),
0–10, sub-check-derived, one judge per product, labels shuffled). Reference arms (OpenSpec, plain) are the
existing frozen designs, re-graded on the new form. Raw arm drafts are run-state by-products (scratch), not
filed as knowledge.

## Results — capped grade on 0–10 (worst-first findings below)

### Checkout pricing

| arm | grade | worst | (#S3,#S4) | capped by |
|---|---|---|---|---|
| plain | 8.5 | 7 (§4 S2) | (0,0) | S2 (primitive obsession — bare `Decimal`) |
| OpenSpec | 8.5 | 7 (§4 S2) | (0,0) | S2 (primitive obsession + §8 SRP) |
| **aims single-pass (new)** | **7.5** | 5 (§13 **S3**) | (1,0) | **S3 (clamp × SOUTH allocation)** |

aims is **last again — but the fault changed kind.** The old panel arm placed last on an **S4** (no
cart-discount→line allocation, SOUTH tax on undiscounted amounts). The new single-pass arm **built the
allocation** (the §13 trace + the review round caught three S4s during construction), so that S4 is gone.
What remains is a subtler **S3**: `SouthMarket.finalize` allocates *every* applied cart adjustment including
the `CART_MINIMUM` clamp, so a SOUTH cart whose discounts exceed the gross yields a **code-less explanation
step** (violates R5) and a negative-total `allocate` call (R6 at risk). The one review round did not probe
that interaction — direct evidence that **one round is a floor, not convergence** (`decisions/0011`).
Notably aims has the **best §4** of the three (the only true `Money` value object); it is the leanest and
best-typed, and the least robust on an implied interaction.

Worst-first (aims): `§13 5/10 [S3] — SouthMarket.finalize allocates the CART_MINIMUM clamp as a per-line
discount; SOUTH cart with discounts > gross → code-less ALLOCATED_PROMO step (R5) + negative-total allocate
(R6). Direction: exclude the clamp from allocation, or cap discounts at application so no clamp step exists.`

### Marketplace (furniture → cars)

| arm | grade | worst | (#S3,#S4) |
|---|---|---|---|
| **aims single-pass (new)** | **9.9** | 9 (§12 S1) | (0,0) |
| plain | 7.5 (capped) | 5 (§6 S3) | (1,0) |
| OpenSpec | 7.4 | 4 (§6 S3) | (2,0) |

aims first, wide margin. No arm carried an S4 (all named an owner for the car title transfer, transport, and
inspection gate). aims won by **absorbing the car category with zero core edits** (single reserve funnel +
version CAS, `record_gate_outcome` rejecting non-owners, category-blind money), where plain and OpenSpec
**reopened** fulfillment/order for cars (§6 S3). Worst-first (aims): `§12 9/10 [S1] — a @runtime_checkable
decorator on a never-read marker is unearned machinery. Direction: drop it.`

### Ledger continuation (code)

| arm | grade | worst | (#S3,#S4) |
|---|---|---|---|
| capsule-aware | 10.0 | 10 | (0,0) |
| blind | 8.5 | 7 (§4 S2) | (0,0) |

The named `Statement` return vs a bare `tuple[list[Entry], int]` — exactly the difference the deterministic
static metrics were blind to ([`../judging-rubric/cross-experiment-regrade.md`](../judging-rubric/cross-experiment-regrade.md)).

## Cross-product reading

**Product-dependence persists, and is the honest headline.** aims **wins marketplace** (change-absorption is
its strength), **loses checkout** (its lean instinct plus a single review round missed an implied
interaction), a **small edge on the ledger**. No product is a verdict on the method. The method upgrade did
its job on the checkout **headline** fault — the S4 is gone — without making aims top the field there: a
different, milder S3 remains.

## Confounds — do not over-read any single grade

- **Judge calibration noise (±0.5).** One judge per product; a 0.5 gap is inside the instrument's precision
  (established repeatedly — e.g. `../iter-plan/README.md`). Checkout's plain vs OpenSpec (8.5 = 8.5) is a tie
  the judge broke only on finding-count; treat it as a tie.
- **Maturity / N/A asymmetry, and it runs *opposite ways*.** Checkout: the reference arms are very large
  (~88KB/140KB) and the new aims arm is 591 lines — the references are the mature ones there. Marketplace:
  the reverse — the new aims arm is a 506-line document vs ~5KB reference sketches, and the judge scored the
  code-leaning §14/§15 for aims but marked them `N/A(code)` for the sketches, which inflates aims' marketplace
  margin. "Length is not a merit" was instructed, but the asymmetry is real; do not read 9.9 vs 7.5 as a
  4-principle gap.
- **n = 1 per product, one judge, one build each.** The value is the recurring shape across products, not any
  single number.

## What this run validates about the method

- The **§13 full-space trace + the mandatory review round removed the checkout S4** that sank the panel arm —
  the build-side discipline works on the fault it was aimed at.
- The residual checkout **S3 shows the review round's floor**: one round is not convergence; the clamp×SOUTH
  interaction is exactly the kind of implied-interaction fault a second round (or a sharper §13 probe list)
  would target. This is a concrete next direction for the method, not a refutation of it.
- The **assessment form behaved as designed**: sub-check-derived rows, severity caps that put an S3 (aims
  checkout) below two S2s (plain/OpenSpec), and a per-product worst-first findings list.
