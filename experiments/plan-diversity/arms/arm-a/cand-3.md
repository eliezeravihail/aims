# The "Responsible Doctor" — MVP Architecture

*Pillar 1 only: managing and steering medical processes (expected-next vs. done), never originating advice.*

---

## 0. Design stance and load-bearing choices

The whole system is organized around one sentence:

> **Every output the system produces is a `Citation` = (an authoritative `Source`) × (a `Reported` medical state). The system never infers state, and never originates advice.**

The architecture treats that sentence as a **type**, not a rule. There is exactly one way for data to leave the system — the **Citation Gateway** — and the only value it can construct is a `Citation`. There is no field on a `Citation` where free-form advice could live, and there is no writer of medical state other than the ingestion port (which stamps the reporter as provenance). Non-advice and non-inference therefore hold because the code has no other shape available, not because reviewers remember to check.

Everything else (accounts, pathways, the ledger) is arranged so that this one invariant is cheap to keep and impossible to route around.

**Stated assumptions (MVP):**
- Single deployable service with an internal module boundary discipline (a modular monolith); the delivery surface is a JSON API. Nothing here depends on that choice.
- Medical concepts are keyed by stable codes (e.g. LOINC-like for results, a local `pathway_step_code` for expected steps). We assume an incoming item carries or is mapped to a code at ingestion; matching is by code equality only, never by clinical reasoning.
- "Reported state" always has a human reporter (the subject, a manager acting for the subject, or a doctor user). The system is never itself a reporter.
- Confidence tier is an **attribute of the source class**, not a computed trust score.

---

## 1. Data model

Two orthogonal axes generate the whole model:

- **Expected axis** — declarative *rails*: what a known pathway says should happen, for whom, when.
- **Reported axis** — *facts*: what the subject/manager/doctor says has actually happened.

The ledger is the **join** of the two. Nothing is enumerated per example.

### 1.1 Accounts

| Entity | Key fields | Notes |
|---|---|---|
| `Manager` | `manager_id`, `identity` | The operating account. A person, a parent, a doctor — all the same. |
| `Subject` | `subject_id`, `demographics{birth_date, sex_at_birth, risk_flags[]}` | The person a tracking file is about. Demographics are **reported facts**, not inferences; they drive rail *applicability*, never diagnosis. |
| `Link` | `link_id`, `manager_id`, `subject_id`, `role`, `scope[]`, `granted_by`, `granted_at`, `revoked_at?` | The single account primitive (see §4). |

A `Subject` may be linked to many `Manager`s and vice-versa; **the file belongs to the subject**, access is via `Link`.

### 1.2 Sources (the authoritative axis)

`Source` is an interface, not a table of one shape. Every source carries provenance and a tier; that is what makes a citation inseparable from its origin (exit criterion 4).

| Field | Meaning |
|---|---|
| `source_id` | Stable id. |
| `source_class` | `PUBLIC_GUIDELINE` \| `DOCTOR_INSTRUCTION` \| `PRESCRIPTION`. |
| `confidence_tier` | Derived **only** from `source_class` (see §5.3). |
| `provenance` | `{origin, issued_by, issued_at, ingested_at, attachment_ref?}` — who said it, when, and the evidence blob. |
| `authority_scope` | Which subject(s)/codes this source is allowed to speak about. |
| `payload` | Class-specific body (rail reference, instruction text-as-data, prescription lines). |

`PUBLIC_GUIDELINE` sources are the **only** ones that carry (a reference to) a **Pathway rail**; the other two are subject-specific and can *authorize a step* or *satisfy a step* but do not define general expectations.

### 1.3 Pathway library (the expected axis, declarative)

