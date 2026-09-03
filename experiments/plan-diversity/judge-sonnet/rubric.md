# Rubric — "Responsible Doctor" MVP architecture judging

Formulated from the frozen brief's 6 exit criteria, before reading any contestant design.
These 8 metrics are FROZEN for the remainder of this evaluation.

---

## M1. Citation-chokepoint enforcement (maps to exit criterion 1)

**Question:** Is there one named place every output must pass through that can *only* construct a
`(source × reported-state)` citation — structurally incapable of emitting free-text advice or an
inferred state?

- **0:** No such gate is named. Outputs (gaps/nudges/messages) can be produced by more than one code
  path, or the "citation" is just a convention/comment ("always cite the source") with no owning
  type/function that gates construction.
- **5:** A single named type/function/service (e.g. a `Citation` value object with the only
  constructor requiring `(SourceRef, ReportedStateRef)`, or a described "citation emitter" that is
  the sole producer of every ledger/nudge item) is named, and the design states or clearly implies
  no other path creates output items — including the doctor-user path.

## M2. `manager → subject(s)` as one unforked primitive (exit criterion 2)

**Question:** Is family-management and doctor-managing-patients literally the same relation/type,
with no branch, subtype, or parallel model for either case?

- **0:** Separate entities/tables/code paths for "family member" vs "patient", or the relation is
  only implicit (e.g. patients live directly under a "doctor" role with no reusable link entity).
- **5:** One named relation type (e.g. `ManagerSubjectLink`/`Guardianship`) used identically for both
  scenarios, with the design explicitly stating both cases instantiate the same abstraction and nothing
  role-specific is bolted onto the subject or manager entity to distinguish them.

## M3. Expected/reported separation with a generic join (exit criterion 3)

**Question:** Are "expected" (pathway rails) and "reported/done" (subject state) modeled as two
distinct aggregates, with gaps produced by one generic diff/join operation over the pathway library
— not enumerated per concrete example (e.g. not "if pathway == mammogram then check X")?

- **0:** Gap logic is example-specific — hardcoded per named pathway (screening schedule, well-baby
  schedule) with duplicated per-example comparison logic, or expected/reported live in one merged
  structure with no seam between them.
- **5:** A generic `Pathway`/`Rail` abstraction (ordered steps/rules, pathway-agnostic) is joined
  against a generic reported-state store by one named join/diff mechanism that works for any pathway
  in the library without per-pathway code.

## M4. Provenance and confidence tier structurally inseparable from output (exit criterion 4)

**Question:** Is `SourceRef` + `ConfidenceTier` a required, non-optional field of the core
expected/gap/nudge type itself (so an item without a citation cannot be constructed/represented) — or
is it separate metadata that could be dropped or looked up out-of-band?

- **0:** Confidence/provenance is not modeled as data at all, or is an optional/nullable field, or is
  computed/attached later (e.g. at render/API-serialization time) rather than part of the domain
  object's required shape.
- **5:** The design states a concrete field/type (e.g. `Citation{source: SourceRef, confidence:
  ConfidenceTier}`) that every expected-item/gap/nudge type carries as a required component, with
  confidence explicitly tiered *by source* as the brief demands.

## M5. Extensibility — new pathway or new source type is one owner's change (exit criterion 5)

**Question:** Does the design name a specific extension point (a registry, plugin interface, or
single-owned table/module) such that adding a new pathway, or a new source type, requires editing
in one place — not touching the ledger's join logic, the account model, and the output layer
separately?

- **0:** No extension mechanism is described, or the design's own examples imply new pathways would
  require new code in the diff logic and new branches in the output formatting (shotgun surgery
  across layers).
- **5:** A named registry/plugin abstraction is described for pathways (e.g. a `PathwayDefinition`
  registered once) and, separately or via the same mechanism, for source types (e.g. a `SourceAdapter`
  interface), with the design stating explicitly that the ledger/join/output code does not change when
  a new instance is added.

## M6. Scope discipline — no speculative build beyond Pillar 1 / stated sources (exit criterion 6)

**Question:** Does the design avoid building structures for the overview (המכלול), for
inference-based suspicion/diagnosis, or for source types/pillars not in the MVP list — versus padding
the architecture with speculative generality "for later"?

- **0:** The design includes concrete components for the overview, an inference/suspicion engine, or
  scaffolding for unstated future sources/pillars (e.g. a "risk scoring" or "diagnosis suggestion"
  module, or an overview dashboard data model) presented as part of the MVP build.
- **5:** The design is explicitly scoped to Pillar 1 + the two named source classes, states what is
  out of scope, and does not introduce components whose only purpose is a future pillar/feature.

## M7. Domain model carries real behavior (anemic-model check)

**Question:** Do the core types (e.g. `Pathway`, `Ledger`, `Citation`, `SubjectRecord`) enforce their
own invariants and expose behavior — or are they described purely as data bags/tables with all logic
living in separately-named "service"/"engine" functions that reach into their fields?

- **0:** Every noun in the design is presented only as a schema/table (columns listed) with all
  computation described as external "the service does X to the record" — no method or invariant is
  attributed to the type itself.
- **5:** At least the citation invariant and the gap computation are attributed as behavior *owned by*
  a named type (e.g. "a `Citation` cannot be constructed without a source" as a type-level rule, or
  "`Ledger.diff()`" as an owned operation), not merely as an external process description.

## M8. Day-zero vocabulary — named domain types, not primitive obsession (deliverable's explicit ask)

**Question:** Does the design state a small set of named day-zero types/terms for the public seams
(e.g. `SubjectId`, `SourceRef`, `ConfidenceTier` as an enum, `PathwayId`) rather than leaving core
concepts as bare strings/ints/free-form JSON at the boundary?

- **0:** No vocabulary section/list is given, or core concepts (confidence, source kind, subject
  identity) are described only as generic strings/JSON blobs with no defined value set or type.
- **5:** The design explicitly enumerates its day-zero vocabulary (named types/enums with the values
  or shape they take, e.g. confidence tiers as a closed enum, source kinds as a closed set) as
  requested by the brief's "state the day-zero vocabulary" instruction.

---

Each metric is applied identically to all four contestants. A score requires a pointer to a concrete
structural fact in the design text (a named type, section, or quoted mechanism) — never tone or
prose quality.
