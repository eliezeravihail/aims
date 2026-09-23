---
title: "BP7 result — the trajectory edge generalizes as VARIANCE REDUCTION on a second axis, but is model-dependent; aims-lite ties"
date: 2026-09-20
---

# BP7 — does the edge generalize off derive-don't-store, and does aims-lite capture it?

Two questions, one 2-stage build (a promotional pricing engine; stage 2 = a priority + exclusivity stacking
policy). The structural axis here is **concept-fit**: model each rule as a first-class object with its own
`discount(cart)` (extensible) vs a **type-branch** `isinstance` chain inside `Engine.total` (the shortcut that
reopens when the combination step changes). Three arms — **plain** (no method), **lite** (a 4-principle prompt
block, no skill/records/review), **aims** (full method) — all opus, stage 2 by fresh sessions. Plus a **base-rate
probe** (6 haiku plain stage-1 builds) to size the shortcut rate, mirroring BP6.

## The opus 3-arm result: a three-way tie, 0 reopens all round

| arm | stage-1 dispatch | correctness (both stages) | reopened-owner events | stage1→2 diff | records |
|---|---|---|---|---|---|
| **plain** | first-class `discount()` (polymorphic) | **19/19** | **0** | ~43 lines | none |
| **lite**  | first-class `discount()` (polymorphic) | **19/19** | **0** | ~19 lines | none |
| **aims**  | first-class `Rule.discount()` (polymorphic) | **19/19** | **0** | ~48 lines | companion + 2 ADRs |

**All three opus arms modeled rules as first-class objects at stage 1** — including the un-prompted plain arm —
so the stacking change was a pure seam extension for everyone (`Engine.total`'s `sum(...)` → a sorted walk with
an exclusivity `break`; each rule's `discount()` untouched). **0 reopens across the board; correctness a
three-way tie.** On opus, the concept-fit shortcut simply isn't taken, so there is nothing for aims' review to
save. The aims records did name the extension seam (ADR 0001 said the engine owns "only the summation and the
floor"), and the fresh aims session recognized stacking as an evolution of exactly that step — a **Q2
continuity signal (n=1)** — and placed the new metadata slightly more cleanly (two kwargs added once on the
`Rule` base vs per-constructor). But that bought no avoided reopen, because none was on offer.

## The base-rate probe: the shortcut IS taken — on a weaker model (2/6 haiku)

| run (haiku, plain) | 1 | 2 | 3 | 4 | 5 | 6 | rate |
|---|---|---|---|---|---|---|---|
| dispatch | poly | **branch** | poly | poly | **branch** | poly | **2/6 branch ≈ 33%** |

Runs 2 and 5 put an `isinstance(rule, …)` if-elif chain **inside the engine** (rule classes as dumb data) —
the exact type-code shortcut aims' review rejects, and the one that would force reopening `Engine.total` when
the stacking policy arrives. On **opus** the rate was **0/3** (all arms polymorphic); on **haiku** it is **2/6**.

## What this establishes (honest, and it sharpens BP6 rather than repeating it)

1. **The trajectory edge generalizes to a second, unrelated axis** — but as the **same mechanism**: variance
   reduction on an early structural choice. On concept-fit, exactly as on derive-don't-store, aims' review
   *reliably* picks the extensible design (first-class rules); a plain builder picks it only *sometimes*; the
   edge is the avoided reopen on the "sometimes it didn't." This is the third axis-independent confirmation
   (BP1/BP2 derive; BP5 ledger; BP7 concept-fit) that the edge is **not** a correctness advantage and **is** a
   probabilistic trajectory one.
2. **The edge is model-dependent, and this is the cleanest demonstration yet of the mixed-tier prediction.**
   The concept-fit shortcut base rate is **~0% on opus** but **~33% on haiku**. So aims' concept-fit edge is
   *invisible on opus* (a capable model already derives the good design — the opus 3-arm null) and *real on a
   weaker executor*. The paper's "the gap widens under a weaker Worker" holds on this axis: the value of the
   method's review scales inversely with how good the raw executor already is. (BP6 found the same shape on
   derive-don't-store: 1/6 on haiku.)
3. **aims-lite tied full aims (and tied plain) — because there was nothing to separate them on opus.** On this
   product the principle injection neither helped nor hurt vs plain: all three opus arms already derived. This
   is a **weak** aims-lite datapoint (a null environment can't discriminate delivery mechanisms); aims-lite's
   real test is a product/model where the shortcut base rate is high (e.g. haiku on this card), which BP7's
   opus arms did not provide. Recorded as inconclusive-for-lite, not a win.

## Verdict

The concept-fit trajectory edge is **real but latent**: it exists (haiku takes the shortcut 2/6) and it is the
same variance-reduction mechanism as every other axis, but on a capable executor (opus) the shortcut base rate
collapses to ~0 and the edge with it — so the opus 3-arm test is a **null by ceiling, not by absence**. Net
campaign reading, now across three structural axes and two model tiers: **aims' measured benefit is
avoided-reopen variance reduction, sized by the shortcut base rate on each axis×model — which is modest for a
strong model (~0–17%) and larger for a weak one (~33% here).** Correctness ties everywhere. n=1 product per
arm, n=6 for the base rate; one card, two tiers. Nulls and ceilings recorded as such.
