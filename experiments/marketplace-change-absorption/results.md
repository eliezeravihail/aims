---
title: "marketplace change-absorption — aims vs OpenSpec vs plain, furniture → cars (informal Q2 probe)"
date: 2026-09-17
---

# Marketplace change-absorption: aims vs OpenSpec vs plain

A **light, informal** re-run of the survival reading (Q2) from the frozen
[`../aims-vs-openspec`](../aims-vs-openspec/README.md) pilot, on a different and larger product: an
online marketplace. Three arms — **aims**, **OpenSpec**, and a **plain** (no-method) control — each design
an antique-furniture marketplace (stage 1), then **minimally extend their own design** to also sell old /
classic cars (stage 2). The reading is the countable one: per named component/seam, does it **survive** /
**extend** / **reopen** / **discard**, and the **reopened + discarded** count (lower = better
change-absorption).

**Headline (three independent blind judges, converging): aims > OpenSpec > plain.** All three rank aims
first, all put its honest reopen count at 2, and all re-classify a rival's self-scored "extend" as a real
reopen. The plain control ranks last on both absorption *and* honesty — so on this product the method, not
the model alone, is doing the work. Still n = 1 — see **Validity**.

> **Not a PROTOCOL-grade experiment — read the readings, not a score.** This is a single-shot probe run
> to answer the user's question "add cars and check how the architecture performs; do it with OpenSpec
> for comparison", not a controlled pilot. It deviates from [`../PROTOCOL.md`](../PROTOCOL.md) and from
> the frozen `aims-vs-openspec` package in ways that matter (see **Validity**). It does **not** extend or
> update that pilot; it sits beside it. n = 1 per arm.

## How it was run (faithful to the method, not role-played)

All three arms were run by **real subagents** — the assistant did not role-play any method. Every arm's
stage-1 design was produced **blind to the car requirement** (cars were introduced only afterward), so no
arm could pre-build for the change it was about to be tested on.

- **aims arm.** Stage-1 design produced by the panel: a Guide set one objective; **three axis-focused
  Workers** (clean-code / correct-encapsulation / correct-genericity) each read
  [`skills/aims-guide/references/panel-plan.md`](../../skills/aims-guide/references/panel-plan.md) §Axes and
  [`design-principles.md`](../../skills/aims-guide/references/design-principles.md) and designed
  independently; a **merge agent** read `panel-plan.md` §"The merge agent" and composed best-from-each.
  Stage 2 (add cars) was handed the stage-1 design and asked to extend minimally and self-classify.
- **OpenSpec arm.** Ran the spec-first shape (capabilities + specs + components + seams), stage 1 then
  stage 2, on the identical furniture→cars card.
- **plain arm (control).** A capable agent told only "design it well" — **no** aims, **no** OpenSpec, no
  method file. Added after the first pass to separate "the method helps" from "a capable agent does this
  anyway." Its stage-1 was designed with no knowledge that cars were coming.

The exact stage-1 designs, stage-2 extensions, and all three self-classification tables are in
[`arms.md`](arms.md). All three judges' prompts and verdicts are in [`judge.md`](judge.md).

## The change (identical for all arms)

Cars add: VIN / year / mileage / registration; **legal title/registration transfer** (not just physical
handover); **different logistics** (pickup/transport, not parcel shipping); an **optional pre-purchase
inspection**. Money, fee, and reviews are stated to work as before.

## Self-scored result

Both arms self-reported **reopened + discarded = 2**, and — notably — both reopened at the **same two
conceptual places**:

| Conceptual place the change stressed | aims arm | OpenSpec arm |
|---|---|---|
| **Item attribute model / product category** (furniture-shaped attributes; a second, disjoint car shape) | **reopened** — Catalog's Listing attribute model / the explicit "category is not a plugin axis" bet | **reopened** — ListingService's furniture-shaped attributes had no category/product-type seam |
| **Completion = physical receipt/handover** (cars complete on *legal* title transfer, not possession) | **reopened** — Sale's handover step (physical-possession-completes must become legal title transfer; unowned legal artifact) | **reopened** — FulfillmentService (parcel logistics *and* completion-equals-receipt both break) |
| Logistics variation (parcel vs pickup/transport) | **extended** — `Transport <: Fulfillment` at the existing Fulfillment plugin seam | folded into the FulfillmentService reopen above |
| Fee for cars | **extended** — new `FeePolicy` at the existing `FeePolicy.quote(ctx)` seam | (Ledger/Payments **survived**) |
| Inspection gate | **extended** (borderline) — into `Sale.complete()` precondition, no new states | **new** InspectionService |
| Title transfer ownership | folded into the handover reopen | **new** TitleTransferService |
| Money / fee / reviews / payment port / provenance | **survived** | **survived** |

