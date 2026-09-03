# Responsible Doctor — MVP Architecture (synthesized best design)

*A single synthesized design, chosen axis by axis from three independent MVP designs
(minimal-structure, extensibility-first, verifiability-first). Each axis takes the strongest
structural choice, not the union. It stands alone.*

**Shape in one sentence.** A modular monolith with a **closed core** (accounts, the ledger
join, the citation egress) and **two open data registries** (sources, pathways); the only value
that can leave the system is a `Citation = (Source × ReportedState)` minted by one sealed
gateway, and the one enum move that makes state-inference *unrepresentable* is that the
`Origin` of any stored fact has **no `SYSTEM` member**.

Guiding principle for the synthesis: **make the illegal state unrepresentable, and make the
legal one checkable.** Where a guarantee can be carried by a type, an enum, or a foreign key,
it is — never by convention. Where extensibility is required by the brief (exit 5), it is a
*seam contract*, not a plugin runtime (that would be speculative — brief §6).

---

## 1. Data model

All **authored** records — `Source` and `ReportedState` — are **immutable and append‑only**;
a correction is a new version linked by `supersedes`. This is the load‑bearing reason any
citation ever emitted can be re‑verified against exactly the record it cited. Pathways are
versioned the same way. The ledger is **never stored** (§5.4).

### 1.1 Provenance spine (shared)

```
Origin = AUTHORITATIVE_GUIDELINE | DOCTOR_INSTRUCTION | PRESCRIPTION
       | SUBJECT_REPORT | MANAGER_REPORT | RESULT_INGEST
       //  SYSTEM is deliberately NOT a member — it cannot be authored.

Provenance = {
  origin: Origin,            // who/what asserted this — never SYSTEM
  author_ref: ActorId,       // manager, subject, guideline publisher, or ingest connector
  captured_at: Timestamp,
  evidence_ref: DocumentId?  // optional pointer to the ingested doc / uploaded result
}

ConfidenceTier = T1_GUIDELINE > T2_DOCTOR_INSTRUCTION > T3_PRESCRIPTION > T4_SELF_REPORT
       //  a total order; assigned BY source class in one file, never by the engine.
```

`Origin` without `SYSTEM` is the single strongest guarantee in the model: "the system never
infers state" holds because **there is no enum value the system is allowed to write**. The
store rejects any record whose provenance cannot name a non‑system author.

### 1.2 Accounts — the `manager → subject(s)` primitive

| Entity | Fields | Notes |
|---|---|---|
| `Manager` | `manager_id`, `actor` | An operating identity. A doctor is just a Manager. |
| `Subject` | `subject_id`, `demographics{date_of_birth, sex_at_birth, …}` | The person a file is *about*. Demographics are **reported facts**, used by rail predicates. |
| `Grant` | `manager_id`, `subject_id`, `scope`, `relation`, `granted_by`, `granted_at` | **The single primitive.** One row = one manager may act on one subject at one scope. |

`scope ∈ {READ < REPORT < MANAGE}` (closed, ordered — the only role nuance, carried as data).
`relation ∈ {self, family_member, patient, …}` is an **open label that changes nothing in
logic**. Tier is **never** derived from `relation` — it comes only from `Source` class (§1.3),
so the account model carries no clinical trust logic.

### 1.3 Source — the authoritative left side of every citation

```
Source = {
  source_id, kind: GUIDELINE_STEP | DOCTOR_INSTRUCTION | PRESCRIPTION,
  tier: ConfidenceTier,      // fixed by kind, assigned in SourceRegistry only
  provenance: Provenance,    // origin ∈ authoritative/instruction/prescription set
  claim: SourceClaim,        // structured — NOT prose
  supersedes: SourceId?
}

SourceClaim =                              // closed, structured — no free-text channel
  | ExpectedAction { code: ActionCode, cadence: Cadence, applicability: Predicate }
  | Directive      { code: ActionCode, issued_for: SubjectId, window: DateRange? }
  | Dispense       { code: MedicationCode, schedule: DoseSchedule }
```

