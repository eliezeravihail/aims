# "Responsible doctor" MVP — architecture (verifiability-first)

Design stance: every structural choice below is made so that the two things the product promises —
**(a) the system only ever emits citations and (b) the expected-vs-done ledger is correct** — can be
*checked* by a compiler, a schema validator, an architecture test, or a property test, rather than
trusted to code review. Where a choice trades flexibility for checkability, checkability wins.

The document is organised as: 0. proof obligation · 1. data model · 2. modules and boundaries ·
3. ownership and enforcement of the citation invariant · 4. `manager → subject(s)` · 5. the join
(expected × reported → ledger) · 6. day-zero vocabulary · 7. verification plan · 8. out of scope ·
9. assumptions.

---

## 0. The proof obligation, stated up front

The invariant the architecture must make *provable*:

> **Every output** about a subject is a `Citation = (SourceRef × StateRef)` where `SourceRef` resolves to
> an authoritative source (public guideline, doctor instruction, prescription) and `StateRef` resolves to
> reported items of that subject. **No code path** originates advice text or derives a medical state.

The proof sketch the design is built to support (each step maps to a structural feature, and §7 lists
the test that pins it):

1. The read API for subject medical content has **one return type**, `Ledger = Citation[]`. *(P1)*
2. `Citation` is a **sealed type**: its constructor is private to the `citation` module. *(P2)*
3. Inside `citation`, the constructor is called from **exactly one function**, `compute_ledger`, and every
   call site passes a `SourceRef` taken from an `Expectation` or a fact's `origin`, and a `StateRef` built
   from the subject's facts. *(P3)*
4. `compute_ledger` is **pure** (no I/O, no clock, no network, no model), takes only closed-grammar inputs,
   and the grammar contains only calendar arithmetic and equality/ordering on reported values. Therefore it
   cannot infer a medical state. *(P4)*
5. Citation **text** is produced only by `render(citation)`, which instantiates a **fixed template per
   `CitationKind`** with slots drawn only from `SourceRef`/`StateRef` fields. Therefore the set of all
   possible output strings is `Templates × Data` — finite, enumerable, reviewable. *(P5)*
6. **Manager role never reaches the join** (`compute_ledger` has no manager parameter), so a doctor user
   gets the same gate as anyone else. *(P6)*

Everything else is in service of these six steps.

---

## 1. Data model

Notation is a neutral typed pseudo-code. Persistence is a relational store (PostgreSQL assumed);
tables map 1:1 to the record types marked `[table]`.

### 1.1 Identity — `access`

```
Manager  [table] { id: ManagerId, login: Login, created_at }
Subject  [table] { id: SubjectId, label: Text, created_by: ManagerId, created_at }
Grant    [table] { manager_id: ManagerId, subject_id: SubjectId, role: Role, granted_at }
           -- PK (manager_id, subject_id); Role ∈ { owner, delegate }

Scope    (in-memory only, unforgeable) { manager_id, subject_id }
           -- constructed ONLY by access.open(manager, subject) after a Grant row is found
```

`Subject` carries no medical data. A person managing themselves is a `Grant` row like any other.
There is no `Patient`, `FamilyMember`, or `Clinician` type. (§4.)

### 1.2 Reported side — `reported`

An **append-only fact log** per subject. Items are immutable; corrections are new items that
`supersede` old ones. This is what makes every `StateRef` a stable, resolvable pointer.

```
ReportedItem [table] {
  id:             ItemId
  subject_id:     SubjectId
  kind:           ItemKind              -- closed enum, §6
  occurred_on:    Date
  payload:        Payload[kind]         -- typed per kind, schema-validated at ingest
  origin:         Origin                -- who authored the underlying thing
  attestation:    document | self_entered
  document_id?:   DocumentId            -- opaque upload; never parsed by the system
  in_response_to: ItemId[]              -- links declared BY THE REPORTER (e.g. "this appointment
                                        --   was for referral X"); never inferred
  supersedes?:    ItemId
  note?:          Text                  -- free text; OPAQUE to the join (§3, INV-5)
  recorded_by:    ManagerId
  recorded_at:    Timestamp
}

Origin { kind: clinician | lab | pharmacy | public_body | self, name?: Text, ref?: Text }

Document [table] { id, subject_id, blob_ref, mime, uploaded_by, uploaded_at }
```

