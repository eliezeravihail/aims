# "Responsible Doctor" MVP — Synthesized Architecture

Scope: **Pillar 1 only** (steering processes: expected vs. done). Delivery surface: a JSON/HTTP service
behind a thin web client; the design is transport-agnostic and only the *seam vocabulary* is normative.
No running code — the shape is the deliverable. Assumptions where the brief is silent are marked **[A]**.

---

## 0. The one sentence the whole architecture defends

> **Every value that leaves the system is a `Citation = (Source × one-or-more ReportedItems)`.
> The system never infers medical state and never originates advice — including for a doctor user.**

Everything below exists to make that sentence *structurally* true — enforced on three mechanical layers
(type visibility, a CI dependency test, and the database schema), not by reviewer discipline or prompt
hygiene. A nudge is not an exception to this rule: it is an ordinary citation of a real source (§3.4, §5.4).

**Design assumptions**
- **[A]** Persistence is a relational store; entity names are the logical model, not table DDL.
- **[A]** "Reported" always means *explicitly asserted by an authenticated human* (subject, family manager,
  or clinician). No importer, parser, sensor, scheduler, or model may ever write a `ReportedItem`.
- **[A]** One deployable service, internally modular; no distributed-systems concerns in MVP.

---

## 1. Data model

Two irreducible fact families — **authoritative** and **reported** — held rigorously apart, plus the
declarative rails and the machinery that joins them. Everything medical hangs off `subject_id`; timestamps
are UTC; versioned rows are immutable (never updated in place).

### 1.1 Identity (module `identity`)

| Entity | Fields | Notes |
|---|---|---|
| `principal` | `id`, `login`, `created_at` | A login. No medical meaning. |
| `manager` | `id`, `principal_id` | A principal acting as a manager. 1:1 with principal in MVP **[A]**. |
| `subject` | `id`, `display_name`, `created_by_manager_id`, `created_at` | **The subject *is* the medical tracking file** (תיק מעקב רפואי). A record, not necessarily a login (covers a baby, a dependent parent). |
| `mandate` | `id`, `manager_id`, `subject_id`, `basis`, `granted_at`, `revoked_at?` | **The single account primitive** (§4). `basis ∈ {SELF, FAMILY, CLINICAL}` is an audit label only — **no code path branches on it**. |

Unique `(manager_id, subject_id)` where `revoked_at IS NULL`.

### 1.2 Sources — the authoritative half of every citation (module `sources`)

| Entity | Fields | Notes |
|---|---|---|
| `source` | `id`, `kind`, `tier`, `subject_id?`, `publisher`, `title`, `version`, `effective_from`, `effective_to?`, `document_ref?`, `content_hash`, `registered_at` | Immutable per version. `kind ∈ {GUIDELINE, INSTRUCTION, PRESCRIPTION}`. `subject_id` is NULL for public guidelines, NOT NULL for subject-scoped instruction/prescription sources. |
| `source_locator` | `source_id`, `locator`, `excerpt` | A citable position inside a source (section id / page / line range) with the **verbatim excerpt**. The only medical prose that can ever reach a user is an `excerpt` or a `report` field. |

**Confidence tier is a property of the source, assigned by `sources` at registration, never computed
downstream and never passed by a caller.** Owned by one policy table:

| Tier | Meaning — assigned when |
|---|---|
| `A` | **Personal directive, document-backed** — `kind ∈ {INSTRUCTION, PRESCRIPTION}` with `document_ref` present. Subject-specific and evidenced. |
| `B` | **Population guideline** — `kind = GUIDELINE` from a registered publisher with a version and effective date. Authoritative but applies to the subject *by rule*, not by name. |
| `C` | **Personal directive, relayed** — `kind ∈ {INSTRUCTION, PRESCRIPTION}` relayed by a manager without an attached document ("my doctor said…"). Subject-specific but unevidenced. |

Results are **not** sources (a lab value carries no directive content); they are reported state only.

### 1.3 Reported state — the "done" / reported half (module `reports`)

