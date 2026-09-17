---
title: "marketplace change-absorption — aims vs OpenSpec, furniture → cars (informal Q2 probe)"
date: 2026-09-17
---

# Marketplace change-absorption: aims vs OpenSpec

A **light, informal** re-run of the survival reading (Q2) from the frozen
[`../aims-vs-openspec`](../aims-vs-openspec/README.md) pilot, on a different and larger product: an
online marketplace. Each method designs an antique-furniture marketplace (stage 1), then **minimally
extends its own design** to also sell old / classic cars (stage 2). The reading is the countable one:
per named component/seam, does it **survive** / **extend** / **reopen** / **discard**, and the
**reopened + discarded** count (lower = better change-absorption).

> **Not a PROTOCOL-grade experiment — read the readings, not a score.** This is a single-shot probe run
> to answer the user's question "add cars and check how the architecture performs; do it with OpenSpec
> for comparison", not a controlled pilot. It deviates from [`../PROTOCOL.md`](../PROTOCOL.md) and from
> the frozen `aims-vs-openspec` package in ways that matter (see **Validity**). It does **not** extend or
> update that pilot; it sits beside it. n = 1 per arm.

## How it was run (faithful to the method, not role-played)

Both arms were run by **real subagents reading this repo's own method files** — the assistant did not
role-play either method:

- **aims arm.** Stage-1 design produced by the panel: a Guide set one objective; **three axis-focused
  Workers** (clean-code / correct-encapsulation / correct-genericity) each read
  [`skills/aims-guide/references/panel-plan.md`](../../skills/aims-guide/references/panel-plan.md) §Axes and
  [`design-principles.md`](../../skills/aims-guide/references/design-principles.md) and designed
  independently; a **merge agent** read `panel-plan.md` §"The merge agent" and composed best-from-each.
  Stage 2 (add cars) was handed the stage-1 design and asked to extend minimally and self-classify.
- **OpenSpec arm.** Ran the spec-first shape (capabilities + specs + components + seams), stage 1 then
  stage 2, in parallel, on the identical furniture→cars card.

The exact stage-1 designs, stage-2 extensions, and both self-classification tables are in
[`arms.md`](arms.md). The independent blind judge's prompt and verdict are in
[`judge.md`](judge.md).

## The change (identical for both arms)

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

## Validity — why this is a probe, not a pilot

- **n = 1 per arm**, one product, one change transition. Run-to-run variance is real (see the
  [self-redesign regression](../self-redesign-regression/results.md) residual). No plain (no-method) arm,
  so "method vs. no method" is **not** separated here.
- **Self-scored first.** The primary table above is each arm grading its own homework, which is exactly
  the bias the frozen pilot avoids with a blind judge. The independent blind judge above is the
  correction; where it disagrees with a self-score, trust the judge.
- **One change, not staged.** The frozen pilot uses three stages because a single change "that falsifies
  nothing leaves nothing to measure". Here a single well-chosen change (cars) did apply real pressure —
  both arms reopened — but a second stage would harden the reading.
- **Not the frozen package.** Different product (marketplace, not a checkout pricing service), different
  substrate, no oracle log, no card freezing. This does not feed `aims-vs-openspec/results.md`.
- **The Q1 rubric caveat still applies** where the judge leans on `design-principles.md` — it is aims'
  own house rubric; the judge was told to keep verdicts structural and quotable so a reader who rejects
  the rubric can still check the fact.

## What it does and does not support

- **Supports:** on this product both methods land at the *same two* conceptual pressure points, so the
  furniture→cars change is a fair, discriminating stress; and aims' one designed-for change axis
  (fulfillment as an abstract plugin seam) measurably absorbed the logistics variation the OpenSpec arm
  had to reopen for.
- **Does not support:** any claim that one method dominates. The counts tie 2–2; the differences are in
  *where* the un-reopened forces landed (aims folded them into existing owners; OpenSpec added services),
  which is texture, not a decisive count. n = 1.