Payload examples (all fields are **reported**, including flags):

```
Payload[dob]                { date }
Payload[sex]                { value: female | male | other }
Payload[lab_result]         { code: Code, value?: Number, unit?: Text, flag?: normal | abnormal }
                            -- `flag` is what the LAB printed; the system never sets it
Payload[procedure_done]     { code: Code }
Payload[vaccination]        { code: Code, dose?: Int }
Payload[diagnosis]          { code: Code }                  -- as stated by a clinician, reported
Payload[referral]           { to: Text, for_code?: Code }
Payload[appointment]        { with: Text, for_code?: Code }
Payload[doctor_instruction] { instructs: MatchRule, due: Window?, in_response_to: ItemId[] }
Payload[prescription]       { medication: Code, follow_up?: { instructs: MatchRule, due: Window } }
```

Note that `doctor_instruction` and `prescription` carry an `instructs: MatchRule` — the **same
closed vocabulary** rail items use (§1.3). A doctor instruction is therefore *structurally* a rail
item authored by a clinician for one subject. That single decision is what lets the ledger treat
guideline expectations and doctor expectations identically.

### 1.3 Expected side — `rails` (declarative pathway library)

A pathway is **data, not code**. It lives in the repository as one directory and is loaded,
schema-validated, content-hashed, and pinned as a `PathwayRevision`.

```
rails/library/<pathway_id>/
  pathway.yaml            -- the rails (schema below)
  fixtures/*.facts.json   -- sample subjects
  fixtures/*.ledger.json  -- the ledger each sample MUST produce (golden)
```

```
Pathway {
  id:           PathwayId
  revision:     ContentHash                     -- computed at load, pinned into every citation
  title:        Text
  authority: {                                  -- REQUIRED by schema → provenance cannot be missing
    body:       Text                            -- e.g. the national screening programme
    document:   Text
    url?:       Url
    published:  Date
  }
  applies_when: Predicate                       -- closed grammar, §6
  items:        RailItem[]
}

RailItem {
  id:               RailItemId
  title:            Text
  locator:          Text                        -- REQUIRED: "§4.2, p.13" — the citable spot
  applies_when?:    Predicate
  expects:          MatchRule                   -- what reported item would satisfy this
  schedule:         Schedule                    -- when it is expected (closed grammar)
}

MatchRule { kind: ItemKind, where?: FieldConstraint[] }         -- e.g. lab_result, code == "HbA1c"
Schedule  = at_age   { from: Duration, to?: Duration }           -- one-off by age
          | every    { period: Duration, from_age?: Duration }   -- recurring
          | after    { trigger: MatchRule, within: Duration }    -- follow-up bound to a fact
Predicate = has(MatchRule) | age_between(Duration, Duration) | sex_is(Sex)
          | and(P, P) | or(P, P) | not(P) | true
```

