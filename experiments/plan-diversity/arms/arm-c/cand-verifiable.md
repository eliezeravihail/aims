# Responsible Doctor — MVP Architecture (Arm C: optimized for verifiability)

**Design bias:** every structural choice below is made to render the core invariant *checkable*. The
non-advice boundary, the expected-vs-done correctness, and the citation guarantee are not intentions
enforced by discipline — they are properties a test suite (or a type checker) can decide mechanically.
Where a choice trades ergonomics for provability, it takes provability.

> **North-star invariant.** Every value that leaves the system is a
> `Citation = (Source × ReportedState × Relation)` where `Source` and `ReportedState` are *references*
> to stored records the system did not author. The system never infers state and never originates advice.

Assumptions stated inline are marked **[A]**. They are reasonable MVP choices, not requirements from the brief.

---

## 0. The verifiability thesis (how each guarantee is made provable)

| Guarantee | Made provable by | The decidable check |
|---|---|---|
| Non-advice: no output originates advice | `Citation` is the **only constructible output type**; it has no free-text/advice field | *Type check*: no public seam returns anything but `Citation`. *Fitness test*: only `CitationGateway` may construct a `Citation`. |
| No state inference | `ReportedState` records carry an `origin` that is **never `SYSTEM`**; the join only *reads* them | *Property test*: `∀ r ∈ ReportedState : r.origin ≠ SYSTEM`. Any write with `SYSTEM` origin is rejected at the store boundary. |
| Citation integrity | A `Citation` holds `source_ref` + `state_ref`, not copied prose | *Referential test*: every emitted citation dereferences to two live records; neither is system-authored. |
| Expected-vs-done correctness | Gaps are the output of one **pure deterministic function** `join(rail, state)` | *Golden-fixture tests*: fixed `(rail, state) → ledger` pairs; the function is total and side-effect-free. |
| Provenance + confidence travel with every item | Provenance/tier are fields **inside** `Source`, and `Citation` cannot exist without a `source_ref` | *Schema test*: `Citation` has no valid instance with a null `source_ref`; tier is derived from the referenced source. |
| New pathway / new source = one owner's change | Pathways and sources are **data in registries**, not code branches in the ledger/account/output layers | *Change-locality test*: adding a fixture pathway/source touches only its registry; ledger, accounts, gateway diffs are empty. |

These six rows are the acceptance suite. The rest of the document is the structure that makes them pass.

---

## 1. Data model

All records are immutable and append-only **[A]** — corrections are new versions, never in-place edits — so
that any citation ever emitted can be re-verified against exactly the record it cited.

### 1.1 Identity & provenance primitives (shared spine)

```
Origin      = AUTHORITATIVE_GUIDELINE | DOCTOR_INSTRUCTION | PRESCRIPTION
            | SUBJECT_REPORT | MANAGER_REPORT | RESULT_INGEST
            //  SYSTEM is deliberately NOT a member. It cannot be authored.

ConfidenceTier = T1_GUIDELINE | T2_DOCTOR | T3_PRESCRIPTION | T4_SELF_REPORT
            //  a total order T1 > T2 > T3 > T4; assigned BY source class, never by the engine.

Provenance  = {
  origin: Origin,             // who/what asserted this — never SYSTEM
  author_ref: ActorId,        // the manager, subject, guideline publisher, or ingest connector
  captured_at: Timestamp,
  evidence_ref: DocumentId?   // optional pointer to the ingested doc / uploaded result
}
```

`Origin` excluding `SYSTEM` is the load-bearing move: "the system never infers state" is enforced because
there is **no enum value the system is allowed to write**. The store rejects any record whose provenance
cannot name a non-system author.

### 1.2 Source (the authoritative left side of every citation)

