# "Responsible Doctor" MVP — Architecture

*Design stance. The dominant risk in this product is structural drift: an advice-shaped sentence
leaking out of an unguarded path, an inferred state sneaking into the file, or a "family vs.
patients" special case metastasizing. The design therefore makes every load-bearing rule
**unforgeable by construction** — the types and seams give you no way to express the forbidden
program — while keeping the moving parts minimal: five modules plus one shared kernel, one output
choke point, one closed seam vocabulary, and a dependency footprint of a relational database plus a
thin HTTP layer. Every seam type is calibrated from both ends: complete for its consumers, no more
specific than every producer can honestly supply. Every abstraction present is justified by a force
stated in the brief; anything without such a force was cut.*

---

## 1. System shape at a glance

```
                ┌─────────────────────────────────────────────────┐
                │                    Surface                      │  thin HTTP/UI; owns zero rules
                └────┬──────────────┬──────────────────┬──────────┘
                     │ authorize    │ report (write)   │ view (READ — the only subject-output path)
                     ▼              ▼                  ▼
              ┌───────────┐  ┌─────────────┐  ┌─────────────────────────────┐
              │ Accounts  │  │   Record    │◄─│           Ledger            │
              │ Grant +   │  │ reported    │  │ join(expected, reported)    │
              │ Subject-  │  │ state, its  │  │ sole mint of Citation and   │
              │ Handle    │  │ sources,    │  │ LedgerEntry                 │
              └───────────┘  │ evaluate()  │  └──────────────┬──────────────┘
                             └─────────────┘                 │
                                    ▲                        ▼
                                    │            ┌───────────────────────┐
                                    └────────────│         Rails         │
                                                 │ declarative pathway   │
                                                 │ library (data, typed) │
                                                 └───────────────────────┘

                ┌─────────────────────────────────────────────────┐
                │        vocabulary (shared kernel, closed)       │  everything depends on it;
                └─────────────────────────────────────────────────┘  it depends on nothing
```

The asymmetry is the enforcement: `Surface` may *write* through `Accounts` and `Record`, but may
*read subject output* only through `Ledger.view`. Rails and Record export their query seams **to
the Ledger only**. An auditor answering "can this system emit advice?" checks one function's return
type.

**Dependency diet (day-zero, closed):** one relational database (SQLite for MVP, Postgres-compatible
SQL), one thin HTTP framework, the language stdlib, and one schema-validation step for pathway data
files at load time. No ORM beyond a row mapper, no rules engine, no workflow engine, no queue, no
vendor SDK. Nothing from this list may appear in a public seam type (§8). Contexts are module
boundaries inside a single deployable, not network boundaries; the seams are what would become
service boundaries later, but that split is not designed now.

---

## 2. Shared kernel: `vocabulary`

The one module every other module may depend on. Deliberately tiny and **closed at day zero**;
extending it is a reviewed design decision, not a convenience. Value types with their own
validation only — no I/O, no services.

