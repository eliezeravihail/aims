# "Responsible Doctor" MVP — Architecture

## 0. Framing and assumptions

The system's only job is to answer two questions per subject: *what is expected next* and *what is done*,
and to flag the gap between them — always as a citation of a source against a reported state, never as a
system-originated opinion. Everything below is organized around that single output type.

Assumptions made to close ambiguity in the brief (stated so they're visible, not load-bearing on the
invariant itself):

- "Reported" means *entered into the system as a fact*, by a subject, a manager, a doctor, or an ingestion
  adapter reading a structured source (a lab feed, a pharmacy feed). A doctor typing a free-text note is
  still a **report** — it becomes a `ReportedState` row, not a system inference and not "advice," because the
  system did not originate it; it only stores and later cites it.
- "Eligibility" (e.g., "this subject is in the age band this screening rail applies to") is arithmetic over
  subject-declared attributes (DOB, stated risk flags), not clinical inference. The architecture treats this
  as a deterministic rule match, structurally distinct from inferring a *medical state* (a diagnosis, a
  risk level, a symptom interpretation) — the latter never happens anywhere in the system.
- One deployable "system," internally modular; no distributed-systems concerns (queues, multi-region) are
  in scope for an MVP design.

---

## 1. Data model

Six entity families. Everything else in the system is a function over these.

### 1.1 Identity and access
```
Account            { account_id, auth_identity, display_name }
Subject            { subject_id, name, dob, declared_attributes: {risk_flags[], ...} }
Mandate            { mandate_id, manager_account_id -> Account,
                     subject_id -> Subject,
                     scope: {access_level: FULL|READ, source_type_allowlist[]},
                     status: ACTIVE|REVOKED }
```
A `Subject` is a record, not necessarily a login-capable account (covers a baby, a dependent parent). An
`Account` becomes a manager of a `Subject` purely by holding an `ACTIVE` `Mandate` — there is no separate
"self" or "family" or "patient" type anywhere (see §4).

### 1.2 Sources (the authoritative half of every citation)
```
Source             { source_id, source_type: PUBLIC_GUIDELINE|DOCTOR_INSTRUCTION|PRESCRIPTION,
                     issuing_authority, confidence_tier: TIER_A|TIER_B|TIER_C,
                     effective_from, effective_to?, raw_ref }
```
`confidence_tier` is a **property of the source type/issuer**, assigned once by the ingestion adapter that
creates the `Source` (see §5) — never computed or overridden downstream. Illustrative default mapping
(owned by ingestion, not fixed in the ledger): `DOCTOR_INSTRUCTION`/`PRESCRIPTION` → Tier A (subject-specific,
authoritative for this person); `PUBLIC_GUIDELINE` → Tier B (population-level default, applies until
superseded by a Tier A instruction for the same step).

### 1.3 Reported state (the "done" half)
```
ReportedState      { reported_id, subject_id -> Subject, source_id -> Source,
                     reported_by_account_id -> Account,
                     reported_at, subject_matter_key, payload: {free_text?, structured_value?},
                     occurred_at? }
```
Every `ReportedState` **must** carry a non-null `source_id`. There is no code path that creates one without
a source — this is the seam that prevents the system from ever asserting a state it wasn't told.

### 1.4 The pathway library (the "expected" half, declarative)
```
PathwayDefinition  { pathway_id, name, version, source_id -> Source (the guideline that authorizes it),
                     eligibility_rule: declarative predicate over Subject.declared_attributes,
                     steps: [PathwayStep] }

PathwayStep        { step_key, description_ref, due_rule: declarative offset
                     (e.g. "age >= 9mo AND age < 12mo", "180d after prior step"),
                     recurrence?: rule,
                     expected_report_matcher: declarative predicate a ReportedState must satisfy
                                               to count as fulfilling this step }
```
A pathway is data, not code: a rule table an eligibility predicate, a due-window function, and a matcher
predicate. Registering a new pathway means adding one `PathwayDefinition` document to the library — nothing
about the join engine, the account model, or the output layer changes (exit criterion 5).

