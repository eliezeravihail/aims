# "Responsible doctor" MVP — synthesized architecture

*This is a single standalone design. It is not a union of the three candidates: on every axis it takes
the one structural choice that best serves the brief, and drops the alternatives. Where a candidate's
idea is load-bearing it is adopted whole; where two ideas collide the weaker one is named and cut in the
companion `divergence.md`.*

Governing principle inherited from all three arms and kept: **the system never holds a medical fact it
was not told, and never emits a sentence it cannot trace to a source × a report.** Everything below is in
service of making that *checkable*, *source-type-agnostic*, and *one-owner-extensible* at once.

---

## 0. Shape at a glance

Two persisted stores, one file library, one pure join, one sealed output type.

```
  manager ──grant──► subject          (access:   who may touch which file)
                        │
                        ▼
              reported_item log        (reported: append-only; the ONLY truth about the subject)
                        │  JoinFact projection (note/document/who stripped)
   rails/library/*.yaml │
   (files, not rows) ───┤
                        ▼
                   sources             (SourceRef · tier() · Expectation; two compilers)
                        │  Expectation[] + JoinFact[]
                        ▼
                  compute_ledger        (citation: the ONE producer of Citation)
                        │  Citation[]  (the only leaf type of subject content)
                        ▼
                       api             (render(); the only I/O; today is a parameter)
```

- **Persisted:** `manager`, `subject`, `grant`, `reported_item`, `document`, and an audit-only
  `ledger_snapshot`. Nothing else.
- **On disk, versioned with the code:** `rails/library/<pathway_id>/` (pathway YAML + golden fixtures).
- **Never stored as truth:** `Expectation`, `Citation`, `Ledger`. They are a pure function of
  `(pathway revisions, reported items, today)` and are recomputed on every read.

---

## 1. Data model

Identifiers are opaque. Codes are opaque namespaced strings `system:code` (`loinc:4548-4`,
`local:colonoscopy`, `moh:mmr.1`); matching is **string equality**, no terminology service (§7). A new
lab test or visit type is a new `code` — never an enum or schema change.

### 1.1 Access — `manager`, `subject`, `grant`, and the `Scope` capability

```
Manager [table] { id, login, created_at }
Subject [table] { id, label, created_by → Manager, created_at }     -- NO medical fields, NO login
Grant   [table] { manager_id, subject_id, role: owner | delegate, granted_at }   PK(manager_id, subject_id)

Scope   (in-memory, unforgeable) { manager_id, subject_id }
        -- constructed ONLY by access.open(manager, subject) after a Grant row is found
```

`Subject` is a person with a file, not an account. Age, sex, and any risk flag are **reported items**
(§1.2), not columns — the system holds no medical state it was not told. `role` governs *write*
authorization only (a `delegate` may not delete the subject); it is invisible to `sources` and
`citation` and **never reaches the join** (§3, §4).

### 1.2 Reported side — `reported_item` (append-only)

The single carrier of everything the subject's file knows. Items are immutable; a correction is a **new**
row that `supersedes` an old one. This is what makes every reference into this log a stable, resolvable
pointer.

```
ReportedItem [table] {
  id, subject_id,
  kind:           ItemKind                 -- CLOSED grammar of six, below
  code:           Code
  occurred_on:    Date
  payload:        Payload[kind]            -- typed per kind, schema-validated at ingest
  origin:         Origin { kind: clinician | lab | pharmacy | public_body | self, name?, ref? }
  attestation:    document | self_entered  -- set from "is a document attached?", NOT from login (§4.1)
  document_id?:   DocumentId               -- opaque upload; never parsed
  in_response_to: ItemId[]                 -- links declared BY THE REPORTER; never inferred
  supersedes?:    ItemId
  note?:          Text                     -- free text, OPAQUE to the join (stripped by JoinFact, §3)
  recorded_by:    ManagerId, recorded_at
}
Document [table] { id, subject_id, blob_ref, mime, uploaded_by, uploaded_at }
```

