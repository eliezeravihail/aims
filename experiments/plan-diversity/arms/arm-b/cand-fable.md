# "Responsible Doctor" MVP — Architecture

Scope: Pillar 1 only (steering processes: expected vs. done). Delivery surface: a web service with a thin
web UI; the design is surface-agnostic. No running code; the shape is what matters.

Assumptions made where the brief is silent are marked **[A]**.

---

## 0. One-paragraph shape

Seven modules, one dependency direction. **Reported facts** enter through `reports` and are never derived.
**Sources** (public guidelines, doctor instructions, prescriptions) are registered in `sources` and are the
only things that may carry medical meaning. `pathways` turns sources into **declarative rails**. `ledger`
performs one pure join — rails × reported facts — and yields expectation rows whose every field is a
*reference*. `cite` is the single constructor of the `Citation` type, the only type `egress` can emit; a
Citation is a pair of database foreign keys `(source_id, report_ids)` with no free-text column, so there is
no place in the system where prose that is not a quotation of a source or a reported record can exist on
the way out. `identity` owns the one account primitive, the **Mandate** (manager → subject), and `egress`
checks it once, at the gate.

```
identity ──┐
reports ───┼──▶ ledger ──▶ cite ──▶ egress (API / UI / digest)
pathways ──┤                ▲
sources ───┘────────────────┘
```

Arrows are the only permitted imports. `egress` may import `cite` only. Nothing imports `egress`.

---

## 1. Data model

All tables are per-tenant-free; a `subject_id` is the partition key for everything medical. Timestamps are
UTC; dates are calendar dates. Versions are immutable rows, never updated in place.

### 1.1 Identity (module `identity`)

| Entity | Fields | Notes |
|---|---|---|
| `principal` | `id`, `login`, `created_at` | A login. Has no medical meaning. |
| `manager` | `id`, `principal_id` | A principal acting as a manager. 1:1 with principal in MVP **[A]**. |
| `subject` | `id`, `display_name`, `created_by_manager_id`, `created_at` | A person of care. **The subject *is* the medical tracking file** (תיק מעקב רפואי): everything medical hangs off `subject_id`. |
| `mandate` | `id`, `manager_id`, `subject_id`, `basis`, `granted_at`, `revoked_at?` | **The single account primitive.** `basis ∈ {SELF, FAMILY, CLINICAL}` is an audit label only; **no code path branches on it**. |

Unique `(manager_id, subject_id)` where `revoked_at IS NULL`.

### 1.2 Sources (module `sources`)

| Entity | Fields | Notes |
|---|---|---|
| `source` | `id`, `kind`, `tier`, `subject_id?`, `publisher`, `title`, `version`, `effective_from`, `effective_to?`, `document_ref?`, `content_hash`, `registered_at` | Immutable per version. `kind ∈ {GUIDELINE, INSTRUCTION, PRESCRIPTION}`. `subject_id` is NULL for public guidelines and NOT NULL for instruction/prescription sources (they are subject-scoped). |
| `source_locator` | `source_id`, `locator`, `excerpt` | A citable position inside a source (section id, page, line range) with the **verbatim excerpt**. The only medical prose that can ever reach a user is an `excerpt` or a `report` field. |

**Confidence tier is a property of the source, assigned by `sources` at registration, never by anyone downstream:**

| Tier | Assigned when |
|---|---|
| `A` | `kind = GUIDELINE` from a registered publisher with a version and effective date. |
| `B` | `kind ∈ {INSTRUCTION, PRESCRIPTION}` backed by an attached document (`document_ref` NOT NULL). |
| `C` | `kind ∈ {INSTRUCTION, PRESCRIPTION}` relayed by the manager/subject without a document. |

No other tiers exist at day zero. Results are **not** sources (a lab value has no directive content); they
are reported state only.

### 1.3 Reported state (module `reports`)

