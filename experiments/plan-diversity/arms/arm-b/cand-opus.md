# The Responsible Doctor — MVP Architecture

*A proactive care-coordinator that manages medical processes and never originates
advice. The unifying object is the personal medical tracking file (**תיק מעקב רפואי**):
a fusion of authoritative sources with the subject's reported state, surfaced as an
expected-vs-done ledger.*

This document specifies the shape only: data model, module boundaries, the ownership
of the citation invariant, the `manager → subject(s)` primitive, and the expected/done
join. No running code.

---

## 0. The one sentence the whole architecture defends

> **Every value that leaves the system is a `Citation = (Source × ReportedState)`.
> The system never infers state and never originates advice.**

Everything below exists to make that sentence *structurally* true — enforced by types
and a single chokepoint, not by reviewer discipline or prompt hygiene.

### Design assumptions (stated, not prescribed by the brief)

- **A1.** Delivery surface is a JSON/HTTP service behind a thin web client; the design
  is transport-agnostic and only the *seam vocabulary* is normative.
- **A2.** "Reported" always means *explicitly asserted by a human* (subject or their
  manager). No sensor, parser, or model may write a `ReportedItem`. Ingesting a lab PDF,
  if ever added, would still terminate in a human confirming the value.
- **A3.** Persistence is a relational store; entity names below are the logical model,
  not table DDL.
- **A4.** Confidence tier is a property of a **source class**, fixed at ingestion — it
  is never computed from content or "how sure the system is."
- **A5.** A **nudge is a citation**, not an exception to citation. Its source is a fixed,
  shipped guideline (see §3.4), so it too is `(Source × ReportedState)`.

---

## 1. Data model

Two irreducible fact families, held rigorously apart, plus the machinery that joins them.

### 1.1 The two fact families

**Authoritative facts — `Source`** (what some authority says *should* hold)

| Field | Notes |
|---|---|
| `source_id` | stable id |
| `source_class` | `PUBLIC_GUIDELINE` \| `DOCTOR_INSTRUCTION` \| `PRESCRIPTION` (day-zero set) |
| `confidence_tier` | derived *only* from `source_class` (see §5.3); stored denormalized so it travels |
| `issued_scope` | `POPULATION` (guideline, matched by rule) \| `PERSONAL` (issued to a named subject) |
| `subject_id?` | present iff `issued_scope = PERSONAL` |
| `content_ref` | the authority's own words / structured payload — the *only* text the system may quote |
| `provenance` | issuer identity, document id, version, effective date |

**Reported facts — `ReportedItem`** (what a human asserts *is* true of a subject)

| Field | Notes |
|---|---|
| `reported_id` | stable id |
| `subject_id` | whose state |
| `reported_kind` | `RESULT` \| `INSTRUCTION_RECEIVED` \| `PRESCRIPTION_HELD` \| `ACTION_DONE` |
| `value` | the asserted fact (e.g. `mammogram, 2021-04`, `HbA1c=6.1`, `filled=true`) |
| `asserted_by` | manager id who reported it (audit) |
| `asserted_at` | when reported |

> The same real-world artifact can spawn both: a paper prescription becomes a
> `Source(PRESCRIPTION)` (the directive "5mg daily") *and* is referenced by a
> `ReportedItem(PRESCRIPTION_HELD)` when the subject says "I filled it." The directive
> and the fact of holding it are different facts and never collapse.

### 1.2 The rails (declarative "expected" side)

**`Pathway`** — a known medical pathway as data, authored into a library (§5).

| Field | Notes |
|---|---|
| `pathway_id`, `version` | |
| `source_id` | the authoritative `Source` this rail encodes (a guideline). A rail with no source cannot exist. |
| `steps[]` | ordered `ExpectedStep`s |

**`ExpectedStep`** — one expectation the rail asserts.

| Field | Notes |
|---|---|
| `step_id` | |
| `applies_when` | predicate over subject attributes + prior reported items (e.g. `age ≥ 50 ∧ sex = F`) |
| `satisfied_by` | predicate over `ReportedItem`s that discharges the step (e.g. `RESULT.kind = mammogram ∧ age_of_report < 24mo`) |
| `cadence` | how "due/overdue" is computed from the last satisfying report |
| `on_open_no_plan` | flag: if applicable, unsatisfied, and no governing `PERSONAL` source exists → this becomes a **nudge** |

Steps are **predicates over facts**, so gaps are *computed by joining*, never enumerated
per example. The library grows by adding `Pathway` documents; no other module changes.

