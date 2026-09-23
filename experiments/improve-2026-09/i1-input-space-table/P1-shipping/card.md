# Product card — parcel shipping-rate engine (design only)

Design the architecture (types + interfaces + the correctness handling) for a **parcel shipping-rate
engine**. Design only — no implementation. A parcel is priced from its weight and destination zone.

## Rules (R)
- **R1** `price = bracket_base(billable_weight_kg) × zone_multiplier(zone)`, rounded to cents (half-up).
- **R2** `billable_weight_kg = max(actual_weight_kg, dimensional_weight_kg)`, where
  `dimensional_weight_kg = (L_cm × W_cm × H_cm) / 5000`.
- **R3** Weight **brackets** are consecutive tiers with a base price each; a parcel is priced by the tier
  its billable weight falls in. The published starter tiers are `0–1kg → $5`, `1–2kg → $8`, `2–5kg → $12`,
  `5kg+ → $20`.
- **R4** An unknown or unsupported zone is **reported as an error**, never silently priced.

## Change-axes (X) — the ways this is expected to vary
- **X1** The warehouse scale sometimes reports an imprecise reading as a **range** (e.g. "1.9–2.1 kg")
  rather than a single number; when it does, billing must use the **worst case** (the range's maximum).
- **X2** New bracket tiers may be inserted or the tier prices re-tabled (promotions).
- **X3** A per-zone fixed **surcharge** may be added on top of the bracketed price.

## Acceptance (C) — visible examples
- **C1** 0.4 kg to zone A (multiplier 1.0) → bracket `0–1kg` = $5.00.
- **C2** 3.0 kg to zone B (multiplier 1.5) → bracket `2–5kg` $12 × 1.5 = $18.00.

Produce the design: the domain types (what a weight, a bracket, a parcel, a price are), the operations and
their contracts, and how R1–R4 crossed with X1–X3 are handled across the full input space. Then run the
method's mandatory self-review and deliver the final design.