### 1.5 Materialized expected/done, and the ledger
```
PathwayEnrollment  { enrollment_id, subject_id, pathway_id, matched_at,
                     eligibility_snapshot }              -- why this subject is on this rail

ExpectedItem       { expected_id, enrollment_id, step_key, due_window: {from, to},
                     source_id -> Source }                -- inherited from PathwayDefinition.source_id

LedgerEntry        { entry_id, subject_id, expected_item_id? , matched_reported_ids: [ReportedState],
                     status: DONE | DUE | OVERDUE | GAP_NO_PLAN,
                     confidence_tier: <copied from the entry's Source, never recomputed> }
```
`GAP_NO_PLAN` is the case where an open process (a `ReportedState` exists — e.g. an abnormal result — with
no `ExpectedItem`/`PathwayEnrollment` covering what happens next). It never gets a synthesized plan; it gets
a `NudgeCitation` (§3).

### 1.6 The output type
```
Citation          := SourceReportedCitation(source: Source, reported: ReportedState | ExpectedItem)
                    | NudgeCitation(subject_id, reason: NO_PLAN_FOR_OPEN_PROCESS,
                                    fixed_text: "Ask your doctor")
```
`Citation` is the **only** type any external seam (API, UI, notification) may receive. It is a closed
(sealed/tagged) union with exactly these two constructors — no third constructor exists, and neither
constructor has a field for free-form system-authored text beyond the one fixed nudge string.

---

## 2. Module / boundary structure

Seven modules, each with a single owner and a narrow public interface. Arrows are allowed data flow;
nothing flows the other direction.

```
[Source Adapters] --> [Ingestion Store: Source, ReportedState]
                                  \
[Pathway Library] --> [Eligibility/Enrollment Engine] --> ExpectedItem
                                  \                              \
                                   \                               v
                                    +---------------------> [Reconciliation Engine] --> LedgerEntry
                                                                        |
                                                                        v
                                                              [Citation Gateway]
                                                                        |
                                                                        v
                                                            [Presentation / API layer]

[Account & Mandate Service] -- (subject scoping, cross-cutting) --> every module above, read-only
```

| Module | Owns | Public interface | New-X change lands only here? |
|---|---|---|---|
| **Source Adapters** | Turning one external source type into `Source` + `ReportedState` rows | `ingest(raw) -> {Source, ReportedState[]}` | new source type = new adapter, yes |
| **Pathway Library** | Catalog of `PathwayDefinition` | `list_pathways()`, `get(pathway_id)` | new pathway = one declarative doc, yes |
| **Account & Mandate Service** | `Account`, `Subject`, `Mandate` graph | `subjects_for(manager)`, `check_access(manager, subject, source_type)` | new relationship shape = doesn't happen; scope field covers variance |
| **Eligibility/Enrollment Engine** | Matching subjects to pathways | `enroll(subject) -> PathwayEnrollment[]`, `materialize(enrollment) -> ExpectedItem[]` | reads Pathway Library + Subject attributes only; no reported data |
| **Reconciliation Engine** | Joining expected × reported | `reconcile(subject_id) -> LedgerEntry[]` | pure function, no source/pathway/account logic embedded |
| **Citation Gateway** | Constructing `Citation` — the invariant's home | `cite(ledger_entry) -> Citation` | the only exported constructor for `Citation`; see §3 |
| **Presentation/API** | Rendering/serving citations | reads only `Citation` objects | cannot import `Source`, `ReportedState`, `LedgerEntry` internals directly |

The **Account & Mandate Service** is consulted by every other module as a scoping filter (a manager can only
trigger reconciliation/see citations for subjects they hold an active `Mandate` over) but owns no medical
content — this keeps criterion 5's "doesn't scatter" true for the account primitive too: changing how
access works never touches pathway or citation code.

---

## 3. Ownership and structural enforcement of the non-advice invariant

**Owner: the Citation Gateway module, and specifically the `Citation` type itself.**

Enforcement is structural, not procedural, on four independent axes — any one of which is redundant on
purpose (defense in depth for a boundary the brief calls non-negotiable):

1. **Closed output type.** `Citation` is a sealed union with exactly two constructors (§1.6). Neither
   constructor accepts an arbitrary string as "the advice." `SourceReportedCitation` requires a real
   `Source` foreign key and a real `ReportedState`/`ExpectedItem` foreign key — both must already exist as
   rows created by Ingestion or Enrollment, so the Gateway cannot fabricate either side. `NudgeCitation`'s
   text is a compile-time constant, not a parameter — there is no field through which any caller, including
   a doctor-facing code path, can inject generated or recommended text.

