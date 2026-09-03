# The "Responsible Doctor" — MVP Architecture (synthesized)

*Pillar 1 only: manage and steer medical processes — show **expected-next** vs **done**, and nudge
the person to ask their doctor when an open process has no plan. The system **never originates advice
and never infers medical state**, for every user including a doctor.*

This is a standalone design. It is a synthesis of three independent MVP designs, taking the strongest
structural choice on each axis (not a union). Where the three diverged, the pick and its reason are
recorded in `divergence.md`.

---

## 0. Design stance and load-bearing choices

The whole system is organized around one sentence, treated as a **type, not a rule**:

> **Every output is a `Citation` = (an authoritative `Source`) × (a `Reported` state, present or
> absent). The system has no code that can originate advice or write/infer a medical state.**

Two structural facts make that hold, and everything else is arranged to keep them cheap:

1. **One egress, one constructor.** There is exactly one module that can mint a value the outside
   world may see — the **Citation Gateway** — and the only thing it can construct is a `Citation`,
   from *references it looks up*, never from content it is handed. Delete the Gateway and the system
   can emit nothing. (Enforcement: §3.)
2. **One writer of state.** Medical state enters at exactly one place — the **Ingestion Port** — and
   only from a `ReportedItem` carrying a human reporter. No other module can write state, so "the
   system infers state" describes code that does not exist. (Enforcement: §3.2.)

**Stated assumptions (MVP):**

- **Delivery surface:** a single deployable service (modular monolith) with a thin read API over
  JSON. Nothing in the invariant depends on this; the UI is a pure consumer of `Citation` streams.
- **Coded matching only.** Guideline steps and reported items carry a code from a small day-zero code
  space (LOINC-like result codes, procedure/screening codes, vaccine codes). Matching is **code
  equality within a time window** — a lookup, never clinical reasoning. Uncoded items are marked
  `uncoded`, never auto-match, and surface at the lowest tier.
- **Confidence tier is an attribute of the source class**, assigned once at ingest and only ever
  copied thereafter — never a computed trust score.
- **Persistence is relational**; entities below are logical, not tables.

---

## 1. Data model

Three families stay physically and conceptually separate — **who** (accounts), **what-should-happen**
(expected rails), **what-was-reported** (subject state). They meet only inside the reconciliation
join, and every result leaves only through the Gateway.

### 1.1 Accounts and stewardship

```
Party        { party_id, kind: person | provider, display_name }
Subject      { subject_id, party_id,
               demographics { birth_date, sex_at_birth, risk_flags[] } }  -- reported facts, drive applicability only
Manager      { manager_id, party_id }
Link         { link_id, manager_id, subject_id,
               role:  self | guardian | clinician,        -- metadata; never a code branch
               scope: ScopeSet,
               granted_by, granted_at, revoked_at? }       -- lifecycle
```

- A **Subject** owns exactly one **medical tracking file** (*תיק מעקב רפואי*). The file belongs to
  the subject; access is only ever via a live `Link`.
- `demographics`/`risk_flags` are **reported facts with provenance**, used to evaluate rail
  applicability predicates. They never yield a new medical conclusion. (See §3.2.)

### 1.2 Sources — the authoritative half of every citation

A `Source` is an authoritative artifact that **defines or authorizes** an expectation. Results are
*not* sources — they are reported facts (§1.4).

```
Source     { source_id, source_class, confidence_tier,
             provenance: Provenance, authority_scope, payload, ingested_at }
Provenance { origin, issued_by, issued_at, ingested_at, attachment_ref?, raw_hash }
```

`source_class` (day-zero closed set — three classes):

| source_class        | subject-bound? | defines a rail?        | confidence_tier      |
|---------------------|----------------|------------------------|----------------------|
| `PUBLIC_GUIDELINE`  | no (library)   | yes (a Pathway)        | `guideline`          |
| `DOCTOR_INSTRUCTION`| yes            | authorizes a step      | `clinician_directive`|
| `PRESCRIPTION`      | yes            | authorizes a step      | `clinician_directive`|