**The closed six-kind grammar (the load-bearing extensibility decision).** Every present and future
source type must express what it knows as one of these six, so the ledger never learns about source
types:

| kind | meaning | payload (all fields reported) |
|---|---|---|
| `fact` | a standing attribute | `{ code, value }`; reserved codes `dob`, `sex`, `flag:<code>` |
| `result` | a measured/observed outcome | `{ code, value?, unit?, flag?: normal \| abnormal }` — `flag` is what the **lab printed** |
| `event` | something done, no value | `{ code, dose? }` — a visit attended, a vaccine given |
| `instruction` | a clinician told the subject to do X | `{ instructs: MatchRule, due: Window? }` |
| `prescription` | a medication/order | `{ medication: Code, follow_up?: { instructs: MatchRule, due: Window } }` |
| `process` | an open/closed matter the subject is in | `{ key, action: opens \| closes \| plansFor, for_code? }` |

Two consequences carried from the candidates and kept:

- **`instruction`/`prescription` carry a `MatchRule` — the same closed vocabulary a pathway rail item
  uses (§1.3).** A doctor instruction is *structurally* a one-item rail authored by a clinician for one
  subject. This single decision lets the ledger treat guideline expectations and doctor expectations
  identically, and is why adding either source touches nothing downstream.
- **An open process exists only because a `process{opens}` item was reported** — never detected. A lab
  `result` with a reported `flag: abnormal` prompts the manager (in the UI) to file a `process{opens}`;
  the *system* never opens one. "No plan for an open process" is then a join over two reports (§5).

### 1.3 Expected side — `rails` (declarative pathway library, files not rows)

A pathway is **data, not code**, loaded, schema-validated, content-hashed, and pinned as a
`PathwayRevision`. It ships with its own goldens so a new pathway proves itself in CI.

```
rails/library/<pathway_id>/
  pathway.yaml            -- the rails
  fixtures/*.facts.json   -- sample subjects
  fixtures/*.ledger.json  -- the ledger each sample MUST reproduce (golden, CI-blocking)
```

```
Pathway {
  id, revision: ContentHash,                       -- pinned into every citation it produces
  title,
  authority: { body, document, url?, published },  -- REQUIRED by schema → provenance cannot be missing
  applies_when: Predicate,                          -- over reported facts only
  items: RailItem[]
}
RailItem { id, title,
           locator: Text,                           -- REQUIRED: "§4.2, p.13" — the citable spot
           applies_when?: Predicate,
           expects: MatchRule,                      -- which reported item would satisfy this
           schedule: Schedule }

MatchRule = { kind: ItemKind, code?, where?: FieldConstraint[] }        -- ops == != in
Schedule  = at_age { from, to? } | every { period, from_age? } | after { trigger: MatchRule, within }
Predicate = has(MatchRule) | age_between(D, D) | sex_is(Sex) | and | or | not | true
```

The grammar is **closed and total**: no expressions, no scripting, no lookup outside the subject's
facts. The only arithmetic anywhere is calendar arithmetic on `dob` and item dates. The schema **requires**
`authority` and every item's `locator`, so a rail author cannot add an expectation the source does not
state, and provenance can never be missing (criterion 4). The library ships day-zero with **two** pathway
instances (a well-baby immunisation schedule and an adult age/sex screening schedule) so "not hardcoded to
one example" is true on day one — same loader, same evaluator, no pathway-specific code anywhere.

### 1.4 Sources and expectations — `sources`

`SourceRef` is a **sealed sum type**; there is no `Source` table (a personal "source" *is* the
instruction/prescription item, referenced by id — no minting, no dual write). `tier()` is a **total,
exhaustive** function over it, so a new source variant fails to compile until its tier is defined.

