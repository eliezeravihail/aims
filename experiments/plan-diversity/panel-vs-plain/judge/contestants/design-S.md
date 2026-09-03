# "Responsible Doctor" MVP — Architecture

*Scope: Pillar 1 only — managing/steering medical processes. The deliverable is the shape: data
model, boundaries, ownership of the citation invariant, the `manager → subject(s)` primitive, the
expected-vs-done join, and the day-zero vocabulary of the public seams.*

---

## 0. The one-paragraph shape

The system is five modules around a shared, closed vocabulary. **Accounts** answers "may this
manager act for this subject?" and mints the capability token every other module requires.
**Sources** is the registry of authoritative sources and the sole owner of the
source-class → confidence-tier mapping. **File** is the subject's medical tracking file
(תיק מעקב): an append-only log of *reported* items, each of which must name its source.
**Rails** is a declarative library of pathway definitions and the one generic engine that
evaluates them against reported facts to produce *expected* items. **Ledger** joins expected
against reported into the expected-vs-done ledger, and is the **only module able to construct a
`Citation`** — the single output type of the system. There is no other output-producing path: the
API layer returns ledger views made of citations, and nothing else. Advice cannot be originated
because no type at any public seam has a field the system could write it into.

```
                 ┌─────────────────────────────────────────────┐
                 │              API (transport only)           │
                 │   speaks the day-zero vocabulary, nothing   │
                 │   else; every read returns LedgerView       │
                 └───────┬─────────────────────────┬───────────┘
                         │ AccessGrant required    │
                 ┌───────▼───────┐         ┌───────▼───────────┐
                 │   ACCOUNTS    │         │      LEDGER       │
                 │ manager→subj  │         │  the join; sole   │
                 │ mints         │         │  Citation mint    │
                 │ AccessGrant   │         └───┬───────────┬───┘
                 └───────────────┘             │           │
                                       ┌───────▼────┐ ┌────▼───────┐
                                       │   RAILS    │ │    FILE    │
                                       │ expected   │ │ reported   │
                                       │ side       │ │ side       │
                                       └───────┬────┘ └────┬───────┘
                                               │           │
                                          ┌────▼───────────▼────┐
                                          │       SOURCES       │
                                          │ registry + tiers +  │
                                          │  ingest adapters    │
                                          └─────────────────────┘
```

Dependency direction is strictly downward in this picture; the shared vocabulary (§6) is the only
thing everyone sees. Persistence is a single relational database behind each module's own
repository; no storage type crosses a seam.

---

## 1. Data model

Types are written in a language-neutral pseudocode. `⊕` marks a closed enum. All ids are their own
small types (no bare strings at seams — see §6).

### 1.1 Identity & access (owned by **Accounts**)

```
Manager      { manager_id: ManagerId, credentials, display_name }

Subject      { subject_id: SubjectId, display_name }
             // deliberately carries NO medical data; the File does

Grant        { manager_id: ManagerId,
               subject_id: SubjectId,
               relation:   ⊕{ Self, Family, Clinician },   // label only — same capability in MVP
               granted_at }

AccessGrant  // opaque capability token, mintable ONLY by Accounts.authorize(...)
             // = proof that (manager, subject, action) was checked.
```

`manager → subject(s)` is **one primitive**: a person managing themselves is a Manager with a
Grant to their own Subject; a parent managing children, and a doctor managing patients, are the
same Manager with more Grants. `relation` is a display label, not a branch point — no code path
switches on it in the MVP. (Assumption: differentiated permissions per relation are post-MVP; the
field exists so the day the product needs them, Accounts is the one owner that changes.)

### 1.2 Sources & provenance (owned by **Sources**)

```
SourceClass     ⊕{ PublicGuideline, DoctorInstruction, Prescription, SubjectSelfReport }

ConfidenceTier  ⊕{ T1_Guideline, T2_Clinician, T3_SelfReported }   // ordered

Source          { source_id:  SourceId,
                  class:      SourceClass,
                  issuer:     text,            // "Ministry of Health", "Dr. Levy", "self"
                  reference:  text,            // e.g. guideline document + section
                  ingested_at }

tier_of(class: SourceClass) -> ConfidenceTier   // the ONLY place tiers are assigned
```

