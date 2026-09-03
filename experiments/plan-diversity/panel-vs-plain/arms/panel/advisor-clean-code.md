# "Responsible Doctor" MVP — Architecture

**Design stance.** The dominant risk in this product is not scale or latency; it is *structural drift* —
an advice-shaped output leaking out of some unguarded path, or a "family vs. patients" special case
metastasizing across the codebase. The design below is therefore built for a minimum of moving parts:
five modules, one closed shared vocabulary, one output choke point, and a dependency footprint of a
relational database plus a thin HTTP layer. Every abstraction present is justified by a force stated in
the brief; anything without such a force was cut.

---

## 1. System shape at a glance

```
                 ┌────────────────────────────────────────────┐
                 │                 surface                    │  thin HTTP/UI; owns zero rules
                 └───────┬───────────────┬────────────┬───────┘
                         │ authorize     │ ingest     │ view (READ — the only read path)
                         ▼               ▼            ▼
                 ┌────────────┐   ┌────────────┐   ┌────────────────────────────┐
                 │  accounts  │   │   record   │◄──│           ledger           │
                 │ manager →  │   │ reported   │   │ join(expected, evidence)   │
                 │ subject(s) │   │ state +    │   │ owns Citation + LedgerEntry│
                 └────────────┘   │ sources    │   └─────────────┬──────────────┘
                                  └────────────┘                 │
                                        ▲                        ▼
                                        │            ┌────────────────────────┐
                                        └────────────│        pathways        │
                                                     │ declarative rail       │
                                                     │ library (data, typed)  │
                                                     └────────────────────────┘

                 ┌────────────────────────────────────────────┐
                 │   vocabulary  (shared kernel, closed set)   │   everything above depends on it;
                 └────────────────────────────────────────────┘   it depends on nothing
```

Five modules plus one shared kernel. `surface` can *write* through `accounts` and `record`, but can
*read subject output* only through `ledger` — this asymmetry is the invariant's enforcement (§4).

**Dependency diet (day-zero, closed):** one relational database (SQLite for MVP, Postgres-compatible
SQL), one thin HTTP framework, the language stdlib, and one schema-validation step for pathway data
files at load time. No ORM beyond a hand-rolled row mapper, no rules engine, no workflow engine, no
queue, no vendor SDK. Nothing from this list may appear in a public seam type (§7).

---

## 2. Shared kernel: `vocabulary`

The one module every other module may depend on. It is deliberately tiny and **closed at day zero**;
extending it is a design decision, not a convenience. It contains only value types with their own
validation — no I/O, no behavior over collections, no services.

| Type | Definition | Rules it owns |
|---|---|---|
| `PersonId`, `SubjectId`, `ManagerId` | opaque ids (`SubjectId`/`ManagerId` are role-typed aliases of `PersonId`) | non-empty, format-checked once at construction |
| `ActivityCode` | a code from the MVP's **closed activity code list** (e.g. `COLONOSCOPY`, `HBA1C_TEST`, `INFANT_VACCINE_MMR`) | must be in the list; constructed only via `ActivityCode.parse` |
| `SourceKind` | enum: `PUBLIC_GUIDELINE` \| `DOCTOR_INSTRUCTION` \| `PRESCRIPTION` | closed enum |
| `ConfidenceTier` | ordered enum: `T1_PRESCRIPTION` > `T2_DOCTOR_INSTRUCTION` > `T3_PUBLIC_GUIDELINE` | total order; **derived from `SourceKind` in exactly one function, `ConfidenceTier.of(kind)`** |
| `SourceRef` | `(source_id, SourceKind, human_label)` | label is stored quoted text from the source, never composed |
| `ReportedRef` | `(reported_item_id, SubjectId)` | — |
| `TimeWindow` | `(due_from, due_until)` dates | `from ≤ until` |
| `LedgerStatus` | closed enum: `DONE` \| `DUE` \| `OVERDUE` \| `NO_PLAN` | closed enum |

**Why a closed activity-code list is the load-bearing choice.** "The system never infers state" is only
enforceable if *matching* expected-to-done can be exact. A closed, validated `ActivityCode` makes the
ledger join a code-equality + date-window comparison — a pure function with no heuristic, no similarity
scoring, no NLP. An item whose code cannot be parsed is **rejected at ingestion** with an actionable
error ("code not in the MVP activity list"), never stored as free text and never fuzzily matched later.
This is the primitive-obsession cure and the no-inference guarantee in one type.

