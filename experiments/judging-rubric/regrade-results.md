---
title: "Re-grade results — checkout designs under the hardened Quality Metrics rubric"
date: 2026-09-17
---

# Re-grade: checkout-pricing designs under the v2 rubric

A single **neutral, blind** judge graded four stage-3 checkout-pricing designs against
[`quality-metrics.md`](quality-metrics.md) (v2, hardened per external review) with the fixed
[`checkout-spec-inventory.md`](checkout-spec-inventory.md) as Step 0. Blind labels A/B/C/D were shuffled;
the sealed mapping (revealed here after the reading): **A = OpenSpec · B = plain · C = aims-upgraded ·
D = aims-old**. `M19` (performance) and `M20` (security) were N/A by the spec; denominator = M1–M18.

## Result

| rank | design | grade | worst metric | (#S3, #S4) | cap fired |
|---|---|---|---|---|---|
| 1 | **A = OpenSpec** | **3.94** | 3 (M10) | (0,0) | none |
| 2 | **B = plain** | **3.89** | 3 (M10/M16) | (0,0) | none |
| 3 | **D = aims-old** | **3.0** | 2 (M8) | (1,0) | S3 → ≤3.0 |
| 3 | **E = aims single-pass, corrected principles** | **3.0** | 2 (§6) | (1,0) | S3 → ≤3.0 |
| 5 | **C = aims-upgraded (panel)** | **2.0** | 0 (M11/§13) | (1,1) | **S4 → ≤2.0** |

(Designs A–D were graded under the M-numbered v2 rubric; E under the unified §-numbered rubric — same
severity mechanics and the same fixed inventory, so the grades are comparable. M11≡§13, M7≡§9, etc.)

Both aims versions land at the bottom, for **different** faults:

- **aims-old (D): S3, tax cram.** Tax folded into the explanation chain as an `AdjustmentKind.TAX` — SOUTH's
  decomposition modeled as a movement entry with an inert zero delta, NORTH's `+tax` forcing the documented
  fold correction. Concept-fit fault (M8), not a wrong number → S3, capped at 3.0. (It *does* allocate cart
  discounts to lines, so M11 correctness = 4.)
- **aims-upgraded (C): S4, correctness.** It has **no primitive that allocates a cart-level discount down to
  the lines**. Cart `PCT`/`AMT` are summed at the cart; line explanations carry BOGO only. So in SOUTH,
  per-line tax `= round_half_even(line_final × 20/120)` is computed on the **undiscounted** line, and
  `Σ line_cost ≠ cart_total`. Its own acceptance case **C2 (line 10.80 / tax 1.80) is unreachable** — the
  single line never receives `SAVE10`, so it yields 12.00 / 2.00. That is a functional-correctness failure
  (M11 = 0, S4) → grade capped at 2.0. (It *also* still carries an S3 tax-modeling split — NORTH movement vs
  SOUTH decomposition — but the S4 is what pins it last.)

OpenSpec and plain are a near-tie at ~3.9, all-4 on every correctness-critical metric, separated only by a
cosmetic S1 (a garbled clause in plain's M16). Both build a real allocation step, so both pass the M11 probe.

## The finding that matters

This is the first time the experiments measured **more than change-locality**. The only countable pilot
metric — survival / reopen — is **M5 alone** in this rubric. And the two readings now openly disagree:

| | survival (M5-only, prior) | full quality rubric (M1–M18, here) |
|---|---|---|
| aims-upgraded | **best** — reopened 1 (vs old aims 11) | **worst** — 2.0, an S4 correctness gap |
| aims-old | worst — reopened 11 | third — 3.0 |

**aims-upgraded won survival and lost quality**, and the two are causally linked: the same lean,
change-local instinct that made stage 3 reopen nothing (reuse the existing chain, add no machinery) is why
it never built the cart-discount→line **allocation** a correct SOUTH multi-line invoice needs — and survival
scoring never tests correctness, so the regression was invisible until now. This is exactly the gap Pavel
named: *the experiments were measuring only change-locality, not most of what aims claims to improve.* Filling
it flips the sign of the result on this product.

## What it validates about the rubric

The v2 mechanism behaved as designed:
- A **real correctness bug (S4)** capped aims-upgraded at 2.0 and was decisive — as it should be.
- A **contested concept call (S3)** capped aims-old at 3.0 **without** acting like a correctness failure —
  the precise confusion the earlier judging made (it had let an S3 concept dispute decide a verdict like an
  S4). The graded cap + profile kept it honest.
- The **near-tie A/B** was separated only by a cosmetic S1, not inflated into a structural gap — "length is
  not a merit" held (plain is 2009 lines, OpenSpec 1251, and plain did not win on bulk).

## Single-pass re-run — does building to §13 prevent the S4?

After `design-principles.md` was made the single source (adding §13 functional correctness) and the rubric
became the build-side discipline too, the aims arm was re-run on the same product with **single-pass
planning** (one designer, not the panel), building to those principles and running the §13 correctness trace
**over the full input space** ([`../aims-single-pass-rerun`](../aims-single-pass-rerun/README.md)). Result:
**grade 3.0, no S4** — the designer discovered, from the SOUTH per-line-tax requirement rather than from a
stated case, that a multi-line cart carrying a cart-level discount needs the discount **allocated across the
lines** so per-line tax lands on the discounted amount, and built that allocation (proportional to gross,
pennies by largest remainder, line finals summing exactly to the cart net). SOUTH tax is a decomposition
(not a delta), NORTH VAT a single appended adjustment; §9 and §13 both hold.

So **building to the corrected principles moved aims from last (2.0, an S4 correctness gap) to 3.0**, on a
single pass, with less machinery than the panel — a direct, if n = 1, demonstration that the missing
principle (§13, treated as a build target with a full-space trace) is what would have prevented the panel's
bug. aims still does not top the field: it is capped at 3.0 by a *different, milder* S3 — an OCP gap where
the engine enumerates the concrete cart-promotion kinds ("all Proportional then all Fixed"), so a fourth
cart-scoped kind would reopen the engine and its order-independence reasoning. Correctness is fixed;
a structural extension-point ceiling remains.

- **n = 1**, one product, one LLM judge. The checkout product's stress axes (tax as decomposition;
  cart-discount allocation) are ones aims stumbled on; the marketplace product (a separate probe) favored
  aims on change-absorption. Quality here is **product-dependent and multi-dimensional** — no single grade
  is a verdict on the method.
- **Design C is an operator consolidation** of the aims-upgraded panel output into a method-neutral doc. The
  M11 allocation gap is not a consolidation artifact: it is present in the underlying merged arm design (which
  explicitly cut per-line allocation as "speculative" at stage 1 and never restored it for SOUTH), and an
  independent earlier judge flagged the same gap. Still, a fuller arm design might have surfaced it.
- One judge, not two dispositions. The rubric's value is the fixed inventory + evidence-per-score + severity
  coupling, which make a re-run reproducible; a second neutral judge on the same inventory would test that.