The tier is a **function of the source's class**, computed by Sources and never stored as an
independent, editable field anywhere else. Anything downstream that shows a tier derives it
through the source — so a citation's tier can never drift from its source (exit criterion 4).

Every source class has one ingest adapter behind a single interface:

```
SourceAdapter.ingest(raw) -> (Source, list[ReportedItemDraft] | list[PathwayDefinition])
```

A guideline adapter yields pathway definitions for the Rails library; the reported-item adapters
(doctor instruction, prescription, self-report) yield reported drafts for the File. **Adding a new
source type = one change in Sources**: a new `SourceClass` variant, its tier, and its adapter.
Rails, File, Ledger, and Accounts see only the generic `Source` / `ReportedItem` /
`PathwayDefinition` types and are untouched (exit criterion 5).

### 1.3 The reported side — the File (owned by **File**)

```
ClinicalCode    { system: CodeSystem, code: text }        // ⊕ CodeSystem: {LOINC, ATC, Local}

ReportedItem    { item_id:      ItemId,
                  subject_id:   SubjectId,
                  kind:         ⊕{ Result, DoctorInstruction, Prescription, Demographic },
                  code:         ClinicalCode,
                  content:      verbatim payload (value/text as stated by the source),
                  observed_at:  date,
                  source_id:    SourceId,        // REQUIRED — no orphan facts
                  opens_process: bool }          // stated BY the source (an instruction says
                                                 // "follow up"; a lab report marks abnormal) —
                                                 // never computed by us
```

The File is **append-only** (corrections are superseding entries, not edits). Two rules are
enforced by its constructor, not by convention:

1. A `ReportedItem` cannot exist without a `source_id` — the reported side is itself provenanced.
2. `content` is stored **verbatim**; the File has no API that synthesizes, summarizes, or derives
   a medical fact. "Age" is not stored — a reported date of birth is, and consumers compute
   elapsed time from it (arithmetic on a reported fact, not inference of a medical state).

`opens_process` deserves emphasis: whether something is an "open process" is a statement made by
the **source** (the doctor wrote "requires follow-up"; the lab flagged the value), carried through
ingestion. The system never decides that a value is abnormal — that would be inferring state.

### 1.4 The expected side — pathway rails (owned by **Rails**)

Pathways are **data, not code**. One generic engine interprets them all.

```
PathwayDefinition { pathway_id:    PathwayId,
                    source_id:     SourceId,          // the guideline that defines this rail
                    applicability: Predicate,         // declarative, over reported facts only
                    steps:         list[StepTemplate] }

StepTemplate      { step_key:      StepKey,
                    satisfied_by:  Matcher,           // kind + ClinicalCode (+ value constraints)
                    due:           ScheduleRule }     // e.g. "every 24 months from age 50",
                                                      // "at ages 2,4,6,12 months from DOB"

ExpectedItem      { subject_id, pathway_id, step_key,
                    due_window:   DateWindow,
                    source_id:    SourceId }          // inherited from the definition — an
                                                      // expected item is born citing its source
```

- `Predicate` is a small closed expression language (`fact(code) exists`, comparisons on reported
  values/dates, and/or/not). The interpreter's **only readable namespace is the subject's reported
  facts**; it has no escape hatch to arbitrary code and no write path. If a fact a predicate needs
  is absent, the rail simply does not fire — absence is never guessed at. This is how "the system
  never infers state" is enforced on the expected side: the *guideline* states its own condition
  ("women 50–74"), and the engine merely evaluates that stated condition against stated facts.
- `ExpectedItem` is **derived, not stored**: computed on read from (definitions × file). The MVP
  needs no scheduler, no materialization, no cache-invalidation story. (Assumption: read volume at
  MVP scale makes recomputation trivially cheap; materializing is a later, one-owner optimization
  inside Rails.)