```
Source = {
  source_id: SourceId,
  kind: GUIDELINE_STEP | DOCTOR_INSTRUCTION | PRESCRIPTION,
  tier: ConfidenceTier,       // fixed by kind
  provenance: Provenance,     // origin ∈ authoritative/instruction/prescription set
  claim: SourceClaim,         // structured, NOT prose advice (see below)
  supersedes: SourceId?       // versioning
}

SourceClaim =
  | ExpectedAction { code: ActionCode, cadence: Cadence, applicability: Predicate }   // from a guideline/protocol
  | Directive      { code: ActionCode, issued_for: SubjectId, window: DateRange? }    // from a doctor instruction
  | Dispense       { code: MedicationCode, schedule: DoseSchedule }                    // from a prescription
```

`claim` is a **closed, structured vocabulary** (codes + cadences + predicates), not natural-language text.
The system can therefore only ever surface what a source *structurally asserts*; it has no channel to
compose an original recommendation, because there is no free-text advice field to fill.

### 1.3 ReportedState (the right side of every citation)

```
ReportedState = {
  state_id: StateId,
  subject_id: SubjectId,
  kind: RESULT | INSTRUCTION_ACK | MEDICATION_STATUS | PROCESS_STATUS | SELF_ATTESTATION,
  provenance: Provenance,     // origin ∈ subject/manager/result-ingest set — never SYSTEM
  observed: ObservedFact      // structured value the person reported; the system copies, never derives
}

ObservedFact =
  | ActionDone     { code: ActionCode, at: Timestamp, result_ref: DocumentId? }
  | MedicationTaken{ code: MedicationCode, at: Timestamp }
  | ProcessOpen    { code: ProcessCode, opened_at: Timestamp }   // "an open process"
  | PlanPresence   { code: ProcessCode, has_plan: bool }         // reported, not inferred
```

Note `PlanPresence.has_plan` is a **reported** fact (the subject/manager says whether a plan exists). The
system never concludes "there is no plan"; it reads that the person reported none. This keeps the
"no-plan → nudge" path on the non-inference side of the line.

### 1.4 Pathway rail (the declarative "expected" library)

```
Pathway = {
  pathway_id: PathwayId,
  title: Label,               // display only, from the library author
  owner: LibraryAuthorId,     // one owner (see §5 / exit criterion 5)
  steps: [RailStep]
}

RailStep = {
  step_id: StepId,
  expects: ActionCode | ProcessCode,
  gate: Predicate,            // applicability over subject facts (age/sex/risk/prior-steps)
  cadence: Cadence,          // when it becomes due
  source_ref: SourceId,      // EVERY rail step points at the authoritative Source that backs it
  on_open_no_plan: NUDGE_ASK_DOCTOR  // the only allowed reaction to an open process without a plan
}
```

A `RailStep` **cannot exist without a `source_ref`** (schema-enforced non-null). This is why "source
provenance travels with every expected item" is a schema property, not a coding convention: an expected
item that isn't backed by a source is not a representable value.

### 1.5 Citation (the sole output atom)

```
Citation = {                         // constructed ONLY by CitationGateway (§3)
  relation: EXPECTED | DONE | GAP | NUDGE_ASK_DOCTOR,
  source_ref: SourceId,              // non-null, always
  state_ref: StateId?,               // present for DONE and for GAP-with-partial-state
  tier: ConfidenceTier,             // copied from the referenced Source; not recomputed
  template_id: TemplateId            // a fixed, reviewed phrasing shell — no generated prose
}
```

There is **no `text`, `recommendation`, `advice`, or `reason` free-field.** Human-readable strings are
produced only at the very edge by binding `template_id` to the *codes* found in the referenced records
(§3.3). The atom that crosses every boundary is pure references + a closed relation tag.

### 1.6 Accounts

```
Manager  = { manager_id, actor: Actor }
Subject  = { subject_id, demographics: SubjectFacts }   // facts used by rail predicates
Grant    = { manager_id, subject_id, scope: READ | REPORT | MANAGE, granted_by, granted_at }
```

`Grant` is the whole account model (§4). A family manager and a doctor differ only in *how many* `Grant`
rows point at them — never in type.

### 1.7 The ledger (a view, not a store)

The expected-vs-done ledger is **not persisted as truth**; it is the deterministic output of
`join(pathways, state)` (§5), materialized on read and re-derivable at any time. Persisting it would create
a second source of truth that could drift from its citations and defeat verification.