**Day-zero public-seam vocabulary (normative).** Public seams — between modules and out of `surface` —
may speak exactly: the `vocabulary` types above, the public domain types each module declares below
(`Grant`, `Evidence`, `Directive`, `ExpectedStep`, `Citation`, `LedgerEntry`), ISO-8601 dates, and
JSON as the wire encoding. Nothing else: no database row types, no framework request/response objects,
no pathway-file parse trees. Error types at seams: one base `DomainError` with message, plus exactly
two subtypes callers actually branch on — `NotAuthorized` (surface → 403) and `RejectedReport`
(surface → 422 with the field-level reason). No other error subtypes exist until a caller needs to
catch one specifically.

---

## 3. Data model

Six tables. Every table has one owner module; no table is written by two modules.

```
person          (id, display_name, born_on, sex)                       -- owner: accounts
grant           (manager_id → person, subject_id → person)             -- owner: accounts
source          (id, kind: SourceKind, label, issued_by, issued_on)    -- owner: record
reported_item   (id, subject_id, source_id → source, activity_code,
                 role: EVIDENCE | DIRECTIVE | OPEN_PROCESS,
                 occurred_on, detail_json)                             -- owner: record
directive_step  (id, reported_item_id → reported_item, activity_code,
                 due_from, due_until)                                  -- owner: record
pathway         (id, version, title, source_id → source,
                 definition_json)                                      -- owner: pathways
```

Notes:

- **`person` is one table for everyone.** A manager is a person; a subject is a person; "self-managed"
  is a `grant(m, m)` row created at signup. Doctors, parents, and self are *not distinguished
  anywhere in the schema* — the distinction the product needs (who may act for whom) is entirely the
  `grant` edge. (MVP assumption: one grant level, "manages"; finer roles are out of scope, §8.)