Self-scored headline: **tie, 2–2**, both methods reopening the same two conceptual places. _(The blind
judge below overturns this tie — the OpenSpec self-score was one reopen too generous.)_

Two texture differences the self-scores show (self-reported, confirm against the blind judge below):

1. **Logistics.** aims absorbed the new logistics *for free* — `Transport` is a new subtype at the
   `Fulfillment{status, completion_signal}` plugin seam it had already designed — where the OpenSpec arm
   counted logistics inside its FulfillmentService **reopen**. This is the one place the designed-for
   change axis (fulfillment-tracking) paid off in the count.
2. **Title + inspection.** aims folded title transfer into its (reopened) handover owner and inspection
   into the existing `complete()` guard; OpenSpec **added two new services** (TitleTransferService,
   InspectionService) rather than reopening — new capabilities do not add to reopened+discarded, so this
   did not move the count, but it is a different structural response to the same force.

## Blind, independent judge

An independent judge — not either producing session — re-derived the counts from both designs
**anonymized as Design A (= OpenSpec) and Design B (= aims)**, no method names, grounded on
`design-principles.md`, told to correct any self-score. Full prompt and verbatim verdict:
[`judge.md`](judge.md).

**It broke the self-scored 2–2 tie: OpenSpec = 3, aims = 2.**

| | self-scored | blind judge |
|---|---|---|
| aims arm (Design B) | 2 | **2** (accepted; "honest, arguably even slightly harsh") |
| OpenSpec arm (Design A) | 2 | **3** (self-score "too generous by one") |

- The extra OpenSpec reopen the judge found is **OrderService**: the OpenSpec arm self-scored its
  completion-condition change ("extended"), but the judge re-classified re-wiring a single-signal
  `ReceiptConfirmed→OrderCompleted` assumption into a three-way conjunction as a **reopen** of a baked-in
  assumption, "not additive growth."
- It **accepted aims' 2 as honest** (aims flagged the handover-could-ride-the-seam caveat and still scored
  itself reopened).

**Verdict: aims absorbed the car change better, on change-locality** — grounded in two `design-principles.md`
criteria, each with a quotation:

1. **§2 (generic interface / subtype-not-cram).** aims' `Fulfillment{status, completion_signal}` supertype
   with `TrackedShipment <: Fulfillment` let the new logistics arrive as `Transport <: Fulfillment` at an
   existing seam — "the §2 Box/OrientedBox discipline done right." OpenSpec had baked receipt-as-completion
   into one concrete FulfillmentService, so cars forced it method-typed and broke the completion signal:
   "A reopens what B extends."
2. **§6 (change-locality / no shotgun surgery).** aims fed inspection "into Sale's existing `complete()`
   guard… no new lifecycle states" — one place — because its stage-1 `CompletionToken`/`completion_signal`
   had already abstracted "what act completes the sale." OpenSpec spread inspection across a new
   InspectionService **and** an OrderService rewrite.

Where the judge saw a genuine tie: **both** reopened the attribute-model / "category is not a plugin axis"
bet (a defensible stage-1 judgment both got wrong equally — aims at least documented it as a deliberate
bet), and **title transfer was roughly a wash** (a genuinely unowned legal-document responsibility both
had to pay for — aims by reopening handover, OpenSpec via OrderService-completion + a new
TitleTransferService).

**So the corrected reading is not the self-scored tie: the blind judge puts aims ahead by one reopen and,
more tellingly, on where the un-reopened forces landed.** Still n = 1 (see **Validity**).

## Three judges, and the plain control

The reading was then hardened two ways (full prompts + verbatim verdicts in [`judge.md`](judge.md)):

1. **A guided judge** (focus: quality / maintainability / ease-of-change, told **not** to use aims' rubric
   file) scored the same two designs and **converged**: aims better, OpenSpec = 3, aims = 2, same
   OrderService override — with one point scored honestly *for* OpenSpec (its `TitleTransferService`
   isolates legal transfer cleanly where aims reopened its handover step).
2. **A plain (no-method) arm** was added, and **a third judge scored all three blind, with the labels
   shuffled** so they do not group by method.

**Three-way ranking: aims > OpenSpec > plain. No genuine ties.**

| arm | self-count | judge's re-derived count | note |
|---|---|---|---|
| **aims** | 2 | **2** | "honest… its two reopens are the two genuinely unforeseeable ones" |
| **OpenSpec** | 2 | **2** (borderline 3) | OrderService completion change is a borderline reopen |
| **plain** | 3 (self-dedups to ≈2) | **3** | Listing "extended" overridden to **reopened**; "least honest self-report" |

