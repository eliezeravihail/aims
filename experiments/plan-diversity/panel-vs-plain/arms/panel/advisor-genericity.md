# "Responsible Doctor" MVP — Architecture

*Design deliverable for the frozen brief. The organizing discipline throughout is **correct
genericity**: every seam's payload type is calibrated from both ends — generic enough to be complete
for its consumers (the floor), no more specific than every producer can honestly supply (the
ceiling). Where the two bounds could not meet in one type, the design splits into a supertype plus a
specialization rather than fabricating or flattening. Each seam below states its calibration
explicitly.*

---

## 0. The one-paragraph shape

Five modules. **Identity** owns the `manager → subject(s)` primitive. **Reporting** owns everything
the subject (or their manager/doctor) *says* — the only place medical state enters the system.
**Rails** owns the declarative pathway library. **Sources** is a seam, not a store: the single
abstraction under which *anything authoritative* — a public guideline instantiated over a subject,
or a doctor's reported directive — produces `Expectation`s with provenance and tier attached.
**Ledger** is the sole consumer of both sides and the sole producer of output: it joins
`Expectation`s (expected) against `ReportedItem`s (done) and can construct only one output type — a
`Citation`-bearing `LedgerEntry` — whose constructor demands a source reference *and* a reported
basis. Presentation renders `LedgerEntry` values verbatim; there is no other output path. Adding a
pathway is a data change inside Rails; adding a source type is one new `Source` implementation;
nothing else moves.

```
                 ┌────────────────────────────────────────────────┐
                 │                   Identity                     │
                 │   Principal ── Grant ──► Subject               │
                 └───────┬───────────────────────┬────────────────┘
                         │ SubjectId             │ SubjectId
            ┌────────────▼───────────┐   ┌───────▼───────────────┐
            │       Reporting        │   │        Rails          │
            │  ReportedItem store    │   │  PathwayDef library   │
            │  (incl. Directives)    │   │  (declarative data)   │
            └───────┬───────┬────────┘   └───────┬───────────────┘
                    │       │ directives         │ defs
                    │       ▼                    ▼
                    │   ┌───────────────────────────────┐
                    │   │        Sources (seam)         │
                    │   │  Source.expectations_for(...) │
                    │   │   • GuidelineSource (rails)   │
                    │   │   • DirectiveSource (reports) │
                    │   └───────────────┬───────────────┘
                    │ ReportedItems     │ Expectations
                    ▼                   ▼
            ┌───────────────────────────────────────────┐
            │                 Ledger                    │
            │  join → LedgerEntry (constructor requires │
            │  SourceRef × ReportedBasis = Citation)    │
            └───────────────────┬───────────────────────┘
                                │ LedgerEntry (read-only)
                        ┌───────▼────────┐
                        │  Presentation  │  (renders; cannot construct)
                        └────────────────┘
```

---

## 1. Data model

### 1.1 Identity side

```
Principal        # a login. No medical meaning whatsoever.
  id: PrincipalId

Subject          # a person being tracked. No login coupling.
  id: SubjectId
  facts: SubjectFacts

SubjectFacts     # ONLY declared/reported demographic facts the MVP rails consult.
  date_of_birth: Date
  sex_at_birth: enum {female, male, unspecified}
  risk_flags: set[RiskFlagCode]     # declared, never derived (see §3)

Grant            # the single manager→subject edge. THE account primitive.
  manager: PrincipalId
  subject: SubjectId
  role: enum {owner, caregiver, clinician}
```

**Genericity calibration.** `SubjectFacts` is deliberately narrow: its floor is what the MVP's two
rail families (age/risk screening, well-baby) need for eligibility — birth date, sex, declared risk
flags — and its ceiling is what a person can *declare without clinical judgment*. A richer
"clinical profile" (conditions, labs) would exceed the ceiling: the system would have to infer it,
which is forbidden. Anything richer lives as `ReportedItem`s, never as facts the rails predicate on.
`risk_flags` are a closed, code-listed vocabulary (`RiskFlagCode`) so a rail's eligibility predicate
and a subject's declaration meet on the same published token — no free-text matching, no primitive
obsession.

### 1.2 Reported side (the only door for medical state)

Two types, because they are genuinely two kinds of object (design-principles §2, the
`Box`/`OrientedBox` resolution):