| Type | Definition | Rules it owns |
|---|---|---|
| `PrincipalId`, `SubjectId` | opaque nominal ids (never bare strings) | format-checked once at construction |
| `ActivityCode` | a code from the **closed, versioned MVP activity registry** (e.g. `COLONOSCOPY`, `HBA1C_TEST`, `INFANT_VACCINE_MMR`) | in-registry; constructed only via `ActivityCode.parse` |
| `RiskFlagCode` | closed, versioned registry of declarable risk flags | same governance as `ActivityCode` |
| `SourceKind` | closed enum: `PUBLIC_GUIDELINE` \| `DOCTOR_INSTRUCTION` \| `PRESCRIPTION` | closed |
| `ConfidenceTier` | ordered enum: `DIRECTED` > `GUIDELINE` | total mapping `ConfidenceTier.of(kind)` exists in exactly one function: prescription, doctor_instruction → `DIRECTED`; public_guideline → `GUIDELINE` |
| `SourceRef` | `(source_id, SourceKind, tier, label: LangText.quoted)` | **no tier parameter exists** — the factory computes tier via `ConfidenceTier.of` internally, so tier and provenance are one value, never split; factory invocable only by `Record` and `Rails` (the two modules that register authorities) |
| `ReportRef` | `(report_id, SubjectId)` | — |
| `DateWindow` | `[not_before, due_by]` ISO dates | `not_before ≤ due_by` |
| `LedgerStatus` | closed enum: `DONE` \| `DUE` \| `OVERDUE` \| `NO_PLAN` \| `UNMATCHED_REPORT` | closed sum, no "other" |
| `LangText` | attributed human-readable text — **the only string type output seams accept** | exactly two constructors: `LangText.quoted(SourceRef, excerpt)` (verbatim source text, minted at source registration) and `LangText.template(key)` (a key into Surface's reviewed copy table). There is no `LangText.of(string)`. |

**Why the closed `ActivityCode` registry is the load-bearing choice.** "Never infers state" is only
enforceable if expected-to-done matching is exact. A closed, validated `ActivityCode` makes the
ledger join a code-equality + date-window comparison — a pure function with no heuristic, no
similarity scoring, no NLP. The registry (with `RiskFlagCode`) is the published language the whole
join runs on, so it is governed as **vocabulary** (additions reviewed and versioned), not as data
edited freely. Two tiers, not three or five: the number of tiers equals the number of distinct
downstream treatments (presentation orders `DIRECTED` above `GUIDELINE` and words them
differently); `SourceKind` still records *which* kind of authority for display and provenance.

---

## 3. Data model

Conceptual model per owning module. **Storage shapes are private to each owner** — one owner per
table, no table written by two modules, and no row type ever crosses a seam; a seam reader never
learns a column name. Within `Record`'s private storage, provenance is a **non-nullable foreign
key**: a reported item that names no source is unrepresentable, not merely invalid.

```
Accounts
  Principal     (principal_id, credentials-ref)                    -- a login; no medical meaning
  Subject       (subject_id)                                       -- a tracked person; no login coupling
  Grant         (principal_id, subject_id, scope: {View, Report, Administer})
                -- self-management = Grant(own principal, own subject, Administer), created at signup

Record  (append-only journal per subject; the ONLY door for medical state)
  Source        (source_id, kind: SourceKind, label, issued_by, issued_on)
  ReportedItem                          -- supertype: anything reported as having happened/been received
    (report_id, subject_id, activity: ActivityCode | UNCODED, occurred_on,
     source → Source [non-null], attestation: Attestation, payload: verbatim text, never interpreted)
  ReportedDirective <: ReportedItem     -- a report that CARRIES AUTHORITY (doctor instruction /
    (steps: [(directed_activity: ActivityCode, due: DateWindow)],  --  prescription): simultaneously
     resolves: ReportRef?)              --  reported state and a producer of expectations; `resolves`
                                        --  is a reporter-declared link closing an open process
  ReportedOpenProcess <: ReportedItem   -- a report the reporter flags as an OPEN process with no
    (plan_domain: [ActivityCode]?)      --  concrete plan ("follow-up pending per Dr. Levi's letter")
  SubjectProfile                        -- restating VIEW over reported demographics + declared
    (dob, sex_at_birth, risk_flags: set[RiskFlagCode])             --  risk-flag reports; contains only
                                        --  what was reported — no derivation beyond restating

Rails  (data, not code — one file per pathway, schema-validated at load)
  PathwayDef    (pathway_id, version, provenance: SourceRef, title, steps: [StepRule],
                 opens_process: [(ActivityCode, plan_domain: [ActivityCode])])
  StepRule      (activity: ActivityCode,
                 eligibility: Predicate,      -- closed grammar: age ∈ [a,b] | sex = s |
                                              --   has RiskFlagCode | AND/OR of these — nothing more
                 schedule: AgeAnchor | DateAnchor)   -- recurring-by-age, or offset from anchor date

Ledger  (computed on read, cacheable; owns no authoritative storage)
```

Design notes:

- **Supertype/subtype, not a fat type with nulls.** The done-side consumer (Ledger) needs only the
  supertype `{subject, activity, occurred_on, source, attestation}` — a plain lab result honestly
  supplies exactly that. A directive additionally carries dated future steps; an open-process report
  additionally carries openness. Putting `steps`/`due` on every report would force results and
  vaccinations to fabricate nulls; flattening directives would lose what the expected side runs on.
  Only the one consumer that needs authority (`DirectiveSource`, §6) ever sees the subtypes; the
  Ledger's done-feed is typed to the supertype.
- **`UNCODED` is a deliberate act, not a fallback.** Intake maps a report to an `ActivityCode`; a
  mistyped or unrecognized code is **rejected** with an actionable error ("code not in the activity
  registry"), never silently stored. An item the registry genuinely cannot express may be stored
  `UNCODED` by the reporter's explicit choice; it is never fuzzily matched later — it surfaces as
  `UNMATCHED_REPORT` (§7). The file stays honest and complete without ever force-fitting a code.
- **Attestation and Source are both required and are different things.** `Attestation =
  (reported_by: PrincipalId, via_grant, reported_at)` records *who put this in the file*; the
  `Source` records *the authority behind it* (the lab report, the doctor, the guideline). A
  self-reported prescription: attested by the patient, sourced to the prescription. A clinician
  filing their own instruction: attested by the clinician principal, sourced to that clinician.
  Same types either way — there is no privileged ingestion path for doctors to abuse.
- **Two deliberate absences:** no free-text "recommendation" field anywhere, and no stored
  "inferred condition" — the schema has no cell an inference could live in.

---

## 4. The non-advice invariant: owned by `Ledger`, enforced by four structural locks

**Restated:** every output is a `Citation = (authoritative source × reported state)`; the system
never infers state and never originates advice — for every user, including a doctor user. And a
second, subtler rule falls out of the types: the system only ever speaks about the **tracking
file** ("your file shows no colonoscopy report in the guideline's window"), never about the
**person** ("you haven't had a colonoscopy" is an inference it is structurally unable to phrase).

```
Citation                          # constructor module-private to Ledger — ONE construction site
  source: SourceRef               # required; carries kind + tier inseparably (§2)
  basis:  ReportedBasis           # required; mintable only by Record (below)

ReportedBasis                     # closed sum, minted ONLY by Record.evaluate — what "reported
  = Fulfilled(ReportRef)          #   state" means per outcome
  | Absent(applicability: [ReportRef | profile-fact refs], searched: DateWindow)
  | OpenUnplanned(ReportRef)

LedgerEntry                       # sealed constructor, Ledger-private; the ONLY type Surface renders
  subject:  SubjectId
  status:   LedgerStatus
  activity: ActivityCode | UNCODED
  window:   DateWindow?           # absent only for UNMATCHED_REPORT
  citation: Citation              # exactly one, non-optional
```

The four locks:

1. **One mint.** `Citation` and `LedgerEntry` have module-private constructors; the only way to
   obtain instances is `Ledger.view(handle) -> list[LedgerEntry]`. A valid `Citation` is *evidence*
   the join happened: its `SourceRef` can only come from `Record`/`Rails` registration (tier welded
   in at construction) and its `ReportedBasis` only from `Record.evaluate`. There is no way to
   construct one from thin air, hence no way to launder an invented recommendation into output
   shape. Provenance and tier travel with every entry not by rule but by shape: tier is a field of
   `SourceRef`, `SourceRef` a field of `Citation`, `Citation` a required field of every entry.

2. **No slot for advice.** `LedgerEntry` carries codes, refs, and a closed status enum — no field
   in which the system could author a sentence. Every human-readable string in an outbound position
   is a `LangText`, constructible only as quoted-and-attributed source text or as a key into
   `Surface`'s static, human-reviewed copy table (keyed by `LedgerStatus`). Advice-shaped prose has
   no constructor: the sentence cannot be built, so the compiler is the reviewer.

3. **One read path.** `Surface`'s sole subject-output dependency is `Ledger.view`; its access to
   `Record` and `Accounts` is write-only. If a future screen needs data the ledger doesn't emit,
   that is a ledger design conversation, not a surface workaround. A doctor user is just a manager
   (§5), reaches the same `Ledger.view` with the same types, and when they *enter* an instruction
   it is stored as an attested, sourced `ReportedDirective` — the system relays and cites it, never
   adds to it. There is no clinician-mode API.

4. **Record, not body — and no door for inferred state.** Medical state has exactly one entry
   point, `Record.submitReport`, which requires an `Attestation`; no internal module holds a write
   capability into the file. The Record answers questions only about *itself*: `evaluate` returns
   `Fulfilled` or `Absent(…, searched window)` — statements about the file's contents. The system
   cannot phrase "the patient hasn't done X"; the only expressible phrase is "no report of X exists
   in this window," fixed by the type, not by discipline. `SubjectProfile` restates reported facts,
   so even rail *applicability* traces to reports, never to derived suspicion. And the matcher
   itself is a pure function — code equality plus `occurred_on ∈ window` (with one Ledger-owned
   tolerance constant) — no scoring, no thresholds, no model; no component exists whose job could
   quietly grow into inference without adding a new module, which is exactly the review event that
   should catch it.

---

## 5. `Accounts`: the `manager → subject(s)` primitive

One concept — the **`Grant`** edge — and one enforcement mechanism — the **`SubjectHandle`**
capability.

```
Accounts public seam:
  register(person-fields) -> (PrincipalId, SubjectId)      # writes Grant(self, self, Administer)
  enroll_dependent(handle{Administer of self}, fields) -> SubjectId   # registrar gets Administer
  grant(handle{Administer}, grantee: PrincipalId, scope)   # explicit act; also revoke
  subjects_of(principal) -> list[SubjectId]
  authorize(principal, subject, scope) -> SubjectHandle    # raises NotAuthorized; the ONLY
                                                           #   authorization question in the system
```

- **Multi-subject is cardinality, not a case.** A person alone: one self-grant. A parent with three
  children: four grants. A doctor with 200 patients: 201 grants. Same rows, same queries, same code
  path; no `FamilyAccount`, no `ClinicianPortal` type exists anywhere.
- **Capability-style, not check-style.** Every subject-scoped seam in every module takes a
  `SubjectHandle` — an opaque, short-lived value minted only by `Accounts.authorize`. No seam in
  `Record`, `Rails`, or `Ledger` accepts a bare `SubjectId`, so authorization cannot be *forgotten*
  at a call site: a call without a handle does not type-check. Accounts is the only module that has
  ever heard of a manager; a change to the account model cannot scatter.
- **Scopes = seam treatments, exactly three.** `View` (required by `Ledger.view`), `Report`
  (required by `Record.submitReport`), `Administer` (required by grant management). Least privilege
  by signature: write seams demand the write-scoped handle type. There are no roles ("caregiver",
  "clinician") — the data model never branches on who a manager socially is; a clinician's higher
  authority enters via the `SourceKind` of what they report, not via their account.

*MVP assumption:* grant creation/revocation is an explicit act by an `Administer`-scoped manager of
that subject; richer consent workflows are out of scope (§9).

---

## 6. The expected side: one interface, two honest producers

The one abstraction in the system with multiple implementations — it exists because the brief
supplies two genuinely different producers of expectations *today*, and because the Ledger must not
know which kind of authority produced an expectation (that ignorance is what keeps a new source
type from touching the join):

```
ExpectationProducer                       # consumed only by Ledger
  expectations_for(handle, profile: SubjectProfile, horizon) -> list[Expectation]

Expectation                               # flat, four-field; the common vocabulary of both producers
  activity: ActivityCode
  window:   DateWindow                    # concrete dates — already resolved
  source:   SourceRef                     # provenance + tier, inseparable, attached at birth
  applicability_basis: [ReportRef | profile-fact refs]   # the REPORTED facts that made this step
                                          #   apply — the directive item, or the demographic/risk
                                          #   reports a rail predicate consumed
```

The type is calibrated from both ends. Floor (what the Ledger needs): what, when, on whose
authority, and which reported facts ground it. Ceiling (what both producers can honestly supply):
exactly those four — so `recurrence` is **not** a field (a one-off doctor instruction has none and
would fabricate; recurring rails are expanded upstream, inside `GuidelineSource`, into concrete
occurrences within the horizon — the Ledger never learns recurrence exists), and the eligibility
*rationale* is not a field (the Ledger doesn't need the predicate; presentation can reach it
through `SourceRef` when showing "why am I seeing this").

The two implementations, both shipping day one:

1. **`Rails.GuidelineSource`** — validates and loads declarative `PathwayDef` files, mints each
   pathway's guideline `SourceRef` at load, evaluates the closed eligibility grammar against the
   (reported-only) `SubjectProfile`, expands schedules into concrete windows, and emits
   expectations at tier `GUIDELINE`. The pathway knows its own rules — nothing outside Rails ever
   opens a definition. **Adding a pathway is adding a reviewed data file; no code change.**
2. **`Record.DirectiveSource`** — promotes each `ReportedDirective`'s dated steps into
   expectations citing the directive's `SourceRef` at tier `DIRECTED`. No predicates, no
   expansion — a translation, honestly thin.

The two producers share no evaluation code: a guideline's recurrence rule and a doctor's dated step
are different concepts that merely rhyme; unifying their internals would be the wrong abstraction.
There is no plugin registry and no dynamic discovery — a hand-maintained list of two. The day a
third source class arrives, it either honestly fills the same four fields or it forces a new-subtype
conversation at this seam — never a nullable field.

---

## 7. The join (the whole algorithm of the product)

Owned by `Ledger`, deterministic, pathway-agnostic — the same procedure for every rail, so gaps are
**computed, never enumerated per example**. The join key is `(ActivityCode, occurred_on ∈ window)`
and nothing else.

```
Ledger.view(handle{View}, asOf):
  profile  = Record.profile(handle)                                  # declared-only facts
  expected = ⋃ producer.expectations_for(handle, profile, horizon)   # rails + directives

  for e in expected:
      basis = Record.evaluate(handle, e.activity, e.window, e.applicability_basis)
      → DONE     Citation(e.source, Fulfilled(report))          if matched
      → DUE      Citation(e.source, Absent(e.applicability_basis, e.window))   window open
      → OVERDUE  Citation(e.source, Absent(e.applicability_basis, e.window))   window passed

  for p in open_processes(handle) not covered:                       # see below
      → NO_PLAN  Citation(p.declaring_source, OpenUnplanned(p.report))

  for r in reports matched by no expectation (including all UNCODED items):
      → UNMATCHED_REPORT  Citation(r.source, Fulfilled(r.report))   # surfaced, never interpreted
```

- **Matching semantics live inside `Record`.** The Ledger tells the Record "evaluate this activity
  and window against yourself"; the Record decides matching (code equality, window membership, the
  one tolerance constant) and mints the `ReportedBasis`. Callers never interpret raw rows.
- **A gap still satisfies the invariant.** A `DUE`/`OVERDUE` citation joins the *expectation's*
  source with the *reported facts that made the expectation apply* plus the searched window.
  Nothing is asserted beyond "this source says X is expected given what you reported, and your file
  shows no report of X in this window."
- **The nudge is a join outcome, not a feature.** Openness is *declared*, never inferred, by
  exactly two authorities — mirroring the two expectation producers: **(a)** the reporter files a
  `ReportedOpenProcess` (attested), or **(b)** rail data lists an `ActivityCode` in
  `opens_process` (sourced), so a plain reported event of that kind counts as open without the
  reporter needing to know it does. **Coverage is mechanical and owned by the declaring
  authority:** a rail-declared opening is covered when an expectation exists whose activity is in
  the rail's declared `plan_domain`; a reported open process is covered when a later
  `ReportedDirective` declares `resolves` → it (a reporter-declared link, never a system guess) or
  when an expectation matches its declared `plan_domain`. An uncovered open process emits
  `NO_PLAN`, whose citation joins the declaring authority against the reported item, and whose
  rendering is the fixed template "you reported an open process and no plan covers it — **ask your
  doctor**." No plan is proposed because no type exists to carry one.
- **Tier arrives inside the citation**, computed once at `SourceRef` construction and copied, never
  recomputed — the Ledger physically cannot assign a tier because no tier-accepting constructor is
  visible to it.

### Change scenarios (one owner per change)

| Change | Touches | Untouched |
|---|---|---|
| New pathway (e.g. well-baby schedule next to colorectal screening) | Rails: one new `PathwayDef` data file (+ any new registry codes, reviewed) | Ledger, Accounts, Record, Surface, all other rails |
| New source kind (e.g. an immunization-registry feed) | `SourceKind` member + one line in `ConfidenceTier.of` (vocabulary, reviewed) + one `ExpectationProducer` implementation in the module that backs it | `Citation`, `LedgerEntry`, join logic, Accounts, Surface — all compile untouched |
| New activity/risk code | the registry (reviewed addition); rails that use it | `evaluate` and the join are code-generic |
| New ledger status | Ledger + one copy-table row in Surface | everything else |
| New family member / new patient | zero code — one `Grant` row | everything |
| New eligibility predicate need | grammar extension inside Rails; `Predicate` never crosses a seam | everything else |

---

## 8. Day-zero vocabulary of the public seams (normative, closed)

Public seams — between modules and out of `Surface` — may speak **only**:

1. **Domain types defined here:** the `vocabulary` kernel types (§2) and the public types declared
   above: `Grant`, `SubjectHandle`, `SubjectProfile`, `ReportedItem` (supertype only, except at the
   `DirectiveSource` seam), `Attestation`, `Expectation`, `Citation`, `ReportedBasis`,
   `LedgerEntry`. All ids are distinct nominal types, never bare strings.
2. **Foundational set:** ISO-8601 date/time types of the host stdlib; UTF-8 text only as
   `LangText`; JSON as the wire encoding at the HTTP edge.
3. **Error vocabulary — one type per distinct caller handling, and no more:** `NotAuthorized`
   (→ 403), `RejectedReport(field-level reason)` (→ 422), `NotFound` (→ 404). Storage and framework
   exceptions are translated at the seam; no further subtype exists until a caller demonstrably
   branches on one.

Nothing else crosses a seam: no database rows, no ORM entities, no framework request/response
objects past the edge, no pathway-file parse trees, no vendor result objects, no free-form `string`
in an outbound position.

`Surface` is thin by rule, not by hope: HTTP translation, the `authorize` call, and the static copy
table. It contains no branch on `SourceKind` and no branch on manager type; its read model *is*
`list[LedgerEntry]`. Endpoints (MVP-complete): `POST /people`, `POST /subjects` (dependents),
`POST /grants`, `GET /subjects`, `POST /subjects/{id}/reports`, `GET /subjects/{id}/ledger`.

---

## 9. Explicitly out of the MVP

Each exclusion is a *shape* exclusion: no interface, enum slot, nullable column, or reserved hook
exists "for when we add it."

- **The integrated overview (המכלול)** — no aggregation, cross-subject dashboards, or cross-pathway
  synthesis beyond the flat ledger; nothing in the schema anticipates it.
- **Inference of any kind** — no suspicion engine, no risk scoring, no fuzzy matching, no NLP or
  auto-coding of report payloads (payloads stay verbatim), no deriving risk flags from reports.
  Structurally absent, not disabled.
- **Source types beyond the three MVP kinds** — no FHIR/HL7/EHR connectors, no lab integrations,
  no document/OCR intake; a future feed is a new producer behind the existing seam, designed then.
- **Roles and consent** beyond the single `Grant` edge with its three scopes — no delegation
  chains, no organizational identity (clinics, staff), no consent workflows.
- **Notification delivery** — the nudge is a ledger row; push/email/scheduling machinery is out.
- **Real clinical code systems** (LOINC/SNOMED/ATC mapping), localization beyond the one copy
  table, audit trails beyond the append-only record and grant log, multi-tenancy.
- **Pathway authoring tooling** — rails are hand-authored, schema-validated, reviewed data files.
- **Generalized rules engine, plugin framework, event sourcing, service decomposition** — no MVP
  consumer exists for any of them.

*Standing assumptions:* single deployable service; persistence per module behind its seam; identity
provider is a commodity dependency hidden inside `Accounts`; the evaluation horizon is a
`Ledger.view` read parameter with a default, not persisted state; prescriptions are modeled as
`ReportedDirective(kind = prescription)` whose expected step is the fill/administration — adherence
tracking beyond that single expectation is out of scope.