| Entity | Fields | Notes |
|---|---|---|
| `report` | `id`, `subject_id`, `kind`, `code`, `value?`, `unit?`, `occurred_on`, `reported_at`, `reporter_manager_id`, `asserted_by`, `document_ref?`, `opens_process?`, `refers_to_report_id?` | One reported fact. `kind ∈ {ATTRIBUTE, RESULT, INSTRUCTION, PRESCRIPTION}`. `code` is from the vocabulary (§6). `asserted_by ∈ {SUBJECT, MANAGER, CLINICIAN_DOC}` says who asserted the fact, never the system. |

Rules owned by `reports`:

- Every row is written by an authenticated manager holding a mandate for `subject_id`. There is no other
  writer: no importer, no scheduler, no ledger. **The system cannot create a `report`.**
- `kind = INSTRUCTION | PRESCRIPTION` rows are additionally registered by `sources` as a subject-scoped
  `source` (tier B or C) in the same transaction. A doctor instruction is therefore *both* a reported fact
  ("my doctor told me X") and a citable source ("X is what the doctor said"). This is the only dual object.
- `opens_process` may be true **only** on `INSTRUCTION` rows (a referral, a "follow-up needed", a diagnosis
  with follow-up). A `RESULT` can never open a process — deciding that a value needs follow-up would be
  inference, and the schema does not allow it (`CHECK (opens_process IS NULL OR kind = 'INSTRUCTION')`).
- `refers_to_report_id` lets a later instruction/prescription say "this is the plan for that open process".
  It is set by the reporter, never matched by the system.

### 1.4 Pathway rails (module `pathways`)

| Entity | Fields | Notes |
|---|---|---|
| `rail` | `id`, `source_id`, `version`, `applies_when` (predicate), `steps[]`, `compiled_from_report_id?` | Declarative document, one per source version. Tier is inherited from `source_id`. |
| `step` (embedded) | `code`, `satisfied_by` (matcher), `anchor`, `due` (window), `repeat?`, `locator` | `locator` points at the `source_locator` this step is quoted from. |

A rail is data, not code. Illustrative schema (YAML for readability; stored as JSON):

```yaml
rail: guideline.crc-screening@2025-1
source_id: src_...          # tier A
applies_when:
  all:
    - { attr: attr.age_years, gte: 45, lt: 76 }      # from report ATTRIBUTE attr.dob, date arithmetic only
    - { not_reported: risk.crc.high }                # a reported flag, never computed
steps:
  - code: screening.colonoscopy
    satisfied_by: { report_kind: RESULT, code: screening.colonoscopy }
    anchor: { attr: attr.dob, offset_years: 45 }
    due:    { window_after_anchor: P0Y, grace: P1Y }
    repeat: { every: P10Y, from: last_satisfying_report }
    locator: "§2.1"
```

```yaml
rail: guideline.well-baby@2024-3
source_id: src_...
applies_when: { all: [ { attr: attr.age_years, lt: 2 } ] }
steps:
  - code: visit.well-baby
    satisfied_by: { report_kind: RESULT, code: visit.well-baby }
    anchor: { attr: attr.dob }
    due: { schedule: [P1M, P2M, P4M, P6M, P9M, P12M, P18M, P24M], grace: P1M }
    locator: "table 1"
```

**Instruction rails.** A `source` of kind INSTRUCTION/PRESCRIPTION is compiled into a rail by the same
module, using the structured fields the reporter supplied (do-what code, by-when). An instruction that
opens a process and has no do-what compiles to the one-step rail:

```yaml
rail: instruction.<report_id>
source_id: src_<same>        # tier B or C
applies_when: { subject: <subject_id> }
steps:
  - code: plan.for-open-process
    satisfied_by: { report_kind: [INSTRUCTION, PRESCRIPTION], refers_to_report_id: <report_id> }
    anchor: { report: <report_id>, field: occurred_on }
    due: { window_after_anchor: P0D, grace: P30D }   # [A] default grace; per-instruction override allowed
    locator: "instruction text"
```

This is what makes a nudge an ordinary gap (§5.4) rather than a special path.

The predicate/matcher language is closed: `attr` comparisons, `reported`/`not_reported` of a code,
`report_kind`/`code`/`refers_to_report_id` equality, and ISO-8601 durations. It has no arithmetic over
result values and no free-form expressions. That closure is what makes "computed, not inferred" a property
of the grammar rather than a promise.

