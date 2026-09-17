---
title: "Fixed inventory (Step 0) — antique marketplace + classic cars"
date: 2026-09-17
---

# Fixed inventory — marketplace (furniture, then cars)

Step 0 lists for grading the marketplace designs with [`quality-metrics.md`](quality-metrics.md). Authored
from the product requirements, not from any design. This product has **no numeric acceptance cases**, so
**C is a set of end-to-end capability checks** rather than value assertions; M11 (correctness) is judged as
"can the stage-2 design actually carry each capability end-to-end without a gap or an unowned step".

## R — rules / invariants

- **R1** A listing is a **unique single item**; it sells **at most once** — reserved by exactly one buyer,
  no double-sale.
- **R2** Money is a single authority: charge = payout + platform fee; payout on completion; refund on abort.
- **R3** A review is allowed only after a **completed** purchase.
- **R4** Each listing carries an immutable provenance/authenticity record.
- **R5** Search/discovery is a read model; it never authorizes a sale (the sale re-checks availability).
- **R6** (furniture) a purchase completes on the buyer's physical handover/receipt.
- **R7** (cars) completing a car sale requires a **legal title/registration transfer**, not just physical
  handover.
- **R8** (cars) logistics differ: pickup/transport, not parcel shipping.
- **R9** (cars) an **optional pre-purchase inspection** may gate completion.
- **R10** (cars) car attributes — VIN, year, mileage, registration — are a **disjoint** attribute shape from
  furniture's (era/style/condition/materials/dimensions).
- **R11** money, fee and reviews behave exactly as before the car addition.

## X — change-axes

- **X1** add a product **category** with a disjoint attribute shape (furniture → cars).
- **X2** vary **fulfillment/logistics** (parcel → pickup/transport).
- **X3** add a **completion prerequisite** (legal title transfer; optional inspection).
- **X4** *(plausible unstated variant)* a third category (e.g. real estate) with its own transfer + inspection
  shape.

## C — end-to-end capability checks (no numeric values)

- **C1** List, search, reserve (single-winner), buy, pay, complete, review a **furniture** item.
- **C2** Do the same for a **car**, including: searching car facets; a **title/registration transfer** step
  with a clear owner; **pickup/transport** fulfillment; an **optional inspection** gate that on failure
  routes to release + refund.
- **C3** Adding cars leaves money/fee/reviews (R2/R3/R11) untouched.
- **C4** A car's disjoint attributes (R10) are carried without distorting the furniture attribute model.

> **Correctness probe (M11):** trace a car sale end-to-end. Does the design name an **owner** for the legal
> title transfer, the transport logistics, and the inspection gate — or does one of these steps have no home
> (an unowned completion prerequisite is a correctness gap, S3–S4 depending on whether the sale can complete
> at all)?
