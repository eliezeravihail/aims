# Blind design-judge report — feed-ranking (X vs Y)

*Blind, structural-only, scored against `design-principles.md` via the assessment form; correctness checked
against the hidden oracle. No method named. Sealed mapping (revealed after scoring): **X = OpenSpec,
Y = aims-single**. §16/§17 N/A for both.*

**Step-0 (identical):** R1 score = Σwᵢ·sᵢ; R2 descending; R3 stable-id tiebreak; R4 weights = config;
R5 signals ∈ [0,1]; stage 2 adds R6 eligibility filter, R7 diversity cap.

## D1 — First-round quality (stage-1 only)

**X-stage-1 — grade 8.5 · worst 7 · (0,0).** §4 primitive obsession = 7 [S2]: bare-float signals
(`Candidate { id, recency, affinity, popularity }`), scorer returns a bare `float`, weights bare — R5 has no
value-object home (only ingress validation). §13 = 9 [S1]: duplicate-id edge only *assumed* unique, not
rejected at the boundary.

**Y-stage-1 — grade 10 · worst 10 · (0,0).** Signals wrapped (`UnitInterval` — "one home for the range
check"; `SignalVector` "prevents a loose triple of floats"); `Score` gives the scorer→orderer seam a
published type; one owner per rule (R1→`FeedScorer`, R2+R3→`OrderingPolicy`, R4→`SignalWeights`/
`WeightsProvider`, R5→`UnitInterval`); the duplicate-id edge X missed is rejected at the boundary; the
subtractive pass (F3) kept each thin type tied to a present force (§12 = 10, no unpaid machinery).

**D1 winner: Y (aims), clear but bounded.** Both correct on every stage-1 check and both separate
scorer/orderer with an extension seam, so the advantage is quality-of-structure on the §4 axis the rubric
names as the dominant failure ("too little structure … primitive obsession"): Y gives domain concepts
value-object homes where X carries bare floats and only "assumed" id-uniqueness. **10 vs 8.5.**

## D2 — Change absorption (stage-1 → stage-2)

**Survival (normalized reading = reopened + discarded): X = 0, Y = 0 — TIE.** Both keep every rule owner
byte-intact (X "Scorer + Orderer — untouched"; Y "No stage-1 rule owner was forced open — scoring, ordering,
weighting, validation byte-for-byte intact") and both slot eligibility + diversity in as new pipeline stages.
Y self-labels one invariant reopen (INV5 "permutation of all" → INV5′ "permutation of eligible", forced
because eligibility must drop items); X does the *identical* completeness re-scoping but labels it
"clarified." Scored symmetrically, neither reopened a rule owner → both **extend**, the oracle's success
shape.

**Stage-2 forms:** X-stage-2 = 8.5 (worst 7 — §4 primitive obsession carried and extended: new author/topic
identifiers bare); Y-stage-2 = 9.9 (worst 9 — a minor diversity-guard wording imprecision; §4 = 10:
"`Author` … used by both R6 block-membership and R7 adjacency; one concept, two rules"; §12 = 10: cut
`BlockList`/`MuteList` wrapper types that "would own nothing beyond set membership").

**Oracle traps — both stayed correct:** trap 1 blocked-as-weight AVOIDED both (both drop, not down-rank);
trap 2 diversity-as-penalty AVOIDED both (both reorder only, never touch scores); trap 3 pipeline ownership
CORRECT both (three distinct owners, scoring intact); both handle the all-one-author unsatisfiable case by
preserving completeness over the cap.

**D2 winner: Y (aims), narrow — absorption itself a TIE.** Both absorbed at the existing seam, kept every
owner intact, passed all three traps, and did the one identical necessary completeness re-scoping. The tie
breaks on the absorbed result's structure (same §4 axis): Y gives the new identity concepts value-object
homes where X carries bare identifiers → higher stage-2 form (9.9 vs 8.5). *A judge weighting
reopen-parsimony/guard-precision over modeling richness could defensibly call D2 no-clear-advantage.*

## Residual tells

Documentation grammar (X = capability specs/Given-When-Then/"change bundle"; Y = objective + Step-0 R/X/C +
value-object tables + Python signatures + a numbered review round) was IGNORED; scored only what the designs
*describe*. Self-reported survival labels ("clarified" vs "reopened INV5") were not taken at face value — the
identical underlying structural move was scored symmetrically, erasing the apparent count difference. The
§4 gap was scored on the modeling choice (value objects vs bare primitives), which a terser design could
equally have made. Same rubric-bias limitation as the series notes; here the rubric-free survival reading is
a clean **tie**.