### 1.3 The join output

**`LedgerEntry`** — the join of one applicable `ExpectedStep` against the subject's
`ReportedItem`s.

| Field | Notes |
|---|---|
| `subject_id` | |
| `expected_step_id`, `pathway_id` | expected side |
| `matched_reported_ids[]` | done side (possibly empty) |
| `status` | `DONE` \| `DUE` \| `OVERDUE` \| `OPEN_NO_PLAN` |
| `source_id` | the `Source` behind the expectation (inherited from the pathway or an escalating result) |
| `reported_ref` | the satisfying/most-relevant `ReportedItem`, or the `NO_REPORT` sentinel |

`LedgerEntry` is an **internal draft**. It is *not* an output. It becomes an output only
after passing through the Citation Kernel (§3), which turns `(source_id, reported_ref)`
into a sealed `Citation`.

### 1.4 The only outward type

**`Citation`** — the sole thing any public seam may return.

| Field | Notes |
|---|---|
| `citation_id` | |
| `kind` | `EXPECTATION` \| `NUDGE` (both are citations) |
| `source` | resolved `Source` (class, tier, provenance, content_ref) |
| `reported` | resolved `ReportedItem` **or** `NO_REPORT` |
| `status` | copied from the `LedgerEntry` |
| `rendered` | human string built *only* from `source.content_ref` + `reported.value` + a fixed template — the system contributes grammar, never a recommendation |

There is no `Advice` type, no `Recommendation` type, no free-text field the system may
author. That absence is the enforcement (§3).

---

## 2. Module / boundary structure

Seven modules; each fact family and each concern has exactly one owner. Arrows are
allowed dependencies (all point toward the kernel and the model).

```
        ┌──────────────────────────────────────────────┐
        │            Public Seam (API)                  │  returns Citation[] ONLY
        └───────────────────────┬──────────────────────┘
                                │
        ┌───────────────────────▼──────────────────────┐
        │         Citation Kernel   (THE CHOKEPOINT)    │  sole constructor of Citation
        └───┬───────────────┬───────────────┬──────────┘
            │               │               │
   ┌────────▼──────┐ ┌──────▼───────┐ ┌─────▼─────────┐
   │ Ledger Engine │ │ Identity &   │ │ (fixed system │
   │ (pure join)   │ │ Access       │ │  nudge source)│
   └──┬────────┬───┘ │ manager→subj │ └───────────────┘
      │        │     └──────────────┘
┌─────▼────┐ ┌─▼──────────────┐   ┌───────────────┐   ┌───────────────┐
│ Pathway  │ │ Reported State │   │   Sources     │   │  Confidence   │
│ Library  │ │ (subject facts)│   │  (ingestion)  │   │  policy (map) │
│ (rails)  │ │                │   │               │   │               │
└──────────┘ └────────────────┘   └───────────────┘   └───────────────┘
   expected        done              authoritative        tier-by-class
```

| Module | Owns | Single-owner change it absorbs |
|---|---|---|
| **Identity & Access** | `Manager`, `Subject`, `Grant`; resolves `SubjectContext` | the account primitive (§4) |
| **Sources (Ingestion)** | `Source` records; one adapter per `source_class` | **adding a new source type** = one adapter + one class registration here |
| **Confidence Policy** | the `source_class → confidence_tier` map | changing tiering = one table |
| **Pathway Library** | `Pathway` / `ExpectedStep` documents + the predicate interpreter | **adding a new pathway** = one declarative doc here |
| **Reported State** | `ReportedItem` records; append-only, human-asserted | new reported kinds |
| **Ledger Engine** | the expected⋈done join → `LedgerEntry` drafts | join logic; touches no I/O and no output type |
| **Citation Kernel** | the *only* `Citation` constructor; renders from templates | the invariant (§3) |

Key boundary rules:
- No module except **Sources** may write a `Source`; no module except **Reported State**
  may write a `ReportedItem`; the Ledger Engine may write neither — it only reads and
  joins. This keeps "authoritative" and "reported" un-forgeable.
- No module except the **Kernel** may construct a `Citation`. The public seam depends on
  the Kernel, not on the Ledger Engine.

---

## 3. The citation invariant — ownership & structural enforcement

**Owner: the Citation Kernel.** It is the one place every output passes through, and it
can *only* emit `(Source × ReportedState)`. Five structural facts make advice and
inference unrepresentable rather than merely discouraged.