**Adding a new pathway = adding one `PathwayDefinition` record** (typically emitted by the
guideline adapter). Nothing else changes anywhere (exit criterion 5).

### 1.5 The output — ledger & citations (owned by **Ledger**)

```
Citation      { source:   SourceExcerpt,     // id, class, tier (derived), issuer, verbatim quote
                reported: ReportedExcerpt }  // the item id(s) and verbatim facts joined against
              // BOTH fields required & non-null. Constructor SEALED inside Ledger (§3).

GapKind       ⊕{ Done, Due, Overdue, NoPlan }

LedgerEntry   { subject_id: SubjectId,
                kind:       GapKind,
                citation:   Citation,
                due_window: DateWindow? }    // absent for NoPlan

LedgerView    { subject_id, as_of: date, entries: list[LedgerEntry] }
```

Note what `LedgerEntry` does **not** have: a free-text message field. The human-readable sentence
("Colonoscopy due — per MoH screening guideline §4, given your reported age") is rendered by the
presentation layer from a **closed template set keyed by `GapKind`**, filled only with the
citation's verbatim excerpts. `NoPlan` renders as the fixed nudge template — *"You have an open
process (‹reported item›) with no plan on file. Ask your doctor."* — never as a suggested course
of action. The system cannot say anything it has no field to say it in.

---

## 2. Module structure & boundaries

| Module | One-sentence responsibility (its single reason to change) | Owns |
|---|---|---|
| **Accounts** | Who may act for whom | `Manager`, `Subject`, `Grant`, `AccessGrant` mint |
| **Sources** | What counts as authoritative, and how much | `Source`, `SourceClass`, tier mapping, ingest adapters |
| **File** | What has been *reported* about a subject | `ReportedItem`, append-only log |
| **Rails** | What a guideline says should happen, as data | `PathwayDefinition`, predicate/schedule engine, `ExpectedItem` |
| **Ledger** | The join of expected × reported, spoken only in citations | `Citation` (sealed), `LedgerEntry`, `LedgerView`, gap computation |
| **API** | Transport | routes, serialization of the vocabulary |

Boundary rules:

- Every File and Ledger read/write takes an `AccessGrant` parameter. The token is mintable only by
  `Accounts.authorize(manager_id, subject_id, action)`, so **no path touches subject data without
  passing through Accounts** — authorization is a required argument, not a middleware convention.
- Modules expose *decisions*, not internals (Tell, Don't Ask): API asks
  `Ledger.view(grant, as_of)`, never "give me the expected items and the file so I can join them
  myself." The join lives in exactly one place.
- Each module has its own repository; the relational schema is private to it. No ORM entity,
  row type, or storage exception crosses a seam — errors are re-raised as the vocabulary's own
  error types (§6).

---

## 3. Ownership & structural enforcement of the non-advice invariant

The invariant — *every output is a `Citation = (authoritative source × reported state)`; the
system never infers state and never originates advice* — is owned by the **Ledger**, and enforced
by four structural facts rather than by review discipline:

1. **One mint.** `Citation` is declared in the shared vocabulary as an *opaque* type; its
   constructor is sealed (package-private / internal) to the Ledger module, callable only from the
   join function. Nothing else in the codebase — including the API layer and including any future
   feature — can fabricate a citation. Auditing "is the rule safe?" means reading one function.
2. **The mint's inputs already carry both halves.** The join consumes `ExpectedItem`s (which are
   born with the guideline's `source_id`, §1.4) and `ReportedItem`s (which cannot exist without a
   `source_id`, §1.3). The constructor requires both a `SourceExcerpt` and a `ReportedExcerpt`,
   non-null. A citation missing either half is unrepresentable, not merely forbidden.
3. **One output path.** The API's read surface returns `LedgerView` and nothing else; there is no
   second endpoint family that could emit medical content. Since `LedgerView` is (structurally)
   a list of citations plus enum tags, every output *is* a citation by type, not by testing.