### 1.5 Ledger (module `ledger`)

| Entity | Fields | Notes |
|---|---|---|
| `expectation` | `id`, `subject_id`, `rail_id`, `step_code`, `occurrence_n`, `due_from`, `due_until`, `status`, `satisfied_by_report_id?`, `basis_report_ids[]`, `computed_at` | One row per (subject, rail, step, occurrence). `status ∈ {EXPECTED, DONE, OVERDUE, NO_PLAN}`. `basis_report_ids` are the reports that made the rail apply. |

The ledger table is a cache of a pure function (§5); it can be truncated and recomputed at any time.
It stores only references.

### 1.6 Citation (module `cite`)

| Entity | Fields | Notes |
|---|---|---|
| `citation` | `id`, `subject_id`, `kind`, `source_id` (NOT NULL FK), `locator_id` (NOT NULL FK), `tier` (copied from source), `expectation_id?`, `created_at` | **No text column.** `kind ∈ {EXPECTED, DONE, GAP, NUDGE}`. |
| `citation_basis` | `citation_id`, `report_id` | 1..n reported records this citation is a join against. FK `(report_id, subject_id)` → `report` composite, so a citation can only cite reports of its own subject. |

A database trigger rejects a `citation` commit with zero `citation_basis` rows. Together with the NOT NULL
`source_id`, the schema itself states the invariant: **a citation is a source and at least one reported
record, or it does not exist.**

---

## 2. Modules and boundaries

| Module | Owns | May import | Public seam |
|---|---|---|---|
| `identity` | principal, manager, subject, mandate; `has_mandate(manager, subject)` | — | Mandate API |
| `sources` | source registry, tiers, locators/excerpts; registration of public guidelines and of subject-scoped instruction sources | identity | Source registry format; `register_guideline`, `register_from_report` |
| `pathways` | rail documents, rail compiler for instruction sources, the predicate/matcher grammar, `applicable_rails(subject_facts)` | sources | Rail document schema |
| `reports` | the fact table; reporter-authenticated writes; dual-registration hook to `sources` | identity, sources | Report ingestion API |
| `ledger` | the join (§5); `expectation` rows | identity, reports, pathways | none (internal) |
| `cite` | `Citation` type, its sole constructor, `citation`/`citation_basis` tables, the mandate check at read time | ledger, sources, reports, identity | `Citation` (read-only value type) |
| `egress` | HTTP API, web UI, daily digest **[A]**; fixed rendering templates keyed by `citation.kind` | cite only | Ledger read API |

Boundary enforcement is threefold and all three are mechanical:

1. **Language visibility.** `Citation` has a private constructor exported only within `cite` (e.g. a
   Go `internal/` package, a Rust `pub(crate)` constructor, a TypeScript class with a `#private` constructor
   and no exported factory outside the module). Other modules can hold a `Citation`, never make one.
2. **Dependency test in CI.** An architecture test (dependency-cruiser / ArchUnit / `go vet` custom rule)
   fails the build if `egress` imports anything but `cite`, or if any module other than `cite` references
   the `citation` tables.
3. **Schema.** `citation.source_id NOT NULL`, `citation_basis` ≥ 1 by trigger, no text column. Even a
   raw-SQL bypass cannot store originated prose in the outbound path.

---

## 3. The non-advice invariant: owner and enforcement

**Owner: `cite`.** Nothing else defines what an output is.

### 3.1 What a Citation is

```
Citation = { kind, source: SourceRef, locator: LocatorRef, tier, basis: ReportRef[1..n], subject_id }
```

The constructor `cite.make(kind, source_id, locator_id, report_ids[])`:

- resolves `source_id` in `sources` (must exist, must be a registered version);
- resolves `locator_id` and checks it belongs to `source_id`;
- resolves every `report_id` in `reports` and checks they all share one `subject_id`;
- if the source is subject-scoped, checks `source.subject_id` equals that subject;
- copies `tier` from the source — the caller cannot pass a tier;
- persists and returns the value.