```
SourceRef = Rail     { pathway_id, revision, rail_item_id, locator }        -- public guideline
          | Reported { item_id, kind: instruction | prescription }          -- clinician, this subject
          | Origin   { item_id }                                            -- the authoritative origin of
                                                                            --   a recorded item (lab/clinician)

Tier = T_guideline            -- Rail source (versioned public guideline with URI + locator)
     | T_clinician_documented -- Reported source, attestation = document
     | T_clinician_reported   -- Reported source, attestation = self_entered
     | T_recorded_only        -- Origin source (on file; nothing expected of it)

tier: SourceRef → Tier        -- exhaustive match; compiler-enforced (criterion 4, 5)

Expectation { source: SourceRef, expects: MatchRule, window: Window{from,to}, after_item?: ItemId }
```

Tiers are **categorical, not blended** — the design never computes a credibility score, because blending
would be an inference about a source. A Citation carries the tier *and* the reported attestation
separately, so "a T_guideline expectation satisfied by a self-stated event" displays as exactly that.

### 1.5 Output — the sealed `Citation`

```
sealed Citation {                       -- constructor PRIVATE to module `citation`
  id: hash(status, source, state, revision, as_of)   -- stable, reproducible
  status:  done | upcoming | due | overdue | no_plan | recorded | superseded   -- CLOSED; join/clock outcomes
  source:  SourceRef
  tier:    Tier                         -- = tier(source); stored, not free
  state:   StateRef
  window?: Window                       -- present for expectation-derived rows
  library_revision: ContentHash[]
  as_of:   Date
}                                       -- NO free-text field anywhere

StateRef = Matched     { item_ids }     -- done
         | NoneMatched { rule, window, nearest? }   -- upcoming | due | overdue ("nothing reported")
         | OpenProcess { item_id }      -- no_plan
         | Item        { item_id }      -- recorded / superseded

Ledger = { subject_id, as_of, library_revision, items: Citation[] }
LedgerSnapshot [table] { id, subject_id, as_of, library_revision, citations: jsonb, computed_at }
        -- audit-only append log of what was shown; NEVER read back into the join
```

The seven `status` values are pure relations between a window and a clock, or the presence/absence of a
linking report — none encodes a medical opinion. `recorded` is an **echo** citation for every non-superseded
item, so even the plain "my items" view is `Citation[]` and no route can carry subject content that
bypassed the gate.

---

## 2. Modules and boundaries

Seven modules, one dependency direction (arrow = "may import"), enforced by a module-boundary lint in CI.

```
vocab ─┬─► access ─┐
       ├─► reported┤ (reads access)
       └─► rails   │  (rails may NOT import reported — it never sees a subject store)
                   ▼
                sources        (reads rails + reported's JoinFact only; may NOT build a Citation)
                   ▼
                citation       (sealed Citation · compute_ledger · templates · render · integrity)
                   ▼
                 api           (the only I/O; may call access, reported writes, citation.compute_ledger)
```

| module | owns | must not |
|---|---|---|
| `vocab` | every closed enum + grammar the seams speak | contain logic |
| `access` | `manager`, `subject`, `grant`, `Scope`; the only constructor of `Scope` | know any medical kind |
| `reported` | the append-only item store, per-kind payload schemas, the `JoinFact` projection, documents | compute anything about expectations |
| `rails` | pathway schema, loader, revision pinning, predicate/schedule evaluator, goldens runner | import `reported`; do I/O beyond loading its files |
| `sources` | `SourceRef`, `tier()`, `Expectation`, the compilers `from_rails` + `from_reported` | construct a `Citation` |
| `citation` | the sealed `Citation`, `compute_ledger` (the join), `templates`, `render`, `integrity` | do I/O; read a clock; accept a manager or role |
| `api` | transport, auth handshake, request validation, snapshot logging | emit subject medical content other than `render(Ledger)` |

**One-owner change locality (criterion 5):**