`claim` is a **closed set of typed variants over a code vocabulary** — never natural‑language
advice. The system can only ever surface what a source *structurally asserts*; there is no
free‑text field to fill with an originated recommendation. `code` is a **namespaced string**
(open vocabulary) so new clinical concepts need no schema migration — the extensibility seam
without a prose hole.

### 1.4 ReportedState — the right side of every citation

```
ReportedState = {
  state_id, subject_id,
  kind: RESULT | INSTRUCTION_ACK | MEDICATION_STATUS | PROCESS_STATUS | SELF_ATTESTATION,
  provenance: Provenance,    // origin ∈ subject/manager/result-ingest set — never SYSTEM
  observed: ObservedFact     // structured value the person reported; copied, never derived
}

ObservedFact =
  | ActionDone   { code: ActionCode, at, result_ref: DocumentId? }
  | MedTaken     { code: MedicationCode, at }
  | ProcessOpen  { code: ProcessCode, opened_at }   // "an open process" — a REPORTED fact
  | PlanMarker   { code: ProcessCode, plan_ref }    // a plan the person reports exists
```

The **openness of a process is always a reported fact** (`ProcessOpen`), never system‑inferred.
The absence of a matching `PlanMarker` is detected by the join as *logical* absence over
reported data (the same category as "overdue"), not by any clinical inference — that is what
keeps the no‑plan → nudge path on the non‑inference side of the line.

### 1.5 Pathway — the declarative "expected" library

```
Pathway = { pathway_id, title, owner: LibraryAuthorId, version, supersedes?, steps: [RailStep] }

RailStep = {
  step_id,
  expects: ActionCode | ProcessCode,
  gate: Predicate,                    // applicability over subject facts (age/sex/prior steps)
  cadence: Cadence,                   // when it becomes due
  plan_required: bool,                // if true, an open process here with no plan → nudge
  source_ref: SourceId (NON-NULL),    // EVERY step points at the Source that backs it
  on_open_no_plan: NUDGE_ASK_DOCTOR   // the only allowed reaction to an open-no-plan process
}
```

Rails are **pure data** in a small **declarative grammar** (age/sex ranges, prior‑item recency,
interval arithmetic) — deliberately too weak to express "looks like diabetes." A `RailStep`
**cannot exist without a non‑null `source_ref`**, so "provenance travels with every expected
item" is a schema fact, not a convention.

### 1.6 Citation — the sole output atom

```
Citation = {                          // constructed ONLY by CitationGateway (§3)
  relation: EXPECTED | DONE | GAP | NUDGE_ASK_DOCTOR,
  source_ref: SourceId (NON-NULL),
  state_ref: StateId?,                // present for DONE / GAP-with-partial-state
  tier: ConfidenceTier,               // copied from the referenced Source, never recomputed
  template_id: TemplateId             // a fixed, reviewed phrasing shell — no generated prose
}
```

There is **no `text`, `advice`, `recommendation`, or `reason` field.** Human strings are
produced only at the edge by binding `template_id` to *codes present in the referenced
records* (§3.3).

---

## 2. Module / boundary structure

Closed core (rarely changes) + two open registries (where growth lands) + dumb delivery. The
dependency arrow points **inward toward references, outward toward citations**.