4. **No inference anywhere upstream.**
   - The File stores verbatim reported content and has no derivation API (§1.3);
     "open process" is a source-stated flag, not a computed judgment.
   - The Rails predicate interpreter reads only reported facts and evaluates only the guideline's
     own stated conditions (§1.4); it cannot synthesize a fact or fire on a guessed one.
   - The Ledger's matcher (`satisfied_by`) is declarative equality/window matching — it decides
     *whether a reported item matches an expected template*, which is bookkeeping, not diagnosis.
   - Free prose exists nowhere in the output schema; presentation templates are a closed,
     `GapKind`-keyed set whose only variable content is verbatim excerpts.

This holds identically for a doctor user: a doctor is just a Manager; a doctor's *instruction*
enters the system as a Source through ingestion like any other, and even the doctor's own screen
is rendered from citations. There is no privileged path.

**The nudge, precisely.** A `NoPlan` entry is produced when a reported item with
`opens_process = true` has (a) no rail whose applicability fires and covers it, and (b) no
subsequent `DoctorInstruction` item matching it. Its citation is
*(the source of the opening item × the opening item itself)* — a real source and a real reported
state, no invention. The "ask your doctor" text is the fixed template for `GapKind.NoPlan`; the
system recommends contact with a clinician, never a course of action.

---

## 4. The `manager → subject(s)` primitive

Covered structurally in §1.1; the design commitments, stated as such:

- **One abstraction, zero special cases.** Self-management, family, and a doctor's (a group) are the
  same three rows (`Manager`, `Subject`, `Grant`) with different cardinalities. There is no
  `FamilyAccount`, no `Clinic(a group)`, no per-role code path. "List my subjects" is one query for
  every kind of manager.
- **Subjects are not accounts.** A Subject has no credentials and no medical fields; a child or a
  patient exists as a Subject before (or without) ever being a Manager. A subject who later signs
  up becomes a Manager holding a `Self` grant to their existing Subject — no migration.
- **Authorization is a value, not a vibe.** The `AccessGrant` capability token (§2) is how the
  primitive is *enforced* rather than merely modeled: File and Ledger cannot be called without
  one, and only Accounts can make one.

---

## 5. The expected-vs-done join

The Ledger's entire algorithm, in one screen — this is the whole of "computed by joining, not
enumerated per example":

```
view(grant: AccessGrant, as_of: date) -> LedgerView:
    reported  = File.items(grant)                       # the reported/done side
    expected  = Rails.expected_items(reported, as_of)   # rails whose predicates fire on
                                                        # reported facts → schedule expansion
    entries = []
    for e in expected:
        match = first reported item satisfying e.satisfied_by within e.due_window
        entries += LedgerEntry(
            kind     = Done | Due | Overdue        # by match + window vs. as_of
            citation = mint(source_of(e), match if match else facts_that_fired(e)))
            # Done: guideline × the satisfying reported item
            # Due/Overdue: guideline × the reported facts that made the rail applicable
    for open in reported where opens_process and not covered(open, expected, reported):
        entries += LedgerEntry(kind = NoPlan,
                               citation = mint(source_of(open), open))
    return LedgerView(subject, as_of, entries)
```

Properties this shape guarantees:

- **Expected and reported never mix at rest.** Rails knows nothing about what was done; File
  knows nothing about what is expected. They meet only inside this function, at read time
  (exit criterion 3).
- **Provenance is conserved, not attached.** Both inputs arrive already carrying `source_id`s;
  the mint *copies* provenance through, it never assigns it. Tier is derived from the source at
  excerpt time via `Sources.tier_of` — one owner, no drift (exit criterion 4).
- **Every branch ends in `mint(...)`** — there is no arm of the computation that yields output
  without a source and a reported state in hand.
- Pure function of (definitions, file, date): trivially testable, idempotent, no stored derived
  state to invalidate.

(Assumption: the MVP surfaces gaps when a ledger is read — pull, not push. Proactive delivery of
nudges is a thin post-MVP notifier that consumes `LedgerView` like any other client; it adds no
new output path and cannot weaken the invariant.)

