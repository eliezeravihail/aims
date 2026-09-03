# "Responsible doctor" MVP — architecture (extensibility-first)

*Design bias declared up front: this shape is optimised so that adding a **new medical pathway** or a
**new source type** later is a single, local change. The seams that absorb that growth are built now;
nothing behind those seams that the MVP does not need is built now.*

---

## 0. One-paragraph shape

The system is two stores and one pure join. The **expected side** is a library of declarative **Rails**
(pathways) — every Rail is a transcription of one authoritative **Source** and can only *point at* that
source. The **reported side** is an append-only log of **Reports** — facts, results, events, instructions,
prescriptions, open processes — each stamped with who reported it and how well attested it is. The
**Ledger** is a pure function `(Rails, Reports) → LedgerEntries`, and every entry, gap and nudge it produces
is wrapped in a **Citation** whose constructor is the only place in the codebase that can produce output, and
which can only be built from a `SourceRef` × `ReportRef[]`. Accounts are a single edge, **Custody:
manager → subject**, and self-care, family care and a doctor's panel are the same edge with different
roles. New pathways are new Rail files; new source types are new **Source Adapters** that map raw input
onto a *closed* six-kind Report grammar — so neither touches the ledger, the account model, or the output
layer.

---

## 1. Data model

All identifiers are opaque. Codes are written `system:code` (e.g. `loinc:2093-3`, `local:well-baby-visit-6m`) —
the model is coding-system-agnostic by construction; the MVP ships a `local:` system and accepts LOINC/ICD
codes verbatim where a guideline or lab document provides them.

### 1.1 Accounts and custody (the single account primitive)

```
Account   { id, login identity, displayName }
Subject   { id, displayName, createdByAccountId }
Custody   { managerAccountId, subjectId,
            role:  self | guardian | clinician,
            scope: { read, report, rails }        -- what this manager may do on this file
            grantedByAccountId, since, until? }
```

* A **Subject** is a person with a medical tracking file. A Subject is *not* an Account; it has no login.
* **Custody** is the only relationship between an Account and a Subject. On sign-up, the system creates
  the account, a Subject for the same person, and a `Custody{role: self}` edge. A parent adding a child adds
  a Subject and a `Custody{role: guardian}` edge. A doctor adding a patient adds (or is granted, by an
  existing custodian) a `Custody{role: clinician}` edge. **Same table, same code path, same API.**
* A Subject may have many custodians (parent *and* doctor). A manager may have many subjects. Both are just
  rows on the edge; there is no "family" or "panel" object.
* `role` does one further job: it fixes the strongest **attestation** a manager can stamp on a Report they
  enter (see 1.3). A clinician custodian can enter a `clinician-entered` report; a guardian cannot.

### 1.2 Sources (the authoritative side's currency)

```
Source   { id, kind: SourceKind, tier: Tier, title, publisher, version,
           uri?, effectiveFrom, retiredAt?,
           backedByReportId?    -- set when the source *is* a reported instruction/prescription
           subjectId?           -- null for public sources; set for personal sources }
```

* A Source is immutable once created. A new guideline version is a new Source row; Rails pin a version.
* **Public** sources (`subjectId = null`) are loaded from rail packs. **Personal** sources (`subjectId` set)
  are created by intake when a manager reports a doctor instruction or a prescription — the Report is the
  evidence, the Source is the citable authority derived from it, and the two are linked both ways.
* `SourceKind` at day zero: `guideline.public`, `instruction.clinician`, `prescription`. Each kind is owned by
  exactly one Source Adapter (§2.3).

### 1.3 Reports (the reported side — the *only* truth about the subject)

```
Report   { id, subjectId, kind: ReportKind, code, value?, unit?,
           occurredAt, reportedAt, reporterAccountId,
           attestation: self-stated | document-attached | clinician-entered,
           attachmentRef?, sourceKind?,          -- which adapter produced it
           supersedesReportId?,                  -- corrections are new rows, never edits
           process?: { key, action: opens | closes | plansFor } }
```

Report **kinds** are a **closed grammar of six**. This is the load-bearing extensibility decision: every
present and future source type must express what it knows as one of these six, so the ledger never learns
about source types.

