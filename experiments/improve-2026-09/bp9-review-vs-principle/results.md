---
title: "BP9 result — the aims review catches the shortcut 4/4 that the principle-in-prompt missed; output inspection is the irreducible value"
date: 2026-09-20
---

# BP9 — review vs principle, on the weak-model output the principle failed to fix

BP8 showed the aims-lite **principle-in-prompt** did nothing to haiku's concept-fit shortcut rate (2/6 → 2/6).
BP9 runs the method's other lever — the **mandatory review** (`references/review.md`), applied by a competent
Guide (opus) as aims' mixed-tier architecture intends — over the **4 branched builds** the weak model produced,
blind and un-primed.

## Result — detection 4/4; the review names the exact defect and seam

| build | shared structural finding | severity | gate | distinguishing finding |
|---|---|---|---|---|
| b1 (plain run2) | anemic rules + Engine type-switch (§4/§8/§9/§7) | **S3** | CLEAR | repr-leak via `get_items` getter (S2) |
| b2 (plain run5) | anemic rules + Engine type-switch | **S3** | **BLOCKED** | Engine reaches into `Cart._items` across a declared-private boundary (S4) |
| b3 (lite run2) | anemic rules + Engine type-switch | **S3** | CLEAR | Cart exposes public `self.items` (S3) |
| b4 (lite run6) | anemic rules + Engine type-switch | **S3** | CLEAR | + missing docstrings (S1) |

**On all four**, the review independently raised the type-switch as a structural finding — *"the three rule
classes are anemic data-bags and Engine dispatches all discount logic through an `isinstance` if/elif
type-switch; the change-axis 'add a new promo rule kind' forces reopening `Engine.total` instead of adding a
self-contained rule type"* — and named the exact repair seam (a polymorphic `rule.discount(cart)`). It cited
the type-code-switch / Strategy / OCP principles by section. **Detection 4/4**, where the principle line was
**0/6**.

**Repair confirmed** (secondary metric): applying the review's recommendation to b1 — convert to polymorphic
`rule.discount(cart)`, close the representation leak with an immutable snapshot — yields
`repaired/b1-plain-run2.py`, which passes the BP7 hidden stage-1 suite **12/12** with **0** `isinstance`. The
recommended design is exactly the extensible one the other builds reached on their own.

## Two honest qualifications (stated, not buried)

1. **The type-switch lands as S3 (structural), which does not gate.** The aims gate BLOCKS only on S4, so on
   three of the four builds the review *surfaces* the shortcut as a noted finding but would let the build
   through as CLEAR; only b2 gates, on a *separate* S4 seam-leak. So the review reliably **detects and names**
   the shortcut and its fix (4/4), but whether it gets fixed still depends on the builder acting on a
   non-blocking S3 — the review informs, it does not force. That is weaker than "the review guarantees the
   fix," and it is the honest ceiling of this result.
2. **The review caught more than the metric.** It flagged representation-leak / encapsulation defects
   (b1 S2, b2 S4, b3/b4 S3) that neither the aims-lite principle nor this experiment's type-branch metric
   looked at — including a genuine cross-boundary violation in b2 that *does* gate. Output inspection surfaces
   a class of defects that prompt-advice structurally cannot.

## What BP9 establishes (closing the BP6–BP9 arc)

The campaign's improvement question resolves cleanly and against the convenient answer:

- aims' trajectory edge = variance reduction on an early structural choice, sized by the shortcut base rate,
  which is model-dependent (BP6/BP7: ~0% opus, ~17–33% haiku across two axes).
- The **cheap delivery** (aims-lite, principle-in-prompt) captures it **only on a strong model** (BP3) and
  **not on the weak model where the edge is largest** (BP8: 2/6 → 2/6).
- The method's **irreducible, non-transferable value is the review** — output inspection by a competent Guide,
  which caught the shortcut **4/4** on weak-model output and named the validated fix (BP9). This is precisely
  the **mixed-tier configuration the paper argues for**: a cheap Worker builds, a competent review catches what
  the Worker (and any prompt line it ignores) missed.

**Verdict:** you cannot compress aims down to a prompt of principles for a weak executor — the principles don't
stick (BP8). What survives compression is the *review*, and that is where the method earns its cost on the tier
where it matters most. Detection 4/4 vs 0/6; repair validated (12/12). n=4 review, one axis/card; the S3
non-gating caveat is real and recorded.