---

## 6. Day-zero vocabulary — what the public seams may speak

The published language, decided normatively now. A public seam (API ↔ Ledger, Ledger ↔
Rails/File, anything ↔ Sources/Accounts) may carry **only**:

**Domain types (this document, closed set):**
`ManagerId`, `SubjectId`, `SourceId`, `ItemId`, `PathwayId`, `StepKey` (opaque id types — never
bare strings), `AccessGrant` (opaque), `SourceClass`, `ConfidenceTier`, `ClinicalCode`,
`ReportedItem` / `ReportedItemDraft`, `PathwayDefinition` (with `Predicate`, `StepTemplate`,
`Matcher`, `ScheduleRule`), `ExpectedItem`, `Citation` (opaque — constructible only in Ledger),
`GapKind`, `LedgerEntry`, `LedgerView`, `DateWindow`.

**Foundational primitives:** ISO dates/datetimes, booleans, integers/decimals, UTF-8 text *inside*
the domain types above, JSON as the wire encoding at the API edge. Nothing else is foundational —
no ORM, HTTP-framework, or vendor type is ever a parameter or return at a seam.

**Error vocabulary** (one type per distinct handling, no decorative hierarchy):
- `NotAuthorized` — Accounts declined; caller re-authenticates or stops.
- `NotFound` — an id names nothing visible to this grant.
- `RejectedItem(reason)` — an ingest/report draft violated a structural rule (e.g. missing
  source); caller can fix and resubmit.
- `InvalidPathway(reason)` — a rail definition failed validation at library load; the library
  owner fixes the data.

Implementation exceptions (DB errors, parser crashes) are translated to these at the seam or, if
unactionable and process-fatal, allowed to fall.

Closed enums (`SourceClass`, `ConfidenceTier`, `GapKind`, `CodeSystem`, item `kind`) are part of
the vocabulary: extending one is a deliberate, versioned vocabulary change with a single owner
(Sources for the first two, Ledger for `GapKind`), never an ad-hoc string.

---

## 7. Explicitly out of the MVP

Not designed for, and no hooks left "just in case" (hooks are speculation; the one-owner change
paths in §1.2/§1.4 are the extension story):

- **The integrated overview (המכלול)** — Pillar 2 entirely; no aggregate-view schema, no
  cross-process summarization.
- **Any inference:** risk scoring, abnormality detection, suspicion generation, "smart" reminders
  derived from patterns. Structurally excluded, not just deferred (§3.4).
- **Interop standards:** FHIR/HL7 ingestion, EMR integration, document OCR/photo parsing. The
  `SourceAdapter` seam is where they would land later; none is built now.
- **Push infrastructure:** schedulers, notification channels, escalation. Nudges exist as ledger
  rows; delivery is a future consumer of `LedgerView`.
- **Differentiated permissions per relation** (read-only family member, delegated clinician
  scopes), consent workflows, subject-approves-manager flows — `Grant.relation` is a label only.
- **Clinician write-back / messaging** between doctor-managers and patient-subjects.
- **Materialized expected items, caching, multi-tenant sharding** — computed-on-read is the MVP.
- **Localization framework** beyond the closed template set; **audit/analytics** beyond the
  File's inherent append-only history.

---

## 8. Assumptions register

1. Single relational database, module-private schemas; MVP scale makes on-read ledger computation
   cheap.
2. Guidelines arrive through a curation step (a human loads/approves a `PathwayDefinition`); the
   MVP does not scrape or auto-parse guideline prose.
3. `opens_process` is determinable from source content at ingestion (instructions and flagged
   results state it); where a source doesn't state it, the item simply never triggers a `NoPlan`
   nudge — under-nudging is accepted over inferring.
4. Time zones and calendar arithmetic use the subject's reported locale defaults; edge cases are a
   Rails-internal concern.
5. The presentation template set ships in the product's languages; templates are copy, not logic,
   and adding a language touches only presentation.