| kind | meaning | example |
|---|---|---|
| `fact` | a standing attribute the subject/manager states | date of birth, sex, a doctor-stated risk flag |
| `result` | a measured/observed outcome | HbA1c value, mammography performed with report |
| `event` | "this was done" without a value | 6-month well-baby visit attended |
| `instruction` | a clinician told the subject to do X (by when / how often) | "repeat lipid panel in 3 months" |
| `prescription` | a dispensed/ordered medication or order | metformin 500 mg, 90 days |
| `process` | an open or closed matter the subject is in | referral to cardiology (open), closed on visit |

* Reports are **append-only**. Corrections supersede; nothing is deleted or edited. Recomputing history is
  therefore always possible.
* `attestation` is set by intake from `(custody.role, attachment present?)`, never chosen freely by the UI.
* `instruction` and `prescription` reports are dual-natured: intake stores the Report *and* asks the matching
  Source Adapter to mint a personal Source + a personal Rail from it (§2.3). The subject's state still says
  only "the doctor instructed X" — the system did not decide anything.

### 1.4 Rails (the expected side — declarative pathways)

A Rail is a data file, validated against a schema, never code.

```
Rail       { id, version, sourceId, sourceVersion,
             scope: global | subject:<id>,
             applicability: Predicate,             -- over reported facts only
             milestones: Milestone[] }
Milestone  { key, label, code,
             schedule:    ScheduleRule,             -- when it is expected
             satisfiedBy: Matcher,                  -- which reports count as done
             locator:     { section?, page?, quote },   -- where in the source this milestone is stated
             graceDays? }
Predicate  := all/any/not over atoms:  fact(key) op literal      -- closed atom set, §6
ScheduleRule := atAge{from,to} | every{interval, from: birth | event(code) | enrollment}
              | after{event: code, within} | once | byDate{date}
Matcher    := { kind: ReportKind, code | codeIn[], withinWindow: true|false, valueConstraint? }
```

* `applicability` reads only `fact` reports (and closed derived projections of them, §3.3). It is how a
  guideline's own eligibility criteria ("women aged 50–74") are applied to a subject's *reported* age and sex.
* Each Milestone must carry a `locator` into its Source. The validator rejects a rail whose milestones are not
  anchored — a rail author cannot add an expectation the source does not state.
* Public rails live in `pathways/library/<source>/<rail>.rail.yaml`. Personal rails (from instructions and
  prescriptions) are generated rows in the same shape with `scope: subject:<id>`; the ledger does not
  distinguish them.

### 1.5 Derived objects (never stored as truth; recomputed from 1.2–1.4)

```
Expectation { subjectId, railId, railVersion, milestoneKey, occurrence,
              window: { from, to }, appliesBecause: ReportId[] }
LedgerEntry { expectation, matchedReports: ReportId[],
              status: done | upcoming | due | overdue | no_plan | superseded,
              citation: Citation }
Citation    { source: SourceRef, locator, state: ReportRef[],      -- state may be empty: "nothing reported"
              tier: Tier, attestation: Attestation | none, rail?: RailRef, computedAt }
```

A **Gap** is a `LedgerEntry` with status `due | overdue | no_plan`. A **Nudge** is a Gap with status
`no_plan`. Neither is a separate type — they are ledger entries, so they cannot exist without a citation.

---

## 2. Modules and boundaries

```
accounts/    Account, Subject, Custody. Authorisation = "is there a Custody edge with this scope?".
intake/      The ONLY writer of Reports and personal Sources/Rails. Receives a raw item from a manager,
             picks the Source Adapter by declared kind, stores what the adapter returns.
sources/     SourceType registry + one adapter per SourceKind:
               sources/guideline_public/   (loads rail packs: Source + Rails)
               sources/instruction/        (Report → Source + personal Rail)
               sources/prescription/       (Report → Source + personal Rail)
pathways/    Rail schema + validator + rail engine (applicability → expectations). Holds the rail library.
state/       Report store (append-only) + the closed Projection list (e.g. age from DOB).
ledger/      Pure join: (Rails, SubjectState) → LedgerEntry[]. Matchers, windows, process/no-plan rule.
citation/    The sealed Citation type and its single constructor (the gate). Depends on nothing but ids.
api/         Read: ledger per subject(s) under a manager; rail library browse. Write: intake.
             Its response schema is generated from citation/ types. It cannot import state/ or pathways/.
```