- Only `PUBLIC_GUIDELINE` carries (a reference to) a **Pathway rail**. The two subject-bound classes
  authorize or satisfy individual steps but do not define general expectations.
- `confidence_tier` is derived **only** from `source_class`, at ingest, immutable thereafter (§5.3).

### 1.3 Pathway library — the expected axis (declarative rails)

```
Pathway      { pathway_id, title, authored_by_source_id }        -- a named rail, from a PUBLIC_GUIDELINE
ExpectedStep { step_code, pathway_id,
               applicability: Predicate,   -- over Subject demographics/risk_flags (evaluated, not reasoned)
               cadence:       Cadence,     -- once | every(interval) | at(age) | conditional
               window:        Window,      -- due/overdue offsets around the anchor
               satisfied_by:  [match_key], -- which reported codes count as done (code equality)
               requires_plan: bool,        -- if open + unplanned past window → nudge
               authorizing_source_ref }    -- the Source that authorizes THIS step (defaults to the pathway's)
```

The library is **pure data**. A pathway is `predicate + steps + the guideline source each step
cites`. Provenance is bound to each step **at authoring time**, so it cannot be lost downstream.

### 1.4 Reported items — the reported/done axis

```
ReportedItem { item_id, subject_id, kind, code, code_space,
               value?, observed_at,
               reporter: Link-ref,          -- who asserted it, under which stewardship
               reported_at,
               linked_source_id?,           -- optional backing artifact (a lab doc, a doctor note)
               attachment_ref? }
kind ∈ { RESULT, DOCTOR_INSTRUCTION, PRESCRIPTION, EVENT }

Absence      { expected_step_ref }          -- typed value, not stored: "no reported item matches this instantiated step"
```

- A `ReportedItem` is a **fact a human reporter asserts**; the engine never produces one.
- **Dual-role registration (at ingest, once):** a `ReportedItem` of kind `DOCTOR_INSTRUCTION` or
  `PRESCRIPTION` also registers a **same-id `Source`** of the matching class. A doctor's "repeat in 3
  months" is simultaneously a recorded fact *and* an authorized expected step — the two axes stay in
  sync **without inference**.
- `Absence` is a first-class typed value so that a gap is still a well-formed `(source × state)`
  citation, with the state side pointing at a concrete instantiated step.

### 1.5 Citation — the sole output type

```
Citation { citation_id, subject_id,
           source_ref:    SourceRef!,       -- MUST resolve to an ingested Source
           reported_ref:  ReportedState!,   -- ReportedItem | Absence  (closed union; no String)
           status:        Status,           -- DONE | DUE | OVERDUE | OPEN_NO_PLAN
           confidence_tier: ConfidenceTier, -- copied from source_ref; inseparable
           rendered:      TemplateFill,     -- fixed template over the two resolved refs (§3.3)
           emitted_by:    'citation_gateway' }

ReportedState = Present(ReportedItem) | Absence(expected_step_ref)
Status        = DONE | DUE | OVERDUE | OPEN_NO_PLAN
```

There is **no** `advice`, `recommendation`, `assessment`, `diagnosis`, `inferred_state`, or free-text
`message` field anywhere on this type. Its entire expressive range is: which authoritative source,
which reported state (or absence), and which of four timing relations. That absence *is* the design.

### 1.6 Ledger

`Ledger = List<Citation>` for a subject — the tracking file. It is **computed on read**, never stored
as authored content. Gaps are the citations whose `reported_ref` is an `Absence` (or an out-of-window
match); the nudge is the citation whose `status = OPEN_NO_PLAN`.

---

## 2. Module / boundary structure

