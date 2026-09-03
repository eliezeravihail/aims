# Frozen rubric — "responsible doctor" MVP architecture (blind judge)

Formulated from the brief BEFORE reading any contestant. Frozen from this point; the same eight
metrics are applied identically to design-1..4. Every score must rest on a concrete structural fact
(a named type, a boundary, a quoted mechanism, a specific decision) — never on tone or wording.

Grounding: the brief's six exit criteria plus the design-principles reference (rule enforcement
location §9, interface generality §2, primitive obsession §4, anemic model §5, shotgun surgery §6,
seam vocabulary §7, SRP §8). The metric set is chosen for THIS product, not copied.

---

## M1 — Citation invariant: one structural chokepoint

**Question.** Is there exactly one place every user-facing output must pass through, and is that place
*structurally* incapable of emitting anything other than a `(authoritative source × reported state)`
join — for every user, including a doctor user — with no alternate path that can originate advice or
infer state?

- **0** — The boundary is a stated policy ("the system never advises"), a prompt, a code-review rule,
  or a UI-layer filter; outputs are free-form text/objects that could carry advice; or a doctor role
  has an authoring path that bypasses it.
- **3** — A named output type carries a source reference and a state reference, but it is optional or
  nullable, or some output routes (notifications, API, doctor view, nudges) are not shown to pass
  through the same gate.
- **5** — A single named type (e.g. a citation/ledger-item type) whose construction *requires* both a
  source reference and a reported-state reference; the only producer of that type is one named module;
  every output surface (ledger, gap flag, nudge, notification, API) is shown to be a projection of that
  type; there is no free-text "recommendation"/"advice" field anywhere in the model; and the doctor
  user's input enters as a *source* (an instruction to be cited), not as an output authoring path.

## M2 — `manager → subject(s)` as a single primitive

**Question.** Is "a manager operates one-or-many subjects" one abstraction that covers self-management,
a family, and a doctor's patients identically, with authorization derived from that one relation?

- **0** — Separate models or code paths for "family" vs "doctor's patients"; or the subject *is* the
  account (single-user), with multi-subject bolted on; or the doctor is a distinct role with its own
  patient list model.
- **3** — One relation exists, but self-management is a special case (a user is not simply a subject
  managed by themselves), or the doctor/family distinction leaks into the relation as a mode switch
  that changes behavior.
- **5** — One explicit relation type (manager, subject, grant/role) is the *only* way any actor reaches
  any subject's file; self-management is the same relation with manager == subject; a doctor and a
  parent are the same manager type; every read/write of a file is scoped by this relation; and it is
  clearly distinct from the "doctor as source" concept (M1).

## M3 — Expected vs reported: distinct sides, gap computed by a generic join

**Question.** Are pathway rails (expected) and subject state (reported/done) modelled as distinct
things, and is the ledger produced by one general join over them — with the join's *matching
semantics* stated (how a rail step matches a reported item), and "open process with no plan" being a
*join outcome* rather than a special-cased rule?

- **0** — Expected and reported live in one table/type; gaps are enumerated per example (e.g. a
  hardcoded well-baby checklist); or no matching rule is stated, so the join cannot actually run.
- **3** — Distinct sides and a join engine exist, but the join key / matching vocabulary is
  unspecified or hand-waved ("match by name"), or "no plan" is a separate hardcoded branch rather than
  a case the join yields.
- **5** — A pathway library of declarative rails (applicability predicate + expected steps), a separate
  reported-state store, and one join/reconciliation component whose input types are exactly those two
  sides; a stated matching key (a shared code/vocabulary, or an explicit mapping owned by the source
  adapter); ledger states (expected/done/gap/no-plan) are the join's enumerated outcomes; nothing in
  the join is specific to any single pathway.

## M4 — Provenance and confidence tier are inseparable from every item

**Question.** Does every expected/gap/nudge item carry its source reference and a confidence tier as
*required* structure, with the tier determined by the source's own definition (not looked up by the
ledger or the UI)?

- **0** — Tier/source is absent, optional, a display-layer decoration, or computed by the presentation
  layer from a separate table.
- **3** — Items carry source + tier fields, but the tier is assigned by the ledger/join code via a
  switch on source kind (so adding a source type touches the ledger), or the nudge item is a different
  shape that lacks them.
