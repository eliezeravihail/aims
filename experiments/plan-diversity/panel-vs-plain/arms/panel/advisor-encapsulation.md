# "Responsible Doctor" MVP — Architecture

*Design stance: every stated rule of this product is owned in exactly one place, and the load-bearing
invariants are made **unforgeable by construction** — you cannot accidentally emit advice, forge a
citation, detach a confidence tier, or touch a subject you were not granted, because the types and
seams give you no way to express those programs. Where a rule cannot be broken, it does not need to be
policed.*

---

## 1. The product in one paragraph, restated as invariants

The system is a care **coordinator**, not an advisor. It maintains one personal **medical tracking
file** per subject, fuses **authoritative sources** (public guidelines, doctor instructions,
prescriptions) with the subject's **reported** state, and shows an **expected-vs-done ledger** with
gaps. Its two hard rules:

- **I1 — Citation-only output.** Every output is a `Citation = (authoritative Source × Reported
  basis)`. The system never originates advice and never infers medical state — for every user,
  including doctor users.
- **I2 — Record, not body.** The system only ever speaks about the *tracking file* ("your file shows
  no colonoscopy result in the guideline's window"), never about the *person* ("you haven't had a
  colonoscopy" is an inference the system is structurally unable to make — see §5.3).

Everything below is arranged so that I1 and I2 are properties of the type system and module graph,
not of code review.

---

## 2. Day-zero published vocabulary (what public seams may speak)

Per the shared-kernel/published-language rule, the set of types allowed to cross **any** public seam
is decided now, normatively, and is closed. Two groups:

**(a) Foundational, cross-infrastructure types** (small, agreed, replacement would rewrite
everything):

| Type | Meaning |
|---|---|
| `Instant`, `LocalDate`, `DateWindow` | ISO-8601 time; a window is `[from, until)` |
| `ConceptCode` | our own coded-clinical-concept value type: `(scheme, code, display)` — schemes are a closed MVP list (an internal event taxonomy; room for LOINC/ATC codes *as data*, not as a dependency) |
| `LangText` | attributed human-readable text; see §5.4 — the only string type output seams accept |

**(b) Our own domain types** (defined in one `vocabulary` package that every context depends on;
no context's internal types ever cross a seam):

| Type | Meaning | Minted by (sole constructor owner) |
|---|---|---|
| `SubjectHandle` | opaque capability proving "this caller may act on this subject in this scope" | **Accounts** (§6) |
| `ManagerId`, `SubjectId` | opaque identities (never cross a seam bare where a `SubjectHandle` is required) | Accounts |
| `EventKind` | closed vocabulary of trackable clinical events (a `ConceptCode` in the event scheme + typed params, e.g. `LabResult(concept)`, `Procedure(concept)`, `Prescription(concept)`, `DoctorInstruction`) | vocabulary |
| `ReportedFact` | one attributed entry in a subject's file | **Subject Record** (§5.3) |
| `Attribution` | who reported: `Self \| ManagerOnBehalf \| Clinician \| DocumentImport` | Subject Record |
| `SourceRef` | reference to one authoritative source, carrying provenance **and** `ConfidenceTier` inseparably (tier is a field of `SourceRef`, not a parallel lookup) | **Sources** (§5.2) |
| `ConfidenceTier` | closed ordered enum: `PublicGuideline < ClinicianInstruction < Prescription` *(ordering is an MVP policy owned by Sources; illustrative)* | Sources |
| `Expectation` | one expected item: `(EventKind, DateWindow, SourceRef, match-predicate)` | **Expected side** producers (§7.1) |
| `ReportedBasis` | what the file says relative to a predicate: `MatchedFacts([ReportedFact]) \| NoMatchingReport(DateWindow)` | Subject Record |
| `Citation` | `(SourceRef × ReportedBasis)` — **private constructor; only the Ledger can mint one** | **Ledger** (§5.1) |
| `LedgerEntry` | `Satisfied(Citation) \| Due(Citation) \| Overdue(Citation) \| OpenWithoutPlan(Citation, Nudge.AskYourDoctor)` | Ledger |
| `Nudge` | closed enum, MVP has exactly one member: `AskYourDoctor` | Ledger |
| Error types | `NotAuthorized`, `UnknownSubject`, `RejectedReport(reason)` — one type per distinct caller handling, phrased in caller concepts; implementation exceptions never escape a seam | each seam's owner |

Nothing else crosses a seam: no ORM entities, no storage rows, no HTTP DTO leaks inward, no vendor
result objects, no free-form `string` in an outbound position (see `LangText`, §5.4).

---

## 3. Data model

Storage shapes are private to each context; what follows is the *conceptual* model (the persisted
form is each owner's business — a reader of a seam never learns a column name).

```
Accounts
  Manager        (managerId, credentials-ref)
  Subject        (subjectId, demographics: dob, sex-at-birth)   -- reported at enrollment
  Grant          (managerId, subjectId, scope: {View, Report, Administer}, grantedBy, at)
                  -- self-management = Grant(managerId of the person, own subjectId, Administer)

Sources
  Source         (sourceId, class: PublicGuideline | ClinicianInstruction | Prescription,
                  provenance, tier: ConfidenceTier, excerpts: [LangText])
    provenance   PublicGuideline    -> (publisher, title, version, effectiveDate, locator)
                 ClinicianInstruction / Prescription
                                    -> (clinician display, date, backing FactId)   -- see §7.1

Pathway Library (data, not code)
  PathwayDef     (pathwayId, version, sourceRef,                 -- the guideline it cites
                  applicability: predicate over SubjectProfile,  -- declarative: age/sex/risk flags
                  steps: [StepDef])
  StepDef        (stepId, expected EventKind, dueRule: offset|recurrence over anchor,
                  matchPredicate: (EventKind, DateWindow) template,
                  opensProcess: bool)            -- marks episode-opening kinds (see §7.3)

Subject Record (append-only journal per subject)
  ReportedFact   (factId, subjectId, EventKind, occurredAt, Attribution, reportedAt,
                  payload: typed per EventKind, attachments-ref)
  SubjectProfile (derived VIEW over reported demographics + reported risk-flag facts;
                  contains only what was reported — no derivation beyond restating reports)

Ledger (computed, not stored authoritatively; cacheable)
  LedgerEntry    (subjectId, Expectation, Citation, status)
```

Two deliberate absences: there is **no free-text "recommendation" field anywhere**, and there is
**no stored "inferred condition"** — the schema has no cell an inference could live in.

---

## 4. Module structure and boundary graph

Five bounded contexts plus a thin presentation layer. Arrows are the *only* allowed compile-time
dependencies (all pointing at published seams, never at internals):

```
                 ┌────────────────────────────────────────────┐
                 │            vocabulary (shared kernel)      │
                 └────────────────────────────────────────────┘
                        ▲        ▲         ▲          ▲
   ┌───────────┐   ┌─────────┐  ┌────────────────┐  ┌───────────────┐
   │ Accounts  │   │ Sources │  │ Pathway Library │  │ Subject Record│
   └───────────┘   └─────────┘  └────────────────┘  └───────────────┘
        ▲               ▲               ▲                  ▲
        │               └───────┐       │        ┌─────────┘
        │                     ┌─┴───────┴────────┴─┐
        │                     │       Ledger       │   ← sole minter of Citation
        │                     └────────────────────┘
        │                               ▲
   ┌────┴───────────────────────────────┴────┐
   │           Presentation / API            │   ← can only utter LedgerEntry,
   └─────────────────────────────────────────┘     ReportedFact echoes, and errors
```

| Context | One-sentence reason to change | Public seam (complete list) |
|---|---|---|
| **Accounts** | the manager→subject grant model changes | `enroll`, `grant`, `authorize(managerId, subjectId, scope) -> SubjectHandle` |
| **Sources** | a source class, its provenance shape, or the tier policy changes | `register(class-specific intake) -> SourceRef`, `describe(SourceRef) -> provenance + excerpts` |
| **Pathway Library** | a rail is added/versioned or the rail schema changes | `expectationsFor(SubjectHandle, SubjectProfile, asOf) -> [Expectation]` (an `ExpectationProducer` — §7.1) |
| **Subject Record** | what counts as a valid report, or matching semantics, changes | `submitReport(SubjectHandle{Report}, draft) -> ReportedFact \| RejectedReport`; `profile(SubjectHandle) -> SubjectProfile`; `evaluate(SubjectHandle, matchPredicate) -> ReportedBasis` |
| **Ledger** | the join rules or gap taxonomy change | `ledgerFor(SubjectHandle, asOf) -> [LedgerEntry]` |
| **Presentation** | delivery surface changes | HTTP/UI; renders only published vocabulary |

Tell-don't-ask at every hop: the Ledger never pulls raw rows and decides outside their owner —
it *tells* the Pathway Library "give me this subject's expectations" (applicability decided inside),
and *tells* the Subject Record "evaluate this predicate against yourself" (matching semantics —
kind comparison, window logic, unit tolerance — decided inside the record). No seam returns data
whose interpretation rules live in the caller.

---

## 5. Invariant I1/I2 — ownership and structural enforcement

The exit criterion is "one place every output must pass through that can *only* emit a
`(source × reported-state)` citation." Four locks, each removing a whole class of accidental
violation:

### 5.1 `Citation` has a private constructor; the Ledger is its sole minter

`Citation` lives in the vocabulary package but its constructor is module-private to Ledger
(package-private / internal / friend — mechanism per implementation language; the design commitment
is: **one construction site**). Its factory signature is total and demanding:

```
Citation.of(source: SourceRef, basis: ReportedBasis) -> Citation     // Ledger-internal only
```

- Both arguments are themselves unforgeable: a `SourceRef` only comes out of Sources (tier welded
  on at registration — §5.2), and a `ReportedBasis` only comes out of Subject Record's `evaluate`.
  So a valid `Citation` is *evidence* that an authoritative source was joined against the actual
  file — there is no way to construct one from thin air, and therefore no way to launder an
  invented recommendation into output shape.
- **Provenance and tier are inseparable** (exit criterion 4) not by a rule but by shape: tier is a
  field *of* `SourceRef`, `SourceRef` is a field *of* `Citation`, and no seam accepts or emits a
  tier or provenance detached from its `SourceRef`.

### 5.2 The output seam's type admits nothing but citations

Presentation depends only on the Ledger seam, whose sole return type is `[LedgerEntry]`, and every
`LedgerEntry` variant **carries a `Citation` by construction** — there is no variant without one.
The nudge is not a message the system composes; it is the `OpenWithoutPlan` variant, whose payload
is a `Citation` (source: the rail definition that declares this kind opens a process; basis: the
opening fact + `NoMatchingReport` for a plan) plus the closed `Nudge.AskYourDoctor` token.
Presentation renders tokens through fixed templates. A developer who wants to output "you should
start statins" has no type to put it in — the compiler is the reviewer.

**Doctor users are not a bypass:** a doctor is just a `Manager` (§6) and reaches the same single
Ledger seam with the same types. There is no clinician-mode API.

### 5.3 State is reported, never inferred — enforced at the Subject Record's write seam

- The **only** write path into a subject's file is `submitReport`, which *requires* an
  `Attribution`. No internal module holds a write capability: Ledger, Pathways, and Sources have
  read-only seams to the record; nothing in the system can author a fact about a subject.
- The record answers questions only about **itself**: `evaluate` returns `MatchedFacts` or
  `NoMatchingReport(window)` — both are statements about the file's contents (I2). The system
  cannot phrase "the patient hasn't done X"; it can only phrase "no report of X exists in this
  window," and that phrasing is fixed by the `ReportedBasis` type, not by discipline.
- `SubjectProfile` is a restating view of reported facts (reported DOB, reported risk flags). The
  Pathway Library predicates on it, so even *applicability* decisions trace to reports, never to
  derived suspicion.

### 5.4 System-authored free text cannot exist in output

Every human-readable string in an outbound type is a `LangText`, which is constructible in exactly
two ways: **(a)** `LangText.quoted(SourceRef, excerpt)` — verbatim, attributed source text, minted
by Sources at registration; **(b)** `LangText.template(key)` — a key into a closed, reviewed
template table owned by Presentation ("Due per {source}", "This open item has no plan — ask your
doctor"). There is no `LangText.of(string)`. Advice-shaped prose therefore has no constructor —
the strongest form of "never originates advice": the sentence cannot be built.

**Ownership summary (exit criterion 1):** the non-advice invariant is owned by the **Ledger**
(sole `Citation` minter, sole output producer), with its raw materials guarded upstream by
**Sources** (unforgeable `SourceRef`+tier) and **Subject Record** (unforgeable `ReportedBasis`,
write-only-by-report). One place to audit each.

---

## 6. The `manager → subject(s)` primitive

One abstraction, zero special cases (exit criterion 2):

- A **Manager** is any authenticated principal. A **Subject** is any tracked person. A **Grant**
  links them with a scope (`View`, `Report`, `Administer`). Self-management, a parent with three
  children, and a doctor with 400 patients are the *same* shape — differing only in grant count and
  scope; no `FamilyAccount`, no `ClinicianPortal` type anywhere in the model.
- **Enforcement is capability-style, not check-style.** Every subject-scoped seam in every context
  takes a `SubjectHandle`, an opaque, short-lived value minted only by
  `Accounts.authorize(managerId, subjectId, scope)`. No seam in Sources, Pathways, Subject Record,
  or Ledger accepts a bare `SubjectId`. Authorization therefore cannot be *forgotten* at a call
  site — a call without a handle does not type-check. The rule "a manager touches only granted
  subjects" is owned in exactly one place (Accounts) and is bypassable nowhere, because the
  bypass cannot be expressed.
- Scope is baked into the handle (`SubjectHandle{Report}` vs `{View}`), so write seams can require
  the write-scoped handle type and read seams the read-scoped one — least privilege by signature.

*Assumption:* consent flows for creating grants (a patient authorizing a doctor) are reduced in
the MVP to an explicit grant action by the subject's administering manager; richer consent is out
of scope (§9).

---

## 7. Expected × Reported → the ledger

### 7.1 The expected side: one interface, two honest producers

`ExpectationProducer` is a real abstraction — two genuinely different implementations exist on day
one, both emitting the same complete type
`Expectation(EventKind, DateWindow, SourceRef, matchPredicate)`:

1. **Pathway Library** — compiles declarative `PathwayDef` rails against a `SubjectProfile`:
   applicability predicate → anchored due rules → expectations, each carrying the *guideline's*
   `SourceRef`. Rails are **data**; the interpreter is generic. Nothing outside this module knows
   any individual pathway exists (exit criterion 3: gaps are computed, never enumerated per
   example).
2. **Instruction Plans** — doctor instructions and prescriptions are dual-natured: they enter the
   system as `ReportedFact`s (they are reported items), and Sources registers each as a `Source`
   (they are authorities), keying provenance to the backing `factId`. This producer turns those
   sources into expectations (a prescription → expected fill/renewal; an instruction → its stated
   follow-ups), each carrying the *instruction's* `SourceRef` at its (higher) tier.

The interface is pinned from both sides: `Expectation` is exactly what the Ledger consumer needs
(what, when, on whose authority, how to check), and both producers can honestly fill every field —
neither fabricates, neither is flattened.

### 7.2 The join (owned by Ledger, and only there)

For each subject, `asOf` a moment:

```
for each e in producers.expectationsFor(handle, profile, asOf):
    basis = subjectRecord.evaluate(handle, e.matchPredicate)
    entry = match basis:
        MatchedFacts(fs)        -> Satisfied( Citation.of(e.sourceRef, basis) )
        NoMatchingReport(w) if asOf in e.window   -> Due(      Citation.of(e.sourceRef, basis) )
        NoMatchingReport(w) if asOf past e.window -> Overdue(  Citation.of(e.sourceRef, basis) )
```

Every entry — including "done" — carries its citation; provenance and tier ride inside
`e.sourceRef` untouched from registration to screen.

### 7.3 The nudge: "open process, no plan" as a join outcome, not a feature

`StepDef.opensProcess` (and the analogous flag on instruction-derived kinds) declaratively marks
episode-opening `EventKind`s in the rail library. The Ledger's second pass: for each reported fact
of an opening kind with **no expectation whose source chain covers it**, emit
`OpenWithoutPlan(Citation.of(railDef.sourceRef, MatchedFacts([openingFact]) ⊕ NoMatchingReport(plan-window)), Nudge.AskYourDoctor)`.
The authority cited is the rail that *declares* the kind process-opening; the basis is the file's
own contents. The nudge never says what the plan should be — it structurally can't (§5.4).

### 7.4 Change scenarios (exit criterion 5 — one owner per change)

| Change | Touches | Untouched |
|---|---|---|
| **New pathway** (e.g. add a well-baby schedule next to colorectal screening) | Pathway Library: one new `PathwayDef` (data) + its guideline registered in Sources via the existing `PublicGuideline` intake | Ledger, Accounts, Subject Record, Presentation, all other rails |
| **New source class** (e.g. a national immunization registry feed) | Sources: one new intake adapter + one line in the tier policy; if it yields expectations, one new `ExpectationProducer` in the same context | Citation, LedgerEntry, join logic, Accounts, Presentation |
| **New trackable event kind** | vocabulary: one `EventKind` entry (+ its typed payload); rails that use it | everything else — `evaluate` and the join are kind-generic |

---

## 8. Rule-ownership table (every stated rule, exactly one owner)

| Stated rule | Sole owner | Enforcement mechanism |
|---|---|---|
| Output = citation only; no originated advice | Ledger | private `Citation` constructor; `LedgerEntry` variants all carry one; `LangText` has no free-text constructor |
| Never infer state; speak about the file only | Subject Record | single attributed write seam; `ReportedBasis` is the only shape answers take |
| Tier travels with every item | Sources | tier is a field of `SourceRef`, minted once at registration |
| Manager acts only on granted subjects, scoped | Accounts | `SubjectHandle` capability required by every subject-scoped seam |
| What is expected, and when it's due | Pathway Library / Instruction Plans | declarative rails + generic interpreter behind `ExpectationProducer` |
| What counts as "done" / matching semantics | Subject Record | `evaluate(predicate)` — callers never see raw rows |
| Which events open a process needing a plan | Pathway Library | `opensProcess` flag in rail data |
| Doctor users get no privileged output path | Accounts + Ledger | doctors are Managers; there is no other output seam to reach |

---

## 9. Explicitly out of the MVP

- **The integrated overview (המכלול)** — Pillar 2 entirely; no schema, seam, or "hook" is reserved
  for it (a reserved hook is speculation the design refuses).
- **Any inference**: suspicion engines, risk scoring, "you may have…", derived conditions — the
  schema has no cell for them (§3) and the output types no constructor for them (§5.4).
- **Source types beyond the three MVP classes** — the intake seam per class exists because three
  classes exist *now*, not as a plugin bus for imagined feeds; FHIR/HL7 integration is out.
- **Notification delivery machinery** — nudges are ledger entries; push/email scheduling is out.
- **Rich consent and clinical-governance workflows** — grants are explicit administrative acts;
  audit trail beyond the append-only record and grant log is out.
- **Guideline authoring tooling / NLP extraction** — rails are hand-authored data in the MVP.
- **Localization beyond the template table**, analytics, and any doctor-side pathway editing.

*Standing assumptions:* single deployable service is sufficient at MVP scale (contexts are module
boundaries, not network boundaries — the seams are what would become service boundaries later, but
that split is not designed now); persistence per context behind its seam; identity provider is a
commodity dependency hidden inside Accounts.