There is no parameter of type `string`. The function cannot be called with a sentence.

### 3.2 Why no path can originate advice

- `egress` render functions have the signature `render(Citation[]) → Response`. Their templates contain only
  structural connectives ("expected", "done", "overdue", "no plan on file — ask your doctor", labels for
  tier), and slots that are filled from `source_locator.excerpt`, `source.title`, `report.code`,
  `report.occurred_on`. The template files are reviewed as part of the `egress` module and the architecture
  test checks that no template slot is bound to anything but those four fields.
- The nudge wording "ask your doctor" is a fixed connective, not a medical statement; it names no action
  other than consulting the source-of-record. It renders only for `kind = NUDGE`, which `cite` produces only
  from a `NO_PLAN` expectation (§5.4), which exists only when an INSTRUCTION report with `opens_process`
  exists.
- A doctor user is a manager. Anything a doctor types enters as a `report` of kind INSTRUCTION (becoming a
  tier B/C source) and comes out as a citation *of that instruction*, attributed to that clinician. The
  system never speaks in its own voice for anyone; there is no author role with a different egress.

### 3.3 Why no path can infer state

- `report` has one writer: an authenticated manager with a mandate. No module holds write credentials to
  the `report` table except `reports`, and `reports` exposes no internal write API.
- `ledger` is a pure function over immutable inputs (rails, reports, clock). Its only computations are
  the closed predicate grammar of §1.4 — code equality, reported/not-reported, and date arithmetic on
  reported dates. Age from a reported date of birth is arithmetic, not inference, and is used for
  applicability only; it is never emitted as a state.
- What the ledger cannot do, by construction of the grammar: compare a result *value* to a threshold,
  combine results into a risk score, decide that a result "looks abnormal", or open a process. Each of those
  would need a matcher the grammar does not have.

### 3.4 Traceability of the invariant

| Exit criterion | Owner | Mechanism |
|---|---|---|
| 1. Non-advice boundary structural | `cite` | Private constructor; `egress` imports only `cite`; schema has no text column and requires source + ≥1 report |
| 2. Single account primitive | `identity` | `mandate` row; no `basis` branching; subject count is cardinality |
| 3. Expected ≠ reported; gaps by join | `pathways` / `reports` / `ledger` | Separate tables; ledger is a pure function with a closed grammar |
| 4. Provenance and tier travel | `cite` | `source_id`, `locator_id`, `tier` NOT NULL on the citation row itself |
| 5. New pathway / source type is one owner's change | `pathways` / `sources` | Rail is data; source kind is an enum + tier rule inside `sources` (§7) |
| 6. Scoped | this document | §8 lists exclusions |

---

## 4. The `manager → subject(s)` primitive

A **Mandate** is the one relation. Every medical read or write in the system passes exactly one check:
`identity.has_mandate(caller_manager_id, subject_id)`. It is called in two places only — `reports` on
write, `cite` on read (the Citation reader filters by mandate before returning values to `egress`).

- A person managing themself: a `subject` row created by their own `manager`, one mandate, `basis = SELF`.
- A parent: several subjects, several mandates, `basis = FAMILY`.
- A clinician: many subjects, many mandates, `basis = CLINICAL`.

These are three cardinalities of one table. No screen, query, or rule enumerates them. The UI's
"switch subject" control is `SELECT subject FROM mandate WHERE manager_id = ?`; a manager with one mandate
simply sees a list of one.

Consequences chosen deliberately:

- A subject may have multiple mandate holders (a parent and a clinician). Each sees the same tracking
  file; each write is attributed via `reporter_manager_id`. Conflicting reports are both kept; the ledger
  treats them as two facts (the matcher takes any satisfying report). No merge logic in MVP **[A]**.
- Mandate granting: the creating manager holds the first mandate; a mandate holder may grant another
  manager a mandate on that subject. Consent capture, revocation workflows, and subject-side login are out
  of scope (§8). **[A]**
- There is no "patient" role and no "doctor" role. A clinician who is also a family manager is one
  `manager` with mandates of two bases.