```
ReportedItem                       # supertype: anything the subject side reports as having
  id: ReportId                     #  happened or been received.
  subject: SubjectId
  activity: ActivityCode | UNCODED # what it was, in the published activity vocabulary
  occurred_at: Date
  attestation: Attestation         # who reported it, when, via which grant
  payload: text                    # verbatim as reported; NEVER interpreted by the system

ReportedDirective <: ReportedItem  # specialization: a report that CARRIES AUTHORITY —
  directed_activity: ActivityCode  #  a doctor instruction or a prescription. It is
  due: DueWindow                   #  simultaneously reported state (it happened: "my doctor
  authority: enum {doctor_instruction, prescription}   #  told me X") and a source of
  open: bool                       #  expectation ("X is now expected").
```

**Why the split, not one fat type.** The Ledger (done-side consumer) needs only the supertype:
`{subject, activity, occurred_at, attestation}` — that is its floor, and a plain lab result can
honestly supply exactly that. A doctor instruction additionally carries a *directive* — an expected
future activity with a due window. Putting `due`/`directed_activity` on `ReportedItem` would force
every result and vaccination record to fabricate nulls (the `angle = 0` cram); flattening
directives down would lose the very information the expected side runs on. So: supertype for the
common part, `ReportedDirective` as the honest specialization, and only the `Sources` seam — the
one consumer that needs authority — depends on the subtype.

**`UNCODED` is deliberate.** Intake maps a report to an `ActivityCode` (by asking the reporter or
by a lookup table). When it can't, the item is stored `UNCODED` and appears in the ledger as an
unmatched report — it is never force-fitted to a code. Fabricating a code to make the join look
clean would be value-plausible and design-wrong.

```
Attestation
  reported_by: PrincipalId
  via_grant: (PrincipalId, SubjectId)
  reported_at: Timestamp
```

Attestation is what makes "reported" auditable: every state datum names the human who asserted it.
A clinician-role reporter does not get a different data type — a doctor user's reports are
`ReportedItem`s like anyone's (the brief's "including a doctor user" clause falls out of the model:
there is no privileged ingestion type to abuse).

### 1.3 Expected side — declarative rails

```
PathwayDef                          # pure data. Lives in the Rails library. No code per pathway.
  id: PathwayId
  title: text
  provenance: SourceRef             # which published guideline this transcribes (tier: guideline)
  steps: list[StepRule]

StepRule
  activity: ActivityCode
  eligibility: Predicate            # closed predicate language over SubjectFacts:
                                    #   age ∈ [a,b] | sex = s | has RiskFlagCode | AND/OR of these
  schedule: AgeAnchor | DateAnchor  # AgeAnchor: at age A, repeat every P, until age B
                                    # DateAnchor: within D of an anchoring date
```

**Genericity calibration of the predicate/schedule language.** Floor: expressive enough for both
MVP rail families (age/risk-gated recurring screening; age-anchored one-shot well-baby visits).
Ceiling: nothing more — no event-driven triggers, no cross-step dependencies, no arbitrary
expressions. A general rules engine here would be speculative generality: no MVP pathway needs it,
and every notch of expressiveness widens what a pathway author can encode and what the evaluator
must be audited for. The language is a closed grammar; extending it is a change *inside Rails* (see
§6, change-axis analysis).

### 1.4 The seam type: Expectation

```
Expectation                         # what any Source emits. THE common vocabulary of both producers.
  subject: SubjectId
  activity: ActivityCode
  window: DueWindow                 # concrete [not_before, due_by] dates — already resolved
  source: SourceRef                 # inseparable provenance (see below)

SourceRef                           # provenance + tier, one value, never split
  kind: enum {public_guideline, doctor_instruction, prescription}
  ref: PathwayId + StepRule index | ReportId
  tier: ConfidenceTier              # derived from kind by a total, closed mapping — travels WITH the ref

ConfidenceTier = enum
  DIRECTED    # subject-specific clinician authority (doctor_instruction, prescription)
  GUIDELINE   # population-level published protocol (public_guideline)
```

**Calibration of `Expectation` — the load-bearing decision.** Two genuinely different producers must
meet here: a guideline instantiated over a subject, and a doctor's directive. Consumers (the Ledger)
need: who, what, by when, on whose authority — that's the floor. The ceiling test: can *both*
producers honestly supply each field?

- `recurrence` fails the ceiling — a one-off doctor instruction has none and would fabricate.
  Resolution: recurrence is *expanded upstream*, inside `GuidelineSource`, into concrete occurrences
  within the evaluation horizon. `Expectation` stays flat; the directive producer is never asked to
  invent periodicity, and the ledger never learns recurrence exists.