| Entity | Fields | Notes |
|---|---|---|
| `report` | `id`, `subject_id`, `kind`, `code`, `value?`, `unit?`, `occurred_on`, `reported_at`, `reporter_manager_id`, `asserted_by`, `document_ref?`, `opens_process?`, `refers_to_report_id?` | One reported fact. `kind ∈ {ATTRIBUTE, RESULT, INSTRUCTION, PRESCRIPTION}`. `code` is from the closed vocabulary (§6). `asserted_by ∈ {SUBJECT, MANAGER, CLINICIAN_DOC}` names the human, never the system. |

Rules owned by `reports`:
- Every row is written by an authenticated manager holding a mandate for `subject_id`. **There is no other
  writer** — no importer, no scheduler, no ledger. The system cannot create a `report`.
- A `kind ∈ {INSTRUCTION, PRESCRIPTION}` row is, in the **same transaction**, also registered by `sources`
  as a subject-scoped `source` (tier A or C). A doctor instruction is therefore *both* a reported fact
  ("my doctor told me X") **and** a citable source ("X is what the doctor said"). This is the only dual object.
- `opens_process` may be true **only** on `INSTRUCTION` rows (a referral, a "follow-up needed", a diagnosis
  with follow-up). A `RESULT` can **never** open a process — deciding a value needs follow-up would be
  inference, and the schema forbids it: `CHECK (opens_process IS NULL OR kind = 'INSTRUCTION')`.
- `refers_to_report_id` lets a later instruction/prescription say "this is the plan for that open process."
  It is set by the reporter, never matched by the system.

### 1.4 Pathway rails — the declarative "expected" side (module `pathways`)

| Entity | Fields | Notes |
|---|---|---|
| `rail` | `id`, `source_id`, `version`, `applies_when` (predicate), `steps[]`, `compiled_from_report_id?` | Declarative document, one per source version. Tier inherited from `source_id`. **A rail with no source cannot exist.** |
| `step` (embedded) | `code`, `satisfied_by` (matcher), `anchor`, `due` (window), `repeat?`, `locator` | `locator` points at the `source_locator` this step is quoted from. |

A rail is **data, not code**. Illustrative (YAML for readability; stored as JSON):

```yaml
rail: guideline.crc-screening@2025-1
source_id: src_...          # tier B (population guideline)
applies_when:
  all:
    - { attr: attr.age_years, gte: 45, lt: 76 }   # from reported ATTRIBUTE attr.dob, date arithmetic only
    - { not_reported: risk.crc.high }             # a reported flag, never computed
steps:
  - code: screening.colonoscopy
    satisfied_by: { report_kind: RESULT, code: screening.colonoscopy }
    anchor: { attr: attr.dob, offset_years: 45 }
    due:    { window_after_anchor: P0Y, grace: P1Y }
    repeat: { every: P10Y, from: last_satisfying_report }
    locator: "§2.1"
```

**Instruction rails.** An INSTRUCTION/PRESCRIPTION source is compiled into a rail by the same module from
the structured fields the reporter supplied (do-what code, by-when). An instruction that opens a process
with no do-what compiles to a one-step rail whose step is satisfied only by a later INSTRUCTION/PRESCRIPTION
report whose `refers_to_report_id` points back at it. **This is what makes a nudge an ordinary gap (§5.4),
not a special path.**

The predicate/matcher grammar is **closed**: `attr` comparisons, `reported`/`not_reported` of a code,
`report_kind`/`code`/`refers_to_report_id` equality, comparators `eq`/`gte`/`lt`, and ISO-8601 durations.
It has **no arithmetic over result values** and no free-form expressions. That closure is what makes
"computed, not inferred" a property of the grammar rather than a promise.

### 1.5 Ledger (module `ledger`)

| Entity | Fields | Notes |
|---|---|---|
| `expectation` | `id`, `subject_id`, `rail_id`, `step_code`, `occurrence_n`, `due_from`, `due_until`, `status`, `satisfied_by_report_id?`, `basis_report_ids[]`, `computed_at` | One row per (subject, rail, step, occurrence). `status ∈ {EXPECTED, DONE, OVERDUE, NO_PLAN}`. `basis_report_ids` are the reports that made the rail apply. |

The `expectation` table is a **cache of a pure function** (§5): it can be truncated and recomputed at any
time, and it stores **only references**. It is never emitted to users.

### 1.6 Citation — the sole outward type (module `cite`)

