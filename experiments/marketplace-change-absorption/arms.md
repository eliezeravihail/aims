---
title: "arms — the two designs as delivered (furniture stage 1, + cars stage 2)"
date: 2026-09-17
---

# Arms — designs as delivered

Verbatim artifacts for [`results.md`](results.md). Both arms were run by subagents reading this repo's
method files (aims) / the spec-first shape (OpenSpec) — not role-played. The stage-2 prompt was identical
in structure for both arms: extend the stage-1 design MINIMALLY for cars, classify each component as
survived / extended / reopened / discarded, and give the reopened+discarded count.

---

## aims arm

### Stage 1 — antique-furniture marketplace (panel design)

Components:
- **Catalog** (Listing aggregate): item attributes, **concrete provenance/authenticity fields**,
  typed-facet search (`SearchQuery(facets)->Page<ListingSummary>`), MediaStore inside. Lifecycle
  behavior-only (`activate/reserve(saleId)/markSold/withdraw`, no setters/status field). Sole
  availability authority; "sold once" enforced by the single `reserve` method + a DB uniqueness
  constraint. Item attributes furniture-shaped: EraStyle, Condition, Dimensions, materials.
- **Sale** (aggregate): sole purchase-lifecycle owner (opened→charged→paid_out→handed_over→completed,
  +cancelled/refunded), guarded methods; owns the **handover step**; mints a `CompletionToken` on
  complete. Consumes a `Fulfillment{status, completion_signal}` value (with `TrackedShipment <:
  Fulfillment` only for genuine trackers).
- **Ledger**: sole money mover; double-entry charge/hold/payout-minus-fee/refund.
  `FeePolicy.quote(ctx)->FeeQuote` seam (owned by Ledger, segregated from the gateway). `PaymentGateway`
  port (domain types only).
- **Reputation**: reviews, gated by `CompletionToken`.

Value objects crossing seams: `Money`, `Fee/FeeQuote`, typed ids, `EraStyle/Condition/Dimensions/
Provenance` (concrete), `Facet`/`ListingSummary`, `CompletionToken`, `Fulfillment{status,
completion_signal}`.

Invariant owners: money+fee→Ledger; purchase lifecycle→Sale; availability/"sold once"→Catalog.reserve;
review-after-completion→CompletionToken.