- `eligibility rationale` fails the floor test in reverse — the ledger doesn't need the predicate,
  only the fact that this step applies; the predicate is reachable *through* `SourceRef.ref` when
  presentation wants to show "why am I seeing this" (a legitimate leak: the pointer, not the
  grammar).
- `tier` sits inside `SourceRef`, not beside it. This is how exit criterion 4 is made structural
  rather than disciplinary: there is no code path where a citation exists without its tier, because
  tier is a field *of* the provenance value, and `SourceRef` has no partially-constructed form.

Two tiers, not five: the number of tiers equals the number of distinct *treatments* downstream
(presentation orders DIRECTED above GUIDELINE and words nudges differently). A finer taxonomy with
no consumer that branches on it would be dead vocabulary (design-principles §7's "one type per
handling" rule, applied to an enum).

### 1.5 Output side — owned by the Ledger, constructible nowhere else

```
Citation                            # the invariant, as a type
  source: SourceRef                 # (an authoritative source …)
  basis: ReportedBasis              # (… × a reported medical state)

ReportedBasis                       # what "reported state" means per outcome — a closed sum:
  = Fulfilled(ReportId)             # the report that satisfied the expectation
  | Absent(FactsSnapshot)           # no matching report; the declared facts that made the
                                    #   expectation applicable ARE the reported state cited
  | OpenUnplanned(ReportId)         # the reporter-flagged open directive/report with no plan

LedgerEntry                         # the ONLY type Presentation can render. Sealed constructor.
  subject: SubjectId
  activity: ActivityCode
  status: enum {DONE, DUE, OVERDUE, NUDGE_ASK_DOCTOR, UNMATCHED_REPORT}
  citation: Citation                # non-optional. No entry without one.
  window: DueWindow | none          # none only for UNMATCHED_REPORT
```

Note what `LedgerEntry` does **not** contain: any free-text field the system authors. Status is a
closed enum; the human-readable sentence for each status is a fixed template in Presentation,
parameterized only by the citation's fields. There is no slot in which advice *could* be placed —
the invariant is enforced by the shape of the type, not by review of its contents (see §3).

---

## 2. Modules and boundaries

| Module | One-sentence responsibility (its single reason to change) | Public seam speaks |
|---|---|---|
| **Identity** | Who may act for which subject | `PrincipalId, SubjectId, Grant, SubjectFacts` |
| **Reporting** | Store and code what the subject side reports | `ReportedItem, ReportedDirective, ActivityCode, Attestation` |
| **Rails** | The declarative pathway library and its predicate grammar | `PathwayDef` in, opaque handle out (only `Sources` reads defs) |
| **Sources** | Turn anything authoritative into `Expectation`s with provenance | `Source` interface: `expectations_for(SubjectId, SubjectFacts, Horizon) -> list[Expectation]` |
| **Ledger** | Join expected against reported; sole mint of `LedgerEntry` | `entries_for(SubjectId, Horizon) -> list[LedgerEntry]` |
| **Presentation** | Render `LedgerEntry` values; route user actions to Identity/Reporting | consumes only the above |

### The `Source` interface is a real abstraction, not decoration

Design-principles §2's test: describe a second, legitimately different implementation. There are
exactly two at day zero, and they differ in kind, not in configuration:

- **`GuidelineSource`** (backed by Rails): evaluates eligibility predicates against `SubjectFacts`,
  expands schedules into concrete windows, emits `Expectation`s citing `(PathwayId, step)` at tier
  `GUIDELINE`.
- **`DirectiveSource`** (backed by Reporting): promotes each open `ReportedDirective` into an
  `Expectation` citing its `ReportId` at tier `DIRECTED`. No predicates, no expansion — a
  translation, honestly thin.

The interface exists *because* the Ledger must not know which kind of authority produced an
expectation — that ignorance is exit criterion 5's mechanism. It is not speculative: both
implementations ship in the MVP, and the brief names "new source type" as a known change axis. What
we do **not** build: a plugin registry, dynamic discovery, or a third hypothetical adapter. The
seam is an interface with a hand-maintained list of two implementations; the day a third source
class arrives, it implements the same four-field `Expectation` or it forces the §2 conversation
again (if it genuinely cannot supply a `DueWindow`, that is a design signal for a new subtype — not
a nullable field).

### Dependency directions

`Presentation → Ledger → Sources → {Rails, Reporting}`; everything reads `Identity`. No cycle. Rails
and Reporting do not know the Ledger exists; the Ledger does not know Rails or Reporting exist —
only the `Source` seam and the `ReportedItem` supertype. The done-side read the Ledger performs goes
through Reporting's query seam (`reports_for(SubjectId, Horizon) -> list[ReportedItem]`) — the
supertype only; the Ledger never sees `ReportedDirective`'s extra fields (Interface Segregation: the
one consumer of directives-as-authority is `DirectiveSource`).