```
                        PUBLIC SEAMS  (read/report only; reads return [Citation])
                                 │
                        ┌────────┴────────┐
                        │ CitationGateway │  ← the ONLY egress; only place Citation is built
                        └────────┬────────┘
                                 │ consumes LedgerItem (internal)
                        ┌────────┴────────┐
                        │  LedgerEngine   │  pure: join(pathways, facts, state) → [LedgerItem]
                        └───┬─────────┬───┘
                  reads     │         │     reads
             ┌──────────────┘         └──────────────┐
      ┌──────┴───────┐         ┌───────────┐   ┌─────┴──────────┐
      │ PathwayLib   │         │ Source    │   │ ReportedStore  │
      │ (rails,data) │         │ Registry  │   │ (subject state)│
      │  OPEN #2     │         │ (+tier)   │   │                │
      └──────┬───────┘         │  OPEN #1  │   └─────┬──────────┘
             │ publish_pathway └─────┬─────┘         │ report
             │                       │ ingest        │
             │                 ┌─────┴─────┐   ┌──────┴──────┐
             │                 │ Ingestors │   │  Reporters  │
             │                 └───────────┘   └─────────────┘

   AccountService (Manager/Subject/Grant) gates EVERY read/write above, in one middleware.
   Delivery surface (API/UI): a dumb renderer of [Citation] — no logic, no other import.
```