| Entity | Fields | Notes |
|---|---|---|
| `citation` | `id`, `subject_id`, `kind`, `source_id` (**NOT NULL FK**), `locator_id` (**NOT NULL FK**), `tier` (copied from source), `expectation_id?`, `created_at` | **No text column.** `kind ∈ {EXPECTED, DONE, GAP, NUDGE}`. |
| `citation_basis` | `citation_id`, `report_id` | The 1..n reported records this citation joins against. Composite FK `(report_id, subject_id) → report` — a citation can only cite reports of its own subject. |

A database trigger rejects a `citation` commit with zero `citation_basis` rows. Together with the NOT NULL
`source_id`/`locator_id` and the absence of any text column, the schema itself states the invariant:
**a citation is a source-quote and at least one reported record, or it does not exist.** There is no
`Advice` type, no `Recommendation` type, and no free-text field the system may author — that absence *is*
the enforcement.

---

## 2. Modules and boundaries

Seven modules, one dependency direction (all arrows point toward `cite`). Arrows are the **only** permitted
imports. `egress` may import `cite` only. **Nothing imports `egress`.**

```
identity ──┐
reports ───┼──▶ ledger ──▶ cite ──▶ egress (API / UI / digest)
pathways ──┤                ▲
sources ───┘────────────────┘
```

| Module | Owns | May import | Public seam |
|---|---|---|---|
| `identity` | principal, manager, subject, mandate; `has_mandate(manager, subject)` | — | Mandate API |
| `sources` | source registry, the `kind → tier` policy table, locators/excerpts; registration of public guidelines and of subject-scoped instruction sources | identity | `register_guideline`, `register_from_report` |
| `pathways` | rail documents, the instruction-rail compiler, the closed predicate/matcher grammar, `applicable_rails(subject_facts)` | sources | Rail document schema |
| `reports` | the fact table; reporter-authenticated writes; the same-transaction dual-registration hook to `sources` | identity, sources | Report ingestion API |
| `ledger` | the pure expected⋈reported join (§5); `expectation` rows | identity, reports, pathways | none (internal) |
| `cite` | the `Citation` type, its **sole** constructor, the `citation`/`citation_basis` tables, and the mandate check at read time | ledger, sources, reports, identity | `Citation` (read-only value type) |
| `egress` | HTTP API, web UI, daily digest **[A]**; fixed render templates keyed by `citation.kind` | cite only | Ledger read API |

**Un-forgeability of the two fact families:** no module except `sources` may write a `Source`; no module
except `reports` may write a `ReportedItem`; `ledger` writes neither — it only reads and joins.

---

## 3. The non-advice invariant — owner and enforcement

**Owner: `cite`.** It is the one place every output passes through, and it can *only* emit
`(Source × ReportedItems)`. Nothing else defines what an output is.

### 3.1 Three mechanical enforcement layers (defense in depth)

1. **Type visibility.** `Citation` has a **private constructor** exported only within `cite` (a Go
   `internal/` package / a Rust `pub(crate)` constructor / a TS class with a `#private` constructor and no
   exported factory). Other modules can hold a `Citation`, never mint one. The public seam's return
   signature is `Citation` (or `Citation[]`) — the *only* outward type — so "return some advice" does not
   typecheck.
2. **CI dependency test.** An architecture test (ArchUnit / dependency-cruiser / custom `go vet` rule)
   fails the build if `egress` imports anything but `cite`, or if any module other than `cite` references
   the `citation` tables, or if any `egress` template slot binds to anything but the four allowed fields
   (§3.2).
3. **Schema.** `citation.source_id` and `locator_id` are NOT NULL FKs; `citation_basis ≥ 1` by trigger; the
   `citation` row has **no text column**. Even a raw-SQL bypass cannot store originated prose in the
   outbound path.

### 3.2 The constructor requires two real handles, and no string

```
cite.make(kind, source_id, locator_id, report_ids[]) -> Citation
```
- resolves `source_id` in `sources` (must be a registered version); a citation with no source cannot be built;
- resolves `locator_id` and checks it belongs to `source_id`;
- resolves every `report_id` in `reports` and checks they share one `subject_id`;
- if the source is subject-scoped, checks `source.subject_id` equals that subject;
- copies `tier` from the source — **the caller cannot pass a tier**;
- persists and returns the value.

