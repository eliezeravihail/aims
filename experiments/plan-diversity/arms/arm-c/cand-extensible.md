# Responsible Doctor — MVP Architecture (extensibility-first)

> Design bias of this candidate: **maximize extensibility**. The whole structure is
> organized so that the two things that will grow — **medical pathways** and **source
> types** — each grow behind a single registry seam, while the invariant-bearing core
> (citations, the manager→subject primitive, the ledger join) stays closed to change.
> Assumptions are stated inline as **[A]**.

---

## 0. One-paragraph shape

The system is a pipeline with a **closed core** and **two open registries**. Authoritative
inputs enter through **Source Adapters** (open registry #1) and are normalized into
`ReportedItem`s, each stapled to a `Source` descriptor carrying a confidence tier. The
**expected** side comes from **Pathway Packs** (open registry #2): declarative rails,
never code branches. A single **Ledger Engine** joins expected-against-reported per subject
and produces `LedgerEntry`s. Nothing reaches a human except through the **Citation
Gateway** — the one egress that can construct only a `Citation = (Source × ReportedState)`.
Adding a pathway touches only a pack; adding a source touches only an adapter; neither can
touch the core, and neither can bypass the gateway.

```
 Source Adapters ─┐                         ┌─ Pathway Packs
 (open registry)  │                         │  (open registry)
                  ▼                         ▼
        ReportedItem[]  ──►  Ledger Engine  ◄──  ExpectedItem[]
        (+Source, tier)         (join)          (rails, versioned)
                                   │
                                   ▼
                            LedgerEntry[]
                                   │
                                   ▼
                        ┌────────────────────┐
                        │  CITATION GATEWAY   │  ◄── the ONLY egress
                        │ emit(Source×State)  │
                        └────────────────────┘
                                   │
                                   ▼
                        Citations to the manager
```

---

## 1. Data model

Everything is either **an authoritative fact**, **a subject's reported fact**, **a
declarative rail**, or **a join of the above**. There is no entity whose payload is
system-authored advice — that is the data-model expression of the invariant.

### 1.1 Identity & access — the `manager → subject(s)` primitive

| Entity | Fields | Notes |
|---|---|---|
| `Principal` | `id`, `kind ∈ {person}`, `display_name` | A human who can log in. A doctor is just a person. |
| `Subject` | `id`, `demographics{date_of_birth, sex_at_birth, …}` | The person a tracking file is *about*. Demographics are **reported facts**, not inferences. |
| `Grant` | `id`, `manager_principal_id`, `subject_id`, `scope`, `relation` | **The single primitive.** One row = one manager may act on one subject at one scope. |
| `TrackingFile` | `id`, `subject_id` | The *תיק מעקב רפואי*: the per-subject aggregate root that owns that subject's reported items and ledger. One per subject. |

`relation ∈ {self, family_member, patient, …}` is a **label only** — it changes nothing in
logic. A person managing themselves is `Grant(manager=P, subject=S_P, relation=self)`. A
parent is another `Grant` row; a doctor's panel of 400 patients is 400 `Grant` rows. **There
is no "single-user mode" and no "clinic mode" in code** — there is only "the set of Grants
this Principal holds," which is a list of length ≥ 1. (Exit criterion 2.)

> **[A]** Authorization is a capability check `∃ Grant(manager=me, subject=X)` on every read/
> write, evaluated in one middleware. Consent/relationship *proof* (how a Grant is created and
> verified) is a policy detail deliberately thin in the MVP — see §7.

### 1.2 The reported/done side — subject state

| Entity | Fields | Notes |
|---|---|---|
| `Source` | `id`, `class`, `confidence_tier`, `issuer`, `issued_at`, `ref` | The provenance descriptor. **Immutable.** Confidence tier lives *here*, so it can never be separated from what it qualifies (Exit criterion 4). |
| `ReportedItem` | `id`, `tracking_file_id`, `type`, `subtype`, `payload`, `source_id`, `observed_at`, `recorded_at` | A single normalized fact the system was *told*. |
| `ReportedState` | *(a query view, not a table)* | The current set of `ReportedItem`s for a subject; what the ledger reads. |

`ReportedItem.type ∈ {result, instruction, prescription, demographic, plan_marker}` — the
**day-zero closed set** (§6). `subtype` (e.g. `result:hba1c`, `instruction:referral`) is an
**open vocabulary** owned by pathway packs and adapters, so new clinical concepts do not
require a schema migration.

`Source.class` and `Source.confidence_tier` — day-zero enums:

| `class` | example | day-zero `confidence_tier` |
|---|---|---|
| `public_guideline` | national screening schedule, well-baby schedule | `T1_authoritative_public` |
| `doctor_instruction` | "repeat lipids in 3 months" | `T1_authoritative_personal` |
| `prescription` | dispensed Rx | `T1_authoritative_personal` |
| `subject_reported` | subject typed "I did the colonoscopy" | `T3_self_reported` |

Tiers are an **ordered enum** (`T1 > T2 > T3`), owned in **one file**, so adding a tier or a
class is a one-line change that automatically travels with every citation.

### 1.3 The expected side — declarative rails

| Entity | Fields | Notes |
|---|---|---|
| `PathwayPack` | `id`, `title`, `version`, `source_id`, `applicability`, `rails[]` | A **versioned, declarative** definition of one known pathway (e.g. adult screening, well-baby). `source_id` binds the pack to the authoritative guideline it encodes. |
| `Rail` | `key`, `expects`, `cadence`, `window`, `preconditions`, `plan_required` | One expected step. Pure data. |
| `ExpectedItem` | *(computed)* `pathway_pack_id`, `rail_key`, `subtype`, `due_window`, `source_id`, `plan_required` | The materialized "what should happen for *this* subject now," produced by evaluating a `Rail` against `ReportedState`. Carries the pack's `source_id`. |

`applicability` and `cadence`/`window` are expressed in a **small declarative rule grammar**
(age ranges, sex, prior-item recency, interval arithmetic) — **not** general code. This is the
line between *allowed deterministic scheduling* and *forbidden clinical inference*: a rail may
say "expected every 10y for ages 45–75"; it may **not** say "looks like diabetes." **[A]** The
grammar is intentionally weak (no free predicates) precisely so a pack author cannot smuggle
inference or advice into the expected side.

### 1.4 The join — the ledger

| Entity | Fields | Notes |
|---|---|---|
| `LedgerEntry` | `id`, `tracking_file_id`, `rail_ref`, `status`, `expected_ref`, `matched_reported_ref?`, `source_id`, `confidence_tier`, `computed_at` | One row of expected-vs-done. **Every entry names a `source_id` and a `confidence_tier`** — structurally, a gap cannot exist without provenance. |
| `Citation` | `source_ref`, `reported_state_ref`, `template_key` | **The only thing the system emits.** See §3. |

`status ∈ {done, due, overdue, open_no_plan}` — a **closed enum**. `open_no_plan` is the state
that becomes the *nudge to ask the doctor*: it means a pathway declared `plan_required=true`
and no `plan_marker` reported item satisfies it. The nudge is not advice — it is a citation of
(the rail that requires a plan) × (the reported absence of one).

---

## 2. Module / boundary structure

Six modules. The dependency arrow points **inward** to the core; the two registries and the
gateway are the only places that change with growth.

```
┌───────────────────────────── CLOSED CORE (rarely changes) ─────────────────────────────┐
│                                                                                          │
│   (M3) Ledger Engine ──uses──► (M4) Citation Gateway ──emits──► Citation                 │
│        ▲              ▲                                                                   │
│        │              │                                                                   │
└────────┼──────────────┼──────────────────────────────────────────────────────────────────┘
         │              │
   ExpectedItem[]  ReportedItem[]
         │              │
┌────────┴───────┐ ┌────┴────────────┐        ┌──────────────────────┐   ┌────────────────┐
│ (M2) Pathway   │ │ (M1) Source     │        │ (M5) Account &        │   │ (M6) Delivery  │
│ Registry       │ │ Registry &      │        │ Grant service         │   │ surface (API/  │
│ + Packs (data) │ │ Adapters        │        │ (manager→subject)     │   │ UI) — dumb     │
│  OPEN #2       │ │  OPEN #1        │        │                       │   │ renderer       │
└────────────────┘ └─────────────────┘        └──────────────────────┘   └────────────────┘
```

| Module | Owns | Depends on | Changes when… |
|---|---|---|---|
| **M1 Source Registry + Adapters** | Turning any external/authoritative input into `ReportedItem` + `Source`. One adapter per source type, self-registering. | Source schema only | a **new source type** is added — *here only*. |
| **M2 Pathway Registry + Packs** | Holding declarative `PathwayPack`s and evaluating rails → `ExpectedItem`. | Rail grammar + Source schema | a **new pathway** is added — *here only*. |
| **M3 Ledger Engine** | The pathway- and source-**agnostic** join: match expected↔reported, assign `status`. | ExpectedItem, ReportedItem interfaces | almost never (only if the *join semantics* change). |
| **M4 Citation Gateway** | The sole egress; constructs `Citation`s. | Source, ReportedState | almost never (it is the invariant). |
| **M5 Account & Grant** | `manager→subject` capability model + access checks. | Grant | almost never. |
| **M6 Delivery surface** | Rendering citations for a manager; no logic. | M4 output only | freely (cosmetic). |

The core (M3+M4+M5) speaks only in **abstract interfaces** (`ExpectedItem`, `ReportedItem`,
`Source`). It never names a specific pathway or a specific source. That is why growth in M1/M2
cannot ripple inward (Exit criterion 5).

### 2.1 The two extensibility seams (the investment)

- **Seam A — `SourceAdapter`** (M1). Contract:
  `parse(raw) -> (ReportedItem[], Source)`. An adapter declares its `Source.class` and default
  `confidence_tier`. Registered by capability key at boot. **Adding a lab-feed, an EHR export,
  a photographed prescription, or a manual form is one new adapter and nothing else.**
- **Seam B — `PathwayPack`** (M2). Contract: a declarative document conforming to the rail
  grammar + one `source_id`. Loaded from a pack directory/table; hot-registerable. **Adding
  "well-baby vaccination schedule" or "post-MI follow-up" is one new pack and nothing else** —
  no engine edit, no ledger edit, no account edit, no gateway edit.

Both seams converge on the same two neutral interfaces the core consumes, so the core is
written **once** against `N=∞` future pathways and sources.

---

## 3. Ownership & structural enforcement of the non-advice invariant

**Invariant:** *every output is a `Citation = (authoritative Source × Reported medical state)`;
the system never infers state and never originates advice.*

This is owned by **M4, the Citation Gateway**, and enforced by **construction, not review**:

1. **Single egress (choke point).** The delivery surface (M6) and every notification path have
   **no access to raw `LedgerEntry`s or free text**. Their only import is
   `CitationGateway.emit(...)`. Architecturally there is exactly one function through which a
   byte can reach a human. (Exit criterion 1.)

2. **`Citation` is unconstructable from advice.** Its only constructor is:
   ```
   Citation.of(source: Source, state: ReportedState, template_key: TemplateKey)
   ```
   There is **no constructor, field, or overload** that accepts system-authored prose. A
   `Citation` is references + a `template_key`, never a sentence the system wrote.

3. **Rendering is projection, not generation.** `template_key` selects from a **fixed, closed
   catalog** of templates whose only fillable slots are (a) *verbatim source text* and (b)
   *verbatim reported-state values*. Day-zero catalog:
   - `EXPECTED_DUE` — "{source.title} expects {rail.label}; last recorded {state.last}."
   - `OVERDUE` — same, plus the reported date that makes it overdue.
   - `DONE` — "{state.item} recorded, satisfying {source.title}."
   - `NUDGE_ASK_DOCTOR` — "{source.title} indicates a plan is expected here; none is recorded.
     **Ask your doctor.**"
   The imperative verb ("ask your doctor") is a **constant string in the catalog**, not a
   generated recommendation — it is the one fixed, non-clinical action the product is allowed
   to speak, and it points *away* from the system, to the doctor. No template can name a
   drug, dose, or course of action the sources didn't.

4. **"Never infers state."** State enters **only** through M1 adapters, each of which stamps a
   `Source`. The Ledger Engine (M3) may compute *schedule position* (date arithmetic over
   rails) but has **no code path that writes a `ReportedItem`** — it can only read them. There
   is therefore no place in the system where a medical state comes into being without an
   external source having asserted it. Absence ("no plan recorded") is itself a *reported*
   fact (the absence of a matching `ReportedItem`), so even the nudge is a citation, not an
   inference.

5. **The invariant holds for a doctor user too.** A doctor is a `Principal` with `patient`
   Grants (§1.1). They read the same `Citation` stream. The system still never originates
   advice *to* them; if the doctor issues an instruction, that instruction enters as a
   `doctor_instruction` **Source** via an M1 adapter — i.e., the doctor authors advice, the
   system merely *cites* it. (Exit criterion, universal boundary.)

> Enforcement test the design must pass: *delete every template that isn't (source×state)
> projection and the system still functions.* If a feature can't be expressed as such a
> projection, it is out of scope by construction.

---

## 4. The `manager → subject(s)` primitive (detail)

- **One table (`Grant`) is the whole model.** Reads and writes are gated by
  `authorize(principal, subject_id)` = `∃ Grant(manager=principal, subject=subject_id)`, in one
  middleware in front of M5. No feature branches on "how many subjects."
- **The manager's home view** is "the ledgers of all subjects I hold Grants for" — a fold over
  a list. Family (2–5 subjects) and a doctor's panel (hundreds) are the *same query*, differing
  only in list length and, optionally, pagination/filter — a delivery concern (M6), not a
  model concern.
- **Scope** on the Grant (`read`, `manage`, `report`) lets a teen-subject or a covering-doctor
  case be modeled without new entities. **[A]** MVP ships `read` + `report` + `manage`; finer
  RBAC is out (§7).
- **Every `Citation` is emitted in the context of one `subject_id`**, so multi-subject never
  leaks: the gateway takes a subject and the fold happens above it.

---

## 5. Expected-vs-done join → the ledger

**Inputs:** for a subject, `ExpectedItem[]` (from M2 evaluating applicable packs against the
subject's `ReportedState`) and `ReportedItem[]` (from M1).

**Algorithm (M3, pathway/source-agnostic):**

1. **Select applicable packs** for the subject via each pack's declarative `applicability`
   (age, sex, prior conditions expressed only as reported items). No hardcoded pathway names.
2. **Materialize `ExpectedItem`s**: evaluate each `Rail`'s `cadence`/`window` against the
   subject's relevant `ReportedItem`s (e.g., "last colonoscopy `observed_at` + 10y").
3. **Match** each `ExpectedItem` to a satisfying `ReportedItem` by `(subtype, window)`.
   Matching is generic set/interval logic — it never inspects clinical meaning.
4. **Assign `status`**:
   - matched in window → `done`
   - unmatched, within lead window → `due`
   - unmatched, past window → `overdue`
   - rail has `plan_required=true` and no `plan_marker` reported → `open_no_plan`
5. **Stamp provenance**: copy `source_id` (the pack's guideline, or the instruction's source)
   and `confidence_tier` onto the `LedgerEntry`. **A `LedgerEntry` is invalid without them** —
   enforced at the type level, so provenance and tier are *inseparable* from the gap (Exit
   criterion 4). When expected and reported come from different-tier sources, the entry carries
   **both** and the gateway renders the lower tier as the entry's effective confidence. **[A]**
6. **Gaps are the output of the join, not a list.** There is no per-example gap enumeration
   anywhere; every gap is `status ∈ {due, overdue, open_no_plan}` falling out of steps 3–4
   (Exit criterion 3). A brand-new pathway pack produces gaps the day it is registered with
   zero engine changes.

**Output:** `LedgerEntry[]` → each mapped by M4 to a `Citation` with the matching
`template_key`. `open_no_plan` → `NUDGE_ASK_DOCTOR`.

---

## 6. Day-zero vocabulary (what the public seams may speak)

The closed, versioned nouns/verbs the API, adapters, and packs share on day zero. Closed sets
are the *stable* contract; open vocabularies are where growth is absorbed.

**Entities (nouns):** `Principal`, `Subject`, `Grant`, `TrackingFile`, `Source`, `ReportedItem`,
`PathwayPack`, `Rail`, `ExpectedItem`, `LedgerEntry`, `Citation`.

**`ReportedItem.type` (closed):** `result`, `instruction`, `prescription`, `demographic`,
`plan_marker`.

**`Source.class` (closed, extend in one file):** `public_guideline`, `doctor_instruction`,
`prescription`, `subject_reported`.

**`confidence_tier` (closed, ordered):** `T1_authoritative_public`, `T1_authoritative_personal`,
`T2_derived`, `T3_self_reported`.

**`LedgerEntry.status` (closed):** `done`, `due`, `overdue`, `open_no_plan`.

**`Grant.scope` (closed):** `read`, `report`, `manage`. **`Grant.relation` (open label):**
`self`, `family_member`, `patient`, …

**Template catalog (closed):** `EXPECTED_DUE`, `OVERDUE`, `DONE`, `NUDGE_ASK_DOCTOR`.

**Open vocabularies (growth lands here, no schema change):** `ReportedItem.subtype`,
`Rail.key`, `PathwayPack.id` — namespaced strings owned by packs/adapters.

**Public verbs (seam operations):**
`ingest(source_adapter_key, raw) → ReportedItem[]`,
`register_pathway_pack(pack)`,
`get_ledger(subject_id) → LedgerEntry[]`,
`emit_citations(subject_id) → Citation[]`,
`grant(manager, subject, scope)`.

Notably **absent** (and permanently so): any `recommend`, `diagnose`, `infer`, or
`advise` verb. The vocabulary itself has no word for advice.

---

## 7. Explicitly out of the MVP

- **Pillar 2 / the integrated overview (*המכלול*).** No cross-pathway synthesis, risk scoring,
  or holistic dashboards. Only per-pathway expected-vs-done.
- **Any inference / suspicion engine.** No "the system thinks you may have X." The rail grammar
  is deliberately too weak to express it; there is no diagnostic module.
- **Originating advice in any form** — no recommendations, no triage, no dosing. The template
  catalog cannot express it.
- **Rich RBAC / consent workflows.** Grants exist; the *proof* and revocation ceremony
  (identity verification, minor-to-adult transitions, clinic hierarchies) is thin/stubbed.
- **Automated clinical source integrations** (live EHR/FHIR feeds). The M1 seam is designed for
  them, but day-zero adapters are: one public-guideline loader, one manual/structured
  subject-report form, one doctor-instruction form. Building more adapters now would be
  speculative.
- **Free-text NLP over documents.** Adapters parse structured/normalized input; extracting facts
  from arbitrary prose is future work behind the same seam.
- **Scheduling/booking, messaging the doctor, notifications infrastructure** beyond emitting the
  citation stream.
- **Versioned pathway conflict resolution** (two packs disagree). MVP applies packs
  independently; reconciliation is future. **[A]**

---

## 8. How this design answers each exit criterion

| # | Criterion | Where it lives |
|---|---|---|
| 1 | Non-advice enforced by architecture | §3 — single Citation Gateway; `Citation` unconstructable from advice; closed projection-only template catalog. |
| 2 | `manager→subject(s)` one primitive | §1.1 / §4 — one `Grant` table; multi-subject is list length, no special case. |
| 3 | Expected & reported distinct, gaps by join | §1.3–1.4 / §5 — separate `PathwayPack`/rails vs `ReportedItem`; gaps are `status` from the join, never enumerated. |
| 4 | Provenance + tier travel with every item | §1.2 / §5 step 5 — tier lives on immutable `Source`; `LedgerEntry` invalid without `source_id` + tier. |
| 5 | New pathway / new source = one owner's change | §2.1 — Seam B (pack) and Seam A (adapter); core is pathway/source-agnostic. |
| 6 | Scoped to Pillar 1 + stated sources | §7 — overview, inference, extra sources explicitly out. |
