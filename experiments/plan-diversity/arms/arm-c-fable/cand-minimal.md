# "Responsible doctor" MVP — minimal-parts architecture

**Design stance.** One service, one relational database with five tables, a directory of declarative
pathway files, and four code modules. Nothing is persisted that can be recomputed; nothing is
abstracted that only one caller needs. Every structural element below exists because a sentence in the
brief demands it, and each element names that sentence.

Assumptions are marked **[A]** inline.

---

## 0. Shape at a glance

```
                       ┌──────────────────────────────────────────────┐
  manager (login) ───► │ accounts   manager · subject · grant         │
                       └───────────────┬──────────────────────────────┘
                                       │ grant check
                       ┌───────────────▼──────────────────────────────┐
  reported items ────► │ file       entry · document   (+ vocabulary)  │  ◄── the subject's REPORTED state
                       └───────────────┬──────────────────────────────┘
                                       │ read-only
  pathway YAML ──────► ┌───────────────▼──────────────────────────────┐
  (library on disk)    │ rails      library/*.yaml → Rail → Expectation│  ◄── the EXPECTED side
                       └───────────────┬──────────────────────────────┘
                                       │
                       ┌───────────────▼──────────────────────────────┐
                       │ ledger     join(Expectation, entry) → Citation│  ◄── owns the invariant
                       └───────────────┬──────────────────────────────┘
                                       │ Citation[] only
                       ┌───────────────▼──────────────────────────────┐
                       │ api        GET /subjects/{id}/ledger          │
                       └──────────────────────────────────────────────┘
```

- **Persisted:** `manager`, `subject`, `grant`, `entry`, `document`. That is the whole database.
- **On disk, versioned with the code:** `rails/library/pathways/*.yaml` and `rails/library/codes.yaml`.
- **Never persisted:** expectations, the ledger, citations. They are a pure function of
  `(entries, library version, today)` and are recomputed on every read. A subject's file is small
  (hundreds of rows at most), so there is no cache, no worker, no queue, no event bus.

---

## 1. Data model

### 1.1 Tables

```
manager    id, email, password_hash, created_at
subject    id, display_name, created_at
grant      manager_id → manager, subject_id → subject, created_at        PK (manager_id, subject_id)
document   id, subject_id → subject, uploaded_by → manager, blob_ref, uploaded_at
entry      id, subject_id → subject, kind, code, value, occurred_at,
           provenance, document_id → document (nullable), re → entry (nullable),
           follow_up_required (bool, default false), expects (json, nullable),
           reported_by → manager, reported_at
```

That is five tables. `subject` carries no medical fields at all — date of birth, sex, and any risk
flag are `entry` rows of kind `attribute`, because those are *reported* facts and the brief forbids the
system from holding any medical state it did not receive as a report.

### 1.2 `entry` — the single carrier of reported state

An `entry` is "the subject (or their manager) reported that *this* is so." Four kinds, closed enum:

| `kind`         | meaning                                                                | uses fields                                  |
|----------------|------------------------------------------------------------------------|----------------------------------------------|
| `attribute`    | a standing fact about the subject: DOB, sex, a reported risk flag       | `code` (`attr.*`), `value`                   |
| `done`         | something happened: a visit, a vaccine given, a screening, a lab result | `code`, `value?`, `occurred_at`, `follow_up_required` |
| `instruction`  | a doctor told the subject to do X (by / every …), possibly *re* a result | `expects`, `re?`, `occurred_at` = instruction date |
| `prescription` | a doctor prescribed a medication / course                               | `expects`, `re?`, `occurred_at` = prescription date |

`provenance` is a closed enum `{document, direct}`: *document* = the entry was entered from an attached
document (`document_id` set); *direct* = typed in with nothing attached (a verbal instruction, a
remembered date).

`expects` (instruction/prescription only) is the smallest declarative "rail" a clinician's note can
express — the same shape a pathway step uses (§5.1):

```json
{ "code": "visit.cardiology", "after": "0d", "before": "90d" }
{ "code": "lab.hba1c",        "after": "0d", "before": "120d", "repeat": "180d" }
{ "code": "med.metformin",    "after": "0d", "before": "30d",  "repeat": "30d" }
null                      ← "doctor said no action needed" (silences a finding, expects nothing)
```

`follow_up_required` on a `done` entry is set **as the source document states it** (a lab report's
abnormal flag, a radiology "recommend follow-up" line). The system never decides that a value is
abnormal; the reporter transcribes that the source said so.