| Module | Owns | Changes when… |
|---|---|---|
| **SourceRegistry + Ingestors** (open #1) | Turning authoritative input into `Source` (+tier). One ingestor per source class. | a **new source type** is added — *here only*. |
| **PathwayLibrary** (open #2) | Declarative `Pathway`/`RailStep` records; evaluating rails. | a **new pathway** is added — *here only*. |
| **LedgerEngine** (core) | The pathway‑ and source‑**agnostic** pure join. | almost never (only if join *semantics* change). |
| **CitationGateway** (core) | The sole egress; constructs `Citation`s. | almost never — it is the invariant. |
| **AccountService** (core) | `manager→subject` capability model + access checks. | almost never. |
| **ReportedStore + Reporters** | `ReportedState`; rejects `origin=SYSTEM`/null author. | a new reported‑fact kind is added — here only. |
| **Delivery surface** | Rendering citations for a manager. | freely (cosmetic). |

**Why two registries and not one Catalog:** exit 5 asks that a *new source* and a *new pathway*
each be **one owner's** change — and they are **different owners** (a source ingester vs. a
clinical library author). Splitting them keeps each change local to its owner.

The seam is a **contract, not a plugin runtime**: `Ingestor.parse(raw) → (ReportedState[],
Source)` and `Pathway` as a data record loaded from a table. Day zero ships a *fixed small set*
(one public‑guideline loader, one structured subject‑report form, one doctor‑instruction form);
a hot‑loadable adapter framework is out (§7) as speculative.

**Boundary rules (each an enforceable fitness test):**
1. `Citation`'s constructor is package‑private to `CitationGateway`; no other module references it.
2. Every public seam's read return type is `Citation` / `[Citation]` — signature scan rejects any other.
3. `ReportedStore.write` rejects `origin = SYSTEM` or null author.
4. `LedgerEngine` imports no I/O, clock, or randomness — a pure function of its passed‑in reads.
5. Only `SourceRegistry` may set `tier`; engine and gateway read but never write it.

---

## 3. Ownership & structural enforcement of the non‑advice Citation invariant

**Invariant:** *every output is a `Citation = (authoritative Source × Reported medical state)`;
the system never infers state and never originates advice — for every user, including a doctor.*

**Owner: `CitationGateway`** — the single choke point, enforced by **construction, not review**.

### 3.1 Advice is *unrepresentable*, on three independent legs

1. **Single egress + sealed type.** The delivery surface and every notification path have no
   access to raw `LedgerItem`s or free text; their only import is the gateway. `Citation` has a
   private constructor and **no advice‑shaped field**. There is exactly one function through
   which a byte can reach a human. (Exit 1.)
2. **Rendering is projection, not generation.** `template_id` selects from a **fixed, closed,
   reviewed catalog** whose only fillable slots are (a) *verbatim source text/label* and (b)
   *codes/values from the referenced reported records*. Day‑zero catalog:
   - `EXPECTED_DUE` — "{source.title} expects {step.label}; last recorded {state.last}."
   - `OVERDUE` — same, plus the reported date that makes it overdue.
   - `DONE` — "{state.item} recorded, satisfying {source.title}."
   - `NUDGE_ASK_DOCTOR` — "{source.title} indicates a plan is expected here; none is recorded.
     **Ask your doctor.**"
   The imperative "ask your doctor" is a **constant string** — the one fixed, non‑clinical action
   the product may speak, pointing *away* from the system to the doctor. No template can name a
   drug, dose, or course of action the sources didn't. *Enforcement test:* delete every template
   that isn't a (source × state) projection and the system still functions.
3. **Closed verb set.** The seam vocabulary (§6) has no `recommend/diagnose/advise/prescribe/
   infer` symbol; a denylist lint over the seam surface fails the build if one appears.

### 3.2 Never infers state

State enters **only** through `Reporters`/`Ingestors`, each stamping a `Provenance` whose
`Origin ≠ SYSTEM` (unrepresentable otherwise, §1.1). `LedgerEngine` has **no code path that
writes** a `ReportedState` — it only reads. So no medical state comes into being without an
external actor having asserted it. Absence (of a done item, of a plan) is *logical* absence over
reported data — arithmetic, not inference.

### 3.3 The nudge is a citation, not an exception

`NUDGE_ASK_DOCTOR` fires when a `plan_required` step (or a reported `ProcessOpen`) has **no**
matching reported `PlanMarker`. The gateway emits it as
`Citation(NUDGE_ASK_DOCTOR, source_ref = step.source_ref, state_ref = the open-process fact)`:
it cites *the rail's expectation of a plan* (source) against *the reported open process with no
plan* (state). The system relays "your protocol expects a plan here and none is recorded — ask
your doctor," never "do X."

### 3.4 Holds for a doctor user too

A doctor is a `Manager` with `patient` Grants. They read the same `Citation` stream. If a doctor
issues an instruction it enters as a `DOCTOR_INSTRUCTION` **Source** via an ingestor — the doctor
authors advice; the system merely *cites* it. The gateway originates nothing on the doctor's
behalf.

### 3.5 Refuse, never coerce

Any gateway input that fails a check (unresolvable source, `SYSTEM`‑origin state, missing
template) is **refused, not patched**. "No valid citation" is a first‑class outcome (surfaced as
*nothing to show*) — which is operationally what "never originate advice" means.

---

## 4. The `manager → subject(s)` primitive

A single relation, `Grant(manager_id, subject_id, scope, relation)`, is the entire account model.

- **Self:** one `Grant` where the manager's actor and the subject coincide.
- **Family:** several `Grant` rows from one manager, one per member.
- **Doctor's panel:** the *same* rows at larger cardinality (400 patients = 400 grants).
- **Doctor as their own subject:** a `Grant` over themselves like anyone; §3 applies identically.

Every read/write is gated by `authorized(actor, subject, needed_scope) = ∃ Grant(...)` in one
middleware. **Multi‑subject is never a branch** — the manager's home view is a fold over "the
subjects I hold grants for," and family vs. clinic differ only in list length (a delivery/paging
concern, not a model one). Every `Citation` is emitted in the context of one `subject_id`, so
multi‑subject never leaks across the gateway. *Test (exit 2):* the family and clinic scenarios
exercise the same `AccountService` methods and the same `Grant` table — the code‑path diff is
empty.

---

## 5. Expected‑vs‑done ledger join (with provenance & confidence tier)

The two sides are **distinct by construction** — expected lives entirely in `PathwayLibrary`
(rails = data); reported/done lives entirely in `ReportedStore` (subject state). Gaps exist
**only** as the difference the join computes.

### 5.1 The pure join

```
join : (Pathways, SubjectFacts, [ReportedState]) → [LedgerItem]   // total, deterministic, no I/O

LedgerItem = { relation, source_ref (from RailStep, always present), state_ref?, step_id, tier }
```