- **`reported_item.role` is the done/expected split at the data level.**
  - `EVIDENCE` — "this happened" (a result, a performed screening). Feeds the *done* side.
  - `DIRECTIVE` — a reported doctor instruction or prescription. It is reported state **and** it
    spawns expected steps (`directive_step` rows, entered as reported — e.g. "repeat HbA1c in 3
    months" — never computed by the system). Feeds the *expected* side.
  - `OPEN_PROCESS` — a reported open condition/process (e.g. "abnormal result, follow-up pending per
    Dr. Levi's letter"). Exists so the *no-plan nudge* has a reported state to cite.
- **Every `reported_item` has a `source_id` — non-nullable.** Provenance is a foreign-key constraint,
  not a convention. A result cites the lab report; an instruction cites the doctor who gave it.
  **Assumption made:** the three brief-mandated kinds are the day-zero closed set, so a reported act
  must name the authoritative document/actor behind it (the prescription, the instruction, the
  guideline appointment it fulfilled); ingestion rejects a report that names none, with an error
  saying which source detail to add. The MVP keeps the kind set closed rather than adding a
  speculative fourth "self-attestation" kind.
- **`pathway.definition_json` is data, not code.** A pathway is a declarative document validated at
  load into a typed `Pathway` object (schema below). Adding a pathway is adding a row/file — no code
  change, satisfying exit criterion 5 for pathways by construction.

---

## 4. The non-advice invariant: owned by `ledger`, enforced by shape

**Exit criterion 1 restated:** one place every output must pass through, which can *only* emit
`(source × reported-state)` citations.

### 4.1 The Citation type

`ledger` owns two types and exports them **without public constructors**:

```
Citation
  source:   SourceRef        # required, no default
  reported: ReportedRef      # required, no default
  tier:     ConfidenceTier   # = ConfidenceTier.of(source.kind); set inside the constructor, not a parameter

LedgerEntry               # closed sum — exactly four shapes, no "other"
  status:   LedgerStatus     # DONE | DUE | OVERDUE | NO_PLAN
  activity: ActivityCode
  window:   TimeWindow
  citation: Citation         # exactly one, required
```

Three structural facts do the enforcing:

1. **`Citation` cannot exist without both halves.** The constructor requires a `SourceRef` and a
   `ReportedRef`; the module exposes only `Ledger.view(subject_id) -> list[LedgerEntry]` as a way to
   obtain instances. There is no `Citation.from_text`, no optional field, no builder.
2. **`LedgerEntry` carries no free text.** Its only fields are the codes and refs above. The system
   *physically has no field* in which to originate a sentence of advice. All human-readable copy —
   including the nudge's "you have an open process with no plan; ask your doctor" — lives in a
   **static copy table in `surface`, keyed by `LedgerStatus`**, written once by humans, containing no
   interpolated medical content beyond the citation's stored `human_label` (which is quoted source
   text, not composed text).
3. **`surface` has exactly one subject-output read path: `Ledger.view`.** `record` and `pathways`
   export their query interfaces (`EvidenceFeed`, `ExpectationSource`, below) *to the ledger*; the
   surface's dependency on them is write-only (ingestion). An auditor answering "can this system emit
   advice?" checks one function's return type. This holds for a doctor user identically: a doctor is
   a manager (§5), reaches the same `Ledger.view`, and when they *enter* an instruction it is stored
   as a `DIRECTIVE` reported item attributed to *them* as source — the system relays and cites it, it
   never adds to it.

### 4.2 No inference, structurally

The ledger's matcher is a pure function: `match(expected: ExpectedStep, evidence: list[Evidence])`
succeeds iff codes are equal and `occurred_on ∈ window`. No scoring, no thresholds, no model. The
absence of an inference capability is not a policy — there is no component in the architecture whose
job could grow into one without adding a new module (which is exactly the review event that should
catch it).

---

## 5. `accounts`: the manager → subject primitive

One concept: the **`Grant`** edge over one `Person` table.

```
accounts public seam:
  register(person fields) -> PersonId            # also writes grant(self, self)
  grant(manager: ManagerId, subject: SubjectId)
  subjects_of(manager: ManagerId) -> list[SubjectId]
  authorize(manager: ManagerId, subject: SubjectId)   # raises NotAuthorized; the ONLY authz question in the system
```

- A parent with three children: four `grant` rows (self + three). A doctor with 200 patients: 201
  rows. **Same rows, same queries, same code path** — multi-subject is cardinality, not a case.
- `authorize` is Tell-Don't-Ask: callers never fetch grant rows to decide; they tell `accounts` the
  pair and proceed or catch `NotAuthorized`. Every `surface` endpoint calls it first; `record` and
  `ledger` take an already-authorized `SubjectId` and know nothing about managers — accounts is the
  *only* module that has ever heard of a manager, so a change to the account model cannot scatter.

---

## 6. Expected vs. done: two feeds, one join

### 6.1 The one real interface in the system

There is exactly one abstraction with multiple implementations, and it exists because the brief
supplies two genuinely different producers of expectations *today*:

```
ExpectationSource                      # interface, consumed only by ledger
  expected_for(subject: SubjectFacts) -> list[ExpectedStep]

ExpectedStep                           # vocabulary-level domain type
  activity: ActivityCode
  window:   TimeWindow
  source:   SourceRef                  # provenance is a required field of the step itself
```

Implementations (both real on day one — this is not an `ICat`):

1. **`pathways.RailSource`** — evaluates the declarative pathway library against `SubjectFacts`
   (born_on, sex, and reported risk-flag evidence — all *reported* data; applicability never infers).
   A pathway definition is: `applicability` (predicates over facts: age range, sex, presence of a
   coded risk flag) + `steps` (activity code, recurrence/offset rule). `Pathway.steps_for(facts)`
   is behavior on the domain object — the pathway knows its own rules; the ledger never opens
   `definition_json`.
2. **`record.DirectiveSource`** — returns the `directive_step` rows of the subject's reported
   instructions/prescriptions, each step citing its directive's source.

Every `ExpectedStep` is born carrying its `SourceRef`; there is no code path where an expectation
exists without provenance, so exit criterion 4 is a field requirement, not a discipline.

### 6.2 The done feed

```
record public seam (read side, consumed only by ledger):
  EvidenceFeed.evidence_for(subject) -> list[Evidence{activity, occurred_on, reported: ReportedRef, source: SourceRef}]
  OpenProcessFeed.open_for(subject)  -> list[OpenProcess{reported: ReportedRef, source: SourceRef}]
record public seam (write side, consumed by surface):
  report(subject, item) -> ReportedRef | RejectedReport     # validates ActivityCode + required source here, once
```

### 6.3 The join (the whole algorithm of the product)

```
Ledger.view(subject):
  facts    = record.facts_for(subject)
  expected = concat(s.expected_for(facts) for s in expectation_sources)   # rails + directives
  evidence = record.evidence_for(subject)
  for step in expected:
      hit = exact match by (activity code, occurred_on ∈ window)
      emit LedgerEntry(DONE|DUE|OVERDUE, step.activity, step.window,
                       Citation(step.source, hit.reported if hit else <the reported fact that made the
                       step applicable — e.g. the risk-flag evidence or the directive item>))
  for proc in record.open_for(subject):
      if no expected step covers proc:
          emit LedgerEntry(NO_PLAN, proc.activity, now-window, Citation(proc.source, proc.reported))
```

- A **gap** (`DUE`/`OVERDUE`) still satisfies the invariant: its citation joins the *expectation's*
  source with the *reported fact that made the expectation apply to this subject* (the directive
  item, or the demographic/risk evidence a rail matched on). Nothing is asserted beyond "this source
  says X is expected given what you reported."
- The **nudge** is not a feature bolted on: it is `LedgerEntry(NO_PLAN, …)` — an ordinary ledger row
  whose citation is (the source of the open process × the reported open process). `surface` renders
  it from the static copy table as "ask your doctor." No plan is proposed because no type exists to
  carry one.
- **Confidence tier** arrives inside the `Citation`, derived from `SourceKind` in the one
  `ConfidenceTier.of` function. Adding a source kind = extend `SourceKind`, add one line to
  `ConfidenceTier.of`, and (if it produces expectations) add one `ExpectationSource` implementation —
  all inside one module's change set; `ledger`, `accounts`, and `surface` compile untouched (exit
  criterion 5).