---

## 5. Expected × reported → ledger

### 5.1 Inputs

- `Rails(subject)` — from `pathways`: all tier-A rails whose `applies_when` holds over the subject's
  ATTRIBUTE reports, plus every instruction rail compiled from the subject's own INSTRUCTION/PRESCRIPTION
  sources.
- `Facts(subject)` — from `reports`: all `report` rows for the subject.
- `now` — the clock.

### 5.2 The join (pure, deterministic)

```
for rail in Rails(subject):
  basis = reports that satisfied rail.applies_when          # provenance of "why expected"
  for step in rail.steps:
    for occ in occurrences(step, Facts, now):               # from anchor + due + repeat, date arithmetic
      hits = Facts ∩ step.satisfied_by ∩ within(occ.window)
      status =
        DONE      if hits ≠ ∅
        EXPECTED  if now ≤ occ.due_until
        NO_PLAN   if step.code = plan.for-open-process        # hits = ∅ and past grace
        OVERDUE   otherwise
      emit expectation(subject, rail, step, occ, status, satisfied_by = first(hits), basis)
```

The function has no branch on subject, rail, publisher, or example. Adding a rail adds rows; it changes
no line here.

### 5.3 From expectation to citation

`ledger` never emits to users. It hands expectation rows to `cite`, which constructs one citation each:

| status | citation.kind | source | locator | basis reports |
|---|---|---|---|---|
| EXPECTED | EXPECTED | rail.source_id | step.locator | `basis_report_ids` (the attributes that made the rail apply) |
| DONE | DONE | rail.source_id | step.locator | `basis_report_ids` + `satisfied_by_report_id` |
| OVERDUE | GAP | rail.source_id | step.locator | `basis_report_ids` |
| NO_PLAN | NUDGE | the opening instruction's source_id | its locator | the opening INSTRUCTION report |

Every row of the ledger view a user sees is therefore a Citation with `source`, `locator`, and `tier`
inline, and a `basis` that names the reported records the item rests on. A tier-A screening expectation
shows "per <guideline title, version>, §2.1 (tier A), because reported: date of birth 1980-02-01". A
tier-C instruction gap shows "per instruction relayed on 2026-08-01 (tier C): <verbatim text>".

### 5.4 The nudge, as an ordinary gap

An INSTRUCTION report with `opens_process = true` (e.g. "referred to gastroenterology") compiles to a
one-step instruction rail (§1.4) whose step is satisfied only by a later INSTRUCTION or PRESCRIPTION report
whose `refers_to_report_id` points back at it. If no such report exists past the grace window, the join
yields `NO_PLAN`, and `cite` produces a `NUDGE` citation whose source is the opening instruction and whose
basis is the same report. Rendering: "Open process: <excerpt> (reported <date>, tier <B|C>). No plan on
file. Ask your doctor." Nothing about *what* the plan should be can appear, because there is no field for it.

### 5.5 Recompute strategy

The ledger is recomputed for a subject on every report write and nightly for the clock **[A]**. Since it
is a pure function, correctness does not depend on the recompute schedule; staleness is bounded by the
nightly run. Citations are re-issued on recompute; superseded citations are retained for audit with a
`superseded_by` pointer **[A]** (omitted from the table above for brevity).

---

## 6. Day-zero vocabulary (what public seams may speak)

Everything below is a closed enumeration owned by one module. Seams reject unknown values.

**Identity (`identity`)** — `manager`, `subject`, `mandate`, `basis ∈ {SELF, FAMILY, CLINICAL}`.

**Source (`sources`)** — `source.kind ∈ {GUIDELINE, INSTRUCTION, PRESCRIPTION}`, `tier ∈ {A, B, C}`,
`locator`, `excerpt`, `version`, `effective_from/to`.

**Report (`reports`)** — `report.kind ∈ {ATTRIBUTE, RESULT, INSTRUCTION, PRESCRIPTION}`,
`asserted_by ∈ {SUBJECT, MANAGER, CLINICIAN_DOC}`, `opens_process`, `refers_to_report_id`, `occurred_on`.

