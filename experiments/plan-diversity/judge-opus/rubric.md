# Judging rubric — "responsible doctor" MVP architecture (FROZEN)

Formulated before reading any contestant. Nine metrics, each tied to a load-bearing
structural requirement of THIS brief (its exit criteria) and/or a named design principle.
Every score must rest on a concrete structural fact in the design — a named type, a section,
a quoted mechanism, a specific ownership decision — never on tone or readability.

Each metric: the question it asks, and what 0 vs 5 looks like *for this product*.

---

## M1 — Citation chokepoint: is the non-advice boundary enforced by structure?
*(Exit 1; principle §9 "where is the rule enforced")*

**Question:** Is there exactly ONE place every output must pass through that can *only* emit a
`(authoritative source × reported state)` citation — such that no path can originate advice or
infer a medical state — and do all real output paths actually route through it?

- **0:** Non-advice is a convention/prose promise; output can be produced in multiple places;
  nothing structurally prevents a code path from emitting a recommendation or inferring state.
- **5:** A single named constructor/gate/type is the only way to make an output; its input type
  *forces* a source reference and a reported-state reference; there is no alternate emit path, and
  "infer state" / "originate advice" are structurally unrepresentable (no such input exists).

## M2 — `manager → subject(s)` as a single primitive
*(Exit 2)*

**Question:** Is `manager → subject(s)` one abstraction covering self-care, a family manager, and
a doctor's panel with the SAME shape — multi-subject being cardinality, not a special case — with
no separate "doctor mode" vs "patient mode" types?

- **0:** Separate models for individual vs family vs doctor; multi-subject handled by branching or
  a distinct entity; self-management is a special case.
- **5:** One relation/entity (e.g. `Manager`, `Subject`, and a `manages` link) where family and
  doctor differ only by how many `Subject`s hang off a `Manager` and by role/permission data on
  the *link*, not by type; self = a manager with one subject (possibly itself), no special path.

## M3 — Expected vs Reported are distinct, and gaps are JOIN-computed
*(Exit 3)*

**Question:** Are the "expected" side (pathway rails) and the "reported/done" side (subject state)
modeled as distinct things, and is a gap *derived by a join/diff function* over them — rather than
gaps being enumerated per pathway example?

- **0:** Gaps are hand-authored per condition; expected and done are entangled in one blob; no
  general join — each pathway ships its own bespoke gap list.
- **5:** Two clearly separate models (a pathway/expected-item model and a reported-state model) and
  a single named reconciliation/diff operation `join(expected, reported) -> ledger` that produces
  gaps generically for any pathway.

## M4 — Provenance & confidence tier are inseparable from every item
*(Exit 4; principle §4 primitive obsession)*

**Question:** Does every expected item / gap / nudge structurally carry its source provenance AND a
confidence tier-by-source, as a required part of its type — so a citation cannot exist without its
source?

- **0:** Source/confidence are optional fields, a loose string, or attached later/out of band; an
  item can be constructed with no source.
- **5:** A dedicated value type (e.g. `Citation{source, confidenceTier, reportedState}` or a
  `Provenance` type) is a non-nullable component of every emitted item; confidence tier is an
  enumerated concept keyed to source class, not a free-form number.

## M5 — Adding a pathway or a source type is one owner's change
*(Exit 5; principles §6 shotgun surgery, §8 SRP)*

**Question:** To add a NEW medical pathway or a NEW source type, is the change localized to one
owner (one registry/module/table), or does it scatter across the ledger logic, the account model,
and the output layer?

- **0:** A new pathway or source requires edits in several layers (join logic + citation layer +
  account model + UI mapping); responsibility is smeared.
- **5:** A pathway is a data entry in a library/registry with one owner; a source type is registered
  in one adapter/ingestion seam; the join, citation gate, and account model are untouched by either
  addition. Explicitly stated ownership.

## M6 — Pathway library as generic rails, not hardcoded examples
*(Principle §2 program-to-an-interface; Exit 3 "not enumerated per example")*

**Question:** Is the pathway/expected side a genuine generic abstraction — data-driven rails that a
second, genuinely different pathway (screening schedule AND well-baby schedule AND a med-refill
cadence) would populate identically — or is it a rename of one worked example?

- **0:** The model is shaped around one example (e.g. fields that only make sense for a screening
  schedule); a well-baby or refill pathway would not fit without new structure.
- **5:** A pathway is expressed in condition-neutral primitives (e.g. triggers/eligibility, expected
  steps with timing, cadence) such that at least two structurally different example pathways slot in
  with only data, no schema change; the abstraction is demonstrably not one example in disguise.

## M7 — Scope discipline: no speculative machinery
*(Exit 6)*

**Question:** Does the design stay within Pillar 1 + the stated MVP sources — with NO structure built
for the integrated overview (המכלול), inference-based suspicions, or unstated future sources?

- **0:** Substantial architecture spent on the overview, ML/inference of state, or speculative
  source connectors not in scope; MVP boundary blurred.
- **5:** Explicitly scoped to Pillar 1; overview/inference/future sources named as out-of-scope or
  simply absent; every component traces to a stated MVP requirement.

## M8 — Day-zero public-seam vocabulary is stated and clean
*(Deliverable requirement "state the day-zero vocabulary"; principle §7 leaky abstractions)*

**Question:** Does the design explicitly name the vocabulary its public seams may speak, and are
those types domain types (Citation, Pathway, Subject, Ledger, Gap…) rather than implementation types
(a DB row, a vendor FHIR object, a raw dict) leaking through?

- **0:** No stated seam vocabulary; boundaries pass raw dicts/DB rows/implementation types; the
  reader cannot tell what a public interface speaks.
- **5:** An explicit day-zero vocabulary section lists the domain types crossing each seam; no
  implementation/storage/vendor type appears in a public signature; primitive obsession avoided
  (real domain types, not bare strings).

## M9 — Domain model carries behavior / enforces its own rules
*(Principles §5 anemic domain model, §1 tell-don't-ask)*

**Question:** Do the core concepts (the citation gate, the ledger, a pathway, the subject state)
own the behavior that enforces their invariants — or are they data bags with all logic in external
"service"/"manager" procedures that reach in and decide everything?

- **0:** All types are DTOs/tables; a big service layer pulls fields out and makes every decision;
  invariants (like "must cite a source") live outside the types they constrain.
- **5:** The invariant-bearing types enforce their own rules (the citation type cannot be built
  invalid; the ledger computes its own gaps; the pathway answers "what is expected" itself);
  callers tell objects what to do rather than asking for fields and deciding externally.

---

*These nine are frozen. M1–M5 map one-to-one to Exit criteria 1–5; M6 sharpens Exit 3's "not
enumerated per example"; M7 is Exit 6; M8 is the deliverable's day-zero-vocabulary requirement.
M1, M3, M4, M5 are the load-bearing axes for THIS brief — a design that loses one of these has
failed a non-negotiable, regardless of total.*
