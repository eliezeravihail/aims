# Responsible Doctor — MVP Architecture (minimal-structure design)

**Shape in one sentence.** A single modular-monolith service over one relational
database, with **four modules and one kernel type**; every byte that leaves the
system is constructed by one function that can *only* bind an authoritative
**Source** to a **Reported** fact — so the non-advice boundary is a compiler-checked
chokepoint, not a review-time convention.

Design bias applied throughout: **minimize moving parts.** No message bus, no
per-example services, no rules engine, no separate "advice" pathway to police —
the invariant is enforced by *making the illegal state unrepresentable*, which is
cheaper than guarding it.

Assumptions (stated inline where they bite): single service + one SQL store is
sufficient at MVP volume; auth is delegated to an external IdP and out of scope
below the `Manager` identity; "medical state" facts arrive already-structured via
ingestion adapters (adapter internals are out of scope — see §7).

---

## 1. Data model

Seven tables. Everything the product does is a query over these.

| Entity | Purpose | Key fields |
|---|---|---|
| **Manager** | An operating identity (a person, a clinician). | `id`, `idp_subject`, `display_name` |
| **Subject** | A person whose file is tracked. | `id`, `display_name`, `birthdate`, `sex` |
| **Membership** | The one account primitive — links a manager to a subject. | `manager_id`, `subject_id`, `role` |
| **Source** | A provenance record. **Confidence tier lives here, nowhere else.** | `id`, `source_type`, `confidence_tier`, `label`, `reference`, `issued_at` |
| **Pathway** | A declarative rail (the *expected* side). | `id`, `name`, `version`, `applies_when` (predicate JSON) |
| **PathwayStep** | One expected item on a rail, citing its guideline. | `id`, `pathway_id`, `item_code`, `timing`, `plan_required`, `source_id` |
| **ReportedItem** | One dated fact about a subject (the *reported/done* side). | `id`, `subject_id`, `item_code`, `value`, `observed_at`, `source_id` |

Notes that carry weight:

- **`Source` is referenced by both sides.** A `PathwayStep` points at the guideline
  `Source` it derives from; a `ReportedItem` points at the `Source` that reported it
  (a lab, a doctor, the subject). This single reference is what makes "provenance is
  inseparable from the item" a **foreign-key fact**, not a discipline.
- **The system stores no free-text medical claims.** `item_code` is a controlled code
  (see §6); `value` is a measured/reported datum. There is no column anywhere that a
  developer could fill with an originated recommendation.
- **The ledger is computed, not stored** (optionally materialized as a cache). It has
  no table of its own, so there is no place for advice to accrete.

---

## 2. Module / boundary structure

One deployable. Four modules + one kernel. Dependencies point inward toward the kernel;
nothing depends on the API layer.

```
                 ┌─────────────────────────────┐
   HTTP / API →  │  Citation Seam (emitter)     │  ← the ONLY exit
                 └──────────────┬──────────────┘
                                │ returns Citation[]
        ┌───────────────────────┴───────────────────────┐
        │                  Ledger (join)                 │
        │  resolves pathways · matches reported · gaps   │
        └───────┬──────────────────────────────┬────────┘
       reads    │                              │   reads
   ┌────────────┴─────────┐         ┌──────────┴───────────┐
   │ Catalog              │         │ Accounts             │
   │ Source + Pathway lib │         │ Manager/Subject/Mem  │
   │ (the EXPECTED side + │         │ (the primitive +     │
   │  confidence tiers)   │         │  authorization)      │
   └──────────────────────┘         └──────────────────────┘
                     ▲
              Kernel: `Citation` type (invariant owner)
```

- **Accounts** — owns `Manager`, `Subject`, `Membership`, and *all* authorization.
  Every ledger request is scoped by a membership check here first.
- **Catalog** — owns `Source` (and therefore the confidence-tier vocabulary) and the
  `Pathway`/`PathwayStep` library. This is the "expected" side and the provenance
  authority. **New pathway or new source type = a change confined to this module** (§5).
- **Ledger** — owns `ReportedItem` (the "reported/done" side) and the **join engine**.
  It computes ledger entries by matching expected against reported. It produces
  *candidate* citations but cannot serialize them.
- **Citation Seam** — the API/output layer. It can serialize `Citation` values and
  nothing else. It has no ability to author text.
- **Kernel** — the `Citation` type (§3). Depended on by everyone; depends on no one.