Per subject:
1. **Select applicable steps:** evaluate each `RailStep.gate` against `SubjectFacts` + prior
   reported facts (age from `date_of_birth`, plus reported risk facts). Data‑driven predicate
   evaluation — *not* a hardcoded pathway. Non‑applicable steps produce nothing (no spurious
   citations).
2. **Match reported state:** find a `ReportedState` whose `ObservedFact.code = step.expects`
   within `cadence`. Matching is generic set/interval logic; it never inspects clinical meaning.
3. **Classify:**

   | Condition | `relation` |
   |---|---|
   | matched in window | `DONE` |
   | unmatched, within lead window | `EXPECTED` (due) |
   | unmatched, past window | `GAP` (overdue) |
   | `plan_required` step / reported `ProcessOpen`, no matching `PlanMarker` | `NUDGE_ASK_DOCTOR` |

4. **Stamp provenance:** copy `source_ref` from the rail step onto every item; `tier` is derived
   from the referenced `Source`. A `LedgerItem` is **invalid without a `source_ref`** (type‑level)
   — so provenance and, via the source, confidence tier are **inseparable** from every
   expected/gap/nudge item (exit 4). Where the expected and matched‑reported sources differ in
   tier, the item carries **both** and the gateway surfaces the **lower** tier as effective
   confidence.

Gaps are the **output of the join, never enumerated per example** (exit 3). Adding the well‑baby
schedule and adding a colon‑screening schedule are the *same act* — insert a `Pathway` fixture;
the engine is untouched.

### 5.2 Confidence tier travels automatically

Tier lives **only** on `Source`, is assigned **only** by `SourceRegistry` by source class, and is
**copied, never recomputed** onto ledger items and citations. There is no ledger or citation field
a developer could forget to populate, and no engine branch that could invent a tier. *Check:*
`citation.tier == referencedSource.tier` for every emitted item.

### 5.3 Determinism → golden tests

Because `join` is pure and total, expected‑vs‑done correctness is checkable with fixtures:
`(pathway, subjectFacts, reportedState) → expectedLedger`. A regression is any deviation — the
same property that makes the design *verifiable* also makes it safe to extend.

### 5.4 The ledger is a view, never stored

The ledger is materialized on read and re‑derivable at any time. Persisting it as truth would
create a second source of truth that could drift from its citations and defeat verification. A
pure input‑keyed cache is permitted as an optimization but is never authoritative.

---

## 6. Day‑zero vocabulary (what the public seams may speak)

Closed sets are the stable contract; open vocabularies are where growth is absorbed.

**Nouns (entities crossable at a seam):** `Manager`, `Subject`, `Grant`, `Source`,
`ReportedState`, `Pathway`, `RailStep`, `LedgerItem` (internal), `Citation`, `Ledger`
(a `[Citation]` view), `ConfidenceTier`, `Provenance`.

**`Origin` (closed; no `SYSTEM`):** `AUTHORITATIVE_GUIDELINE`, `DOCTOR_INSTRUCTION`,
`PRESCRIPTION`, `SUBJECT_REPORT`, `MANAGER_REPORT`, `RESULT_INGEST`.

**`Source.kind` (closed, extend in one file):** `GUIDELINE_STEP`, `DOCTOR_INSTRUCTION`,
`PRESCRIPTION`.

**`ConfidenceTier` (closed, total order):** `T1_GUIDELINE > T2_DOCTOR_INSTRUCTION >
T3_PRESCRIPTION > T4_SELF_REPORT`, surfaced on every citation as its source's trust label.

**`ReportedState.kind` (closed):** `RESULT`, `INSTRUCTION_ACK`, `MEDICATION_STATUS`,
`PROCESS_STATUS`, `SELF_ATTESTATION`.

**`Citation.relation` (closed):** `EXPECTED`, `DONE`, `GAP`, `NUDGE_ASK_DOCTOR`.

**`Grant.scope` (closed, ordered):** `READ < REPORT < MANAGE`.
**`Grant.relation` (open label, no logic):** `self`, `family_member`, `patient`, …