2. **Single constructor visibility.** Only the Citation Gateway module exports a way to build a `Citation`.
   Every other module (Reconciliation, Enrollment, Ingestion) produces internal, non-renderable DTOs
   (`LedgerEntry`, `ExpectedItem`, `ReportedState`). The Presentation/API layer is wired, at the dependency
   level, only to the Gateway's interface — it has no import path to construct or accept a `Citation`-shaped
   object from anywhere else, and no import path to the internal DTOs at all. This makes "a path that
   originates advice" a compile-time-unreachable state, not a rule someone has to remember to follow.

3. **No inference surface anywhere upstream.** `ReportedState` rows are created only by Source Adapters
   from actual source payloads (`source_id` and `reported_by_account_id` are non-nullable at the schema
   level) — there is no module with permission to synthesize a `ReportedState` from reasoning about other
   data. The Reconciliation Engine is a pure function `(ExpectedItem[], ReportedState[]) -> LedgerEntry[]`
   using only declarative matching (`expected_report_matcher`, due-window arithmetic) — it has no access to
   an LLM, no free-text output field, and its output (`LedgerEntry`) still isn't renderable, so even a bug
   here cannot reach a user without passing back through the Gateway's constructor discipline in (1)-(2).

4. **Doctor users are not a special case.** A doctor's clinical judgment enters the system exactly like any
   other report: as a `Source` of type `DOCTOR_INSTRUCTION` (Tier A) plus a `ReportedState` carrying what
   the doctor said. The system then cites *that* — "Dr. X instructed Y, reported on date Z" — it never
   re-emits it as if the system itself recommended Y, and a doctor account has no elevated API that skips
   the Gateway. This is what makes the invariant hold "for every user, including a doctor user": the
   Gateway doesn't know or care who the manager is, only that its two inputs are a real `Source` and a real
   `ReportedState`/`ExpectedItem`.

The one place this could be violated is if a future module were given write access to construct a
`Citation` directly. That surface is exactly one module wide, which is what makes it auditable: a code
review of "does anything besides `citation_gateway/` construct a `Citation`" is a complete check of the
invariant.

---

## 4. The `manager → subject(s)` account primitive

One relationship type, `Mandate(manager_account_id, subject_id, scope, status)`, is the entire primitive.
There is no `Family` type and no `PatientRoster` type — both are the same shape read differently:

- **Self-tracking:** `Mandate(manager=Alice, subject=Alice)`. An account manages itself by holding a
  `Mandate` over a `Subject` record that happens to share its identity.
- **Family:** a parent account holds `Mandate(manager=Parent, subject=Child)` for each child, and
  optionally `Mandate(manager=Parent, subject=Parent)` for themselves. N mandates, same table.
- **Doctor managing patients:** `Mandate(manager=DoctorAccount, subject=Patient_i, scope={access_level:
  READ, source_type_allowlist:[DOCTOR_INSTRUCTION, PUBLIC_GUIDELINE]})` for each patient. Same table, a
  different `scope` value — not a different code path.
- **Multiple managers per subject** (both parents, or a family member plus a treating doctor) falls out for
  free: it's just more than one `Mandate` row pointing at the same `subject_id`. No modeling change needed.

`scope` is the only axis of variation (what the manager can see/do), never the shape of the relationship.
Every module that needs "which subjects can this account see" calls one function —
`Account&MandateService.subjects_for(manager_account_id)` — so a manager operating one subject and a manager
operating fifty subjects exercise identical code (criterion 2).

---

## 5. Joining expected and reported into the ledger

Two independently-owned inputs, joined by one pure function.

**Expected side (owned by Pathway Library + Eligibility/Enrollment Engine):**
1. For a subject, the Enrollment Engine evaluates every `PathwayDefinition.eligibility_rule` against
   `Subject.declared_attributes` (age from DOB, stated risk flags). Matches produce `PathwayEnrollment` rows.
2. Each enrollment is materialized into `ExpectedItem` rows, one per `PathwayStep`, with a `due_window`
   computed from the step's `due_rule` and a `source_id` copied straight from
   `PathwayDefinition.source_id` — the expected side's provenance is fixed at authoring time, not at
   join time.

**Reported side (owned by Source Adapters):** `ReportedState` rows accumulate independently, each already
carrying its own `source_id` (which doctor, which prescription, which lab feed) and thus its own
`confidence_tier` via that `Source`.