Why so few parts: the brief has exactly two data provenances (guideline, reported) and
one output shape (citation). Any additional module would be an abstraction no present
force demands.

---

## 3. Ownership & structural enforcement of the citation invariant

**The invariant:** every system output is a `Citation = (authoritative Source × Reported
state)`; the system never infers state and never originates advice.

**Owner:** the kernel `Citation` type, with a **private constructor** and a single factory:

```
Citation.of(source: Source, reported: ReportedFact) -> Citation
```

There is **no other constructor and no setter.** A `Citation` is structurally a pair of
references — a `source_id` and a `reported_fact` — plus a rendered surface derived *only*
from those two. It carries no field that a caller can fill with originated prose.

How each guarantee falls out of the type, not out of vigilance:

- **Never originates advice.** The Citation Seam's return type is `Citation[]`. The only
  way to obtain a `Citation` is `Citation.of(...)`, which *requires* a real `Source`. There
  is no code path from "the system had a thought" to "the user saw text": text can only be
  the projection of an existing Source bound to an existing fact. Advice is *unrepresentable*.
- **Never infers state.** `ReportedFact` can only be built from a stored `ReportedItem`
  (or the *absence* of one — see the nudge). The ledger's status logic is pure temporal/logical
  arithmetic over stored items (done / due / overdue), which is a fact *about* reported data,
  not a new medical fact. No module can synthesize a `ReportedItem`; they arrive only through
  ingestion adapters writing to the store.
- **The nudge is also a citation, not an exception.** A "no plan for an open process" gap is
  emitted as `Citation.of(guidelineSource, ReportedFact.absence(item_code, subject))`. It says,
  in effect: *"Guideline X expects a plan here; you have reported none — ask your doctor."* The
  source is the guideline that expects a plan; the reported state is the observed **absence** of
  one. The system never says *what* the plan should be, so even the nudge originates nothing.

**One-line audit rule this buys us:** grep for the return types of public handlers — if it is
`Citation`/`Citation[]`, the boundary holds by construction. There is no second place to check.

---

## 4. The `manager → subject(s)` primitive

One table, `Membership(manager_id, subject_id, role)`, is the *entire* primitive. There is no
"individual user" type and no "clinic" type — those are just cardinalities of the same edge:

- A person tracking **only themselves** → one membership (`role = self`).
- A person managing **their family** → several memberships from one manager.
- A **doctor** managing patients → many memberships from one manager (`role = clinician`).

Every read/write path takes `(manager_id, subject_id)` and authorizes by *existence of a
membership row*. Multi-subject is never a branch in the code; it is `WHERE manager_id = ?`
returning N rows instead of 1. The doctor case reuses the same query as the family case — the
only difference is `role`, which affects the confidence tier a doctor's *own* reported items get
(§6), not the account shape.

Crucially, **a doctor user is still bound by §3**: their outputs are Citations too. A doctor can
*author a ReportedItem* (a doctor instruction, tier B) — which then becomes citable Source-backed
state — but the system still never originates advice on the doctor's behalf.

---

## 5. Joining "expected" and "reported/done" into the ledger

The two sides are **distinct by construction** — different tables, different modules — and gaps
are **computed by a join**, never enumerated per example.

**The join, in four declarative steps (one function in the Ledger module):**

1. **Resolve rails.** Select every `Pathway` whose `applies_when` predicate evaluates true against
   the subject's facts (age from `birthdate`, plus any reported risk facts). This is data-driven
   predicate evaluation over the library — *not* a hardcoded pathway. Adding the well-baby schedule
   or a screening schedule is adding rows, not code.
2. **Expand expectations.** For each resolved pathway, expand `PathwaySteps` into expected
   *occurrences* using each step's `timing` rule and the subject's age → a set of
   `(item_code, due_window, source_id, plan_required)`.
3. **Match against reported.** Left-join each expected occurrence to `ReportedItem`s for that
   subject with the same `item_code` inside the window.
4. **Classify.** Produce a `LedgerEntry` per expected occurrence:

   | Condition | Status |
   |---|---|
   | matching reported item found | `done` |
   | window open, none yet | `due` |
   | window passed, none found | `overdue` |
   | `plan_required` step, process open, no plan reported | `open_no_plan` → **nudge** |