- **5** — A single source-reference type with a mandatory tier; the tier is a property of the source
  (each source kind declares its own tier — the mapping lives with the source, not the ledger); the
  item type cannot be constructed without a source reference; nudge items are the same shape and carry
  the (absent-plan) provenance too; the tier's enumeration is closed and named.

## M5 — Change locality: a new pathway and a new source type are each one owner's change

**Question.** Walk the two brief-mandated changes: (a) add a new pathway; (b) add a new source type.
Does each land in exactly one owner, leaving the ledger/join, the account model, and the output layer
untouched?

- **0** — Either change requires edits in the join, the account model, and the output/presentation
  layer (shotgun surgery); pathways are code branches inside the ledger.
- **3** — Pathways are data/plugins, but a new source type requires touching the join (matching logic)
  or the ledger (tier switch) as well as an adapter; or the design asserts locality without showing
  the path.
- **5** — A pathway is a declarative entry in the pathway library speaking the shared vocabulary; a
  source type is one adapter behind a stated source interface emitting the common reported-item /
  source-reference type (with its own tier); the design explicitly walks both changes and shows the
  untouched components.

## M6 — Seam vocabulary and domain types (day-zero published language)

**Question.** Does the design state the vocabulary the public seams may speak — its own named domain
types with identity (ids, tiers, statuses, codes) rather than bare strings/dicts, no vendor/impl types
crossing a seam, and a closed foundational set?

- **0** — No vocabulary stated; seams pass dicts/JSON blobs/free strings; or a chosen implementation
  (a specific DB row, a vendor object, a framework model) is the seam type.
- **3** — Domain types are named but key concepts remain primitives (a subject as a string id, a tier
  as a free string, a source as a URL), or the vocabulary is listed but not tied to specific seams.
- **5** — A named, closed day-zero vocabulary: typed ids, a closed tier enum, a closed ledger-status
  enum, a source-reference type, a reported-item type, a pathway/rail type; each public seam's in/out
  types are named from that set; foundational dependencies (if any) are declared as a small closed set;
  error vocabulary only where a handling exists.

## M7 — Scope discipline against the frozen brief

**Question.** Is the design confined to Pillar 1 + the two mandated source classes, with extension
points only where the brief demands them (new pathway, new source type)? Anything for the overview,
inference/suspicion, or unstated future sources counts against.

- **0** — Designs the integrated overview, an inference/suspicion engine, ML, EHR/FHIR/HL7
  integrations, multi-tenant billing, or a generic plugin platform beyond the two mandated seams.
- **3** — Core is scoped, but reserves fields/tables/modules "for later" (overview hooks, inference
  slots, unnamed future source connectors) or over-generalizes the source interface for sources not in
  the brief.
- **5** — Exactly the MVP: one guideline class, reported items (results, instructions, prescriptions),
  pathway library, join, ledger, nudge, the one account relation; the two extension seams exist and no
  others; any noted future work is explicitly excluded from the structure, not pre-built into it.

## M8 — Responsibility placement and domain-model behavior

**Question.** Do the core concepts (pathway/rail, reported item, source, citation/ledger item, the
manager→subject relation) own their own rules with one stated reason to change each — or is the logic
concentrated in a single "care service"/"engine" god object operating on anemic data bags?

- **0** — One service/engine holds applicability, matching, tiering, authorization, and rendering;
  domain types are field bags; module boundaries are by technical layer only (controllers/models/utils).
- **3** — Modules are split by concept, but key rules are misplaced (e.g. the ledger decides a
  pathway's applicability; the output layer decides what counts as a gap; the source adapter knows the
  ledger's schema).
- **5** — Each concept owns its rule: the pathway decides its own applicability and expected steps; the
  source declares its own tier and emits its own reported items; the join owns only the reconciliation;
  the citation type validates its own completeness; the relation owns access; each module's one reason
  to change can be stated in one sentence and is stated (or is evident from the boundaries).

---

Scoring rule reminder: an invalid justification (tone/wording/"reads cleanly") voids the score. A
score without a concrete structural reason must not be given. Totals are secondary; the per-metric
picture is primary, and M1 / M3 / M5 are load-bearing (they map directly to exit criteria 1, 3, 5).