### 3.1 A sealed type with a private constructor
`Citation` is a sealed/opaque type whose constructor is package-private to the Kernel.
No other module — not the Ledger Engine, not the API — can instantiate one. The public
seam's return signature is `Citation` (or `Citation[]`); it is the *only* outward type,
so "return some advice" does not typecheck.

### 3.2 Construction requires two real handles
The constructor signature is:

```
mint(source: SourceRef, reported: ReportedRef, status, kind) -> Citation
```

- `SourceRef` must resolve against the Sources store; a citation with no source cannot
  be built.
- `ReportedRef` must resolve against the Reported State store **or** be the singleton
  `NO_REPORT` sentinel. There is no "system-derived state" value to pass — so the system
  **cannot infer state**: it has no channel to assert one.

### 3.3 Rendering quotes, never authors
`rendered` is produced by `template(status) applied to (source.content_ref,
reported.value)`. The template set contains exactly two families — **expectation
templates** and **nudge templates** — and both interpolate the *source's own words* and
the *reported value*. There is no template whose subject is the system, and no
imperative/recommending verb originates from the system. The system supplies connective
grammar only ("The guideline *[source]* expects X; you reported Y; status: overdue").

### 3.4 A nudge is a citation, so there is no advice bypass
"An open process has no plan" is not the system deciding what to do. It is a
`LedgerEntry(status = OPEN_NO_PLAN)` cited against a **shipped, fixed system guideline**
`Source(PUBLIC_GUIDELINE, id = ASK_YOUR_DOCTOR)` whose content is, verbatim, *"An open
process without a governing plan should be raised with your doctor."* The nudge cites
that source × the reported gap. So the *only* thing the system can ever say when it has
no plan is "ask your doctor" — because that is the only source it owns for that
situation, and it still cannot author a course of action.

### 3.5 The doctor user is not exempt
A `clinician`-role manager may **author `Source`s** (`DOCTOR_INSTRUCTION`) through the
Sources module — that is data entry, an authority recording its own words. But the system
still only re-emits those instructions as Citations; it never synthesizes a new
instruction. The boundary is identical for every user, doctor included: authorities
supply sources; the system joins and cites.

> **Net effect:** to originate advice you would need either a `Citation` with no `Source`
> (unbuildable — §3.2), a template that speaks in the system's voice (nonexistent — §3.3),
> or an outward type other than `Citation` (untypeable — §3.1). All three are closed.

---

## 4. The `manager → subject(s)` primitive

One relation, one abstraction, no special cases.

**`Grant`** (stewardship edge)

| Field | Notes |
|---|---|
| `grant_id` | |
| `manager_id` | who is acting |
| `subject_id` | on whose file |
| `role` | `SELF` \| `FAMILY` \| `CLINICIAN` |
| `scope` | what the manager may read/report/author |
| `status` | active / revoked |

- **A person managing their own file** is a `Grant(role = SELF)` where the manager is the
  subject's owner — a self-edge, *not* a distinct "single-user" code path.
- **A family manager** is several `Grant`s from one `manager_id` to several `subject_id`s.
- **A doctor** is several `Grant(role = CLINICIAN)`s to their patients.

All three are *N* rows in one table. Every request resolves a **`SubjectContext`** by
looking up an active `Grant(manager, subject)`; **there is no un-scoped API**. Cardinality
(one vs many subjects) is a query result, never a branch. `role` gates only *what sources
a manager may author* (a clinician may write `DOCTOR_INSTRUCTION`s; a family manager may
not) — it **never** changes how outputs are formed. The ledger and the kernel are
identical for a parent, a patient, and a physician.

---

## 5. Expected vs Done — how the two sides join into the ledger

### 5.1 The two sides are distinct by construction
- **Expected** lives only in the **Pathway Library** as `ExpectedStep` predicates.
- **Done** lives only in **Reported State** as `ReportedItem` facts.
They never share a store and never write to each other.

### 5.2 The join (one algorithm, example-independent)
For a `SubjectContext`:

1. **Applicability filter.** From all `Pathway`s, keep every `ExpectedStep` whose
   `applies_when` predicate holds over the subject's attributes and prior reports. → the
   subject's *expected set*.
2. **Satisfaction join.** For each applicable step, find `ReportedItem`s matching its
   `satisfied_by` predicate. This is a relational join `ExpectedStep ⋈ ReportedItem` on
   the satisfaction predicate — **not** a per-pathway hand-written check.