**Provenance & confidence travel automatically (exit 4).** Each `LedgerEntry` already holds two
`source_id`s: the **expected** side's guideline `Source` (from `PathwayStep.source_id`) and, if
matched, the **reported** side's `Source` (from `ReportedItem.source_id`). The confidence tier is
read from whichever `Source` backs the flag — the guideline for an expected/nudge item, the
reporter for a done item. Because the tier lives only on `Source`, it *cannot* be dropped in
transit: there is no ledger field to forget to populate.

The Ledger hands these entries to the Citation Seam, which calls `Citation.of(source, reportedFact)`
per entry. Gaps flagged = entries with status `due` / `overdue` / `open_no_plan`, each an emitted
Citation carrying its source and tier.

---

## 6. Day-zero vocabulary the public seams may speak

Closed, small, and owned. The public API nouns and enums:

**Nouns (DTOs):** `Manager`, `Subject`, `Membership`, `Source`, `Pathway`, `PathwayStep`
(a.k.a. *ExpectedItem*), `ReportedItem`, `LedgerEntry`, `Citation`, `Nudge` (a `Citation` whose
status is `open_no_plan`).

**`MembershipRole`** — `self` · `family_manager` · `clinician`

**`SourceType`** — `public_guideline` · `doctor_instruction` · `prescription` · `lab_result` ·
`self_report`

**`ConfidenceTier`** (mapped from `SourceType`, owned by Catalog):
`A` = public guideline / protocol · `B` = doctor instruction / prescription / lab result ·
`C` = self-reported

**`LedgerStatus`** — `done` · `due` · `overdue` · `open_no_plan`

**Item identity** — `item_code`: a controlled code shared between `PathwayStep.item_code` and
`ReportedItem.item_code` (the join key). At day zero it is a small internal code list; it maps to a
standard terminology later without changing the seam.

Every public response is `Citation[]` (a `Nudge` is a member of that set). No other output shape
exists at the seam.

**Adding capability is one owner's change (exit 5):**
- *New pathway* → insert `Pathway` + `PathwayStep` rows (and their guideline `Source`) in **Catalog**.
  The join, accounts, and seam are untouched because the join is generic over `item_code`.
- *New source type* → add one `SourceType` value + its `ConfidenceTier` mapping in **Catalog**.
  Nothing downstream changes, because tier is read from `Source`, not branched on in the ledger.

---

## 7. Explicitly out of the MVP

Named so the design is legible about its edges (and so speculative structure scores against us if added):

- **The integrated overview (*המכלול*) / Pillar 2+.** No cross-pathway synthesis, no dashboards
  beyond the per-subject ledger. The data model has no aggregation entity by intent.
- **Any inference of medical state.** No "suspicion" engine, no risk scoring that produces new facts,
  no ML. State is only ever what was reported. Status classification is arithmetic, not inference.
- **Any origination of advice.** No recommendation engine, no treatment suggestion, no "what plan to
  choose." The nudge points to the doctor; it never fills the plan.
- **Unstated future sources.** No EHR/FHIR integration, no device feeds, no pharmacy APIs. Ingestion
  adapters that populate `ReportedItem`/`Source` are assumed to exist but their connectors are out of
  scope; the model is ready for them (a new adapter is a new `SourceType`, §5) without being built for
  any specific one.
- **Notifications / scheduling / reminders infrastructure.** The ledger *computes* what is due; a
  delivery channel (push, email) is a later concern, not a module here.
- **Identity/auth internals.** Delegated to an external IdP below the `Manager` boundary.
- **Free-text authoring anywhere.** There is deliberately no note/comment field that could become a
  back door around the Citation Seam.

---

### Why this is the minimal shape that still satisfies every exit criterion

| Exit criterion | Where satisfied | Structural (not conventional) because |
|---|---|---|
| 1 — boundary enforced by architecture | §3 kernel | private constructor makes advice unrepresentable; one return type |
| 2 — `manager→subject(s)` one primitive | §4 | a single `Membership` edge; multi-subject is cardinality, not a branch |
| 3 — expected vs reported joined, not enumerated | §5 | separate tables/modules; gaps are a 4-step query generic over `item_code` |
| 4 — provenance + tier travel with every item | §1, §5 | tier lives only on `Source`; both sides carry `source_id` by FK |
| 5 — new pathway / source = one owner | §5, §6 | both are Catalog-only inserts; join & seam are generic |
| 6 — scoped to Pillar 1 & MVP sources | §7 | no overview, inference, or unstated-source structure exists in the model |