`re` points an instruction/prescription at the `done` entry it responds to. This is what lets the ledger
tell "an open finding with a plan" from "an open finding with no plan" (§5.3) without inferring anything.

### 1.3 `document`

A blob plus who uploaded it. No OCR, no parsing **[A: out of MVP]** — a document exists to (a) be the
provenance that raises an entry's tier and (b) be linked from the citation so the person can open the
original. Fields are transcribed by the manager.

### 1.4 What is deliberately *not* a table

- **Pathways** — files in the repo, not rows (§5.1). They change by pull request, are reviewed like code,
  and have a version string. A pathway table would add write endpoints, an admin UI, and a migration
  story that nothing in the brief asks for.
- **Expectations / ledger / citations** — derived (§0).
- **Roles on `grant`** — **[A]** every grantee has full read/write on the subject's file. Family and
  doctor need the same rights in the MVP; roles are a future force (§7).

---

## 2. Modules and boundaries

Four modules plus a thin HTTP layer. Dependencies point strictly downward; no module imports from one
above it.

| module     | owns                                                              | may read                       | may write         |
|------------|-------------------------------------------------------------------|--------------------------------|-------------------|
| `accounts` | `manager`, `subject`, `grant`; login; `assert_grant(manager, subject)` | its own tables            | its own tables    |
| `file`     | `entry`, `document`; the vocabulary enums (§6); the `tier()` map   | its own tables                 | its own tables    |
| `rails`    | `library/` (pathway YAML + `codes.yaml`); `Rail`, `Expectation`; loader + validator | `file` entries (read-only) | nothing   |
| `ledger`   | `Citation`; the join                                              | `rails`, `file` entries (read-only) | **nothing**  |
| `api`      | HTTP routes, session, JSON                                        | all of the above through their public functions | via `accounts`/`file` only |

Public functions (the whole internal API surface):

```
accounts.assert_grant(manager_id, subject_id)            → ok | 403
accounts.create_subject(manager_id, display_name)        → subject_id   (also creates the grant)
accounts.share(manager_id, subject_id, other_manager_id) → grant        (grantee may add grantees)

file.add_entry(manager_id, subject_id, EntryInput)       → entry_id     (validates code ∈ codes.yaml)
file.add_document(manager_id, subject_id, blob)          → document_id
file.entries(subject_id)                                 → [Entry]       (read-only view)
file.tier(source_kind, provenance)                       → Tier

rails.applicable(attributes: [Entry]) → [Rail]           (library pathways whose applies_when holds)
rails.from_entry(entry: Entry)        → Rail | None      (instruction/prescription → single-step rail)
rails.expand(rail, anchor_date, dones: [Entry], today)   → [Expectation]

ledger.build(subject_id, today)       → [Citation]       (the only producer of Citation)
```

`ledger` and `rails` are handed a **read-only** repository — at the database level a role with `SELECT`
only **[A: Postgres/SQLite; either works]** — so "the system never infers state" is not a code-review
rule but an absence of write capability in the modules that compute.

---

## 3. The non-advice invariant: ownership and structural enforcement

**Owner: `ledger`.** It is the only module that can construct a `Citation`, and `Citation` is the only
medical output type the service has.

### 3.1 The type

```
Citation
  subject_id
  verdict     : done | upcoming | due | overdue | no_plan          (closed enum, join outcomes only)
  source      : { kind: pathway | instruction | prescription,
                  ref:  "<pathway_id>@<version>" | "<entry_id>",
                  tier: T1 | T2 | T3,
                  title, publisher?, url?, document_id? }           (copied verbatim from the pathway's
                                                                     citation block or the entry/document)
  expected    : { code, after, before } | null                     (null only for no_plan)
  evidence    : [ { entry_id, kind, code, occurred_at, provenance } ]   ← length ≥ 1, always
```

The constructor is private to `ledger` and rejects: a missing `source`; an empty `evidence` list; any
field not in the schema. **There is no free-text field.** Every string in a `Citation` is copied from
either a pathway file's `citation:` block, a `codes.yaml` label, or an `entry`/`document` row — i.e. it
is traceable to an authoritative source or a report.