---

## 2. Module / boundary structure

```
                      PUBLIC SEAMS  (read-only; return [Citation])
                              │
                     ┌────────┴─────────┐
                     │  CitationGateway │   ← the ONLY egress; only place Citation is constructed
                     └────────┬─────────┘
                              │ consumes LedgerItem (internal)
                     ┌────────┴─────────┐
                     │   LedgerEngine   │   pure: join(pathways, state) → [LedgerItem]
                     └───┬──────────┬───┘
             reads       │          │      reads
        ┌────────────────┘          └───────────────┐
┌───────┴────────┐   ┌──────────────┐        ┌──────┴─────────┐
│ PathwayLibrary │   │ SourceRegistry│        │ ReportedStore  │
│ (rails, data)  │   │ (sources+tier)│        │ (subject state)│
└────────────────┘   └───────┬──────┘        └──────┬─────────┘
                             │ ingest                │ report
                     ┌───────┴──────┐        ┌───────┴─────────┐
                     │  Ingestors   │        │  Reporters      │
                     │ (guidelines) │        │ (subject/mgr)   │
                     └──────────────┘        └─────────────────┘

         AccountService (Manager/Subject/Grant) gates every read/write above.
```

**Boundary rules (each is an enforceable fitness test):**

1. `Citation` is a sealed type whose constructor is package-private to `CitationGateway`. *Test:* grep/AST
   fitness check — no other module references the constructor. (Compiler-enforced in a language with
   sealed types / friend visibility **[A]**.)
2. Public seams' return signatures are `Citation` or `[Citation]` only. *Test:* signature scan of the seam
   layer rejects any other return type.
3. `ReportedStore.write` rejects any record with `origin = SYSTEM` or a null author. *Test:* boundary unit
   test + runtime guard.
4. `LedgerEngine` imports no I/O, clock, or randomness — it is a pure function of its arguments. *Test:*
   dependency-direction lint; it may depend only on the three registries' read interfaces passed in.
5. Only `SourceRegistry` assigns `tier`; the engine and gateway may read but never set it. *Test:* write
   access to `tier` restricted to `SourceRegistry`.

The dependency graph is acyclic and points **inward toward references, outward toward citations** — data
enters as authored records, and the only thing that comes out the far side is a join over them.

---

## 3. Ownership of the citation invariant

### 3.1 One owner: `CitationGateway`

Exit criterion 1 asks for *one place every output must pass through that can only emit a
`(source × reported-state)` citation.* That place is `CitationGateway`. It is:

- **The sole constructor of `Citation`** (sealed type, private constructor).
- **The sole export of the public-seam layer's payloads** — seams call the gateway; they cannot mint output
  themselves.
- **Total on a closed input** — it accepts only a `LedgerItem` (an internal, already-joined,
  already-source-backed record) and emits exactly one `Citation`, or refuses.

### 3.2 What the gateway checks before it emits (the provable contract)

For every `Citation` it constructs, the gateway asserts — and a test can assert the same:

1. `source_ref` resolves to a live `Source`; `tier := that source's tier` (copied, not chosen).
2. If `relation = DONE`, `state_ref` resolves to a live `ReportedState` and its `origin ≠ SYSTEM`.
3. If `relation = NUDGE_ASK_DOCTOR`, the backing `RailStep.on_open_no_plan = NUDGE_ASK_DOCTOR` **and** the
   state shows `ProcessOpen` with reported `PlanPresence.has_plan = false`. The nudge cites the *rail's*
   expectation of a plan (source) against the *reported* absence of one (state). It is therefore a citation,
   not advice: the system relays "your protocol expects a plan here and you reported none — ask your
   doctor," never "do X."
4. `template_id` is drawn from a reviewed, finite template table; it is bound only to codes present in the
   referenced records.

Any input that fails a check is **refused, not coerced** — the gateway has no branch that fabricates a
missing source. "No valid citation" is a first-class outcome (surfaced as *nothing to show*), which is
exactly what "never originate advice" means operationally.