| Entity | Key fields | Notes |
|---|---|---|
| `Pathway` | `pathway_id`, `title`, `authored_by_source_id` | A named rail (e.g. "Adult screening schedule", "Well-baby schedule"). Sourced from a `PUBLIC_GUIDELINE`. |
| `ExpectedStep` | `step_code`, `pathway_id`, `applicability`, `cadence`, `satisfied_by[]`, `authorizing_source_ref` | The unit of "expected." Pure data. |
| `applicability` | `{predicate over Subject demographics/risk_flags}` | Declarative predicate (e.g. `age >= 45`, `sex_at_birth = F`). Evaluated, not reasoned about. |
| `cadence` | `{once \| every(interval) \| at(age)}` | When the step is expected / recurs. |
| `satisfied_by` | list of `match_key` (codes) | Which reported items count as "done" for this step — **code equality only**. |

A `Pathway` is entirely declarative: adding one is data entry into this library and touches nothing else (exit criterion 5).

### 1.4 Reported items (the reported axis)

| Entity | Key fields | Notes |
|---|---|---|
| `ReportedItem` | `item_id`, `subject_id`, `kind`, `match_key`, `observed_at`, `value?`, `reported_by`, `reported_at`, `attachment_ref?`, `linked_source_id?` | The subject's actual state. `kind ∈ {RESULT, DOCTOR_INSTRUCTION, PRESCRIPTION, EVENT}`. |
| `Absence` | *(not stored; a typed value)* | The explicit "no matching reported item exists for this expected step." Absence is a first-class reported-state value so a gap can still be a well-formed citation. |