**Template catalog (closed):** `EXPECTED_DUE`, `OVERDUE`, `DONE`, `NUDGE_ASK_DOCTOR`.

**Open vocabularies (growth lands here, no schema change):** `code` (ActionCode / ProcessCode /
MedicationCode — namespaced strings, the join key shared by `RailStep.expects` and
`ObservedFact.code`), `pathway_id`. Maps to a standard terminology later without changing the
seam.

**Public verbs (seam operations):**
`grant(manager, subject, scope)` / `revoke(...)`,
`report(subject, ObservedFact)` — copy, never derive,
`ingest(source_class, raw) → (Source, ReportedState[])`,
`publish_pathway(pathway)`,
`view_ledger(subject) → [Citation]` — the only read of joined output.

**Verbs permanently absent (denylist lint over the seam):** `recommend`, `advise`, `diagnose`,
`prescribe`, `infer`, `suggest_treatment`, `conclude`. The vocabulary has no word for advice.

---

## 7. Explicitly out of the MVP

- **Pillar 2 / the integrated overview (*המכלול*).** No cross‑pathway synthesis, risk scoring, or
  unified health picture. The data model has no aggregation entity by intent.
- **Any inference / suspicion engine.** No "the system thinks you may have X." The rail grammar is
  too weak to express it and `Origin` has no `SYSTEM` member — inference is unbuildable, not merely
  disallowed.
- **Originating advice in any form** — no recommendations, triage, or dosing; no "smart" phrasing of
  nudges beyond the fixed templates. The template catalog and closed verb set cannot express it.
- **A hot‑loadable adapter/pack plugin runtime.** The seam is a *contract*; day zero ships a fixed
  trio (one guideline loader, one subject‑report form, one doctor‑instruction form). More adapters
  now would be speculative.
- **Rich RBAC / consent ceremony.** Grants exist and are scoped; the *proof* and revocation
  ceremony (identity verification, minor‑to‑adult transitions, clinic hierarchies) is thin/stubbed.
- **Automated clinical source integrations** (live EHR/FHIR feeds, device streams, pharmacy APIs),
  and **free‑text NLP** over documents. The M1 seam is ready for them; none is built.
- **Scheduling, booking, notifications, messaging the doctor.** The ledger *computes* what is due; a
  delivery channel is a later concern.
- **A persisted ledger as system‑of‑record.** Always a derived view (§5.4).
- **Free‑text authoring anywhere.** No note/comment field that could become a back door around the
  gateway; reported free text may be *stored* as evidence but never re‑emitted as an originating
  claim.
- **Identity/auth internals.** Delegated to an external IdP below the `Manager` boundary.

---

## 8. Exit criteria → structure

| # | Criterion | Where satisfied — structurally |
|---|---|---|
| 1 | Non‑advice enforced by architecture | §3 — one sealed `CitationGateway` egress; `Citation` has no advice field; rendering is closed‑catalog projection; verb denylist. |
| 2 | `manager → subject(s)` one primitive | §4 — one `Grant` relation; multi‑subject is cardinality; family/clinic share code paths. |
| 3 | Expected & reported distinct; gaps by join | §1.4–1.5 / §5 — separate `PathwayLibrary` vs `ReportedStore`; gaps are `relation` from a pure `join`, never enumerated. |
| 4 | Provenance + tier travel with every item | §1.1–1.5 / §5.2 — tier on immutable `Source`, assigned in one place, copied; non‑null `source_ref` on `RailStep`, `LedgerItem`, `Citation`. |
| 5 | New pathway / source = one owner's change | §2 — `PathwayLibrary` (author) and `SourceRegistry` (ingester) are separate data registries; the core ranges over the closed spine, not example content. |
| 6 | Scoped to Pillar 1 + MVP sources | §7 — overview, inference, extra sources, plugin runtime all explicitly out; `SYSTEM` origin unrepresentable. |