### 3.3 Why advice is *unrepresentable*, not merely *prohibited*

- The output type has no advice-shaped field to populate.
- Human strings are `template(template_id) ⊗ codes(referenced records)` — a fill-in of vetted shells with
  values that already exist in authoritative/reported records. There is no generation step, so there is no
  place for an original recommendation to enter.
- The verb set the system may speak is closed (§6) and contains no `recommend/diagnose/advise/prescribe`.

---

## 4. The `manager → subject(s)` primitive

A single relation, `Grant(manager_id, subject_id, scope)`, is the entire account model.

- **One person managing their family:** several `Grant` rows, one per family member, all pointing at the
  same `manager_id`.
- **A doctor managing patients:** the *same* rows at larger cardinality.
- **A person managing themselves:** one `Grant` where the manager's actor and the subject coincide.
- **A doctor as a subject of their own care:** they hold a `Grant` over themselves like anyone — the
  invariant (§1, §3) applies identically, satisfying "this holds for every user, including a doctor user."

There is no `Family` type, no `Practice` type, no per-role code path. Multi-subject is cardinality on one
relation. *Test (exit criterion 2):* the family scenario and the clinic scenario exercise the **same**
`AccountService` methods and the same `Grant` table; a diff of code paths between them is empty.

Authorization is a predicate over `Grant`: every read/write in §2 is gated by
`authorized(actor, subject, needed_scope)`. Scope tiers (`READ < REPORT < MANAGE`) are the only role
nuance, and they are data on the grant, not subclasses.

---

## 5. Joining "expected" and "reported/done" into the ledger

### 5.1 The pure join

```
join : (Pathways, SubjectFacts, [ReportedState]) → [LedgerItem]      // total, deterministic, no I/O

LedgerItem = {
  relation: EXPECTED | DONE | GAP | NUDGE_ASK_DOCTOR,
  source_ref: SourceId,     // from the RailStep — always present
  state_ref: StateId?,      // the matching reported item, if any
  step_id: StepId
}
```

Algorithm (per subject):

1. **Select applicable steps:** for each `RailStep`, evaluate `gate` against `SubjectFacts` and prior
   reported facts. Non-applicable steps are dropped (they never produce output → no spurious citations).
2. **Match reported state:** for each applicable step, look for a `ReportedState` whose `ObservedFact.code`
   equals `step.expects` within `cadence`.
   - Match found → `LedgerItem{DONE, source_ref, state_ref}`.
   - No match, step due → `LedgerItem{GAP, source_ref, state_ref=null}`.
   - No match, step not yet due → `LedgerItem{EXPECTED, source_ref}`.
3. **Open-process-without-plan:** if reported state has `ProcessOpen(code)` and a reported
   `PlanPresence(code, has_plan=false)`, and the pathway's step for `code` carries
   `on_open_no_plan = NUDGE_ASK_DOCTOR`, emit `LedgerItem{NUDGE_ASK_DOCTOR, source_ref=step.source_ref}`.

Every branch attaches `source_ref` from the rail step, so **provenance and (via the source) confidence tier
are inseparable from every expected/gap/nudge item** by construction (exit criterion 4). There is no code
path that yields a ledger item without a source.

### 5.2 Distinctness and "computed, not enumerated"

- **Expected** lives entirely in `PathwayLibrary` (rails = data).
- **Reported/done** lives entirely in `ReportedStore` (subject state).
- Gaps exist **only** as the difference `join` computes; they are never authored, listed, or hardcoded per
  example (exit criterion 3). Adding the "well-baby schedule" pathway and adding a "colon-screening" pathway
  are the same act: insert a `Pathway` fixture; the engine is untouched.

### 5.3 Determinism → golden tests

Because `join` is pure and total, correctness of expected-vs-done is checked with fixtures:
`(pathway, subjectFacts, reportedState) → expectedLedger`. A regression is any deviation. Confidence-tier
propagation is checked by asserting `citation.tier == referencedSource.tier` for every item. This is the
heart of "expected-vs-done correctness as testable as possible."

### 5.4 One-owner change (exit criterion 5)