---

## 7. `surface`

Thin by rule, not by hope: it owns HTTP translation, the `authorize` call, and the static copy table.
It contains no branch on `SourceKind`, no branch on manager type, and no access to `EvidenceFeed` —
its read model *is* `list[LedgerEntry]`. If a future endpoint needs data the ledger doesn't emit,
that is a ledger design conversation, not a surface workaround.

Endpoints (MVP-complete): `POST /people`, `POST /grants`, `GET /subjects`,
`POST /subjects/{id}/reports`, `GET /subjects/{id}/ledger`.

---

## 8. Explicitly out of the MVP

- **The integrated overview (המכלול)** — no aggregate views, no cross-subject dashboards; nothing in
  the schema anticipates it.
- **Inference of any kind** — no suspicion engine, no fuzzy matching, no NLP over documents, no
  risk scoring. Structurally absent, not disabled.
- **Unstated source types** — no FHIR/EHR connectors, no lab integrations, no importers. `SourceKind`
  is the closed three-kind set from the brief.
- **Roles/permissions beyond the single `Grant` edge** — no read-only grants, no delegation chains,
  no consent workflows.
- **Notification delivery** — the nudge is a ledger row; push/email/scheduling machinery is out.
  (A cron that re-renders the ledger would be additive later; nothing here presumes it.)
- **Real clinical code systems** (LOINC/SNOMED mapping), localization beyond the one copy table,
  audit trails, multi-tenancy, and pathway authoring tooling (MVP pathways are reviewed data files).

Each exclusion is also a *shape* exclusion: no interface, enum slot, or nullable column exists "for
when we add it."

---

## 9. Design self-check against the smells

- **One-sentence reason per module:** `vocabulary` changes if the shared code list changes; `accounts`
  if who-acts-for-whom changes; `record` if what can be reported or its provenance rules change;
  `pathways` if rail semantics change; `ledger` if the join or the citation contract changes;
  `surface` if the wire format changes. No module has a second sentence.
- **Shotgun-surgery probes:** new pathway → one data file. New source kind → `record` (+ enum line).
  New ledger status → `ledger` + one copy-table row. New family member / new patient → zero code.
- **Feature envy:** the ledger never opens pathway definitions (`Pathway.steps_for`), never reads
  grant rows (`authorize`), never parses reported detail JSON (feeds return typed `Evidence`).
- **No decorative abstraction:** one interface (`ExpectationSource`), two shipping implementations,
  both demanded by the brief. `Citation` and `LedgerEntry` are closed concrete types on purpose —
  a second implementation of "citation" is precisely what the product must never have.
- **Duplication accepted where honest:** rails and directives both produce `ExpectedStep`s but share
  no evaluation code — a guideline's recurrence rule and a doctor's dated step are different concepts
  that merely rhyme; unifying their internals would be the wrong abstraction.