A `ReportedItem` of kind `DOCTOR_INSTRUCTION` or `PRESCRIPTION` is **dual-role**: it is a reported fact *and* it registers a same-id `Source` (so a doctor's "repeat in 3 months" both records what happened and authorizes an expected step). This dual registration is done once, at ingestion, so the two axes stay in sync without inference.

### 1.5 Citation (the sole output type)

| Field | Meaning |
|---|---|
| `citation_id` | Stable id. |
| `source_ref` | **Required.** The `Source` this citation stands on. |
| `reported_ref` | **Required.** Either a `ReportedItem` or a typed `Absence`. |
| `subject_id` | Whose file. |
| `confidence_tier` | Copied from `source_ref` — inseparable. |
| `status` | `DUE` \| `DONE` \| `OVERDUE` \| `OPEN_NO_PLAN`. |
| `rendered` | A **template fill**, not authored prose (see §3.3). |

There is **no** `advice`, `recommendation`, `assessment`, or `free_text` field anywhere on this type. That absence is the point.

### 1.6 Ledger

A `Ledger` is just `List<Citation>` for a subject: the tracking file (*תיק מעקב רפואי*). It is computed on read, never stored as authored content.

---

## 2. Module / boundary structure

```
                 ┌───────────────────────────────────────────────┐
   PUBLIC SEAM   │   API layer (speaks day-zero vocabulary, §6)   │
                 └───────────────────────────────────────────────┘
                        │ writes                    │ reads
          ┌─────────────┴──────────┐        ┌───────┴────────────────┐
          ▼                        ▼        ▼                        │
 ┌─────────────────┐   ┌────────────────────────┐                    │
 │  Accounts       │   │  Ingestion Port         │                    │
 │  (§4)           │   │  (the ONLY state writer)│                    │
 │  manager→subject│   └───────────┬─────────────┘                    │
 └───────┬─────────┘               │ normalizes → Source + ReportedItem
         │ authorizes              ▼                                  │
         │           ┌─────────────────────────┐                     │
         │           │  Sources module         │  owns provenance +  │
         │           │  (source classes, tiers)│  confidence tier    │
         │           └───────────┬─────────────┘                     │
         │                       │                                   │
         │           ┌───────────┴─────────────┐                     │
         │           │  Pathway Library        │  owns the "expected"│
         │           │  (declarative rails)    │  rails              │
         │           └───────────┬─────────────┘                     │
         │                       ▼                                   │
         │           ┌─────────────────────────┐                     │
         └──────────▶│  Reconciliation Engine  │ pure join, no advice│
                     │  expected × reported     │                    │
                     └───────────┬─────────────┘                     │
                                 ▼                                   │
                     ┌─────────────────────────┐                     │
                     │  CITATION GATEWAY        │◀────────────────────┘
                     │  the ONLY egress;        │
                     │  builds only Citations   │
                     └─────────────────────────┘
```

**Boundaries and single owners (exit criterion 5):**

| Module | Owns | "One owner's change" it absorbs |
|---|---|---|
| **Accounts** | `Manager`, `Subject`, `Link`, authorization scoping | new role/relationship shapes |
| **Ingestion Port** | the *only* write path into medical state; stamps provenance | new intake channel |
| **Sources** | source classes + confidence-tier mapping | **a new source type** (add a class + adapter + tier — nothing else moves) |
| **Pathway Library** | declarative rails | **a new pathway** (add rail data — nothing else moves) |
| **Reconciliation Engine** | the expected×reported join | matching/status rules (generic over any step & item) |
| **Citation Gateway** | construction of `Citation`; the egress type | rendering templates |
| **API layer** | the public vocabulary seam | transport concerns |

The Reconciliation Engine is generic over `ExpectedStep` and `ReportedItem`; the Gateway is generic over `Source` and reported-state. Neither knows any specific pathway or source type. So a new rail or source **cannot** scatter into the ledger, the account model, or the output layer — the type each touches is closed and owned in one place.

---

## 3. Ownership of the citation invariant (exit criterion 1)

This is the core of the design. Three structural facts, together, make non-advice and non-inference unbreakable.

### 3.1 One egress, one type

Every read handler in the API layer has return type `Citation` (or `Ledger = List<Citation>`). No other DTO is exported from the domain. The Gateway is the **only** constructor of `Citation`, and its constructor signature is:

```
Citation.build(source_ref: SourceRef!, reported_ref: ReportedState!, status: Status) -> Citation
```

- `SourceRef!` is non-nullable and must resolve to an ingested `Source`. **A citation with no source cannot be built** — so nothing can be emitted that isn't standing on an authoritative source.
- `ReportedState` is a closed union of `ReportedItem | Absence`. There is no `String` overload. **A citation cannot be built from prose.**
- There is no parameter, field, or overload that accepts advice, a recommendation, a diagnosis, or an inferred state.

Because the domain exports nothing but `Citation`, and `Citation` can only be built from `(Source × ReportedState)`, **every** system output is structurally a `(source × reported-state)` join. There is no "other path."

### 3.2 One writer of state — inference is designed out

Medical state is written in exactly one place: the **Ingestion Port**, and only in response to a `ReportedItem` that carries a human `reported_by`. Consequences:

- The Reconciliation Engine is **read-only** over state. It may only *match* reported items to expected steps by `match_key` equality and compute a `status`. It cannot create, derive, or upgrade a medical fact. Matching by code equality is a lookup, not a clinical inference.
- Demographics/risk_flags used for rail applicability are themselves reported facts with provenance; the engine evaluates a declared predicate over them but never concludes a new medical fact about the subject.
- There is no module capable of writing state that isn't the Ingestion Port, so "the system infers state" has no code that could do it — for any user, **including a doctor user** (a doctor's input enters as a reported item / source with provenance, exactly like anyone else's).

### 3.3 The nudge is a citation, not advice

The hard case is the "open process with no plan." The system must *nudge the person to ask their doctor* without recommending a course of action. It is handled as a `Citation` where:

- `status = OPEN_NO_PLAN`,
- `source_ref` = the guideline/instruction that opened the expectation,
- `reported_ref` = `Absence(step_code)` — the explicit fact that no plan/result is on file,
- `rendered` = a **fixed template** filled only from those two references:
  `"{source.title} expects {step.label}; nothing is on file. Ask your doctor about it."`

The template is a constant owned by the Gateway. It contains no branch that selects a treatment, dose, or course of action; it only names the source and points back to the doctor. It therefore *originates no advice* — it reflects the source and reports an absence. That is still a `(source × reported-state)` citation, so it flows through the same single egress as everything else.

---

## 4. The `manager → subject(s)` primitive (exit criterion 2)

There is one relationship type, `Link`, and one traversal:

```
Manager --Link{role, scope}--> Subject     (0..* on both sides)
```

- A person tracking only themselves is a `Manager` with one `Link` to one `Subject` (which happens to be themselves).
- A parent tracking a family is the *same* `Manager` with several `Link`s.
- A doctor tracking patients is the *same* `Manager` with many `Link`s.

Multi-subject is **not** a special case or a separate "clinic" entity — it is just cardinality on the one primitive. Every read and write is parameterized by `(manager_id, subject_id)` and authorized by checking that an active `Link` exists with a `scope` covering the operation. `role` (`SELF | GUARDIAN | CLINICIAN`) only tunes default `scope`; it does not fork the model. The tracking file is always addressed as "this subject's file, accessed through this link" — identical machinery for one subject or ten thousand.

> Assumption: the doctor user gets no special authoring power. A `CLINICIAN` link grants access scope, not the ability to emit advice — outputs are still Citations. This is what "the boundary holds for every user, including a doctor user" means structurally.

---

## 5. Expected vs. done — the ledger join (exit criterion 3)

### 5.1 The two sides stay distinct

- **Expected** lives only in the Pathway Library as `ExpectedStep` rails.
- **Reported/done** lives only as `ReportedItem`s.

They are never merged at rest. They meet only inside the Reconciliation Engine, on read.

### 5.2 The join algorithm (generic, not per-example)

For a given `(manager, subject)`:

1. **Instantiate rails.** From the Pathway Library, select every `ExpectedStep` whose `applicability` predicate is true for the subject's demographics/risk_flags. This yields the subject's *instantiated expected steps* — computed, never hardcoded per pathway.
2. **Match reported items.** For each instantiated step, find `ReportedItem`s whose `match_key ∈ step.satisfied_by` (code equality). Apply `cadence` to decide whether an existing match still satisfies the step (e.g. a match older than `every(1y)` no longer covers the current window).
3. **Assign status** purely from the match + cadence:
   - a satisfying match in-window → `DONE`
   - due now, no match → `DUE`
   - past-due, no match → `OVERDUE`
   - an open expectation the subject/doctor has flagged as active but with no plan/step on file → `OPEN_NO_PLAN`
4. **Emit through the Gateway.** For each step, call `Citation.build(source = step.authorizing_source_ref, reported = matched_item ?? Absence(step), status)`. Gaps (`DUE`/`OVERDUE`/`OPEN_NO_PLAN`) are exactly the citations whose reported side is `Absence` (or an out-of-window match).

Because gaps *fall out of the join*, adding a new pathway needs no new gap logic — the same four-step engine consumes any rail. This is what "computed by joining, not enumerated per example" means.

### 5.3 Provenance and confidence tier travel with every item (exit criterion 4)

Each emitted `Citation` copies `confidence_tier` and `provenance` off its `source_ref` at build time; they are non-optional fields on the citation. A gap flag literally cannot exist without its source and tier attached, because the Gateway constructor requires the source and stamps the tier. Default tier ladder (owned by Sources module, adjustable in one place):

| Tier | Source class | Rationale |
|---|---|---|
| **T1 – Specific clinical authority** | `DOCTOR_INSTRUCTION`, `PRESCRIPTION` | Individualized, clinician-issued, for this subject. |
| **T2 – Authoritative general** | `PUBLIC_GUIDELINE` | Population-level rail; authoritative but not individualized. |
| **T3 – Self-reported** | `RESULT`/`EVENT` reported by the subject with no clinical source | Fact on file, lowest verification. |

The tier is a property of *where the citation stands*, so the same expected step cited from a doctor instruction outranks the same step cited from a general schedule — surfaced on the flag, not buried.

---

## 6. Day-zero vocabulary (the public seams)

The API/public seams may speak **only** these nouns and verbs. This is the contract the outside world sees; anything not here is internal.

**Nouns**
- `Manager`, `Subject`, `Link` (`role`, `scope`)
- `Source` (`source_class`, `provenance`, `confidence_tier`)
- `Pathway`, `ExpectedStep`
- `ReportedItem` (`kind`, `match_key`, `observed_at`, `reported_by`)
- `Citation` (`source_ref`, `reported_ref`, `status`, `confidence_tier`, `rendered`)
- `Ledger` (a subject's tracking file = `List<Citation>`)
- `Gap` and `Nudge` are **not** separate types — a Gap is a `Citation` with `status ∈ {DUE, OVERDUE}`; a Nudge is a `Citation` with `status = OPEN_NO_PLAN`.

**Verbs (operations)**
- `linkSubject(manager, subject, role, scope)` → `Link`
- `reportItem(link, item)` → `ReportedItem` *(only state writer)*
- `ingestSource(item)` → `Source` *(may co-register from a reported doctor instruction/prescription)*
- `listPathways()` / `getPathway(id)` → declarative rails (read)
- `getTrackingFile(link, subject)` → `Ledger` *(returns only Citations)*
- `listGaps(link, subject)` → `List<Citation>` filtered to gap/nudge statuses

**Invariant of the seam:** every read verb returns `Citation`/`Ledger` and nothing else. There is no verb that returns advice, a plan, a recommendation, or a computed medical state. Writes only accept reported facts and authoritative sources — never system-authored content.

---

## 7. Explicitly out of the MVP

Building any of these should count *against* the design (exit criterion 6):

- **The integrated overview (*המכלול*)** — cross-process synthesis, whole-person dashboards. Pillar 1 only.
- **Inference / suspicion engines** — deriving, suggesting, or scoring likely diagnoses or states from data. The system has no state-writer other than human reports, by design.
- **Advice generation of any kind** — recommending tests, doses, courses of action, or interpreting results. Only Citations leave; the nudge points to the doctor.
- **Source types beyond the two mandated classes** — labs/EHR integrations, wearables, insurer feeds, imaging, etc. New source types are *possible* (one owner's change) but must not be pre-built.
- **Cross-subject analytics / population dashboards** for the manager (e.g. a doctor's cohort view). Multi-subject access is supported; aggregate analytics is not.
- **Scheduling, booking, reminders/notification delivery infrastructure.** A `Nudge` is a citation object; delivering it is out.
- **Rich clinical ontology / auto-coding.** MVP assumes items arrive mapped to codes; NLP mapping, terminology servers, and fuzzy clinical matching are out.
- **Identity/authn provider, consent lifecycle UX, audit tooling** beyond the `Link` scoping and per-item provenance already in the model.

---

## 8. How each exit criterion is met (traceability)

| # | Requirement | Where enforced |
|---|---|---|
| 1 | Non-advice by architecture, single egress | §3 — Citation Gateway is the sole constructor of the sole export type `Citation`; no advice field; single state-writer bans inference |
| 2 | `manager → subject(s)` single primitive | §4 — one `Link` type, multi-subject is cardinality, doctor is `role`, not a new model |
| 3 | Expected vs. reported distinct, gaps by join | §5 — rails vs. reported items kept separate; four-step generic join; gaps fall out of it |
| 4 | Provenance + tier travel with every item | §1.5, §5.3 — Gateway requires source, stamps non-optional tier/provenance onto every citation |
| 5 | New pathway / source = one owner's change | §2 — Pathway Library owns rails; Sources owns classes+tiers; engine & gateway are generic |
| 6 | Scoped to Pillar 1 + MVP sources | §7 — overview, inference, extra sources explicitly excluded |