**There is no parameter of type `string`. The function cannot be called with a sentence.** `egress` render
functions have signature `render(Citation[]) → Response`; their templates contain only structural
connectives ("expected", "done", "overdue", "no plan on file — ask your doctor", tier labels) and slots
filled *only* from `source_locator.excerpt`, `source.title`, `report.code`, `report.occurred_on`. The
system contributes connective grammar, never a recommendation.

### 3.3 Why no path can infer state
- `report` has exactly one writer (an authenticated mandate holder); no module holds write credentials to it.
- `ledger` is a pure function over immutable inputs (rails, reports, clock) using only the **closed grammar**
  of §1.4 — code equality, reported/not-reported, and date arithmetic on reported dates. Age from a reported
  DOB is arithmetic used for *applicability only*; it is never emitted as a state. The grammar cannot compare
  a result value to a threshold, compute a risk score, decide a result "looks abnormal", or open a process.

### 3.4 The nudge is an ordinary citation, so there is no advice bypass
"An open process has no plan" is not the system deciding what to do. An INSTRUCTION report with
`opens_process = true` compiles to a one-step instruction rail; when no satisfying follow-up report exists
past the grace window, the join yields `status = NO_PLAN`, and `cite` mints a `NUDGE` citation **whose
source is the opening instruction itself** (the doctor's own referral) and whose basis is that report.
The only thing the system can say when there is no plan is "ask your doctor," rendered as a fixed connective
against the real source — because **there is no field in which a course of action could appear.**

### 3.5 The doctor user is not exempt
A clinician is a manager. Anything a doctor types enters as a `report` of kind INSTRUCTION (dual-registered
as a tier-A/C source) and comes out as a citation *of that instruction*, attributed to that clinician. The
system never synthesizes a new instruction and never speaks in its own voice for anyone. There is no author
role with a different egress.

| Exit criterion | Owner | Mechanism |
|---|---|---|
| 1. Non-advice boundary is structural | `cite` | Private constructor; `egress` imports only `cite`; schema has no text column and requires source + locator + ≥1 report |
| 2. Single account primitive | `identity` | `mandate` row; no `basis` branching; subject count is cardinality |
| 3. Expected ≠ reported; gaps by join | `pathways` / `reports` / `ledger` | Separate tables; ledger is a pure function over a closed grammar |
| 4. Provenance + tier travel | `cite` | `source_id`, `locator_id`, `tier` NOT NULL on the citation row itself |
| 5. New pathway / source type = one owner's change | `pathways` / `sources` | Rail is data; source kind is an enum + one tier rule inside `sources` (§7) |
| 6. Scoped to Pillar 1 MVP | this document | §8 lists exclusions |

---

## 4. The `manager → subject(s)` primitive

A **Mandate** is the one relation. Every medical read or write passes exactly one check,
`identity.has_mandate(caller_manager_id, subject_id)`, called in **exactly two places**: `reports` on write
and `cite` on read (the Citation reader filters by mandate before returning values to `egress`). There is no
un-scoped API.

- **Self:** a `subject` created by their own `manager`, one mandate, `basis = SELF` (a self-edge, not a
  distinct single-user path).
- **Family:** one manager, several subjects, several mandates, `basis = FAMILY`.
- **Clinician:** one manager, many subjects, many mandates, `basis = CLINICAL`.

These are three **cardinalities of one table**. No screen, query, or rule enumerates them — the "switch
subject" control is `SELECT subject FROM mandate WHERE manager_id = ?`; a manager with one mandate simply
sees a list of one. Multiple mandate holders per subject (a parent *and* a treating clinician) falls out for
free as extra rows; each write is attributed via `reporter_manager_id`, conflicting reports are both kept as
facts (no merge logic in MVP **[A]**). `basis` gates nothing in output formation; a clinician who is also a
family manager is **one** `manager` holding mandates of two bases.

---

## 5. Expected × Reported → the ledger

### 5.1 Inputs (the two sides are distinct by construction)
- `Rails(subject)` — from `pathways`: all guideline rails whose `applies_when` holds over the subject's
  ATTRIBUTE reports, plus every instruction rail compiled from the subject's own INSTRUCTION/PRESCRIPTION
  sources. **Expected lives only here.**
- `Facts(subject)` — from `reports`: all `report` rows for the subject. **Done/reported lives only here.**
- `now` — the clock.

The two sides never share a store and never write to each other.

### 5.2 The join (pure, deterministic, example-independent)

```
for rail in Rails(subject):
  basis = reports that satisfied rail.applies_when          # provenance of "why expected"
  for step in rail.steps:
    for occ in occurrences(step, Facts, now):               # from anchor + due + repeat, date arithmetic
      hits = Facts ∩ step.satisfied_by ∩ within(occ.window) # relational join, not a hand-written check
      status =
        DONE      if hits ≠ ∅
        EXPECTED  if now ≤ occ.due_until
        NO_PLAN   if step.code = plan.for-open-process       # hits = ∅ and past grace
        OVERDUE   otherwise
      emit expectation(subject, rail, step, occ, status, satisfied_by = first(hits), basis)
```

The function has **no branch on subject, rail, publisher, or example**. Adding a rail adds rows; it changes
no line here. Gaps are the join's residue (applicable ∧ unsatisfied), never enumerated per example.

### 5.3 From expectation to citation — provenance and tier travel with every item

`ledger` never emits to users; it hands `expectation` rows to `cite`, which mints one citation each:

| status | citation.kind | source | locator | basis reports |
|---|---|---|---|---|
| EXPECTED | EXPECTED | rail.source_id | step.locator | attributes that made the rail apply |
| DONE | DONE | rail.source_id | step.locator | those attributes + `satisfied_by_report_id` |
| OVERDUE | GAP | rail.source_id | step.locator | the applying attributes |
| NO_PLAN | NUDGE | the opening instruction's source_id | its locator | the opening INSTRUCTION report |

Each `expectation` inherits its rail's `source_id`; the `Source` carries `provenance` and a `tier` fixed by
class; both are copied onto the `citation` row (NOT NULL) and resolved at read. **A citation is inseparable
from its source** — there is no outward field that holds an expectation *without* a resolved source, and tier
is a stored attribute, never a runtime judgment. A tier-B screening expectation renders "per *&lt;guideline
title, version&gt;*, §2.1 (tier B), because reported: date of birth 1980-02-01"; a tier-C instruction gap
renders "per instruction relayed 2026-08-01 (tier C): *&lt;verbatim excerpt&gt;*."

### 5.4 The nudge, concretely
An INSTRUCTION report with `opens_process = true` ("referred to gastroenterology") → one-step instruction
rail → satisfied only by a later INSTRUCTION/PRESCRIPTION report whose `refers_to_report_id` points back at
it → if none past grace, `NO_PLAN` → `NUDGE` citation, source = the opening instruction, basis = that report.
Rendering: "Open process: *&lt;excerpt&gt;* (reported *&lt;date&gt;*, tier *&lt;A|C&gt;*). No plan on file.
Ask your doctor." Nothing about *what* the plan should be can appear — there is no field for it.

### 5.5 Recompute
The ledger is recomputed for a subject on every report write and nightly for the clock **[A]**. Because it is
a pure function, correctness does not depend on the schedule; staleness is bounded by the nightly run.
Superseded citations are retained for audit via a `superseded_by` pointer **[A]**.

---

## 6. Day-zero vocabulary — what the public seams may speak

Every list below is a closed enumeration owned by one module; seams reject unknown values. No seam exposes
internal terms ("eligibility rule", "matcher", "enrollment") to end users.

- **Identity (`identity`)** — `manager`, `subject`, `mandate`, `basis ∈ {SELF, FAMILY, CLINICAL}`.
- **Source (`sources`)** — `kind ∈ {GUIDELINE, INSTRUCTION, PRESCRIPTION}`, `tier ∈ {A, B, C}`, `locator`,
  `excerpt`, `version`, `effective_from/to`.
- **Report (`reports`)** — `kind ∈ {ATTRIBUTE, RESULT, INSTRUCTION, PRESCRIPTION}`,
  `asserted_by ∈ {SUBJECT, MANAGER, CLINICIAN_DOC}`, `opens_process`, `refers_to_report_id`, `occurred_on`.
- **Item codes** (owned by `reports`; `pathways` may only *reference* them) — a small namespaced list, each
  with an optional external-code slot left empty at day zero **[A]**: `attr.dob`, `attr.sex`, `risk.<code>`
  (reported flags only), `screening.<code>`, `immunization.<code>`, `visit.well-baby`, `visit.followup`,
  `rx.<code>`, and the reserved, non-reportable step code `plan.for-open-process`.
- **Rail (`pathways`)** — `rail`, `applies_when`, `steps[]`, `step.code`, `satisfied_by`, `anchor`, `due`,
  `repeat`, `locator`; predicate atoms `attr`, `reported`, `not_reported`, `report_kind`, `code`,
  `refers_to_report_id`; comparators `eq`/`gte`/`lt`; ISO-8601 durations.
- **Ledger status** (internal, but named in citations) — `EXPECTED, DONE, OVERDUE, NO_PLAN`.
- **Citation (`cite`)** — `kind ∈ {EXPECTED, DONE, GAP, NUDGE}`, `source`, `locator`, `tier`, `basis[]`,
  `subject_id`.
- **Egress (`egress`)** — `GET /subjects` (via mandates), `GET /subjects/{id}/ledger → Citation[]`,
  `POST /subjects/{id}/reports`, `POST /mandates`. The ledger response schema *is* the Citation schema; no
  other response shape carries medical content.

**Deliberately absent from every seam, type, and template:** *recommend, advise, suggest, should, diagnose,
suspected, abnormal, likely, risk score, predict, infer, Advice, Recommendation.* Their absence from the
type system and the template slots is the enforcement, checked by the same architecture test that binds
template slots (§3.1).

---

## 7. Change paths (exit criterion 5)

| Change | Files touched | Modules untouched |
|---|---|---|
| New public pathway (e.g. hypertension follow-up) | one rail document + one guideline registration in `sources` | ledger, identity, cite, egress, reports |
| New version of an existing guideline | new source version row + new rail version; expectations recompute | everything else |
| New instruction shape ("repeat lab in N weeks") | one function in the `pathways` rail compiler | ledger, cite, egress, identity |
| New source *type* (e.g. HMO care plan) | one `sources.kind` enum value + one tier rule (+ a compiler entry in `pathways` if it carries steps) | ledger, cite, egress, identity, reports |
| New item code | one entry in the `reports` code list | everything else |

The ledger join, the citation constructor, the mandate check, and the egress templates are written once and
do not change when content changes.

---

## 8. Explicitly out of the MVP (speculative if built)

- **Pillar 2 / the integrated overview (המכלול)** — no aggregate views, no cross-subject dashboards, no
  cross-pathway synthesis. Only the per-subject ledger.
- **Any inference of state** — abnormal-value detection, risk stratification, "suspected" anything,
  drug-interaction checks, symptom checkers. The closed grammar has no place for them, and the
  `opens_process` CHECK forbids a result triggering follow-up.
- **Any origination of advice** beyond the fixed "ask your doctor" nudge — structurally impossible, and not
  to be added.
- **Document understanding** — uploads are opaque attachments that raise an instruction source to tier A;
  no OCR, parsing, or extraction. Structured fields are entered by the reporter.
- **External integrations** — HMO/EHR/lab feeds, FHIR, LOINC/SNOMED mapping (the code list keeps an empty
  slot). All facts are human-reported.
- **Clinician-side tooling** — order entry, e-prescribing, clinician↔family messaging. A clinician is a
  manager who reports instructions, nothing more.
- **Consent & subject-side identity** — subject login, consent capture beyond mandate creation, revocation
  workflows, guardianship verification, audit export.
- **Scheduling/booking, push reminders, adherence tracking** — a single nightly digest of that day's
  `GAP`/`NUDGE` citations is the only proactive surface **[A]**.
- **Multi-guideline conflict resolution** — if two applicable rails expect the same code, both expectations
  show, each with its own citation and tier; no ranking or merge.
- **Pathway authoring UI, pathway versioning/migration semantics, localization beyond UI connectives**
  (source excerpts render in their original language), billing, and clinic multi-tenancy.

Each omission is a clean seam — a *future owner's* change (a `sources` adapter, a `pathways` document, an
overview module), never a retrofit that reopens the citation kernel or the account primitive. Anything that
later proves necessary enters as a new `source.kind`, a new rail document, or a new item code — never as a
new kind of output, because `Citation` remains the only thing the system is allowed to say.