---

## 3. Ownership of the non-advice invariant

The invariant — *every output is (authoritative source × reported state); never infer state; never
originate advice* — is owned by the **Ledger** module and enforced three ways, all structural:

1. **One mint.** `LedgerEntry` and `Citation` have sealed constructors, package-private to Ledger
   (language mechanism per stack: package-visibility / module-internal constructor / opaque type
   with a factory only Ledger links against). Presentation's entire input type is
   `list[LedgerEntry]`; it cannot construct one, and it has no other data dependency to render
   from. There is no second output path to audit: a reader verifying "can this system emit
   advice" checks one module.

2. **No slot for advice.** `LedgerEntry` carries a closed status enum and a `Citation`; the citation
   is non-optional and `ReportedBasis` is a closed sum with no "system judgment" variant. The
   nudge is not generated text — `NUDGE_ASK_DOCTOR` is a *join outcome* (an `OpenUnplanned` basis:
   a reporter-flagged open directive with no covering `Expectation`), rendered by a fixed template
   ("You reported X is open and no plan covers it — ask your doctor."). The system contributes set
   operations, never content.

3. **No door for inferred state.** Medical state has exactly one entry point — Reporting — and
   every `ReportedItem` requires an `Attestation` naming the human asserter. `SubjectFacts` is
   declared-only and closed. The Ledger's inputs are typed as `(list[Expectation],
   list[ReportedItem])`; it computes matchings over them and cannot create either. "Overdue" and
   "open-with-no-plan" are relations *between* reported data and declared rails — computed absence,
   not inferred presence; the cited basis in those cases (`Absent(FactsSnapshot)`,
   `OpenUnplanned(ReportId)`) is itself reported/declared data, so even a gap output is a genuine
   (source × reported) join, satisfying the invariant *in the same type* rather than as an
   exception to it.

The doctor-user case needs no special handling: a clinician's instruction enters as a
`ReportedDirective` (attested, reported), becomes an `Expectation` via `DirectiveSource`, and exits
only through the same mint. Authority raises the tier; it never opens a bypass.

## 4. The `manager → subject(s)` primitive

One edge type, `Grant(manager, subject, role)`, and nothing else:

- **Self-management** = a grant from a principal to a subject record (there is no "my own file"
  special case; a person's own file is a subject they hold an `owner` grant on).
- **Family** = several grants from one principal.
- **A doctor's panel** = many grants with `role = clinician`.

Multi-subject is therefore not a feature — it is the absence of a 1:1 restriction. Every seam that
touches medical data takes a `SubjectId` and is authorized by grant lookup; no API is shaped
"for me" vs "for my dependents" vs "for my patients". `role` is the ceiling-honest amount of
differentiation the MVP needs: it gates *actions* (a `clinician` grant may file
`ReportedDirective`s with `authority = doctor_instruction`; `owner`/`caregiver` may file plain
reports and prescriptions-as-received) — it never changes the data model or the output path.
Organizations, delegation chains, and consent workflows are out (§7); the primitive was chosen so
they attach *to the edge* later without reshaping it.

## 5. The expected-vs-done join

Deterministic, pathway-agnostic, and the same procedure for every rail — exit criterion 3's
"computed, not enumerated":

```
entries_for(subject, horizon):
  facts    = Identity.facts(subject)                          # declared only
  expected = ⋃ source.expectations_for(subject, facts, horizon)   # both Source impls
  reported = Reporting.reports_for(subject, horizon)          # supertype view

  for e in expected:
    match = best report r with r.activity == e.activity and r.occurred_at ∈ tolerance(e.window)
    → DONE     Citation(e.source, Fulfilled(r.id))            if match
    → DUE      Citation(e.source, Absent(facts_snapshot))     if no match, window open
    → OVERDUE  Citation(e.source, Absent(facts_snapshot))     if no match, window passed

  for d in open directives with no covering expectation match:
    → NUDGE_ASK_DOCTOR  Citation(d.as_source_ref, OpenUnplanned(d.id))

  for r in reported not matched and UNCODED or un-expected:
    → UNMATCHED_REPORT  Citation(r.attestation_as_basis)      # surfaced, never interpreted
