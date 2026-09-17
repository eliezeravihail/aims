---
title: "judge — independent, blind re-derivation of the change-absorption counts"
date: 2026-09-17
---

# Blind judge

An independent judge, **not** either of the sessions that produced a design, was given both stage-1
designs and both stage-2 extensions **anonymized as Design A and Design B** — no method names, no mention
of aims or OpenSpec, no directory tells. Mapping (sealed from the judge): **Design A = OpenSpec arm**,
**Design B = aims arm**. The judge was told to read
[`design-principles.md`](../../skills/aims-guide/references/design-principles.md) for grounding, to
**re-derive its own** survived/extended/reopened/discarded classification rather than trust the arms'
self-reports, and to correct any self-score it found too generous or too harsh. Full designs it was shown:
[`arms.md`](arms.md) (identical content, relabelled A/B).

## Verdict (verbatim)

> ## Independent architecture judgment: which design absorbed cars better
>
> ### Design A — my re-derived classification
> - ListingService — **reopened** (agree). Furniture-shaped schema had no category axis; "car attributes
>   not a variant of furniture schema... requires category-specific attribute schema stage-1 lacked."
> - CatalogQuery — **extended** (agree; "new car facets additive").
> - OrderService — **reopened** (team said *extended* — too generous). Stage-1 completion was one
>   hardcoded source: "FulfillmentService→OrderService ReceiptConfirmed→OrderCompleted." Stage-2 makes it
>   "a conjunction of (handover) AND (title transferred) AND (inspection passed OR waived)." OrderService
>   owns the completion condition and had no composite/pluggable gate; re-wiring it to aggregate two new
>   signal sources is a structural change to a baked-in assumption, not additive growth.
> - LedgerService — **survived** (agree).
> - FulfillmentService — **reopened** (agree). "logistics method-typed (parcel vs pickup/transport);
>   physical receipt no longer the completion signal for cars" — the receipt-as-completion assumption
>   broke and a type axis was retrofitted.
> - ReputationService, ProvenanceService, PaymentGatewayAdapter — **survived** (agree).
> - TitleTransferService, InspectionService — **new** (additive; don't count).
>
> **My reopened+discarded count for A = 3** (ListingService, FulfillmentService, OrderService). Team A
> self-reported **2**; that is too generous by one — it scored the completion-condition change as
> "extended" on OrderService when the underlying single-signal assumption was actually reopened.
>
> ### Design B — my re-derived classification
> - Catalog availability/lifecycle, MediaStore, concrete Provenance — **survived** (agree).
> - typed-facet search — **extended** (agree).
> - Catalog attribute model / "category NOT a plugin axis" bet — **reopened** (agree; "cars are a disjoint
>   attribute shape, so a category axis the design declined must be introduced"). Same miss as A.
> - Sale purchase lifecycle — **extended** (agree; inspection "rides completion_signal path; no new
>   lifecycle states").
> - Sale handover step — **reopened** (agree). "a car completes on legal title transfer with a document to
>   move/record — a responsibility no current owner holds."
> - Sale Fulfillment/TrackedShipment — **extended** (agree; "add Transport <: Fulfillment... Fulfillment
>   stays abstract").
> - CompletionToken, Ledger, PaymentGateway, Reputation — **survived**; FeePolicy — **extended** (agree).
>
> **My reopened+discarded count for B = 2** (Catalog attribute model, Sale handover). Team B self-reported
> **2** — honest, arguably even slightly harsh: it flagged the caveat that title "could ride that seam and
> handover would only extend," and still scored itself reopened. I accept 2, because the legal-document
> responsibility is genuinely unowned.
>
> ### Verdict: Design B absorbed the car change better.
>
> Re-derived counts: **A = 3, B = 2.** But the count understates it; the decisive difference is *where*
> each change landed, per §2 and §6.
>
> **Fulfillment is the separator.** design-principles §2 rewards abstracting to "a describable second
> implementation... the anticipated generic continuation." B built exactly that seam: `Fulfillment{status,
> completion_signal}` as a supertype with "TrackedShipment <: Fulfillment only for genuine trackers." When
> pickup/transport arrives, it is `Transport <: Fulfillment` at "the existing Fulfillment plugin seam" — a
> clean subtype addition. This is the §2 Box/OrientedBox discipline done right: abstract *up* to the shared
> concept, let the richer case (tracking) be the subtype, so Transport is never "forced to fabricate" a
> tracking number. A instead baked receipt-as-completion into one concrete FulfillmentService, so cars
> forced it "method-typed (parcel vs pickup/transport)" and broke "physical receipt... completion signal"
> — the value-correct cram breaking under a second case. A reopens what B extends.
>
> **Inspection shows the same change-locality gap (§6 shotgun surgery).** B feeds it "into Sale's existing
> complete() guard... no new lifecycle states" — one place changes. A absorbs it by adding
> InspectionService *and* rewriting OrderService's completion into a conjunction — the change is spread
> across two components. B's stage-1 CompletionToken / `completion_signal` had already abstracted "what act
> completes the sale" (§9: one enforcement point, parameterized), so inspection dropped in; A had no such
> seam.
>
> **Where they tie:** both reopened the attribute model — both bet "category is NOT a plugin axis" and the
> domain refuted it. This is a defensible §2 judgment call (no describable second attribute shape at stage
> 1) that both got wrong equally; B at least documented it as a "deliberate stage-1 bet." And title is
> roughly a wash: cars introduced a genuinely unowned legal-document responsibility, so *both* had to pay
> one reopen-ish cost for it — A via OrderService-completion + a new TitleTransferService (clean §8
> single-responsibility for the new concept), B via reopening Sale's handover.
>
> Net: A's extra, avoidable reopen is FulfillmentService — a seam B had correctly foreseen and abstracted.
> B wins on change-locality, grounded in §2 (generic-interface / subtype-not-cram) and §6 (localized
> change, no shotgun surgery). A's own self-score of 2 also masks a third reopen (OrderService) that B's
> design avoided.

## What the blind pass changed vs. the self-scores

- It **broke the self-scored 2–2 tie**: OpenSpec (A) → **3**, aims (B) → **2**. The extra OpenSpec reopen
  is **OrderService**, which the OpenSpec arm self-scored as "extended" and the judge re-classified as a
  reopen (a single-signal completion assumption re-wired into a conjunction).
- It **accepted aims' self-score of 2 as honest** (even slightly harsh, given aims flagged the
  handover-could-ride-the-seam caveat and still scored itself reopened).
- It **confirmed the two texture readings** in [`results.md`](results.md): the `Fulfillment` subtype seam
  is where aims extends and OpenSpec reopens (§2), and inspection is a change-locality separator (§6).

**Still n = 1.** One blind judge, one product, one change transition. The judge grounds every claim in a
quotation and a numbered `design-principles.md` criterion, so a reader who rejects the house rubric can
still check each fact — but this is a suggestive probe, not a robust result. See the **Validity** section
of [`results.md`](results.md).

---

# Judge #2 — guided (quality / maintainability / ease-of-change), no rubric file

A second independent, blind judge, given the **same two designs** (mapping unchanged: **A = OpenSpec,
B = aims**), told to focus on **code/design quality, maintainability, and ease of change** but **not** to
read any external rubric file — general software-engineering judgment only. This tests whether the
verdict survives dropping aims' house rubric.

**It converged with Judge #1: aims (B) is better, A = 3 reopens, B = 2.** Same override — OrderService's
completion-condition change on the OpenSpec arm is a reopen the arm self-scored "extended" ("too
generous"). Verbatim highlights:

> **Verdict: Design B is better on quality / maintainability / ease-of-change.** Counts: A = 3 reopens
> (self-claimed 2), B = 2 reopens (honest)… **B pre-modeled the two variabilities that the car requirement
> actually stresses, so they landed as extensions.** (1) "What act completes a sale" was abstracted into
> `completion_signal` + `CompletionToken`, so buyer-optional inspection "rides the completion_signal path;
> no new lifecycle states." (2) "What shape is fulfillment" was abstracted into an abstract `Fulfillment`
> with `TrackedShipment <: Fulfillment`… so pickup/transport is just `Transport <: Fulfillment` at an
> existing seam. Design A hardwired both… and therefore had to *reopen* FulfillmentService… and rewrite
> OrderService's completion predicate. On the two heaviest parts of the car requirement, B extends where A
> reopens.

One point this judge scored **for OpenSpec (A)**, honestly:

> **Where A wins: title transfer.** A's `TitleTransferService` cleanly isolates legal transfer as its own
> authority, explicitly "distinct from money and physical handover; not provenance" — a sharp refusal to
> conflate three concepts… B instead *reopens Sale's handover step* to absorb legal-document movement,
> folding an unrelated legal concern into the Sale aggregate — weaker single-ownership on that axis.

Net: B wins, "with A conceding only the title-transfer modelling."

---

# Judge #3 — three-way, blind (aims vs OpenSpec vs plain)

After the **plain arm** (a capable agent with no method — see [`arms.md`](arms.md)) was added, a fresh
independent judge scored **all three** designs, anonymized and **shuffled** so the labels do not group by
method. Sealed mapping (kept from the judge): **X = OpenSpec, Y = plain, Z = aims.** It was told to focus
on change-locality / maintainability / quality, to re-derive its own counts, and specifically to test
whether any "extended" on the attribute model was really a reopen.

## Ranking: Z > X > Y  →  **aims > OpenSpec > plain.** No genuine ties.

Re-derived counts (self-scores it overrode in **bold**):

| Design (= arm) | self-count | judge #3 count | override |
|---|---|---|---|
| Z = **aims** | 2 | **2** | none — "honest, and its two reopens are the two genuinely unforeseeable ones" |
| X = **OpenSpec** | 2 | **2** (borderline 3) | OrderService flagged a borderline reopen; self-count "roughly honest" |
| Y = **plain** | 3 (self-dedup ≈2) | **3** | Listing "extended" → **reopened**; the dedup-to-2 "masks the attribute reopen"; "least honest self-report" |

Verbatim on the two decisive points:

> **1. Z.** Same reopen count as X, but Z's reopens are *cushioned* and its extends are *real*. The
> decisive contrast is logistics and inspection: where X and Y both **reopen fulfillment**, Z absorbs it
> as "Transport <: Fulfillment beside TrackedShipment at existing Fulfillment plugin seam; Fulfillment
> stays abstract." Inspection lands in "Sale's existing complete() guard (rides completion_signal; no new
> lifecycle states)."

> **3. Y** [plain]. Genuinely the most reopens (**3**: Order, Fulfillment, attribute model) and the
> weakest honesty: it reports the disjoint-attribute change as "extended (car attributes added at attribute
> seam)" while simultaneously conceding it must introduce a brand-new cross-cutting category axis — a
> self-contradiction… the fix is explicit **saga surgery**… Keeping Payment survived is its one genuine
> locality win, which is why it isn't disastrous — but it is clearly third on both change-absorption and
> honesty.

**Why the plain arm matters.** It is the control that separates *"the method helps"* from *"a capable
agent does this anyway."* The plain agent, unguided, welded completion to physical handover (no reified
completion to cushion the title change), built no fulfillment polymorphism (so logistics forced a reopen),
and under-counted its own attribute-model reopen. aims' method produced a design that both **absorbed the
change with fewer reopens** and **scored itself more honestly** than the unguided agent — on this one
product. That is a data point *for* aims' central claim, and (unlike the frozen pilot's Q1 split) it is the
method, not the model alone, doing the work here.

**Cross-judge convergence.** Three independent blind judges — one on aims' own `design-principles.md`, one
on general quality with no rubric, one three-way with shuffled labels — all rank **aims first**, all put
its honest reopen count at **2**, and all re-classify the rival's completion/attribute "extend" as a
**reopen**. Convergence across a rubric change and a label shuffle is the strongest thing an n = 1 probe
can offer; it is still n = 1. See **Validity** in [`results.md`](results.md).