Allowed dependency direction (enforced by a module-boundary lint in CI):

```
api → { accounts, intake, ledger(read-only), citation }
ledger → { pathways, state, citation }
intake → { sources, state(write), pathways(write personal rails), accounts }
sources/* → { state types, pathways schema, citation.Tier }
citation → { nothing }
```

### 2.1 What lives where — the ownership table (exit criterion 5)

| Change | Files touched | Owner |
|---|---|---|
| Add a new public pathway under an existing guideline | `pathways/library/<source>/<new>.rail.yaml` | pathways |
| Add a new public guideline (new Source, same kind) | one rail pack: `source.yaml` + rail files | pathways |
| Add a new **source type** (e.g. a lab-portal export) | `sources/<new_adapter>/` + one registry line | sources |
| Add a new schedule-rule or matcher shape | `pathways/schema` + rail engine | pathways |
| Add a new derived projection (e.g. gestational age) | `state/projections` (closed list, one entry) | state |
| Add a new custody role | `accounts/` (and the attestation table in intake) | accounts |

The ledger, the account model, the citation gate and the API do not appear in the first three rows. That is
the extensibility claim, and it holds because of the two contracts in §2.2–2.3.

### 2.2 The Rail contract (how pathways plug in)

A rail pack is `source.yaml` (one Source record: title, publisher, version, uri, tier) plus N rail files. The
loader validates every rail against the schema, checks every milestone has a `locator`, checks every
`applicability` atom is in the closed atom vocabulary (§6), and rejects the pack otherwise. Loading a pack
creates one Source row and N Rail rows; nothing else changes. The rail engine is generic over the schema;
it has no knowledge of any specific guideline.

### 2.3 The Source Adapter contract (how source types plug in)

```
SourceAdapter {
  kind: SourceKind
  accepts(rawItem) -> bool
  ingest(rawItem, ctx{subjectId, custodyRole, attachment?}) ->
        { reports: Report[],  sources: Source[],  rails: Rail[] }     -- any may be empty
  tierOf(source) -> Tier
  snippet(source, locator) -> QuotedText          -- the only text the output layer may show for a source
}
```

* An adapter may only emit the six Report kinds, Sources of its own kind, and Rails that validate. It cannot
  reach the ledger or the API. It cannot construct a Citation (the constructor is not exported to it).
* MVP ships three adapters because the brief requires three source classes. The registry is a map; the
  fourth adapter is one folder. That is the seam — the fourth adapter is **not** built.

---

## 3. The non-advice invariant: ownership and structural enforcement

**Statement.** Every system output is a `Citation = Source × ReportedState`. The system never infers state
and never originates advice, for every user including a clinician.

**Owner:** the `citation/` module. It is the only module that may construct a `Citation`, and `Citation` is
the only leaf type the `api/` layer can return.

### 3.1 Four structural locks

1. **Sealed output type.** `Citation` has a private constructor. The single exported factory is
   `cite(source: SourceRef, state: ReportRef[], locator, rail?)`. Both arguments are typed references that
   must resolve to persisted rows; there is no string field on `Citation`. A module that wants to "say"
   something must point at a source row and at report rows — there is nothing else to say with.
2. **Closed status enum, no free text.** `LedgerEntry.status` is a six-value enum. The user-facing sentence
   for each status is a fixed template in the output layer (`"<source> expects <milestone> in <window>;
   nothing reported"`, `"…; ask your doctor about <process>"`), parameterised only by the citation. Nobody
   writes a sentence per case. The nudge's wording is therefore the *same fixed template* for every no-plan
   gap, and it is a citation of the report that opened the process.
3. **Single writer of state, pure reader of state.** Only `intake/` writes Reports, and only from a manager's
   submission via an adapter. `ledger/` is a pure function with read-only access; it has no store handle. Its
   verdicts are computed solely from *presence or absence of matching reports inside a window*. The vocabulary
   makes this visible: the ledger never says "not done" — it says `due`/`overdue` with `state: []`, rendered
   as "nothing reported".