3. **Status.** Derive from the match + `cadence`:
   - satisfying report within cadence → `DONE`
   - none, within window → `DUE`; past window → `OVERDUE`
   - applicable, unsatisfied, `on_open_no_plan`, and no active `PERSONAL` source governs
     it → `OPEN_NO_PLAN` (becomes a nudge)
4. **Draft.** Emit `LedgerEntry` carrying `source_id` (from the pathway, or from an
   escalating result-triggered step), the matched/`NO_REPORT` `reported_ref`, and status.
5. **Mint.** The Kernel turns each draft into a `Citation`. The ledger the seam returns is
   a list of Citations.

Because gaps fall out of steps 1–3 as *the join's residue* (applicable ∧ unsatisfied),
adding a pathway adds expectations without touching the join, the account model, or the
output layer — satisfying exit criterion 5.

### 5.3 Provenance & confidence travel with every item
Each `ExpectedStep` inherits its `Pathway`'s `source_id`; the `Source` carries
`provenance` and a `confidence_tier` fixed by class. Both are copied into the
`LedgerEntry` and resolved into the `Citation`. **A citation is inseparable from its
source** — there is no field on the outward type that holds an expectation *without* a
resolved source, and tier is a stored attribute of that source, not a runtime judgment.

Day-zero tier mapping (owned by Confidence Policy, one table):

| Source class | `issued_scope` | Confidence tier |
|---|---|---|
| `DOCTOR_INSTRUCTION` | PERSONAL | **A — personal directive** (highest for this subject) |
| `PRESCRIPTION` | PERSONAL | **A — personal directive** |
| `PUBLIC_GUIDELINE` | POPULATION | **B — population guideline** (applies by rule, not to you by name) |
| `PUBLIC_GUIDELINE` (`ASK_YOUR_DOCTOR`) | POPULATION | **B**, surfaced as a nudge |

---

## 6. Day-zero vocabulary — the public seams may speak *only* these

The seam is a controlled vocabulary. Anything not on these lists is not sayable.

**Nouns (the file's ontology).**
`Manager`, `Subject`, `Grant` (stewardship), `Source`, `SourceClass`
(`PUBLIC_GUIDELINE` | `DOCTOR_INSTRUCTION` | `PRESCRIPTION`), `ConfidenceTier` (`A` | `B`),
`ReportedItem`, `ReportedKind` (`RESULT` | `INSTRUCTION_RECEIVED` | `PRESCRIPTION_HELD` |
`ACTION_DONE`), `Pathway`, `ExpectedStep`, `LedgerEntry`, `Status`
(`DONE` | `DUE` | `OVERDUE` | `OPEN_NO_PLAN`), `Citation` (`kind` = `EXPECTATION` | `NUDGE`),
`NO_REPORT`.

**Verbs (the operations).**
`grantStewardship` / `revokeStewardship`, `attachSource` (authoritative data-in),
`reportItem` (human-asserted state-in), `computeLedger(subjectContext) -> Citation[]`,
`getCitation`. Read paths return `Citation` exclusively.

**Deliberately absent — not in the vocabulary, at any layer.**
`recommend`, `advise`, `diagnose`, `suggestTreatment`, `infer`, `predict`, `Advice`,
`Recommendation`. Their absence from the type system and the template set is the
enforcement, not a lint rule.

---

## 7. Explicitly out of the MVP (speculative if built)

- **Pillar 2 / the integrated overview (המכלול).** Cross-process fusion, whole-person
  synthesis — out. MVP is Pillar 1: the pathway / next-step side only.
- **Any inference of state.** No suspicion engine, no risk scoring, no deriving a
  `ReportedItem` from a document, sensor, or model. State is human-asserted only (A2).
- **Any origination of advice.** No recommendation generation — structurally impossible,
  and not to be added.
- **Sources beyond the day-zero three.** No EHR/lab auto-ingestion, no imaging feeds; new
  source classes are a *future* Sources-module change, not MVP surface.
- **NLP/parsing of free-text results into structured state.** A result is reported as a
  typed value by a human.
- **Notification/reminder delivery, scheduling infra.** MVP *produces* nudges as
  Citations; it does not own channels, cad's, or push.
- **Multi-manager conflict resolution, consent workflows, sharing/audit UX** beyond a
  simple active/revoked `Grant`.
- **Cross-subject analytics or population dashboards.** The primitive is one subject file
  at a time; aggregation is out.

Each omission is a clean seam: it is a *new owner's* future change (a Sources adapter, a
Pathway document, an overview module), never a retrofit that reopens the citation kernel
or the account primitive.