**Item codes (`reports` owns the list; `pathways` may only reference it)** — a small namespaced list,
each entry with an optional external code field left empty at day zero **[A]**:

- `attr.dob`, `attr.sex`, `risk.<code>` (reported risk flags only, e.g. `risk.crc.high`)
- `screening.<code>` (e.g. `screening.colonoscopy`, `screening.mammography`, `screening.fit`)
- `immunization.<code>`
- `visit.well-baby`, `visit.followup`
- `rx.<code>` for prescriptions
- `plan.for-open-process` (reserved step code; not reportable)

**Rail (`pathways`)** — `rail`, `applies_when`, `steps[]`, `step.code`, `satisfied_by`, `anchor`, `due`,
`repeat`, `locator`; predicate atoms `attr`, `reported`, `not_reported`, `report_kind`, `code`,
`refers_to_report_id`; comparators `eq/gte/lt`; ISO-8601 durations.

**Ledger status (internal, but named in citations)** — `EXPECTED, DONE, OVERDUE, NO_PLAN`.

**Citation (`cite`)** — `citation.kind ∈ {EXPECTED, DONE, GAP, NUDGE}`, `source`, `locator`, `tier`,
`basis[]`, `subject_id`.

**Egress (`egress`)** — endpoints: `GET /subjects` (via mandates), `GET /subjects/{id}/ledger` →
`Citation[]`, `POST /subjects/{id}/reports`, `POST /mandates`. The response schema for the ledger is the
Citation schema; there is no other response shape carrying medical content.

Words deliberately **absent** from every seam: *recommend, suggest, should, risk score, suspected,
abnormal, likely, diagnosis (as a system-produced value)*. Their absence is checked by the same template
lint that binds slots (§3.2).

---

## 7. Change paths (criterion 5)

| Change | Files touched | Modules untouched |
|---|---|---|
| New public pathway (e.g. hypertension follow-up schedule) | one rail document + one source registration in `sources` | ledger, identity, cite, egress, reports |
| New version of an existing guideline | new source version row + new rail version; old expectations recompute | everything else |
| New instruction shape (e.g. "repeat lab in N weeks") | rail compiler in `pathways` (one function) | ledger, cite, egress, identity |
| New source *type* (e.g. HMO care plan) | `sources.kind` enum + one tier rule; a rail compiler entry in `pathways` if it carries steps | ledger, cite, egress, identity, reports |
| New item code | one entry in the code list | everything else |

The ledger join, the citation constructor, the mandate check and the egress templates are written once
and are not expected to change when content changes.

---

## 8. Explicitly out of the MVP

- **The integrated overview (המכלול)** — Pillar 2. No aggregate views, no cross-subject dashboards, no
  summaries beyond the per-subject ledger.
- **Any inference**: abnormal-value detection, risk stratification, "suspected" anything, drug-interaction
  checks, symptom checkers. The predicate grammar has no place for them, and none will be added in the MVP.
- **Document understanding**: uploads are stored as opaque attachments to raise a source to tier B; no OCR,
  no parsing, no extraction. Structured fields are entered by the reporter.
- **External integrations**: HMO/EHR/lab feeds, FHIR, LOINC/SNOMED mapping (the code list keeps an empty
  slot for it). All facts are reported by a mandate holder.
- **Clinician-side tooling**: order entry, e-prescribing, messaging between a clinician and a family
  manager. A clinician is a manager who reports instructions; nothing more.
- **Consent and subject-side identity**: subject login, consent capture beyond mandate creation,
  revocation workflows, audit export.
- **Scheduling/booking, reminders as push notifications, adherence tracking.** A single nightly digest
  that lists that day's `GAP`/`NUDGE` citations is the only proactive surface **[A]**.
- **Localisation beyond Hebrew/English UI connectives** — source excerpts render in their original language.
- **Multiple guideline publishers per code with conflict resolution.** If two applicable tier-A rails expect
  the same code, both expectations are shown, each with its own citation; no ranking.
- **Speculative source types**: nothing is pre-modelled for sources the brief does not name. `source.kind`
  has three values.