The plain control is the point of the whole exercise: it separates *"aims helps"* from *"a capable agent
does this anyway"*. The unguided agent **welded completion to physical handover** (no reified completion to
cushion the title change), built **no fulfillment polymorphism** (so logistics forced a reopen — where aims
just added `Transport <: Fulfillment`), and **under-counted its own attribute-model reopen** (it called
introducing a brand-new cross-cutting category axis an "extend"). aims absorbed the change with fewer
reopens *and* scored itself more honestly than the plain agent.

**Cross-judge convergence.** Three independent blind judges — on aims' own `design-principles.md`, on
general quality with no rubric, and three-way with shuffled labels — **all rank aims first**, all put its
honest reopen count at **2**, and all re-classify a rival's self-scored "extend" as a **reopen**.
Convergence across a rubric change and a label shuffle is the strongest thing an n = 1 probe can offer.
Still n = 1.

## Validity — why this is a probe, not a pilot

- **n = 1 per arm**, one product, one change transition. Run-to-run variance is real (see the
  [self-redesign regression](../self-redesign-regression/results.md) residual). The plain control is
  present, so "method vs. no method" *is* separated here — but on a single sample.
- **Self-scored first, then corrected.** Each arm graded its own homework — exactly the bias the frozen
  pilot avoids. The three blind judges are the correction; where a judge disagrees with a self-score,
  trust the judge (and note the plain arm's self-score was the one most overturned).
- **One change, not staged.** The frozen pilot uses three stages because a single change "that falsifies
  nothing leaves nothing to measure". Here a single well-chosen change (cars) did apply real pressure — all
  three arms reopened — but a second stage would harden the reading.
- **Not the frozen package.** Different product (marketplace, not a checkout pricing service), different
  substrate, no oracle log, no card freezing, stages not run in fresh sessions (the plain arm's stage 2
  reused the stage-1 agent, though blind to cars at stage 1). This does **not** feed
  `aims-vs-openspec/results.md`.
- **The house-rubric caveat is partly offset here.** One judge used aims' `design-principles.md`, but the
  other two did **not** (general quality; shuffled three-way) and still ranked aims first — so the verdict
  does not depend on the house rubric. Every judge grounds claims in quotations, so a reader who rejects
  any one framing can check the facts.
- **This result is not comparable to the frozen pilot's Q1 as "same method, different product."** Between
  the two runs **aims itself changed**: the self-redesign refactor that corrected the panel role model
  (`panel-plan.md`: three axis-focused Workers over one shared objective, merged best-from-each) and the
  measurement lens (`review-panel.md`) merged 2026-09-16 20:19 → 2026-09-17 00:09 (#60). The pilot ran
  2026-09-15/16 on **pre-upgrade** aims (placed third); this probe read the **upgraded** files (placed
  first). So the pair cannot be read as product-dependence — that reading silently assumed a constant
  method. The version change is a confound, and because the refactor targeted precisely the panel/
  measurement mechanisms this probe exercises, **the more plausible reading is that the upgrade moved aims
  forward**, not that outcomes merely "depend on the product." Isolating upgrade-from-product cleanly would
  need a same-product before/after: re-running the pilot's checkout-pricing product with upgraded aims.
  Until that is run, this probe is n = 1 on the upgraded method, and the two probes measure two different
  aims versions.

## What it does and does not support

- **Supports (on this product):** the furniture→cars change is a fair, discriminating stress — all three
  arms reopened somewhere; aims' pre-built abstractions (`Fulfillment` as an abstract seam; completion
  reified as `completion_signal`/`CompletionToken`) absorbed logistics and inspection as *extensions*
  where both other arms **reopened**; and three blind judges under different framings all rank aims first
  with the smallest honest reopen count. The plain control makes this a claim about the **method**, not the
  model — the unguided agent, given the same product, produced the least change-absorbing and least
  honestly-scored design.
- **Does not support:** any general claim that upgraded aims dominates. This is **n = 1** on the upgraded
  method, on a product whose natural variation axes (fulfillment, completion) are ones aims abstracted well.
  It is **not** contradicted by the frozen pilot's third-place Q1 — that pilot measured a *different,
  pre-upgrade* aims (see Validity), so the two are not a like-for-like pair. What is still open: whether the
  upgraded method also lifts the pilot's own product (a same-product before/after would isolate upgrade from
  product), and whether the win holds beyond n = 1.
