# The Responsible Doctor — MVP Architecture

> A proactive care-coordinator that **manages and steers** medical processes and **never originates
> advice**. The unifying object is a personal medical tracking file (*תיק מעקב רפואי*) that fuses
> authoritative sources with the subject's reported state, shows what is **expected** vs **done**, and — when
> an open process has no plan — **nudges the subject to ask their doctor**.

This document specifies the MVP shape: the data model, the module boundaries, the ownership of the citation
invariant, the `manager → subject(s)` primitive, the expected-vs-done ledger, the day-zero vocabulary, and
what is deliberately excluded.

---

## 0. Design stance & load-bearing assumptions

- **The invariant is a type, not a rule.** The non-advice boundary is enforced by making `Citation` the only
  value that can cross the outbound seam, and by making `Citation` *unconstructable* except from two
  pre-existing, resolved references. If it cannot be expressed as `(authoritative source × reported state)`,
  it cannot leave the system. There is no code path that emits free text.
- **"Nudge" is not advice.** A nudge is a fixed, content-free system affordance ("ask your doctor about this
  open process"). It carries no clinical recommendation. It is itself a `Citation` — the source is the
  pathway/guideline that says *a plan is expected here*; the reported state is *no plan on file*.
- **Absence is observed, never inferred.** The engine may report that no reported item matches an expectation.
  That is a set-membership fact over reported data, not a medical inference about the subject.
- **Assumption (stated):** clinical matching uses coded identifiers on both sides (guideline steps and
  reported items are tagged with a code from a small day-zero code space — e.g. LOINC-like test codes,
  procedure/screening codes, vaccine codes). Where a source arrives uncoded, ingestion attaches a code or
  marks it `uncoded`; uncoded items never auto-match and surface at the lowest confidence tier.
- **Assumption (stated):** persistence is a relational store; the design is storage-agnostic and names
  logical entities, not tables.
- **Delivery surface** is not prescribed by the brief; this design exposes a service/API seam and leaves the
  UI as a pure consumer of `Citation` streams.

---

## 1. Data model

Five bounded vocabularies of nouns. Each is owned by exactly one module (§2). Arrows are references, not
embedding.

### 1.1 Account & stewardship

```
Party            { party_id, kind: person | provider, display_name }
Subject          { subject_id, party_id }                     -- the person a file is about
Manager          { manager_id, party_id }                     -- an operator of files
Stewardship      { stewardship_id, manager_id, subject_id,
                   role: self | family | clinician,
                   scope: ScopeSet, granted_by, granted_at, revoked_at? }
```

- A **Subject** is the owner of exactly one **medical tracking file**.
- A **Manager** operates one-or-many subjects **only** through `Stewardship` edges. There is no other way to
  reach a subject's data.
- **Self-management is not a special case:** a person managing themselves is a `Stewardship` with
  `role = self` where the manager's and subject's `party_id` are the same. Family and clinician are the same
  edge with a different `role` label and a wider/narrower `scope`. (See §4.)

### 1.2 Sources (the authoritative half of every citation)

```
Source           { source_id, subject_id?, source_type,
                   provenance: Provenance,
                   confidence_tier: ConfidenceTier,
                   payload: normalized authoritative content,
                   ingested_at }
Provenance       { origin, authority, document_ref, captured_by, captured_at, raw_hash }
```

`source_type` (day-zero closed set):

| source_type            | subject-bound? | typical confidence_tier |
|------------------------|----------------|-------------------------|
| `public_guideline`     | no (library)   | `guideline`             |
| `doctor_instruction`   | yes            | `clinician_directive`   |
| `prescription`         | yes            | `clinician_directive`   |
| `result_source`        | yes            | `measured`              |

A **public_guideline** source is not subject-bound — it is authoritative content referenced by the pathway
library. The other three are subject-bound authoritative artifacts.

### 1.3 Reported state (the reported half of every citation)

```
ReportedItem     { reported_item_id, subject_id, code, code_space,
                   value?, status: done | received | declined | in_progress,
                   observed_at, reporter: Stewardship-ref,
                   source_id?,                          -- optional backing Source
                   confidence_tier: ConfidenceTier }
```

- A `ReportedItem` is a **state asserted by a reporter** (the subject, a family manager, or an importer acting
  under a `Stewardship`). It is never produced by the engine.
- It may or may not be backed by a `Source` (e.g. a lab result is a reported item backed by a `result_source`;
  a self-reported "I got the flu shot" is a reported item with no source and a lower tier).

### 1.4 Expected side — the pathway rails (declarative)

```
Pathway          { pathway_id, name, version, owner: 'library',
                   applicability: Predicate,             -- over subject attributes
                   steps: [ExpectedStep] }
ExpectedStep     { step_id, code, code_space,
                   cadence: Cadence,                     -- one-time | age-anchored | interval | conditional
                   window: Window,                       -- due/overdue offsets
                   requires_plan: bool,                  -- if true and open+unplanned → nudge
                   source_ref: source_id (public_guideline) }
```

- The pathway library is **declarative data**, not code. A pathway is a rail: predicate + steps + the guideline
  source each step cites. Adding a rail is adding a `Pathway` row (§5, exit criterion 5).
- `ExpectedStep.source_ref` binds each step to its authoritative `public_guideline` source — **provenance is
  attached at authoring time**, so it cannot be lost downstream.

### 1.5 Materialized expectation & the ledger

```
ExpectedItem     { expected_item_id, subject_id, pathway_id, step_id,
                   code, due_at, window, requires_plan,
                   source_ref }                          -- inherited from ExpectedStep
LedgerEntry      { entry_id, subject_id, code,
                   status: LedgerStatus,
                   expected_item_id?, matched_reported_item_id?,
                   citation: Citation }                  -- MANDATORY, non-null
```

`LedgerStatus` (day-zero closed set): `done`, `due`, `overdue`, `gap`, `open_unplanned`.

### 1.6 Citation — the only outbound value

```
Citation         { source_ref: SourceRef,               -- MUST resolve to a Source
                   state_ref: StateRef,                  -- ReportedItem | Absence
                   confidence_tier: ConfidenceTier,      -- copied from source_ref's Source
                   emitted_by: 'citation_kernel' }
StateRef         = Present(reported_item_id)
                 | Absence(expected_item_id)             -- "no reported item matches this expectation"
```

- A `Citation` **cannot be constructed** except by the Citation Kernel (§3) from a `source_ref` that resolves
  to a stored `Source` and a `state_ref` that resolves either to a stored `ReportedItem` or to a typed
  `Absence` pointing at a stored `ExpectedItem`.
- There is **no free-text field** on `Citation`. Every rendered sentence is a template over these resolved
  references. The system literally has no place to put advice.

---

## 2. Module / boundary structure

```
                          ┌──────────────────────────────────────────────┐
                          │              OUTBOUND SEAM                    │
                          │   speaks ONLY Citation / LedgerEntry          │
                          └───────────────▲──────────────────────────────┘
                                          │  Citation (only)
                          ┌───────────────┴──────────────────────────────┐
                          │           CITATION KERNEL  (§3)               │
                          │   sole constructor of Citation               │
                          │   resolves SourceRef + StateRef, copies tier  │
                          └───────▲───────────────────────▲──────────────┘
                                  │ ExpectedItem          │ ReportedItem / Absence
                  ┌───────────────┴─────────┐   ┌─────────┴───────────────┐
                  │  RECONCILIATION / LEDGER │◄──┤   REPORTED STATE STORE   │
                  │  joins expected × done   │   │   (subject state)        │
                  └───────────▲──────────────┘   └─────────▲───────────────┘
                              │ ExpectedItem                │ ReportedItem
                  ┌───────────┴──────────┐        ┌─────────┴───────────────┐
                  │  EXPECTATION ENGINE  │        │      INGESTION           │
                  │  Pathway × Subject   │        │  adapters → canonical    │
                  └───────────▲──────────┘        │  Source + ReportedItem   │
                              │ Pathway            │  + provenance + tier     │
                  ┌───────────┴──────────┐        └─────────▲───────────────┘
                  │   PATHWAY LIBRARY    │                  │ raw sources
                  │  declarative rails   │        ┌─────────┴───────────────┐
                  └──────────────────────┘        │  ACCOUNT / STEWARDSHIP   │
                                                   │  authorizes every read/  │
                                                   │  write by subject_id     │
                                                   └──────────────────────────┘
```

**Boundaries and single owners:**

| Module | Owns | May not |
|---|---|---|
| **Account / Stewardship** | `Party`, `Subject`, `Manager`, `Stewardship`; all authorization | know anything clinical |
| **Ingestion** | `Source`, `ReportedItem`, provenance capture, tier assignment | compute expectations or citations |
| **Pathway Library** | `Pathway`, `ExpectedStep` (declarative rails) | know any subject's state |
| **Expectation Engine** | `ExpectedItem` (materialize rails for a subject) | read reported state |
| **Reconciliation / Ledger** | `LedgerEntry`, the expected×reported join, status | construct a `Citation` |
| **Citation Kernel** | `Citation` construction, tier propagation | invent a source or a state |
| **Outbound Seam** | serialization to the delivery surface | hold logic; it is a pass-through |

The load-bearing rule: **data flows up and narrows.** Reconciliation decides *status*; only the Kernel turns a
status into an emittable `Citation`; only the seam serializes. No module downstream of the Kernel can add a
field the Kernel did not resolve.

---

## 3. Ownership of the citation (non-advice) invariant

This is the heart of the design. Exit criterion 1 asks for *one place every output must pass through that can
only emit a `(source × reported-state)` citation.* That place is the **Citation Kernel**.

### 3.1 The single choke point

- The outbound seam's type signature is `Stream<Citation>` (or `Stream<LedgerEntry>`, and every `LedgerEntry`
  carries a non-null `Citation`). **No other type is serializable outward.** There is no `Advice`, `Message`,
  `Recommendation`, or `String` in the outbound contract.