The grammar is *closed and total*: there is no escape hatch (no expressions, no scripting, no
lookups outside the subject's facts). The only arithmetic anywhere is calendar arithmetic on
`dob` and item dates. This is the concrete content of "never infers".

### 1.4 Sources and expectations — `sources`

```
SourceRef = Rail     { pathway_id, revision, rail_item_id, locator }        -- public guideline
          | Reported { item_id, kind: doctor_instruction | prescription }   -- clinician for this subject
          | Origin   { item_id }   -- the authoritative origin of a reported item (lab, clinician);
                                   --   used only for Recorded and AskDoctor citations

Tier = T1_clinician_documented    -- Reported source with attestation = document
     | T2_public_guideline         -- Rail source
     | T3_clinician_self_entered   -- Reported source with attestation = self_entered
     | T4_recorded_only            -- Origin source (nothing expected; the item is simply on file)

tier: SourceRef → Tier            -- total function; exhaustive match over SourceRef (compiler-enforced)

Expectation {                     -- the normalised "expected" unit, whichever side it came from
  source:      SourceRef
  expects:     MatchRule
  window:      Window { from: Date, to: Date }
  after_item?: ItemId             -- set when the expectation is a follow-up to a specific fact
}
```

### 1.5 Output — `citation` (the sealed type)

```
sealed Citation {                 -- constructor private to module `citation`
  id:               CitationId    -- hash(kind, source, state, revision, today) → stable, reproducible
  kind:             CitationKind  -- Done | ExpectedOpen | AskDoctor | Recorded
  source:           SourceRef
  tier:             Tier          -- = tier(source); stored, not passed
  state:            StateRef
  template:         TemplateId    -- = template_for(kind); fixed per kind
  library_revision: ContentHash[] -- pathway revisions in force
  as_of:            Date          -- the `today` used
}

StateRef = Matched     { item_ids: ItemId[] }                             -- Done
         | NoneMatched { rule: MatchRule, window: Window, nearest?: ItemId } -- ExpectedOpen
         | OpenProcess { item_id: ItemId }                                -- AskDoctor
         | Item        { item_id: ItemId }                                -- Recorded

Ledger = { subject_id, as_of, library_revision, items: Citation[] }

LedgerSnapshot [table] { id, subject_id, as_of, library_revision, citations: jsonb, computed_at }
  -- audit-only append log of what was shown; never read back into the join
```

`Citation` has **no free-text field**. Wording exists only in `templates`, keyed by kind and locale.

---

## 2. Modules and boundaries

Seven modules, one dependency direction. The arrow means "may import".

```
                 ┌────────┐
                 │ vocab  │  closed enums + grammars (ItemKind, SourceKind, Tier, Predicate, Schedule, MatchRule)
                 └───┬────┘
      ┌──────────────┼───────────────┐
      ▼              ▼               ▼
 ┌─────────┐   ┌──────────┐    ┌──────────┐
 │ access  │   │ reported │    │  rails   │   rails may NOT import reported (they never see a subject store)
 └────┬────┘   └────┬─────┘    └────┬─────┘
      │             │  JoinFact      │  Pathway
      │             └───────┬────────┘
      │                     ▼
      │              ┌────────────┐
      │              │  sources   │  SourceRef · Tier · Expectation · the two compilers
      │              └─────┬──────┘
      │                    ▼
      │              ┌────────────┐
      │              │  citation  │  sealed Citation · compute_ledger (the join) · templates · render · integrity
      │              └─────┬──────┘
      └──────────┬─────────┘
                 ▼
           ┌───────────┐
           │    api    │  HTTP/JSON; the only I/O layer; may call: access, reported (writes), citation.compute_ledger
           └───────────┘
```

| Module     | Owns                                                                                        | May depend on          | Must not                                                             |
|------------|---------------------------------------------------------------------------------------------|------------------------|----------------------------------------------------------------------|
| `vocab`    | Every closed enumeration and grammar the seams speak                                        | —                      | Contain logic                                                        |
| `access`   | `Manager`, `Subject`, `Grant`, `Scope`; the only constructor of `Scope`                     | `vocab`                | Know any medical kind                                                |
| `reported` | `ReportedItem` store, per-kind payload schemas, `JoinFact` projection, `Recorded` echo input | `vocab`, `access`      | Compute anything about expectations                                  |
| `rails`    | Pathway schema, library loader, revision pinning, predicate/schedule evaluator               | `vocab`                | Import `reported`; perform I/O beyond loading its own files          |
| `sources`  | `SourceRef`, `tier()`, `Expectation`, compilers `from_rails` and `from_reported`            | `vocab`,`rails`,`reported` (read-only `JoinFact`) | Construct a `Citation`                    |
| `citation` | `Citation` (sealed), `compute_ledger`, `templates`, `render`, `integrity`                   | `vocab`, `sources`     | Perform I/O; read a clock; accept a manager/role                     |
| `api`      | Transport, auth handshake, request validation, snapshot logging                             | everything above       | Build response text for subject content other than `render(Ledger)` |

**Change-locality guarantees (exit criterion 5):**

- *New pathway* → one new directory under `rails/library/`. Zero code changes. CI runs its goldens.
- *New source type* (e.g. a hospital discharge instruction) → one change in `sources`: add a `SourceRef`
  variant, its `tier()` row (the exhaustive match fails to compile until added), and a compiler. If the
  source arrives as a new reported kind, its payload schema is added in `reported` and the enum in `vocab`;
  `citation`, `access`, and `api` are untouched.
- *New reported kind* that is *not* a source (e.g. `imaging_done`) → `vocab` enum + `reported` payload
  schema. Rails may start referencing it in `MatchRule` with no further code.

---

## 3. Ownership and structural enforcement of the citation invariant

**Owner: the `citation` module.** It is small on purpose (~4 files) so it can be read end-to-end in
review and is the only module with a "no changes without the invariant test suite green" CODEOWNERS
rule.

### 3.1 The gate is a type, not a checkpoint

Most designs enforce "outputs must be citations" with a middleware that inspects responses. That is a
convention: a new endpoint can bypass it. Here the enforcement is by **construction**:

- `Citation` is `sealed`; its constructor is module-private (Rust `pub(crate)` on private fields /
  TypeScript branded type with a non-exported factory / Java package-private constructor — pick the
  language's mechanism, the test in §7 checks it).
- The **only** exported function that returns `Citation` values is
  `compute_ledger(expectations: Expectation[], facts: JoinFact[], today: Date) → Ledger`.
- `api` handlers for subject medical content are typed `Scope → Ledger`. A handler that wants to say
  anything about a subject has no type it can return other than `Ledger`, and no way to make a
  `Citation` other than calling the join.

### 3.2 "Never originates advice" — the output language is finite

`render(c: Citation, locale) → Text` looks up `templates[locale][c.kind]` and substitutes slots.
Slots are an enumerated set drawn from `SourceRef` and `StateRef` fields
(`{authority.body}`, `{locator}`, `{rail.title}`, `{window.from}`, `{item.occurred_on}`, ...).
Templates for day zero (English shown; Hebrew mirrors):

| Kind           | Template (slots in braces)                                                                                                    |
|----------------|-------------------------------------------------------------------------------------------------------------------------------|
| `Done`         | "{source.title} — recorded: {state.items} on {state.dates}. Source: {source.authority}, {source.locator}."                     |
| `ExpectedOpen` | "{source.title} — expected between {window.from} and {window.to}; nothing matching is on file{, last recorded: nearest}. Source: {source.authority}, {source.locator}." |
| `AskDoctor`    | "{state.item.kind} recorded on {state.item.date} ({state.item.origin}) has no instruction or pathway step on file. **Ask your doctor** what comes next." |
| `Recorded`     | "{state.item.kind} recorded on {state.item.date} ({state.item.origin})."                                                        |

No template contains a verb of recommendation other than the fixed phrase "Ask your doctor", and the
`AskDoctor` kind can only be emitted for a `StateRef.OpenProcess` whose item's `kind.opens_process`
is true in `vocab`. Templates are content, reviewed like content, and diffed in CI.

### 3.3 "Never infers state" — the join's inputs are projections with no room to infer

- `compute_ledger` receives `JoinFact`, a projection of `ReportedItem` that **omits** `note`,
  `document_id`, and `recorded_by`. The join cannot read free text, cannot open documents, cannot see
  who typed the item.
- The only operators available to any evaluator are the closed `Predicate`/`Schedule`/`MatchRule`
  grammars. The evaluator is a pattern match over that grammar; there is no `eval`, no plugin hook, no
  scripting. Adding an operator is a `vocab` change that a grammar-enumeration test will flag.
- No ML/LLM component exists in the MVP anywhere; `citation` and `sources` have zero I/O dependencies
  (arch test).
- `today` is a parameter. The join never reads a clock, so a ledger is a pure function of
  `(pathway revisions, facts, today)` and can be replayed exactly.

### 3.4 Fail-closed integrity at the seam

Before `api` renders a `Ledger`, `citation.integrity(ledger, facts, library)` re-resolves every
`SourceRef` and `StateRef` against the actual rows and revisions. Any dangling reference aborts the
response (HTTP 500 with a diagnostic id) rather than degrading. This turns "the citation is inseparable
from its source" from a promise into a runtime assertion with a test.

### 3.5 The doctor user

A doctor is a `Manager` with many `Grant`s. When a doctor enters an instruction, it is stored as a
`ReportedItem{kind: doctor_instruction}` — the doctor originated it, the system will only cite it.
`compute_ledger` has no manager or role parameter, so there is no code path in which a doctor's
session can widen what the system says. (§7, P6.)

---

## 4. The `manager → subject(s)` primitive

One relation, `Grant(manager_id, subject_id, role)`, and one capability type, `Scope`.

- **Self**: Alice creates subject "Alice" → `Grant(alice, s_alice, owner)`.
- **Family**: Alice creates subjects for two children → two more `Grant` rows.
- **Clinic**: Dr. B is a manager with 300 `Grant(dr_b, s_i, owner|delegate)` rows.
- **Shared subject** (two parents): two `Grant` rows on one subject. Structurally supported; the
  invitation UI is out of MVP (§8).

Enforcement, so it is checkable rather than habitual:

- Every repository method in `reported` and every read of a ledger takes a `Scope`, **never** a bare
  `SubjectId`. `Scope` has no public constructor outside `access`. A handler that forgets authorization
  fails to compile because it cannot produce a `Scope`.
- `access.open(manager_id, subject_id) → Scope | Denied` is the single lookup.
- `api` listing routes are `GET /subjects` (= the manager's grants) and everything else is under
  `/subjects/{id}/…` resolved through `open`.
- Role affects **write** permissions only (`delegate` may not delete a subject). It is not visible to
  `sources` or `citation`.

---

## 5. The join: expected × reported → ledger

### 5.1 Inputs

```
facts:  JoinFact[]      = reported.project(scope)              -- immutable, note-free
exps:   Expectation[]   = sources.from_rails(library, facts, today)
                        ∪ sources.from_reported(facts)
today:  Date
```

`sources.from_rails` evaluates, per pathway: `applies_when(facts)`; then per rail item:
`applies_when`, and turns `schedule` into a concrete `Window`:

| Schedule                     | Window                                                        | `after_item` |
|------------------------------|---------------------------------------------------------------|--------------|
| `at_age{from,to}`            | `[dob+from, dob+to]` (requires a `dob` fact; otherwise no expectation is produced) | — |
| `every{period,from_age}`     | `[today−period, today]` if age ≥ from_age                     | —            |
| `after{trigger,within}`      | one Expectation **per fact** matching `trigger`: `[fact.date, fact.date+within]` | that fact |

`sources.from_reported` turns each `doctor_instruction` (and each `prescription.follow_up`) into an
Expectation with `source = Reported{item_id}`, `expects = payload.instructs`, `window = payload.due`,
`after_item = payload.in_response_to[0]` if present.

### 5.2 The algorithm (the entire body of `compute_ledger`)

```
compute_ledger(exps, facts, today):
  out = []

  -- (A) expected vs done
  for e in exps:
    m = facts.filter(f => matches(e.expects, f) && within(e.window, f.occurred_on) && !superseded(f))
    if m ≠ ∅:  out += Citation(Done,         e.source, Matched{m.ids})
    else:      out += Citation(ExpectedOpen, e.source, NoneMatched{e.expects, e.window, nearest(e.expects, facts)})

  -- (B) open process with no plan → nudge
  for f in facts where vocab.opens_process(f.kind, f.payload) && !superseded(f):
    planned  = ∃ e ∈ exps : e.after_item == f.id
    answered = ∃ g ∈ facts : f.id ∈ g.in_response_to
    if !planned && !answered:
               out += Citation(AskDoctor, Origin{f.id}, OpenProcess{f.id})

  -- (C) echo of what is on file (so even "your items" view passes the gate)
  for f in facts where !superseded(f):
               out += Citation(Recorded, Origin{f.id}, Item{f.id})

  return Ledger{ as_of: today, library_revision, items: sort(out) }
```

`opens_process` is a table in `vocab` (day zero: `referral` → true; `diagnosis` → true;
`lab_result` → true iff the **reported** `flag == abnormal`; `prescription` → true iff it has
`follow_up`; everything else false). It reads reported fields only.

Gaps are therefore never enumerated per pathway: **every** gap is either an `ExpectedOpen` from (A) or
an `AskDoctor` from (B), and both are produced by the same two loops regardless of which pathways are
loaded.

### 5.3 What the ledger row carries (exit criterion 4)

Every row is a `Citation`, so every row carries: `source` (with pathway revision + locator, or the
clinician item id), `tier`, `state` (the item ids, or the exact rule + window that found nothing),
`library_revision`, and `as_of`. There is no field in which to put a row *without* these; the type has
no optional source.

### 5.4 Correctness properties the join must satisfy (tested, §7)

- **Referential**: every `source` and `state` in the output resolves against the inputs.
- **Coverage**: `|Done ∪ ExpectedOpen| == |exps|` — every expectation yields exactly one row.
- **Echo**: `|Recorded| == |facts non-superseded|`.
- **Emptiness**: `compute_ledger([], [], d) == []`; `compute_ledger(exps, [], d)` contains only
  `ExpectedOpen` rows whose sources are all `Rail` with `at_age`/`every` schedules that do not
  require `dob`… i.e. in practice empty, since day-zero schedules all need `dob`. Stated as: no
  `Done`, no `AskDoctor`, no `Recorded` rows when there are no facts.
- **Nudge soundness**: every `AskDoctor` row's item has `opens_process = true`, no expectation
  with `after_item == it`, and no fact answering it.
- **Determinism**: same inputs → byte-identical `Ledger` (ids are content hashes).
- **Role-blindness**: the function signature has no role; trivially true, but also asserted at the API
  layer: two managers with grants on the same subject get identical ledgers for the same `today`.

---

## 6. Day-zero vocabulary (what the public seams may speak)

All of these live in `vocab` and are the *only* words allowed across the three public seams:
the HTTP API, the pathway file format, and the ledger JSON.

**ItemKind** — `dob`, `sex`, `lab_result`, `procedure_done`, `vaccination`, `diagnosis`, `referral`,
`appointment`, `doctor_instruction`, `prescription`

**Origin.kind** — `clinician`, `lab`, `pharmacy`, `public_body`, `self`

**Attestation** — `document`, `self_entered`

**SourceRef kinds** — `rail`, `reported` (doctor_instruction | prescription), `origin`

**Tier** — `T1_clinician_documented`, `T2_public_guideline`, `T3_clinician_self_entered`, `T4_recorded_only`

**CitationKind** — `Done`, `ExpectedOpen`, `AskDoctor`, `Recorded`

**StateRef kinds** — `Matched`, `NoneMatched`, `OpenProcess`, `Item`

**Predicate ops** — `has`, `age_between`, `sex_is`, `and`, `or`, `not`, `true`

**Schedule forms** — `at_age`, `every`, `after`

**MatchRule** — `kind` + `where` over payload fields with ops `==`, `!=`, `in`

**Duration** — ISO-8601 (`P6M`, `P50Y`); **Date** — ISO calendar date

**Code** — an opaque string namespaced by the pathway author (`loinc:4548-4`, `local:colonoscopy`).
The MVP does **not** ship a terminology service; equality is string equality. (§9.)

**Pathway file keys** — `id, title, authority{body, document, url, published}, applies_when, items[]{id,
title, locator, applies_when, expects, schedule}`

**HTTP seam**

```
POST   /managers                                   → Manager
GET    /subjects                                   → Subject[]   (the caller's grants)
POST   /subjects                                   → Subject     (+ owner Grant)
POST   /subjects/{id}/items                        → ItemId      (validated ReportedItem; document upload separately)
POST   /subjects/{id}/documents                    → DocumentId
GET    /subjects/{id}/ledger?as_of=YYYY-MM-DD      → Ledger      (the ONLY read of subject medical content)
GET    /rails                                      → PathwayMeta[] (catalog: id, title, authority, revision — subject-free)
```

Ledger JSON shape is the `Citation` record verbatim plus `text: render(c, locale)`; clients render
`text` and may group by `kind`/`tier`. Clients receive no other subject content.

---

## 7. Verification plan — the invariant as a test suite

Each row is a named, CI-blocking test. P-numbers refer to §0.

| Id     | Proves | Mechanism                                                                                                                                                         |
|--------|--------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| INV-1  | P2     | Architecture test: no module other than `citation` references the `Citation` constructor (import-linter / ArchUnit / `cargo` visibility + a grep-based guard).    |
| INV-2  | P1     | Type-level: every `api` route under `/subjects/{id}` that returns a body returns `Ledger`, `Subject`, `ItemId`, or `DocumentId`. Enumerated route table test.       |
| INV-3  | P3     | Unit: inside `citation`, the constructor is called only in `compute_ledger`; AST test counts call sites.                                                          |
| INV-4  | P4     | Arch test: `citation` and `sources` import no I/O, clock, HTTP, or ML packages. Grammar test: the `Predicate`/`Schedule`/`MatchRule` evaluators match exactly the enumerated ops in `vocab`. |
| INV-5  | P4     | Type: `JoinFact` has no `note`/`document_id`/`recorded_by` field; property test shows changing `note` never changes the ledger.                                    |
| INV-6  | P5     | Template test: for every kind and locale, `render` with all slots replaced by sentinel markers yields a string in the committed template table; snapshot-diffed.  |
| INV-7  | P6     | API test: two managers with different roles on one subject receive byte-identical ledgers.                                                                        |
| INV-8  | crit.4 | Schema: `authority.*` and `items[].locator` are required in `pathway.yaml`; a pathway missing either fails to load (test with a bad fixture).                       |
| INV-9  | crit.4 | Runtime: `integrity()` rejects a ledger with a dangling ref (test by deleting a revision after computing).                                                          |
| INV-10 | crit.2 | Type: no repository method accepts `SubjectId`; all accept `Scope`; `Scope` is unconstructible outside `access` (arch test).                                       |
| INV-11 | crit.3 | Property tests in §5.4 (referential, coverage, echo, emptiness, nudge soundness, determinism) run against generated facts and generated pathways.                  |
| INV-12 | crit.5 | Golden: each `rails/library/*/fixtures` pair must reproduce exactly; adding a pathway with no code change is exercised by a CI job that adds a synthetic one.       |
| INV-13 | crit.5 | Exhaustiveness: `tier()` is an exhaustive match — adding a `SourceRef` variant without a tier row fails compilation.                                               |

Because the invariant is expressed as types, closed grammars, and a single constructor site, the review
question for any PR is mechanical: *did INV-1..13 stay green?* rather than *does this look like advice?*

---

## 8. Explicitly out of the MVP

- The integrated overview (*המכלול*) — no cross-process summary, no timeline view beyond the ledger list.
- Any **inference**: suspicions, risk scores, "you may have…", trend detection, abnormality detection by
  the system (a lab's own printed flag is reported data; the system computing a flag is not).
- Free-text understanding: NLP over `note`, OCR of uploaded documents, parsing of PDFs. Documents are
  opaque attachments.
- External integrations: EHR/FHIR/HL7, HMO portals, pharmacy feeds, lab feeds. All items are entered
  by a manager.
- A terminology service (ICD/LOINC/SNOMED mapping). Codes are opaque strings.
- Notifications/reminders (push, email, SMS). The nudge is a ledger row, not a message.
- Sharing/invitation flows between managers, audit UI, consent management. The `Grant` relation
  supports them; the product surface does not.
- Medication interaction checks, dosing, contraindications.
- Any ML/LLM component, including for "just wording".
- More than one guideline class beyond what ships in `rails/library/` (day zero: an adult
  age/sex-based screening schedule and a well-baby schedule as **instances**; the machinery is
  pathway-agnostic).

---

## 9. Assumptions made

- Guidelines are **transcribed by maintainers** into `pathway.yaml` with locators; the authority
  block cites the public document. Curation quality is a content-review concern, not an architectural
  one — but the schema makes omission impossible.
- Managers enter items in **structured form** (kind + payload). Free text is allowed as a `note` for
  their own use only. This is the price of a checkable join and is stated to users at entry.
- Doctor instructions are entered using the same `MatchRule` vocabulary (a small picker: kind, code,
  due window). An instruction that cannot be expressed in the vocabulary is stored as a `Recorded`
  item with a note and does not become an expectation — it will not produce a false `ExpectedOpen`,
  and if it was `in_response_to` an open process, it counts as answering it.
- `today` is supplied by `api` from the server clock (or from the `as_of` query parameter, which
  makes replay and testing trivial).
- Persistence is PostgreSQL with `reported_items` append-only (no `UPDATE`/`DELETE` grants for the
  application role), so `StateRef` pointers never dangle in normal operation; `integrity()` covers the
  abnormal case.
- Locale: templates ship in Hebrew and English; the template table is the only localised surface.
