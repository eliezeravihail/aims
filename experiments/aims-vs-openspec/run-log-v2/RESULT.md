---
title: "aims-v2 re-run — measured result"
date: 2026-09-16
---

# aims-v2 (sharpened §2) re-run — measured

The aims arm alone, re-run against the sharpened `design-principles.md` §2 (merged to master as 7204326),
same three stage cards, oracle answers reused verbatim from v1. OpenSpec and plain were **not** re-run;
their v1 stage-3 designs were reused in the blind set. So this measures aims-v2 against v1-OpenSpec and
v1-plain, and aims-v1 against aims-v2 within-method.

## Results

| Reading | aims-v1 | **aims-v2** | best in the v2 set |
|---|---|---|---|
| Survival (reopened+discarded) | 11 | **5** (T1:1, T2:4) | **aims-v2** (vs OpenSpec 8, plain 9) |
| Design quality (two full-rubric judges) | third; judges **split** (OpenSpec/plain) | **third; judges agree: OpenSpec** | OpenSpec |
| Design length (words, stage 1/2/3) | 5345 / 10022 / 12363 | **3103 / 4962 / 5179** | aims-v2 |

Blind map (sealed until all readings in): P = aims-v2, Q = plain, R = OpenSpec.
Both quality judges: **R > Q > P** → OpenSpec > plain > aims-v2.

## What the §2 fix moved, and what it did not

**Moved (the things §2 governs):**
- **Survival more than halved (11 → 5)** and is now lowest of any arm. aims-v2 kept the discount pipeline
  tax-agnostic and made tax a `Market` post-pass (`model/promotions/catalog/allocation` untouched at
  stage 3), so the second market was absorbed with far less structural churn than v1.
- **Compactness:** roughly half v1's word count at every stage.
- **Interfaces:** the arm cited the sharpened §2 directly ("three implementations today, a describable
  fourth tomorrow — earns its place (§2)"), and the YAGNI judge did not fault its interface count.

**Did not move (a decision §2 does not govern):**
- **aims-v2 is still third on design quality, under BOTH judges, for the same reason as v1:** it folds the
  VAT into the explanation ledger — a zero-delta `Adjustment` minted by the market into `result.py`. Both
  judges named this precisely as the fault ("architectural padding + coupling to output vocabulary";
  INV-7's sum invariant gets multiple co-owners). §2 is about interfaces and uniform abstraction; the
  decision that keeps aims third is *tax as a movement vs a decomposition*, which flows from the method's
  own "the explanation is the single source of truth" instinct — a stage-2 strength over-applied at
  stage 3, still, even with §2 corrected.
- Note the sharper contrast: v1's judges split (no clear design winner); v2's judges agree on OpenSpec.
  aims did not close the quality gap; it improved on the axes §2 touches.

## Caveats
- **aims-only re-run**, n=1 each; part of the survival drop may be run-to-run variance, not solely the §2
  fix. A clean claim would re-run all three arms and repeat.
- Judges on Opus 4.8 (Fable unavailable), same deviation as v1.
- aims-v2 also overstated one "unchanged" self-claim (Money §1 vs §4/§12) — the same self-description
  looseness every v1 arm showed; the survival judge caught and discounted it.

## The honest one-line reading
Fixing the principle the pilot faulted (§2) improved exactly what that principle governs — aims-v2 absorbs
change far better and is far more compact — but did **not** move aims off third place on code-quality,
because that standing rests on a different decision (tax in the explanation chain) the method keeps making
and §2 does not address. The next lever is not §2; it is whether the method's "explanation is the single
source of truth" doctrine should yield when a later concept (tax) is a decomposition, not a movement.