4. **Rails cannot compute.** A rail is data, validated at load, and every milestone is anchored to a
   source locator. Applicability atoms read only `fact` reports and closed projections. A rail author can
   transcribe a guideline; they cannot embed a judgement the guideline does not state.

### 3.2 Derivation vs inference (stated assumption)

Age from a reported date of birth, "is within window", "3 months after the instruction date" — these are
**derivations**: deterministic, lossless arithmetic on reported facts, and each derived value carries the ids
of the reports it was derived from (`appliesBecause`). **Inference** — producing a medical state nobody
reported (e.g. "this value is abnormal", "this person is high-risk") — has no place to live: projections are
a closed, reviewed list of pure arithmetic in `state/projections`, and rail atoms cannot reference anything
outside `fact` + projections. If a guideline's criterion needs a state (e.g. "high risk"), it must arrive as a
`fact` report stated by the manager or clinician — the ledger will then cite *that report*.

### 3.3 The clinician user is not special

A doctor is an Account with `Custody{role: clinician}` edges. When they enter an instruction, intake stores a
`Report{kind: instruction, attestation: clinician-entered}` and the instruction adapter mints a personal
Source + Rail. From that moment the system cites *the doctor*; it never speaks in its own voice, and the
doctor never gets an output that is not a citation of a source against a report. The role changes the
attestation stamp and the tier of the resulting source — nothing else.

### 3.4 Verification hooks (structural, cheap)

* A dependency lint: `api/` may not import `state/` or `pathways/`; nothing but `citation/` may name the
  `Citation` constructor.
* A contract test walks every API response schema and asserts every leaf object is a `Citation` or is a
  container of them.
* A property test: for any random set of rails and reports, every `LedgerEntry.citation.source` resolves and
  every `state` id resolves to a Report of that subject.

---

## 4. The join: expected vs done ledger

Pure pipeline, recomputed per subject on read (cached by `(reportsVersion, railsVersion)`):

```
1. enroll     : for each Rail in scope (global ∪ subject-personal), evaluate applicability over
                SubjectState.facts → Enrollment{ railId, appliesBecause: ReportId[] }
2. expand     : for each enrolled rail, instantiate milestones by schedule rule → Expectation[]
                (windows computed from DOB / event dates / instruction dates, each with appliesBecause)
3. match      : for each Expectation, find Reports satisfying its Matcher inside (or, if allowed, outside)
                its window → matchedReports
4. status     : done if matched; else upcoming / due / overdue by clock vs window; superseded if the
                rail version is retired and a newer rail's expectation covers the same milestone
5. processes  : for each open `process` (opened, not closed) with no `plansFor` instruction and no personal
                rail attached → LedgerEntry{status: no_plan, citation: cite(source of opening report, [])}
6. cite       : every entry gets cite(rail.source, matchedReports ∪ appliesBecause, milestone.locator, rail)
                with tier = adapter.tierOf(source) and attestation = weakest of the cited reports
```

* Step 5 is the *only* rule about "open process with no plan", and it is the same rule for every source
  type. A process is open only because a Report says so (a referral, a clinician's "follow up", a manager's
  explicit "open matter"); the system does not decide something is open.
* Public and personal rails go through the identical pipeline. A doctor's "repeat in 3 months" is a
  one-milestone rail with `schedule: after{event: instruction, within: 3 months}` — no special case.
* Multi-subject views (family, panel) are `for subject in custodies(manager): ledger(subject)` — the
  account model contributes nothing but the subject list.

### 4.1 Confidence tiers (by source) and attestation (by state)

| Tier | Source |
|---|---|
| T1 | Published public guideline, versioned, with URI |
| T2 | Clinician instruction / prescription backed by an attached document |
| T3 | Clinician instruction entered directly by a `clinician` custodian, no document |
| T4 | Instruction / prescription transcribed by self or guardian, no document |

`tierOf` is owned by each Source Adapter. Attestation (`clinician-entered > document-attached > self-stated`)
is owned by intake. A Citation carries both, separately, so a T1 expectation matched by a self-stated event is
displayed as exactly that. No blended score is computed — blending would be an inference about credibility.

---

## 5. The `manager → subject(s)` primitive in use