Why `evidence` is *always* non-empty, even for an item that is merely "due": an expectation only
exists because a rail applied, and a rail applies only because reported `attribute` entries satisfied
its `applies_when` (or because a reported `instruction` entry exists). Those entries are the evidence.
So a "due" citation reads: *per [Ministry of Health well-baby schedule 2024] × [you reported DOB
2025-03-02], `vax.mmr.1` is due 2026-03-02..2026-04-02*. The join is visible in every item, not just
in the "done" ones.

### 3.2 Why no path can originate advice

1. **One output type, one producer, one route.** `api` exposes exactly one read of the file's medical
   content: `GET /subjects/{id}/ledger → Citation[]`. Every other route echoes what the manager just
   wrote (`entry`, `document`, `subject`) or is account plumbing. Nothing else can carry a medical
   sentence to the user.
2. **Verdicts are join outcomes, not judgements.** The enum is the set of relations between a window and
   a date: done (a matching `done` entry lies in the window), upcoming (today < after), due (today in the
   window, no match), overdue (today > before, no match), no_plan (a `follow_up_required` finding has no
   `instruction`/`prescription` with `re` pointing at it). None of these encodes a medical opinion.
3. **The nudge is fixed.** `no_plan` is the only "nudge", and the client template for it has exactly one
   sentence with one slot: *"Ask your doctor about ‹finding› (‹source›, ‹date›) — no instruction is on
   file."* There is no slot in which a recommendation could appear.
4. **Rails cannot condition on results.** The library validator rejects any `applies_when` key that is
   not an `attr.*` code (§5.1). A pathway therefore cannot say "if HbA1c > 6.5 then …"; that decision
   belongs to a doctor, arrives as an `instruction` with `re:` the result, and is cited as *the
   doctor's* instruction. The only arithmetic the system performs on reported data is date arithmetic
   (age from reported DOB, windows from anchors).
5. **Compute modules cannot write.** `rails` and `ledger` hold a SELECT-only handle (§2). The system
   cannot "discover" a state and record it; the only writers of `entry` are the manager-facing
   `file.add_*` calls, each stamped with `reported_by`.
6. **A doctor user is not special.** A doctor is a `manager` with grants. Whatever they know enters the
   system as an `entry` of kind `instruction`/`prescription` and comes back out as a `Citation` whose
   `source` *is that entry* with a tier set by its provenance (§5.2). A doctor cannot push text to a
   patient's ledger; they can only add an instruction that the ledger will cite as theirs.

### 3.3 Rendering

The server returns structured `Citation` JSON; the web client renders it with one template per
`verdict`, filling slots only from `Citation` fields. **[A]** The client is part of this codebase and
the templates are the whole of its medical copy. No LLM, no generated prose, anywhere.

---

## 4. The `manager → subject(s)` primitive

```
grant (manager_id, subject_id)         many-to-many, no other columns beyond created_at
```

- **A person managing themself:** one `manager`, one `subject`, one `grant`. There is no "self" flag;
  the subject is simply a subject. **[A]** Sign-up creates all three rows.
- **A parent managing a family:** one `manager`, N `subject` rows, N `grant` rows.
- **A doctor managing patients:** one `manager`, M `subject` rows, M `grant` rows — identical.
- **A patient who also has a doctor:** two `manager` rows, one `subject`, two `grant` rows. Sharing is
  `accounts.share`, which is "insert a grant"; any current grantee may do it **[A]**.

Every route is `/subjects/{id}/…` and every handler's first line is `accounts.assert_grant`. There is no
family object, no practice object, no patient-list object; "my subjects" is `SELECT subject_id FROM
grant WHERE manager_id = ?`. Multi-subject is the cardinality of a join table, not a feature.

---

## 5. Expected vs. reported — the join

### 5.1 The expected side: pathway rails as files

`rails/library/pathways/<id>.yaml`, one file per pathway, validated at boot:

```yaml
id: il-moh-well-baby
version: "2024-03"
citation:
  publisher: Israel Ministry of Health
  title: Routine childhood immunisation schedule
  url: https://…
  retrieved: "2026-01-10"
applies_when:                      # predicates over attr.* codes ONLY (validator-enforced)
  attr.dob: { age_max: 6y }
anchor: attr.dob                   # the attribute entry whose value is day zero for this rail
steps:
  - code: vax.hepb.1
    after: 0d
    before: 7d
  - code: vax.dtap_ipv_hib.1
    after: 2m
    before: 3m
  - code: vax.mmr.1
    after: 12m
    before: 13m
```