```
                 ┌────────────────────────────────────────────────────┐
   PUBLIC SEAM   │        API layer — speaks day-zero vocabulary (§6)  │
                 └───────────────┬───────────────────────▲─────────────┘
                    writes       │                        │ reads: Citation / Ledger only
          ┌──────────────────────┴───────┐                │
          ▼                              ▼                 │
 ┌─────────────────┐        ┌──────────────────────────┐  │
 │  ACCOUNTS  (§4) │        │  INGESTION PORT          │  │
 │  manager→subject│        │  the ONLY state writer   │  │
 │  authorizes all │        │  normalizes → Source +   │  │
 │  reads/writes   │        │  ReportedItem, stamps     │  │
 └───────┬─────────┘        │  provenance + tier        │  │
         │ scopes           └───────────┬───────────────┘  │
         │                              ▼                   │
         │                  ┌───────────────────────────┐  │
         │                  │  SOURCES                   │  │
         │                  │  source classes + tiers    │  │
         │                  └───────────┬───────────────┘  │
         │                  ┌───────────┴───────────────┐  │
         │                  │  PATHWAY LIBRARY           │  │
         │                  │  declarative rails         │  │
         │                  └───────────┬───────────────┘  │
         │                              ▼                   │
         │                  ┌───────────────────────────┐  │
         └─────────────────▶│  RECONCILIATION ENGINE     │  │
                            │  expected × reported join  │  │
                            │  emits GateRequests only   │  │
                            └───────────┬───────────────┘  │
                                        ▼                   │
                            ┌───────────────────────────┐   │
                            │  CITATION GATEWAY          │───┘
                            │  the ONLY egress;          │
                            │  sole constructor of Citation
                            └───────────────────────────┘
```

Data flows **up and narrows**: the Reconciliation Engine decides *status*; only the Gateway turns a
status into an emittable `Citation`; only the API seam serializes. No module downstream of the Gateway
can add a field the Gateway did not resolve.

| Module | Owns | May NOT do |
|---|---|---|
| **Accounts** | `Party`, `Subject`, `Manager`, `Link`; **all authorization** | hold clinical content |
| **Ingestion Port** | the *only* write path into medical state; provenance capture | compute gaps or citations; infer state |
| **Sources** | `source_class` set + confidence-tier mapping | know any subject's expected/done status |
| **Pathway Library** | `Pathway`, `ExpectedStep` (declarative rails) | know any specific subject |
| **Reconciliation Engine** | the expected×reported join; `status` | construct a `Citation`; write prose or state |
| **Citation Gateway** | construction of `Citation`; rendering templates | originate content — it only *assembles* resolved refs |
| **API layer** | the public vocabulary seam | hold logic; it is a pass-through |

The Reconciliation Engine is generic over `ExpectedStep` and `ReportedItem`; the Gateway is generic
over `Source` and reported-state. Neither knows any specific pathway or source class — so a new rail
or source class **cannot scatter** into the ledger, the account model, or the output layer (§7).

---

## 3. Ownership of the citation (non-advice, non-inference) invariant

This is the core of the design. Exit criterion 1 asks for *one place every output must pass through
that can only emit a `(source × reported-state)` citation.* That place is the **Citation Gateway**,
backed by the **single-writer** rule for state.

### 3.1 One egress, one type, one door

Every read handler in the API returns `Citation` (or `Ledger = List<Citation>`). No other domain type
is exported. `Citation` has a **sealed, module-private constructor**; the only public entry point is:

```
Gateway.cite(request: GateRequest, viewer: StewardshipContext) -> Citation

GateRequest { source_ref: source_id!,      -- MUST resolve to a stored Source
              state_ref:  state_id | ABSENT(expected_step_ref),
              status:     Status }

  require  resolve(source_ref) is a stored Source                       else REJECT
  require  resolve(state_ref)  is a stored ReportedItem  OR  a typed Absence
           whose expected_step_ref names a live instantiated step        else REJECT
  confidence_tier := resolve(source_ref).confidence_tier                 -- copied, never chosen
  rendered        := template[status].fill(resolved source, resolved state)
  return Citation{ ... emitted_by = 'citation_gateway' }
```

- The Gateway takes **references, never content.** There is no text parameter, no template *engine*,
  no LLM call, no advice vocabulary. It looks references up and copies their fields.