| To add… | Owner | Files touched |
|---|---|---|
| a new pathway | Library author | one `Pathway` record in `PathwayLibrary` (+ the `Source`s its steps cite) |
| a new source type/class | `SourceRegistry` owner | one `SourceClaim` variant + its `tier` mapping + one `Ingestor` |
| a new reported fact kind | `ReportedStore` owner | one `ObservedFact` variant + one `Reporter` |

The `LedgerEngine`, `AccountService`, and `CitationGateway` do **not** change when the library or source set
grows — they range over the closed relation/enum spine (§1.1), not over example content. *Change-locality
test:* adding a fixture pathway yields an empty diff outside `PathwayLibrary`.

---

## 6. Day-zero vocabulary (what the public seams may speak)

The seams speak a closed vocabulary. Its closedness is itself a guarantee: absent verbs cannot be uttered.

**Nouns (the only entities crossable at a seam):**
`Manager`, `Subject`, `Grant`, `Source`, `ReportedState`, `Pathway`, `RailStep`, `Citation`, `Ledger`
(a `[Citation]` view), `ConfidenceTier`, `Provenance`.

**Relations a `Citation` may carry (closed set):**
`EXPECTED`, `DONE`, `GAP`, `NUDGE_ASK_DOCTOR`.

**Verbs the seams expose (closed set):**
- `grant / revoke` (manager↔subject)
- `report` (subject/manager submits a `ReportedState` — copy, never derive)
- `ingest` (load an authoritative `Source`)
- `publish_pathway` (library author registers rails)
- `view_ledger(subject)` → `[Citation]` (the only read of joined output)

**Verbs deliberately absent (must never appear in the vocabulary):**
`recommend`, `advise`, `diagnose`, `prescribe`, `infer`, `suggest_treatment`, `conclude`. Their absence is a
lint rule over the seam surface: any symbol matching this denylist fails the build.

**Confidence tiers (public, ordered):** `T1_GUIDELINE > T2_DOCTOR > T3_PRESCRIPTION > T4_SELF_REPORT`,
surfaced on every citation as the trust label of its source.

---

## 7. Explicitly out of the MVP

- **Pillar 2 / the integrated overview (*המכלול*).** No cross-pathway aggregation, risk scoring, or unified
  health picture.
- **Any inference / suspicion engine.** The system never derives a medical state, computes a diagnosis, or
  flags a suspected condition. `Origin` has no `SYSTEM` member precisely to keep this unbuildable.
- **Advice generation of any kind**, including "smart" phrasing of nudges beyond the fixed templates.
- **Source types beyond the three named** (guideline/protocol, doctor instruction, prescription). New source
  classes are a post-MVP owner change (§5.4), not scaffolded now.
- **Free-text notes as output.** Reported free text may be *stored* as evidence, but never re-emitted as an
  originating claim.
- **Scheduling/notifications, billing, EHR write-back, multi-language NLG.** Out of scope; seams are
  read-and-report only.
- **Persisted ledger as system-of-record.** The ledger is always a derived view (§1.7) to avoid a
  drift-prone second truth.

Anything built for the overview, for inference-based suspicion, or for unstated future sources is speculative
and, per the brief, should count against the design.

---

## 8. Traceability: exit criteria → structure

1. *Non-advice enforced by architecture* → sealed `Citation`, single `CitationGateway` egress, no advice
   field, closed verb set (§1.5, §3, §6).
2. *`manager → subject(s)` one primitive* → single `Grant` relation; multi-subject is cardinality (§4).
3. *Expected vs reported distinct; gaps joined* → `PathwayLibrary` vs `ReportedStore`; pure `join` (§5).
4. *Provenance + tier travel with every item* → non-null `source_ref` on `RailStep` and `Citation`; tier
   copied from source (§1.4, §1.5, §5.1).
5. *New pathway/source = one owner's change* → registries are data; engine ranges over the closed spine
   (§5.4).
6. *Scoped to Pillar 1 + MVP sources* → §7 fences the boundary; `SYSTEM` origin is unrepresentable.