```

The join key is `(SubjectId, ActivityCode, time window)` — nothing else. This is why the published
`ActivityCode` vocabulary (§6) is the single most load-bearing decision in the system: expected and
done meet *only* on it. There are no per-pathway matchers, no fuzzy matching, no special cases per
source kind; a pathway that needs a matching rule the join key can't express is a future
conversation about the vocabulary, not a code branch in the Ledger. Provenance and tier arrive
already inside each `Expectation` and are copied, never recomputed — the Ledger physically cannot
assign a tier because no constructor for `SourceRef` is visible to it.

## 6. Day-zero vocabulary of the public seams

Per design-principles §7, decided normatively now, not discovered empirically later. Public seams
may speak **only**:

1. **Domain types defined here:** `PrincipalId, SubjectId, ReportId, PathwayId, Grant,
   SubjectFacts, RiskFlagCode, ActivityCode, ReportedItem, ReportedDirective, Attestation,
   PathwayDef, Expectation, DueWindow, SourceRef, ConfidenceTier, Citation, ReportedBasis,
   LedgerEntry`. All ids are distinct nominal types, not strings (§4, primitive obsession).
2. **Foundational cross-infrastructure set (closed):** ISO-8601 date/time and duration types of the
   host language's standard library; UTF-8 text; JSON as the serialization of the above at the HTTP
   edge. Nothing else — no ORM entities, no FHIR resources (FHIR is a *possible future source
   adapter's* internal concern, translated inside a `Source` implementation, never crossing a seam),
   no storage rows, no framework request/response types past the edge.
3. **Error vocabulary:** two public error types, matching the two distinct handlings that exist:
   `NotPermitted` (grant check failed — caller can re-request access) and `NotFound`. Storage and
   framework exceptions are translated at the seam; no subtype taxonomy until a caller
   demonstrably branches on one.

`ActivityCode` and `RiskFlagCode` are closed, versioned code lists owned by Reporting and Rails
respectively acting on a single shared registry file — they are the published language on which the
whole join operates, so they are governed as vocabulary (additions reviewed), not as data (edited
freely).

### Change-axis check (exit criterion 5)

- **New pathway** (e.g. add a colonoscopy schedule): author one `PathwayDef` — data — plus, at
  most, new `ActivityCode` entries in the registry. Rails is the single owner. Ledger, Sources,
  Identity, Presentation: zero changes.
- **New source type** (e.g. a national immunization registry feed): one new `Source`
  implementation + one `SourceRef.kind`/tier-mapping entry. It must emit the same four-field
  `Expectation`; if it honestly can't, that is the §2 unmeetable-bounds signal handled at the seam
  (a new specialization), never by nulling fields. Ledger join, account model, output types: zero
  changes.
- **New predicate need** inside eligibility: grammar extension inside Rails; the `Predicate` type
  never crosses a public seam, so the change cannot scatter.

## 7. Explicitly out of the MVP

- **The integrated overview (המכלול)** — no aggregation, dashboarding, or cross-pathway synthesis
  beyond the flat ledger. Nothing is pre-built "for it": the ledger's output type was floor-set by
  the MVP's presentation only.
- **Any inference:** no suspicion engine, no risk derivation, no auto-coding of report text
  (payloads are verbatim), no deriving `risk_flags` from reports. Structurally excluded, not just
  descoped (§3.3).
- **Interoperability:** no FHIR/HL7 ingestion, no EHR integration, no document/OCR intake. Each is
  a future `Source` or intake adapter behind existing seams.
- **Scheduling/notification engine:** the ledger computes states on read; push reminders, digests,
  and delivery channels are out.
- **Organizational identity:** clinics, staff hierarchies, consent/audit workflows beyond
  `Attestation` and `Grant`.
- **Pathway authoring tooling:** defs are hand-authored data; no editor, no validation UI.
- **Generalized rules engine, plugin framework, event sourcing, multi-region anything** — no MVP
  consumer exists for any of them; per the brief, building them would be speculation.

---

## Appendix — assumptions stated

- Delivery surface assumed to be a single web service + thin client; nothing in the design depends
  on it.
- "Horizon" (how far ahead expectations are expanded) is a Ledger read parameter with a default,
  not persisted state.
- Prescriptions in the MVP are modeled as `ReportedDirective(authority = prescription)` — i.e., as
  received-and-reported directives whose expected activity is the fill/administration; adherence
  tracking beyond that single expectation is out of scope.
- The tolerance function in the join (how near a report must be to a window to count) is a Ledger
  constant, not per-pathway data, until a real pathway demonstrates the need — duplication of a
  simple rule is cheaper than a speculative per-step knob (design-principles §10).