**The join (owned by Reconciliation Engine), run per subject:**
```
for each ExpectedItem e in enrollment set:
    candidates = ReportedState rows for subject where
                 e.expected_report_matcher(candidate) is true
                 and candidate.occurred_at within/near e.due_window
    if candidates non-empty:  LedgerEntry(status=DONE, matched=candidates, source=e.source)
    elif now() > e.due_window.to:  LedgerEntry(status=OVERDUE, source=e.source)
    else:  LedgerEntry(status=DUE, source=e.source)

for each ReportedState r not matched by any ExpectedItem above,
    where r indicates an open/ongoing process (e.g. an abnormal result, a new diagnosis report)
    and no PathwayEnrollment exists that would cover "what happens after r":
        LedgerEntry(status=GAP_NO_PLAN, subject=r.subject_id)  -- no source join possible, by definition
```
Every `LedgerEntry` except `GAP_NO_PLAN` carries a `source_id`/`confidence_tier` that traces back to either
the `PathwayDefinition` (expected side) or the specific `ReportedState`'s `Source` (done side) — provenance
is never re-derived or guessed at join time, only carried through. `GAP_NO_PLAN` has structurally no source
to cite (that's what "no plan" means), which is exactly why it can only ever become a `NudgeCitation`
rather than a `SourceReportedCitation` — the Gateway's type signature makes that the only option available
for that status.

The join is symmetric to future growth: adding a pathway grows the expected set; adding a source type grows
the reported set; the reconciliation algorithm above is unchanged either way (criterion 3 and 5).

---

## 6. Day-zero vocabulary (what the public seams may speak)

The API/UI/notification layer is typed against this vocabulary only — no seam exposes internal terms like
"eligibility rule," "matcher predicate," or "enrollment" to end users, and no seam exposes anything not on
this list:

| Term | Meaning at the seam |
|---|---|
| **Subject** | The person whose medical tracking file this is |
| **Manager** | The account acting on behalf of a subject (may be the subject themself) |
| **Source** | An authoritative origin: a public guideline, a doctor instruction, or a prescription |
| **Reported item** | Something entered as fact about a subject (a result, an instruction, a fill) |
| **Expected item** | A step a recognized pathway says should happen, with a due window |
| **Done** | An expected item with a matching reported item |
| **Due / Overdue** | An expected item with no match yet, before/after its window |
| **Gap — no plan** | An open process with nothing expected covering its next step |
| **Nudge** | The fixed "ask your doctor" prompt attached to a no-plan gap |
| **Citation** | The pairing of a source and a reported/expected item behind any statement the app makes |
| **Confidence tier** | How authoritative a citation's source is (e.g. personalized instruction vs. general guideline) |

Deliberately absent from the public vocabulary: "diagnosis," "risk," "recommendation," "we suggest," or any
verb implying the system concluded something — those words have no corresponding type anywhere in the model
(§1.6), so they cannot leak through a seam that only ever serializes a `Citation`.

---

## 7. Explicitly out of the MVP

- **Pillar 2 / המכלול**, the integrated overview across pathways/subjects — no aggregation module, no
  cross-pathway dashboard object exists in this design.
- **Any inference engine**: no symptom checking, no risk scoring beyond arithmetic eligibility over
  subject-declared attributes, no ML/LLM-based state estimation anywhere in the data flow.
- **System-authored recommendations of any kind** beyond the one fixed nudge string — no "suggested next
  step," no treatment-option surfacing, no triage.
- **Pathway authoring UI.** `PathwayDefinition` rows are added by an internal content owner via a
  declarative artifact (config/document), not by end users; no in-product authoring flow.
- **Multi-source conflict resolution UI** (e.g., what happens when a Tier A instruction contradicts a Tier B
  guideline) — the model records both with their tiers; resolving/surfacing conflicts is a v2 concern.
- **Notification delivery mechanics** (push/SMS/email channels, scheduling, digesting) — the Presentation
  layer receiving `Citation`s is in scope; how/when it pushes them to a device is not.
- **Consent/legal workflow** beyond the `Mandate.scope` flag — revocation UX, guardianship verification,
  minors' consent transitions, audit trails for access grants.
- **Real EHR/FHIR integration protocols** — Source Adapters are specified as an interface shape; building a
  production-grade adapter for any specific external system is out of scope.
- **Pathway versioning/migration semantics** (what happens to existing `ExpectedItem`s when a
  `PathwayDefinition` is revised) — `version` is modeled as a field; the migration policy is not designed.
- **Billing, payments, multi-tenancy/organization admin** for clinic deployments.
- **Localization/i18n** of pathway content or UI strings.

Anything in this section that later proves necessary should enter as a new `Source` type, a new
`PathwayDefinition`, or a new `scope` value on `Mandate` — not as a new kind of output, since `Citation`
remains the only thing the system is allowed to say.