- `Citation` has a **private constructor**. The only public entry point is:

  ```
  CitationKernel.cite(source_ref, state_ref) -> Citation
      require  resolve(source_ref)  is a stored Source        else REJECT
      require  resolve(state_ref)   is a stored ReportedItem
               OR a stored ExpectedItem (as Absence)          else REJECT
      confidence_tier := resolve(source_ref).confidence_tier  -- copied, not chosen
      return Citation{ source_ref, state_ref, confidence_tier, emitted_by }
  ```

- The Kernel takes **references, never content**. It cannot be handed a sentence. Both halves must already
  exist in a store the Kernel does not write to. This makes fabricating either half impossible: you cannot
  cite a source that was never ingested, and you cannot cite a state that was never reported.

### 3.2 Why this forecloses the two failure modes

- **Never originates advice.** The only textual output is rendered by templates keyed on `LedgerStatus` and the
  two resolved references (e.g. *"Guideline X (tier: guideline) expects step Y; no matching result on file"*).
  Templates are fixed strings with reference slots. There is no generation step, so there is nothing to
  originate.
- **Never infers state.** `state_ref` is either `Present(reported_item_id)` — a stored assertion by a reporter
  — or `Absence(expected_item_id)` — a set-membership fact ("the reported-state store contains no item matching
  this expectation"). Neither is a clinical inference. The Kernel has no access to any inference facility.

### 3.3 The nudge is a citation

For `LedgerStatus = open_unplanned` (a step with `requires_plan = true`, past its window, with no reported plan):

```
Citation{ source_ref = the guideline step's source (says: a plan is expected),
          state_ref  = Absence(expected_item_id) (no plan reported),
          confidence_tier = guideline }
```

The seam renders this through the fixed `open_unplanned` template: *"This open process expects a plan and none
is on file — ask your doctor."* The phrase "ask your doctor" is a **constant affordance of the template**, not
generated content and not a clinical recommendation. There is no template that says what the doctor should do.

### 3.4 Universality (including doctor users)

The Kernel sits below the account layer's role distinctions. A `clinician` manager reads the *same* `Citation`
stream through the *same* Kernel. A doctor gets citations, never a channel to originate advice **inside this
system**. (A doctor originating advice out-of-band becomes a `doctor_instruction` **Source** on ingest — i.e.
it re-enters as an authoritative source to be cited, never as system output.)

---

## 4. The `manager → subject(s)` primitive

One abstraction: the **`Stewardship`** edge. Everything is expressed as edges; nothing is a special case.

```
Stewardship(manager_id, subject_id, role, scope)
```

- **Self**: `role = self`, manager and subject are the same party. One edge.
- **Family**: one `manager_id` with N `Stewardship` rows to N `subject_id`s, `role = family`.
- **Clinician**: one `manager_id` (a provider party) with M `Stewardship` rows to M patients, `role = clinician`.

Multi-subject is **the same abstraction applied more than once** — a set of edges — not a distinct
"family mode" or "clinician mode." The engine never branches on cardinality.

**Authorization gate.** Every read or write names a `subject_id` and must present a live (`revoked_at = null`)
`Stewardship` from the acting `manager_id` to that `subject_id`; `scope` narrows which `source_type`s /
operations are permitted (e.g. a `family` steward may report items and read the ledger; a `clinician` steward
may additionally attach `doctor_instruction` sources). Role changes what `scope` allows — it does **not** open
a second data path and does **not** change what the Kernel emits.

**Reporter identity.** A `ReportedItem.reporter` is the `Stewardship` under which it was asserted, so
provenance of *who reported* travels with reported state, parallel to source provenance on the authoritative
side.

---

## 5. Joining expected × reported → the ledger

The two sides are **physically distinct stores** and are joined at reconciliation time — gaps are *computed*,
never enumerated per example (exit criterion 3).

### 5.1 Pipeline

1. **Materialize expectations.** Expectation Engine evaluates each `Pathway.applicability` predicate against
   the subject's attributes; for matching pathways it expands `ExpectedStep`s into `ExpectedItem`s with
   concrete `due_at`/`window`, each inheriting `source_ref` from its step.
2. **Load reported state.** Reconciliation reads the subject's `ReportedItem`s.
3. **Join on `(code, code_space)` within the temporal window.** For each `ExpectedItem`:

   | condition | `LedgerStatus` | citation shape |
   |---|---|---|
   | matching `ReportedItem` with `status = done`, in window | `done` | source × `Present(reported)` |
   | no match, `now < due_at` | `due` | source × `Absence(expected)` |
   | no match, `now > window.overdue_at` | `overdue` | source × `Absence(expected)` |
   | no match, not one-time, no history | `gap` | source × `Absence(expected)` |
   | `requires_plan`, open, past window, no plan reported | `open_unplanned` | source × `Absence(expected)` → **nudge** |

4. **Emit.** For each `LedgerEntry`, call `CitationKernel.cite(source_ref, state_ref)`; attach the `Citation`.
   The `confidence_tier` on the entry is the source's tier, **copied through the Kernel** — a citation is
   inseparable from its source (exit criterion 4).

### 5.2 Provenance & confidence travel end to end

`ExpectedStep.source_ref` (authoring) → `ExpectedItem.source_ref` (materialization) → `Citation.source_ref` +
`Citation.confidence_tier` (emission). At no hop is the source detachable from the item; an `ExpectedItem`
without a resolvable `source_ref` is rejected at materialization, so an uncited expectation can never reach
the ledger.

### 5.3 Confidence tiers (day-zero closed set, ordered)

`measured` > `clinician_directive` > `guideline` > `self_reported` > `uncoded`.

Tier is a property of the **source**, assigned once at ingestion, and only ever copied thereafter — never
recomputed by the ledger or the Kernel.

---

## 6. Extensibility — one owner per change (exit criterion 5)

| Change | Single owner | Touches |
|---|---|---|
| **Add a new pathway/rail** | Pathway Library | one new `Pathway` (data row: predicate + steps + guideline source). Nothing in the ledger engine, account model, Kernel, or seam changes — they operate on canonical `ExpectedItem`. |
| **Add a new source type** | Ingestion (adapter + source-type/tier registry) | one adapter that normalizes to canonical `Source`/`ReportedItem` and registers a `confidence_tier`. The join works on `code`, the Kernel on references — neither is aware of `source_type`. |

Because Reconciliation and the Kernel see only the canonical abstractions (`ExpectedItem`, `ReportedItem`,
`Source`), a new rail or source type does **not scatter** across the ledger, the account model, and the output
layer. That is the structural payoff of narrowing to canonical types before the join.

---

## 7. Day-zero vocabulary (what the public seams may speak)

The seam's contract is closed. These are the only nouns, verbs, and enums that cross it.

**Nouns:** `Subject`, `Manager`, `Stewardship`, `Source`, `ReportedItem`, `Pathway`, `ExpectedItem`,
`LedgerEntry`, `Citation`, `Provenance`, `ConfidenceTier`.

**Enums:**
- `role`: `self | family | clinician`
- `source_type`: `public_guideline | doctor_instruction | prescription | result_source`
- `LedgerStatus`: `done | due | overdue | gap | open_unplanned`
- `ConfidenceTier`: `measured | clinician_directive | guideline | self_reported | uncoded`
- `StateRef`: `Present | Absence`

**Verbs (seam operations):**
- `grantStewardship(manager, subject, role, scope)` / `revokeStewardship(...)`
- `report(subject, ReportedItem)` — assert a reported state (authz via Stewardship)
- `ingestSource(subject?, Source)` — attach an authoritative source
- `viewLedger(subject) -> Stream<LedgerEntry>` — read-only; every entry carries a `Citation`

**The seam may not speak:** `advice`, `recommendation`, `diagnosis`, `suggestion`, or any free-text clinical
field. There is no verb that emits text the Kernel did not build from references. This closed vocabulary *is*
the enforcement surface.

---

## 8. Explicitly out of the MVP (exit criterion 6)

- **The integrated overview (*המכלול*)** — Pillar 1 only; no cross-pathway synthesis or unified health picture.
- **Any inference / suspicion engine** — no deriving medical state from data; `Absence` is the only
  "negative," and it is set membership, not inference.
- **Advice generation of any kind** — no generative text, no recommendations, no triage. The Kernel forecloses
  it structurally.
- **Unstated future source types** — only the four day-zero `source_type`s. New ones arrive via §6, not by
  anticipation.
- **Cross-subject analytics, population/cohort views, scheduling/booking, messaging with providers,
  billing** — none are in scope.
- **Auto-coding of uncoded sources** — uncoded items surface at the lowest tier and never auto-match; NLP
  coding is out.

Anything built for the overview, for inference-based suspicions, or for unstated sources is speculative and
counts against the design.

---

## 9. How each exit criterion is met (traceability)

1. **Boundary enforced by architecture** → §3: `Citation` is the only outbound type, privately constructed by
   the Kernel from two resolved references; no path can originate advice or infer state.
2. **`manager → subject(s)` single primitive** → §4: one `Stewardship` edge; self/family/clinician differ only
   by `role`/`scope`; multi-subject is repeated edges, not a mode.
3. **Expected vs reported distinct, gaps computed** → §1.4–1.5, §5: separate stores joined on `(code, window)`;
   status is derived, not listed per example.
4. **Provenance + tier inseparable** → §5.2–5.3: `source_ref` and `confidence_tier` propagate step → item →
   citation; an uncited item is rejected before the ledger.
5. **New pathway / source = one owner's change** → §6: a `Pathway` row; an ingestion adapter. Canonical types
   keep it from scattering.
6. **Scoped to Pillar 1 + MVP sources** → §8: overview, inference, and unstated sources are excluded by
   construction.