| change | files touched | owner |
|---|---|---|
| new public pathway | one new dir under `rails/library/` (+ its goldens). **Zero code.** | rails |
| new public guideline (new authority) | same — a pathway file with a new `authority` block | rails |
| new **source type** (e.g. hospital discharge instruction) | one `sources` change: a `SourceRef` variant, its `tier()` row (exhaustive match won't compile until added), and a compiler function | sources |
| new reported **kind** that is not a source (e.g. `imaging`) | one `vocab` enum value + one `reported` payload schema; rails may reference it immediately | vocab+reported |

`citation`, `access`, and `api` appear in none of the first three rows. That is the extensibility claim,
and it holds because the closed six-kind grammar (§1.2) means the ledger never learns source types, and
because the exhaustive `tier()` and the pinned-file library force each addition into exactly one owner.

---

## 3. The non-advice invariant: ownership and structural enforcement

**Owner: the `citation` module** — small on purpose (~4 files), readable end-to-end, guarded by a
"no merge without the invariant suite green" CODEOWNERS rule.

**Statement.** Every output about a subject is a `Citation = SourceRef × StateRef`, where `SourceRef`
resolves to an authoritative source (public guideline, doctor instruction, prescription, or the recorded
item's origin) and `StateRef` resolves to reported items of that subject. No code path originates advice
text or derives a medical state. This holds for **every** user, including a doctor.

The enforcement is **by construction, not by checkpoint** — ten structural locks, each pinned by a
CI-blocking test:

1. **Sealed output type.** `Citation`'s constructor is module-private (branded type / `pub(crate)` /
   package-private — the arch test checks the language mechanism). There is no string field on it: to
   "say" anything you must point at a source row and report rows. *(arch test: no module but `citation`
   names the constructor.)*
2. **One producer, one route.** The only exported function returning `Citation` is
   `compute_ledger(exps, facts, today) → Ledger`. `api`'s subject-medical handlers are typed
   `Scope → Ledger`; there is no other return type in which subject content could travel. *(route-table
   test.)*
3. **The join cannot read free text, documents, or identity.** `compute_ledger` receives `JoinFact`, a
   projection of `ReportedItem` that **omits** `note`, `document_id`, and `recorded_by`. *(type test +
   property test: mutating `note` never changes the ledger.)* As defense-in-depth the compute path also
   holds a SELECT-only DB role, so it cannot record a state it "discovered."
4. **The join is pure and clockless.** `today` is a parameter; `citation` and `sources` import no I/O,
   HTTP, clock, or ML package. A ledger is therefore a replayable function of
   `(revisions, facts, today)`. *(arch test; no ML/LLM component exists anywhere in the MVP.)*
5. **Closed grammar, no escape hatch.** The `Predicate`/`Schedule`/`MatchRule` evaluators are pattern
   matches over the enumerated `vocab` ops — no `eval`, no plugin, no lookup outside the subject's facts.
   The only arithmetic is calendar arithmetic. *(grammar-enumeration test.)*
6. **Output language is finite.** `render(citation, locale)` instantiates a **fixed template per
   `status`** with slots drawn only from `SourceRef`/`StateRef` fields. The whole set of possible strings
   is `Templates × Data` — enumerable and reviewed like content. No template carries a verb of
   recommendation other than the fixed phrase **"Ask your doctor,"** and that phrase's `no_plan` status is
   emitted only for an `OpenProcess` state. *(template snapshot test.)*
7. **Provenance is inseparable.** `tier()` is an exhaustive match over `SourceRef`; every `Citation`
   carries `source` (with pathway revision + locator, or the clinician item id), `tier`, and the reported
   `attestation` of its evidence. There is no citation without a source — the type has no optional source
   field. *(compile + schema test.)*
8. **Fail-closed integrity.** Before `api` renders, `citation.integrity(ledger, facts, library)`
   re-resolves every `SourceRef` and `StateRef` against actual rows and revisions; a dangling reference
   aborts the response rather than degrading. *(runtime assertion + test.)*
9. **The doctor is not special.** `compute_ledger` has no manager or role parameter. A doctor is a
   `Manager` with grants; when they enter an instruction it is a `ReportedItem{kind: instruction}` the
   system will only *cite*, never speak in its own voice. Two managers with grants on one subject get
   byte-identical ledgers for the same `today`. *(signature + API-equality test.)*
10. **Authorization is a capability, not a habit.** Every `reported` repository method and every ledger
    read takes a `Scope`, never a bare `SubjectId`; `Scope` is unconstructible outside `access`. A handler
    that forgets to authorize **fails to compile.** *(arch test.)*

### 3.1 Derivation vs. inference (the line drawn explicitly)

Age from a reported `dob`, "is within window," "3 months after the instruction date" are **derivations**:
deterministic, lossless arithmetic on reported facts, each carrying the ids of the reports it used.
**Inference** — producing a state nobody reported ("this value is abnormal," "this person is high-risk")
— has nowhere to live: predicate atoms read only `fact` reports, there are no projections beyond `age(dob)`,
and a lab's `flag` is *reported data the lab printed*, never a value the system computes. If a guideline's
criterion needs a state ("high risk"), it must arrive as a reported `fact` — and the ledger then cites
*that report*.

---

## 4. The `manager → subject(s)` primitive

One relation and one capability. Self-care, family care, and a doctor's panel are the **same edge at
different cardinality** — there is no `Patient`, `Family`, or `Panel` type.

```
Grant(manager_id, subject_id, role)     Scope = access.open(manager, subject)
```

| scenario | rows |
|---|---|
| person tracking themselves | `Grant(A, S_A, owner)` |
| parent tracking two children | two `Grant` rows, `role: owner` |
| doctor with a panel | `Grant(D, S_i, owner\|delegate)` per patient — identical |
| child with a parent **and** a doctor | two `Grant` rows on one subject |
| grown child takes over their file | new `Grant(C, S_child, owner)`; the parent's edge is revoked |

"My subjects" is `SELECT subject_id FROM grant WHERE manager_id = ?`. Every route is `/subjects/{id}/…`
and resolves through `access.open`, which yields the `Scope` that every downstream call demands (§3, lock
10). Multi-subject is the cardinality of a join, not a feature.

### 4.1 Attestation and tier are set by evidence, not by login

`attestation ∈ {document, self_entered}` is fixed by **whether a document is attached**, never by the
reporter's account type. The MVP does not verify clinician identity, so a doctor's login **never** raises a
tier — only an attached document does. This is deliberate: it keeps "doctor user" from becoming a special
case anywhere, and keeps the tier honest (the authority is the document, not the login). A clinician's
undocumented instruction is `T_clinician_reported`, cited as the clinician's word; the same instruction
with the referral letter attached is `T_clinician_documented`.

---

## 5. The join: expected × reported → ledger

### 5.1 Inputs

```
facts : JoinFact[]    = reported.project(scope)                 -- immutable, note/document/who-free
exps  : Expectation[] = sources.from_rails(library, facts, today) ∪ sources.from_reported(facts)
today : Date          = api-supplied (server clock, or ?as_of= for replay)
```

`from_rails`, per pathway, evaluates `applies_when(facts)`, then per rail item turns `schedule` into a
concrete `Window`:

| schedule | window | `after_item` |
|---|---|---|
| `at_age{from,to}` | `[dob+from, dob+to]` (no `dob` fact → no expectation produced) | — |
| `every{period,from_age}` | `[today−period, today]` if age ≥ `from_age` | — |
| `after{trigger,within}` | one Expectation **per fact** matching `trigger`: `[fact.date, fact.date+within]` | that fact |

`from_reported` turns each `instruction` (and each `prescription.follow_up`) into an Expectation with
`source = Reported{item_id}`, `expects = payload.instructs`, `window = payload.due`, and `after_item` from
the reporter-declared `in_response_to`. **Guideline and doctor expectations are the same `Expectation`
type** and flow through the identical join.

### 5.2 The whole of `compute_ledger`

```
compute_ledger(exps, facts, today):
  out = []

  -- (A) expected vs done
  for e in exps:
    m = facts.filter(f => matches(e.expects, f) ∧ within(e.window, f.occurred_on) ∧ ¬superseded(f))
    if m ≠ ∅: out += Citation(done, e.source, Matched{m.ids}, window=e.window)
    else:     out += Citation(status_by_clock(e.window, today),        -- upcoming | due | overdue
                              e.source, NoneMatched{e.expects, e.window, nearest(e.expects, facts)},
                              window=e.window)

  -- (B) open process with no plan → nudge
  for f in facts where f.kind == process ∧ f.payload.action == opens ∧ ¬closed(f) ∧ ¬superseded(f):
    planned  = ∃ e ∈ exps : e.after_item == f.id
    answered = ∃ g ∈ facts : f.id ∈ g.in_response_to
    if ¬planned ∧ ¬answered:
              out += Citation(no_plan, Origin{f.id}, OpenProcess{f.id})

  -- (C) echo, so the plain "my items" view is also Citation[]
  for f in facts where ¬superseded(f):
              out += Citation(recorded, Origin{f.id}, Item{f.id})

  return Ledger{ as_of: today, library_revision, items: sort(out) }
```

Gaps are **never enumerated per pathway.** Every gap is either an `upcoming/due/overdue` from loop (A) or a
`no_plan` from loop (B), produced by the same two loops regardless of which pathways are loaded. "Open
process" is not inferred — a `process{opens}` report opened it, and it is unplanned because *no reported
expectation and no reported answer references it*. Both halves are reports.

### 5.3 Provenance and confidence tier travel with every item (criterion 4)

Every row is a `Citation`, so every row carries `source` (pathway revision + locator, or the clinician item
id, or the recorded origin), `tier = tier(source)`, the reported `attestation` of its evidence,
`library_revision`, and `as_of`. There is no field in which a row could exist without these; the type has
no optional source. The nudge template is the single fixed sentence keyed to `no_plan`, citing the report
that opened the process.

### 5.4 Correctness the join must satisfy (all CI-blocking property tests)

Referential (every `source`/`state` resolves) · Coverage (`|done ∪ upcoming ∪ due ∪ overdue| == |exps|`) ·
Echo (`|recorded| == |non-superseded facts|`) · Nudge soundness (every `no_plan` item is an open process,
unplanned, unanswered) · Determinism (same inputs → byte-identical ledger; ids are content hashes) ·
Role-blindness (two managers, one subject, one `today` → identical ledger).

---

## 6. Day-zero vocabulary the public seams may speak

These live in `vocab` and are the **only** words that cross a module boundary, the pathway file format, or
the ledger JSON. Everything else is an opaque `system:code`.

- **ItemKind** — `fact · result · event · instruction · prescription · process`
- **Reserved fact codes** — `dob · sex · flag:<code>`
- **Process action** — `opens · closes · plansFor`
- **Origin.kind** — `clinician · lab · pharmacy · public_body · self`
- **Attestation** — `document · self_entered`
- **Role** — `owner · delegate`
- **SourceRef kinds** — `rail · reported(instruction|prescription) · origin`
- **Tier** — `T_guideline · T_clinician_documented · T_clinician_reported · T_recorded_only`
- **Citation status** — `done · upcoming · due · overdue · no_plan · recorded · superseded`
- **StateRef kinds** — `Matched · NoneMatched · OpenProcess · Item`
- **Predicate ops** — `has · age_between · sex_is · and · or · not · true`
- **Schedule forms** — `at_age · every · after`
- **MatchRule** — `kind` + optional `code` + `where` (ops `== · != · in`)
- **Duration** ISO-8601 (`P6M`, `P50Y`) · **Date** ISO calendar date · **Code** opaque `system:code`
- **Pathway file keys** — `id · title · authority{body,document,url,published} · applies_when ·
  items[]{id,title,locator,applies_when,expects,schedule}`

Adding to any list above is a versioned change in its owning module. **Codes never need it** — a new test,
visit, vaccine, or milestone is just a new `system:code`.

**HTTP seam** (the only read of subject medical content is `/ledger`):

```
POST /managers                              → Manager
GET  /subjects                              → Subject[]        (the caller's grants)
POST /subjects                              → Subject          (+ owner Grant)
POST /subjects/{id}/custody                 → Grant            (share a subject)
POST /subjects/{id}/items                   → ItemId           (validated ReportedItem)
POST /subjects/{id}/documents               → DocumentId
GET  /subjects/{id}/ledger?as_of=YYYY-MM-DD → Ledger           (Citation[]; the ONLY medical read)
GET  /rails                                 → PathwayMeta[]     (catalog: id, title, authority, revision)
```

Ledger JSON is the `Citation` record verbatim plus `text: render(c, locale)`; clients render `text` and may
group by `status`/`tier`, and receive no other subject content. Labels and templates ship in Hebrew and
English; source snippets are quoted in the source's own language.

---

## 7. Explicitly out of the MVP

- **The integrated overview (*המכלול*, Pillar 2)** — no cross-subject or cross-process synthesis object,
  no table, no route, no placeholder.
- **Any inference** — suspicion flags, risk scoring, abnormality detection, trend detection, credibility
  blending. A lab's printed flag is reported data; the system computing a flag is not built. The
  closed-grammar + `age`-only-projection rule closes the door structurally.
- **Automated document understanding** — OCR/NLP of PDFs. Documents are opaque attachments; fields are
  transcribed by the manager.
- **External integrations** — EHR/FHIR/HL7, HMO portals, pharmacy and lab feeds. A new source type is one
  `sources` compiler; none beyond the required classes is built.
- **A terminology service** — ICD/LOINC/SNOMED mapping. Codes are opaque strings; equality is string
  equality.
- **Notifications** — push/email/SMS. The nudge is a ledger row, not a message; the ledger is pull, so
  there is nothing to run offline.
- **Invitation/consent flows, clinician identity verification, audit UI, subject-facing logins.** The
  `Grant` relation supports sharing; the product surface and identity proofing do not.
- **Persisted expectations/ledger, caching beyond `(reports, revisions)` keying, event sourcing.**
  Recomputation is cheap and removes a second source of truth; `ledger_snapshot` is audit-only and never
  read back.
- **Medication adherence, interactions, dosing, contraindications.**
- **Any ML/LLM component, including for "just wording."** Would be a second output path; the design allows
  exactly one.

---

## 8. Exit-criteria trace

| criterion | where satisfied |
|---|---|
| 1 — boundary enforced by architecture | §3 locks 1–8: sealed single-constructor `Citation`, one `/ledger` route, `JoinFact` strips free text/documents/identity, closed clockless pure join, fixed templates, fail-closed `integrity()` |
| 2 — one `manager → subject(s)` primitive | §4: `Grant` edge + unforgeable `Scope`; self/family/panel are cardinalities; a forgotten authorization fails to compile |
| 3 — expected & reported distinct, gaps joined | §1.2 vs §1.3, §5.2: rails/instructions produce `Expectation[]`, items produce `JoinFact[]`, gaps are two generic loops — no per-example enumeration |
| 4 — provenance + tier inseparable from every item | §1.4/§5.3: `SourceRef` + exhaustive `tier()` + reported attestation are fields of the only output type; `authority`+`locator` required by schema |
| 5 — new pathway / source type is one owner's change | §2 locality table: pathway = one file dir + goldens (zero code); source type = one `sources` compiler forced complete by exhaustive `tier()` |
| 6 — scoped to Pillar 1 and stated sources | §7; two persisted stores, one file library, seven modules, two shipped pathway instances, nothing built for the overview or for inference |