Deliberate stage-1 bets: provenance/authenticity kept **concrete** ("not a plugin axis, no describable
2nd implementation today"); item category is **not** a plugin axis; the change axes designed for were
fee, payment provider, fulfillment-tracking only.

### Stage 2 — add cars (self-report)

Extension (minimal):
- **Logistics** → add `Transport <: Fulfillment` (pickup/transport) beside `TrackedShipment` at the
  existing Fulfillment plugin seam. Fulfillment stays abstract.
- **Fee** → register a car `FeePolicy` at `FeePolicy.quote(ctx)`; ctx already carries what's needed.
- **Inspection** → a buyer-optional pre-completion outcome fed into Sale's existing `complete()` guard as
  a completion precondition (rides the completion_signal path; no new lifecycle states).
- **Car attributes** → the hard part. Catalog's Listing carries only concrete furniture fields, and
  stage-1 explicitly bet "item category is NOT a plugin axis." Cars (VIN, year, mileage, registration)
  are a disjoint attribute shape, so a category axis the design declined must be introduced.
- **Title/registration transfer** → stage-1 handover = physical possession = deal done. A car completes
  on a *legal* title transfer with a real document to move and record — a responsibility no current owner
  holds. The handover step's semantics must change.

| Component / seam | Verdict | Why |
|---|---|---|
| Catalog — availability authority / lifecycle | survived | Item-agnostic; a car reserves/sells-once identically |
| Catalog — MediaStore | survived | Unchanged |
| Catalog — typed-facet search | extended | New car facets (year, mileage, VIN) at the existing facet seam |
| Catalog — Listing attribute model / "category not a plugin axis" bet | **reopened** | Disjoint attribute shape forces the category axis the design declined |
| Catalog — Provenance/authenticity (concrete) | survived | VIN rides in as a plain attribute; title lives with the sale |
| Sale — purchase lifecycle | extended | Inspection folds into `complete()`; no new states (borderline) |
| Sale — handover step | **reopened** | Physical-possession-completes must become legal title transfer; new legal-artifact ownership |
| Sale — Fulfillment / `TrackedShipment` | extended | Add `Transport` subtype at the designed plugin axis; `TrackedShipment` untouched |
| Sale — CompletionToken minting | survived | Same semantics |
| Ledger — double-entry money mover | survived | Larger amounts, identical mechanics |
| Ledger — `FeePolicy.quote(ctx)` seam | extended | Car fee plugged into the existing fee seam |
| Ledger — PaymentGateway port | survived | Unchanged |
| Reputation — reviews gated by CompletionToken | survived | Unchanged |
| VOs (Money/ids/Fee/FeeQuote/CompletionToken) | survived | Unchanged |
| VOs (Facet/ListingSummary) | extended | New car facets/summary fields |

**Reopened + discarded = 2** (Catalog attribute model / category bet; Sale handover step. Discarded:
none.)

Honest caveats (self-reported): (a) if stage-1's handover already delegated "what act completes the sale"
to `completion_signal`, title transfer could ride that seam and handover would merely *extend* — but the
legal-document ownership is genuinely unowned, so scored reopened; (b) inspection is a borderline extend
that becomes a reopen if the lifecycle can't gate completion without a new state.

Most-falsified assumption: **Catalog** — its explicit bet that "item category is not a plugin axis /
provenance is concrete with no describable second implementation" is directly contradicted by cars being
a wholesale second item shape the aggregate was designed not to admit.

---

## OpenSpec arm

### Stage 1 — antique-furniture marketplace (spec-first)

Capabilities: Listing Management (Draft→Active→Reserved→Sold→Completed|Withdrawn); Discovery
(browse/search by era/style/price/material — read model); Purchasing/Checkout (order lifecycle,
single-winner reservation); Payments & Payouts (fee %, charge=payout+fee, payout on completion);
Fulfillment (Shipped/handover→receipt→Completion); Reputation (review gated on completed order);
Provenance/Authenticity (immutable provenance record on a listing).

Components: **ListingService** (CRUD + listing state machine; attributes furniture-shaped:
era/style/material/dimensions/condition), **CatalogQuery** (read model), **OrderService** (order
aggregate + purchase lifecycle), **LedgerService** (charge/fee/payout/refund, double-entry, sole money
authority), **FulfillmentService** (shipment/handover/receipt tracking), **ReputationService** (reviews
gated on completion), **ProvenanceService** (authenticity records), **PaymentGatewayAdapter** (PSP behind
a port).

Seams: ListingService⇄OrderService `reserve/release/markSold`; OrderService→LedgerService
`charge(order,amount)`/`settle(order)`; LedgerService→PaymentGatewayAdapter
`authorize/capture/refund/transfer`; FulfillmentService→OrderService `ReceiptConfirmed`→`OrderCompleted`
consumed by Ledger (payout) + Reputation (unlock review); Listing events→CatalogQuery.

Invariant owners: money→LedgerService; purchase lifecycle→OrderService; listing lifecycle→ListingService;
review-eligibility→ReputationService (keyed off OrderCompleted).

### Stage 2 — add cars (self-report)

Extension:
- **Changed — Listing Management:** gains a product-category axis (Furniture | Car). Car attributes are
  not a variant of the furniture schema (VIN/year/mileage/registration, VIN as identity); requires a
  category-specific attribute schema the stage-1 "furniture-shaped" model did not have. Listing lifecycle
  unchanged.
- **Changed — Discovery:** new car facets (make/model/year/mileage) projected additively.
- **Changed — Fulfillment:** logistics becomes method-typed (parcel vs pickup/transport); physical
  receipt is no longer the completion signal for cars.
- **Changed — Completion condition:** `OrderCompleted` becomes a conjunction of (physical handover) AND
  (title transferred) AND (inspection passed OR waived).
- **NEW — Title / Ownership Transfer:** legal transfer of the title/registration as a completion
  prerequisite. New **TitleTransferService** (distinct from money and physical handover; not provenance).
- **NEW — Inspection:** optional buyer inspection gate; on fail → existing `release` + refund. New
  **InspectionService**.

| Component / Capability | Verdict | Why |
|---|---|---|
| ListingService | **reopened** | "furniture-shaped" attributes had no category/product-type seam; second category with different identity attributes forces a structural attribute-model change. Lifecycle survives. |
| CatalogQuery | extended | read model adds car projections/facets additively at the Listing-events seam. |
| OrderService | extended | already owned "precondition event → OrderCompleted"; the guard grows to a conjunction. |
| LedgerService | **survived** | money/fee/charge/payout/refund unchanged. |
| FulfillmentService | **reopened** | parcel-shaped "Shipped/handover" logistics and its completion-equals-receipt assumption both break for cars. |
| ReputationService | **survived** | keyed off OrderCompleted; indifferent to what completion now means. |
| ProvenanceService | **survived** | immutable listing-attached record is category-agnostic. |
| PaymentGatewayAdapter | **survived** | authorize/capture/refund/transfer unchanged. |
| TitleTransferService | *new* | — |
| InspectionService | *new* | — |

**Reopened + discarded = 2** (ListingService, FulfillmentService). Zero discarded.

Most-falsified assumption: **FulfillmentService**'s belief that completion = confirmed physical receipt
of a shipped parcel — cars need legal title transfer plus transport logistics, so receipt is neither
sufficient nor correctly shaped.