| Scenario | Rows |
|---|---|
| Person tracking themselves | `Custody{A, S_A, self}` |
| Parent tracking two children | `Custody{A, S_child1, guardian}`, `Custody{A, S_child2, guardian}` |
| Doctor with a panel of patients | `Custody{D, S_i, clinician}` for each i |
| Child with a parent and a doctor | two Custody rows on the same subject |
| Grown child takes over own file | new `Custody{C, S_child, self}`; parent's edge gets `until` |

Authorisation is one query: *does a live Custody edge exist with the required scope?* Every API call is
`(managerAccount, subjectId, …)`; there are no manager-less or subject-less calls. Listing "my subjects" is
listing edges. Nothing in `intake/`, `ledger/` or `api/` branches on role except intake's attestation stamp.

---

## 6. Day-zero vocabulary the public seams may speak

These are the *only* enumerations that cross a module boundary or the API. Everything else is `system:code`.

* **ReportKind** — `fact | result | event | instruction | prescription | process`
* **Attestation** — `self-stated | document-attached | clinician-entered`
* **CustodyRole** — `self | guardian | clinician`;  **CustodyScope** — `read | report | rails`
* **SourceKind** — `guideline.public | instruction.clinician | prescription`
* **Tier** — `T1 | T2 | T3 | T4`
* **LedgerStatus** — `done | upcoming | due | overdue | no_plan | superseded`
* **ScheduleRule kinds** — `atAge | every | after | once | byDate`
* **Predicate atoms** — `fact(sex)`, `fact(dob)`, `fact(flag:<system:code>)`, `age` (projection),
  with operators `= ≠ < ≤ > ≥ in`
* **Projections (closed)** — `age(dob, asOf)`; nothing else at day zero
* **Process actions** — `opens | closes | plansFor`
* **Reserved fact keys** — `dob`, `sex`, `flag:*`

Adding to any list above is a versioned change in its owning module (table in §2.1). Codes never need
this — a new lab test, a new visit type, a new milestone is just a new `system:code`.

### 6.1 API surface (shape only)

```
POST /subjects                                  -> Subject + Custody{self|guardian}
POST /subjects/{s}/custody                      -> grant edge (clinician, guardian)
POST /subjects/{s}/reports                       -> intake: {kind, code, value?, occurredAt, attachment?, process?}
GET  /subjects/{s}/ledger?asOf=                  -> LedgerEntry[]        (each carries Citation)
GET  /subjects/{s}/ledger/gaps                   -> LedgerEntry[] filtered to due|overdue|no_plan
GET  /me/subjects                                -> Custody edges
GET  /rails?applicableTo={s}                     -> Rail summaries with Source (browse the library)
```

---

## 7. Explicitly out of the MVP

* The integrated overview (*המכלול*) — no cross-subject or cross-pathway synthesis object exists.
* Any inference-based output: suspicion flags, risk scoring, "abnormal" detection, credibility blending.
* Automated document understanding (OCR/NLP of lab PDFs). Attachments are stored and cited; values are
  entered by the manager.
* External integrations: EHR/FHIR, lab portals, pharmacy feeds, HMO APIs. The adapter contract is the seam;
  no adapter beyond the three required is built.
* Notification channels (push/email/SMS scheduling). The ledger exposes gaps; delivery is not designed.
* Rail authoring UI; rails are files reviewed in version control. Rail translation/localisation tooling.
* Medication adherence, interactions, dosing — prescriptions are tracked only as "expected refill / expected
  follow-up" milestones the prescription itself states.
* Regulatory audit export, consent workflows beyond the Custody edge, subject-facing (non-manager) logins.
* Multi-tenant clinic administration (departments, delegation trees) — a doctor is one Account with edges.

---

## 8. Assumptions stated

* The delivery surface is a web service with a thin client; nothing above depends on it.
* Guideline transcription into rails is a human, reviewed act; the system trusts the rail pack's locators.
* "Open process" is declared by reports, never detected. MVP UI lets a manager mark an instruction/referral
  as opening a process; a closing report is likewise explicit.
* Clocks: `asOf` is a request parameter defaulting to now, so the ledger is reproducible for any date.
* Hebrew/English: labels and templates are localisable strings keyed by status/milestone; source snippets are
  quoted in the source's language.