```yaml
id: il-moh-adult-screening
version: "2025-01"
citation: { publisher: Israel Ministry of Health, title: Preventive screening for adults, url: https://…, retrieved: "2026-01-10" }
applies_when:
  attr.dob: { age_min: 50y, age_max: 74y }
anchor: attr.dob
steps:
  - code: screen.colorectal
    after: 50y
    before: 51y
    repeat: 10y
    satisfied_by: [screen.colonoscopy, screen.fit]     # which done-codes count; default [code]
  - code: screen.mammography
    after: 50y
    before: 52y
    repeat: 2y
    only_if: { attr.sex: female }                      # per-step predicate, same attr.* rule
```

A **Rail** is the loaded, validated form of one pathway *or* of one instruction/prescription entry
(`rails.from_entry` builds a one-step rail whose `citation` is the entry itself, `anchor` is
`occurred_at`, and step is the entry's `expects`). Both kinds are the same shape from here on — this is
the one abstraction the brief's "public guideline **and** the subject's own instructions" forces, and
it is why adding either kind of source touches nothing downstream.

**Expansion** (`rails.expand`) is a small pure function: for each step, compute the window from the
anchor; if `repeat`, find the latest matching `done` entry and roll the window forward from it. It emits
`Expectation { code, satisfied_by, after, before, rail }`. `Expectation` is internal — it is never
exposed, because an expectation without its evidence is precisely the kind of unjoined output the
brief forbids.

The library ships day-zero with **two** pathways (above) so that "not hardcoded to one example" is true
on day one: same loader, same expander, no pathway-specific code anywhere.

### 5.2 Source provenance and confidence tier

Tier is a total function of `(source kind, provenance)`, owned by `file.tier`:

| source                                        | tier | label            |
|-----------------------------------------------|------|------------------|
| pathway (published guideline)                 | T1   | public guideline |
| instruction / prescription, provenance=document | T2 | clinician document |
| instruction / prescription, provenance=direct | T3   | reported verbally |

**[A]** The MVP does not verify clinician identity, so a manager's account type never raises a tier —
only an attached document does. This keeps "doctor user" from becoming a special case anywhere and
makes the tier honest: the authority is the document, not the login.

Tier is copied into `Citation.source.tier` at construction; it cannot be separated from the citation
because there is no other object that carries it. Provenance of the *done* side travels too: each
`evidence` item carries its entry's `provenance`, so a "done, but from a verbal report" is visible.

### 5.3 The join (`ledger.build`)

```
entries   = file.entries(subject)
attrs     = latest entry per attr.* code
dones     = entries where kind = done
rails     = rails.applicable(attrs) ++ [rails.from_entry(e) for e in entries if e.expects]

for rail in rails:
  for exp in rails.expand(rail, anchor(rail, attrs), dones, today):
    match = dones with code ∈ exp.satisfied_by and occurred_at ∈ [exp.after, exp.before]
    verdict = done      if match
            | upcoming  if today < exp.after
            | due       if exp.after ≤ today ≤ exp.before
            | overdue   if today > exp.before
    emit Citation(verdict, source = rail.citation, expected = exp,
                  evidence = match or rail.trigger_entries)     # attrs that applied, or the instruction entry

for f in dones where f.follow_up_required:
  planned = any entry with re = f.id and kind ∈ {instruction, prescription}
  if not planned:
    emit Citation(no_plan, source = f.source (document or the entry itself),
                  expected = null, evidence = [f])
```

Gaps are `due`, `overdue`, `no_plan`. They are computed — there is no list of gaps anywhere in code or
data; there are rails, entries, and a comparison of dates. "Open process" is not inferred: a process is
open because a *source document said follow-up is required* and it is unplanned because *no reported
instruction references it*. Both halves are reports.

### 5.4 One-owner changes (exit criterion 5)

| change                                                     | files touched                                     | owner     |
|------------------------------------------------------------|---------------------------------------------------|-----------|
| new pathway (e.g. a pregnancy schedule)                    | `rails/library/pathways/<id>.yaml` (+ new codes in `codes.yaml`) | library |
| new source type that yields expectations (an insurer's protocol) | same — it is a pathway file                | library   |
| new way reported items arrive (a pharmacy export, a lab PDF flow) | an ingester that calls `file.add_entry`; if it needs a new `provenance` or `kind`, one enum + one row in the `tier` map, both in `file` | file |

`ledger`, `accounts`, and `api` are untouched by any of these. `ledger` knows only `Rail`, `Entry`,
`Tier`; `api` knows only `Citation`.

---

## 6. Day-zero vocabulary

These are the only nouns the public seams (HTTP API, pathway files, the ingest call) speak.

**Nouns:** `manager`, `subject`, `grant`, `entry`, `document`, `pathway`, `citation`.

**Enums (closed):**

- `entry.kind` — `attribute | done | instruction | prescription`
- `entry.provenance` — `document | direct`
- `citation.verdict` — `done | upcoming | due | overdue | no_plan`
- `citation.source.kind` — `pathway | instruction | prescription`
- `tier` — `T1 | T2 | T3`
- durations — `<n>d | <n>m | <n>y`

**Codes** (`rails/library/codes.yaml`; every `entry.code`, step `code`, and `satisfied_by` must be in
it; each has a human label). Day-zero set, namespaced:

```
attr.dob  attr.sex  attr.risk.family_colorectal            (reported facts only)
vax.hepb.1  vax.hepb.2  vax.dtap_ipv_hib.1..4  vax.mmr.1  vax.mmr.2  vax.rota.1..2  vax.pcv.1..3
screen.colorectal  screen.colonoscopy  screen.fit  screen.mammography  screen.cervical
lab.hba1c  lab.lipids  lab.cbc  bp.measure
visit.gp  visit.cardiology  visit.dermatology  visit.oncology  visit.wellbaby
med.<generic-name>                                         (open sub-namespace, still listed per name)
other                                                      (never matched by any rail; label = free text
                                                            entered by the manager, echoed only in the
                                                            entry list, never in a Citation)
```

**Routes:**

```
POST /subjects                              GET  /subjects
POST /subjects/{id}/grants
POST /subjects/{id}/entries                 GET  /subjects/{id}/entries
POST /subjects/{id}/documents
GET  /subjects/{id}/ledger[?today=…]        → Citation[]
```

**Pathway file keys:** `id version citation{publisher title url retrieved} applies_when anchor
steps[]{code after before repeat? satisfied_by? only_if?}`.

**[A]** Codes are internal; no LOINC/SNOMED mapping in the MVP. Labels in `codes.yaml` are
Hebrew+English pairs.

---

## 7. Explicitly out of the MVP

| not built                                                     | why it is out                                                     |
|---------------------------------------------------------------|-------------------------------------------------------------------|
| The integrated overview (המכלול)                              | Pillar 2; brief excludes it. No table, no route, no placeholder.  |
| Any inference: abnormal-value detection, risk scoring, "suspected" states, reminders derived from results | Forbidden by the boundary; the validator's `attr.*`-only rule closes the door structurally. |
| OCR / parsing of uploaded documents                           | A document is a blob; fields are transcribed. Parsing is an ingester later (§5.4 row 3). |
| EHR / HL7 / FHIR / lab-feed integrations                      | Unstated future sources; would be ingesters calling `file.add_entry`. |
| Clinician identity verification, roles/permissions on `grant`  | One right level is enough for family and doctor alike today.       |
| Push/email notifications, scheduled jobs, background workers   | The ledger is pull; there is nothing to run offline.               |
| Persisted ledger, caching, event sourcing, audit log beyond `reported_by`/`reported_at` | Recomputation is cheap and removes a second source of truth. |
| Pathway admin UI / pathway rows in the DB / per-subject pathway overrides | Pathways change by pull request; a doctor's deviation from a guideline is an `instruction` entry, cited as such. |
| External code systems, translation beyond the label pairs      | Not a present force.                                               |
| Any generated prose (LLM or otherwise)                         | Would be a second output path; the brief allows exactly one.       |

---

## 8. Exit-criteria trace

| criterion | where it is satisfied |
|-----------|-----------------------|
| 1 — boundary enforced by architecture | §3: private `Citation` constructor in `ledger`, single `/ledger` route, no free-text field, `attr.*`-only predicates, SELECT-only compute modules |
| 2 — one `manager → subject(s)` primitive | §4: the `grant` join table; self, family, and practice are cardinalities |
| 3 — expected and reported distinct, gaps joined | §5: rails (files + `expects`) vs `entry` rows; `ledger.build` is a date comparison, no per-example list |
| 4 — provenance and tier inseparable from every item | §3.1/§5.2: `source.tier` and `evidence[].provenance` are fields of `Citation`, the only output |
| 5 — new pathway / source type is one owner's change | §5.4 |
| 6 — scoped to Pillar 1 and the stated sources | §7; five tables, four modules, two pathway files |