- Both halves must already exist in stores the Gateway does not write to. You **cannot cite a source
  that was never ingested**, and you **cannot cite a state that was never reported**. Fabricating
  either half is impossible.

### 3.2 One writer of state — inference is designed out

State is written in exactly one place: the **Ingestion Port**, only in response to a `ReportedItem`
with a human `reporter`. Therefore:

- The Reconciliation Engine is **read-only over state**. It may only match reported items to expected
  steps by code equality and compute a `status`. It cannot create, derive, or upgrade a medical fact
  — code equality is a lookup, not a clinical inference.
- Demographics/risk_flags driving applicability are themselves reported facts with provenance; the
  engine evaluates a *declared predicate* over them and never concludes a new fact.
- Because no module other than the Ingestion Port can write state, "the system infers state" has no
  code that could do it — for any user, **including a doctor** (a doctor's input enters as a reported
  item / co-registered source with provenance, exactly like anyone else's).

### 3.3 The nudge is a citation, not advice

For `status = OPEN_NO_PLAN` (a step with `requires_plan = true`, open, past its window, no plan
reported):

```
Citation{ source_ref  = the guideline/instruction step that says a plan is expected,
          reported_ref = Absence(expected_step_ref),          -- no plan/result on file
          status = OPEN_NO_PLAN,
          rendered = "{source.title} expects {step.label}; nothing is on file. Ask your doctor about it." }
```

`"ask your doctor"` is a **constant slot of the fixed template**, not generated content. No template
selects a test, dose, or course of action; it only names the source and points back to the human
authority. It is still a `(source × reported-state)` citation and flows through the same single
egress as everything else.

### 3.4 Universality (including doctor users)

The Gateway sits **below** the account layer's role distinctions. A `clinician` manager reads the
*same* `Citation` stream through the *same* Gateway. A doctor originating advice out-of-band re-enters
the system as a `DOCTOR_INSTRUCTION` **Source** on ingest — an authoritative source to be *cited*,
never as system output. There is no channel that lets any user make the system originate advice.

---

## 4. The `manager → subject(s)` primitive

One relationship type, `Link`, and one traversal. No special cases.

```
Manager --Link{ role, scope }--> Subject          (0..* on both sides)
```

- **Self:** `role = self`, manager and subject the same party — a one-subject case of the same edge,
  not a separate user type.
- **Family:** one `Manager` with N `Link`s to N subjects, `role = guardian`.
- **Clinician:** one `Manager` (a provider party) with M `Link`s to M patients, `role = clinician`.

Multi-subject is **cardinality on the one primitive**, not a "family mode" or "clinic entity." Every
read and write is parameterized by `(manager_id, subject_id)` and authorized by resolving a live
`Link` whose `scope` covers the operation. Multi-subject views are just iteration over a manager's
link set; the engine and Gateway operate **per subject** and never branch on cardinality.

`role` only tunes default `scope` (e.g. a guardian may report items and read the ledger; a clinician
may additionally attach `DOCTOR_INSTRUCTION` sources). Role changes what `scope` allows — it does
**not** open a second data path and does **not** change what the Gateway emits.

**Reporter identity** travels with reported state: `ReportedItem.reporter` is the `Link` under which
it was asserted — provenance of *who reported*, parallel to source provenance on the authoritative
side.

---

## 5. Expected vs done — the ledger join

### 5.1 The two sides stay distinct

**Expected** lives only in the Pathway Library as `ExpectedStep` rails. **Reported/done** lives only
as `ReportedItem`s. They are **never merged at rest**; they meet only inside the Reconciliation
Engine, on read.

### 5.2 The join algorithm (generic, not per-example)

For a given `(manager, subject)`, over the manager's authorized scope:

1. **Instantiate rails.** Select every `ExpectedStep` whose `applicability` predicate is true for the
   subject's demographics/risk_flags; expand `cadence`/`window` into concrete **instantiated steps**
   (subject_id + step_code + due window), each inheriting `authorizing_source_ref`. Instantiated
   steps are ephemeral (computed on read), but each is **addressable** so an `Absence` can point at
   one — computed, never hardcoded per pathway.
2. **Match reported items.** For each instantiated step, find `ReportedItem`s whose `code ∈
   step.satisfied_by`, in window. Apply `cadence` to decide whether an existing match still covers
   the current window.
3. **Assign status** purely from match + cadence:

   | condition | `status` | citation shape |
   |---|---|---|
   | satisfying match, in window | `DONE` | source × `Present(item)` |
   | no match, `now < due` | `DUE` | source × `Absence(step)` |
   | no match, `now > overdue` | `OVERDUE` | source × `Absence(step)` |
   | `requires_plan`, open, past window, no plan on file | `OPEN_NO_PLAN` | source × `Absence(step)` → **nudge** |

4. **Emit through the Gateway.** For each instantiated step call
   `Gateway.cite(source = step.authorizing_source_ref, state = matched_item ?? Absence(step), status)`.
   Every ledger row is therefore a `Citation`; there is no ledger row that is not provenanced and
   tiered.

Because gaps **fall out of the join**, adding a new pathway needs no new gap logic — the same engine
consumes any rail. This is what "computed by joining, not enumerated per example" means (criterion 3).

### 5.3 Provenance and confidence tier travel with every item

`authorizing_source_ref` (authoring) → instantiated-step source (materialization) →
`Citation.source_ref` + `Citation.confidence_tier` (emission). At no hop is the source detachable from
the item; an instantiated step whose `source_ref` does not resolve is rejected before it reaches the
join, so an uncited expectation can never reach the ledger. The Gateway copies `confidence_tier` from
the resolved source and stamps it as a **non-optional** field — a gap flag cannot exist without its
source and tier attached (criterion 4).

**Confidence tier — day-zero closed set, ordered (property of the source class):**

| Tier | Assigned to | Rationale |
|---|---|---|
| `clinician_directive` | `DOCTOR_INSTRUCTION`, `PRESCRIPTION` | Individualized, clinician-issued, for **this** subject — outranks a population rail. |
| `guideline` | `PUBLIC_GUIDELINE` | Authoritative but population-level, not individualized. |
| `self_reported` | a `ReportedItem` standing on no clinical source (self-entry) | On file, lowest verification. |
| `uncoded` | any item that could not be coded at ingest | Never auto-matches; surfaced lowest, flagged for a human. |

The tier is a property of *where the citation stands*: the **same** expected step cited from a doctor
instruction outranks it cited from a general schedule — surfaced on the flag, never buried. The ladder
is owned in one place (Sources module) and adjustable there alone.

---

## 6. Day-zero vocabulary — the public seams

The API/public seams may speak **only** these nouns and verbs. Anything not here is internal; the
closed vocabulary *is* the enforcement surface.

**Nouns:** `Party`, `Manager`, `Subject`, `Link` (`role`, `scope`), `Source` (`source_class`,
`provenance`, `confidence_tier`), `Pathway`, `ExpectedStep`, `ReportedItem` (`kind`, `code`,
`observed_at`, `reporter`), `Citation` (`source_ref`, `reported_ref`, `status`, `confidence_tier`,
`rendered`), `Ledger` (a subject's file = `List<Citation>`).

`Gap` and `Nudge` are **not** separate types — a Gap is a `Citation` with `status ∈ {DUE, OVERDUE}`;
a Nudge is a `Citation` with `status = OPEN_NO_PLAN`.

**Enums:**
- `role`: `self | guardian | clinician`
- `source_class`: `PUBLIC_GUIDELINE | DOCTOR_INSTRUCTION | PRESCRIPTION`
- `ReportedItem.kind`: `RESULT | DOCTOR_INSTRUCTION | PRESCRIPTION | EVENT`
- `status`: `DONE | DUE | OVERDUE | OPEN_NO_PLAN`
- `confidence_tier`: `clinician_directive | guideline | self_reported | uncoded`
- `ReportedState`: `Present | Absence`

**Verbs (seam operations):**
- `linkSubject(manager, subject, role, scope) -> Link` / `revokeLink(link_id)`
- `reportItem(link, item) -> ReportedItem` — the **only** state writer (may co-register a Source from
  a reported doctor instruction / prescription)
- `ingestSource(subject?, source) -> Source` — attach an authoritative source
- `publishPathway(Pathway) -> pathway_id` — declarative rail authoring
- `getTrackingFile(link, subject) -> Ledger` — read-only; returns only `Citation`s
- `listGaps(link, subject) -> List<Citation>` — filtered to gap/nudge statuses

**The seam may not speak:** `advice`, `recommendation`, `diagnosis`, `suggestion`, `assessment`, or
any free-text clinical field. No read verb returns anything but `Citation`/`Ledger`; no write verb
accepts system-authored content. That absence, expressed as a public contract, is the invariant.

---

## 7. Extensibility — one owner per change

| Change | Single owner | Touches |
|---|---|---|
| **Add a new pathway/rail** | Pathway Library | one new `Pathway` (predicate + steps + guideline source). Ledger engine, account model, Gateway, seam operate on canonical `ExpectedStep` — unchanged. |
| **Add a new source class** | Sources + Ingestion | one class + one adapter that normalizes to canonical `Source`/`ReportedItem` and registers a tier. The join works on `code`, the Gateway on references — neither is aware of `source_class`. |

Because Reconciliation and the Gateway see only canonical abstractions (`ExpectedStep`,
`ReportedItem`, `Source`), a new rail or source class does **not scatter** across the ledger, the
account model, and the output layer (criterion 5).

---

## 8. Explicitly out of the MVP

Building any of these should count **against** the design (criterion 6):

- **The integrated overview (*המכלול*)** — cross-process synthesis, whole-person dashboards or scores.
  Pillar 1 only.
- **Any inference / suspicion engine** — no deriving, suggesting, or scoring likely states. `Absence`
  is the only "negative," and it is set membership, not inference. There is no state-writer but human
  reports.
- **Advice generation of any kind** — no treatment suggestions, doses, triage, or result
  interpretation. The only counsel is *ask your doctor* (the `OPEN_NO_PLAN` citation), pointing to a
  human authority.
- **Unstated future source types** — wearables, EHR/lab feeds beyond the reported-result channel,
  imaging, insurer data. Each is a future adapter (§7), deliberately not pre-built.
- **Cross-subject analytics / cohort views** for a manager. Multi-subject *access* is supported;
  aggregate analytics is not.
- **Scheduling, booking, reminder/notification delivery.** A Nudge is a citation object; delivering
  it is out.
- **Auto-coding of uncoded sources** — NLP mapping, terminology servers, fuzzy clinical matching.
  Uncoded items surface at the lowest tier and never auto-match.
- **Identity/authn provider, consent-lifecycle UX, audit tooling** beyond the `Link` scoping and
  per-item provenance already modeled.

---

## 9. How each exit criterion is met (traceability)

| # | Requirement | Where enforced |
|---|---|---|
| 1 | Non-advice/non-inference by architecture, single egress | §3 — sealed `Citation`, single `Gateway.cite`, four-status closed grammar, reference-only inputs; single state-writer bans inference |
| 2 | `manager → subject(s)` single primitive | §4 — one `Link`; self/guardian/clinician differ only in cardinality + a metadata role; doctor unprivileged past the boundary |
| 3 | Expected vs reported distinct; gaps by join | §1.3–1.4, §5 — separate library and reported store; generic four-step join; gaps fall out of it |
| 4 | Provenance + tier travel with every item | §5.3 — tier stamped at ingest by source class, welded onto every citation by the Gateway; uncited item rejected before the ledger |
| 5 | New pathway / source = one owner's change | §7 — Pathway = data; source = one class + adapter; engine & Gateway generic over canonical types |
| 6 | Scoped to Pillar 1 + MVP sources | §8 — overview, inference, and unstated sources excluded by construction |
