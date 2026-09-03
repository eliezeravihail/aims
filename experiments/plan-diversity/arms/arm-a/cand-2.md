# The Responsible Doctor — MVP Architecture

*A proactive care-coordinator that manages medical processes and never originates advice.
Every output is a **Citation**: an authoritative **Source** joined against a **Reported** medical
state. This design makes that invariant a structural property of the system, not a coding
convention.*

---

## 0. Design stance and assumptions

- **Kind:** an architecture/shape. No running code; types below are conceptual contracts, written
  in a language-neutral pseudo-notation.
- **Delivery surface:** a backend service with a thin read API. The surface is not load-bearing to
  the invariant, so it is left generic.
- **The one idea that organizes everything:** there is exactly **one manufacturer of outputs** in
  the system — the **Citation Gate**. It is the only code that can mint a value the outside world is
  allowed to see. Every other module produces *inputs to the gate*, never outputs. This is what turns
  "never originate advice" from a rule people must remember into a wall the type system enforces.
- **Assumption (stated inline):** "authoritative" is a property carried by a Source, not judged at
  runtime; the system trusts its ingested sources and never editorializes them. Ranking/triage of
  gaps is presentation, done downstream of the gate, and may never add or infer medical content.

---

## 1. Data model

The model has three families that stay physically and conceptually separate: **who** (accounts),
**what-should-happen** (expected rails), and **what-was-reported** (subject state). They meet only
inside the ledger, and only under the gate.

### 1.1 Core value types

```
# ---- Provenance & trust: these travel with everything ----

SourceKind      = enum { PUBLIC_GUIDELINE, DOCTOR_INSTRUCTION, PRESCRIPTION, REPORTED_RESULT }

ConfidenceTier  = enum { A_AUTHORITATIVE,   # public guideline / protocol (highest)
                         B_DIRECTED,        # a specific doctor instruction / prescription
                         C_SELF_REPORTED }  # subject-entered state, unverified
                  # Tier is a property OF THE SOURCE, assigned at ingest, immutable thereafter.

Source = {
  source_id
  kind            : SourceKind
  confidence_tier : ConfidenceTier      # fixed at ingest by the source's adapter
  issuer          : string              # "Ministry of Health well-baby schedule v3", "Dr. Cohen"
  reference       : string              # citable locator: guideline section, Rx id, doc id
  effective_at    : timestamp
}

# A Reported medical state — a FACT THE SUBJECT (or their record) ASSERTS.
# The system stores it; it never derives, upgrades, or infers one.
ReportedState = {
  state_id
  subject_id
  observation     : CodedObservation   # coded fact: "HbA1c = 6.9%", "MMR dose 1 given 2025-04"
  reported_at     : timestamp
  origin_source   : source_id           # who asserted it (a result upload, a doctor note, self-entry)
}
```

### 1.2 The Citation — the only shape the world may receive

```
# Citation is a SEALED type. Its constructor is private to the Citation Gate (§3).
# No other module in the system can build one. There is no text field the gate did
# not fill from a (Source, ReportedState) pair.
Citation = {
  citation_id
  source          : Source              # the authoritative "expected" side
  reported_state  : ReportedState?      # the "done"/observed side  (may be ABSENT -> a gap)
  relation        : CitationRelation    # SATISFIED_BY | OUTSTANDING | NO_PLAN
  confidence_tier : ConfidenceTier      # copied verbatim from source; inseparable
  rendered_at     : timestamp
}

CitationRelation = enum {
  SATISFIED_BY,   # expected item is met by a reported state (source × state, both present)
  OUTSTANDING,    # expected item exists, no matching reported state  (source × ABSENCE)
  NO_PLAN         # an open process with no governing rail -> becomes the ask-your-doctor nudge
}
```

Note what is **not** here: no `advice`, no `recommendation`, no free-text `message`, no
`inferred_state`. A Citation can express only three relations between a real Source and a real (or
absent) Reported state. That is the entire expressive range of the system's output.

### 1.3 Accounts (detailed in §4) and Pathways (detailed in §5) round out the model

```
Manager     = { manager_id, display_name }
Subject      = { subject_id, display_name, dob? }
Stewardship = { manager_id, subject_id, role, scope }   # the manager->subject edge

Pathway     = { pathway_id, title, governing_source_id, applicability, steps[] }  # a declarative rail
```

---

## 2. Module / boundary structure

Six modules. Data flows left-to-right; **outputs exist only at the far right, and only the gate can
mint them.**

```
        INGEST                    STATE                COMPUTE                 EMIT
  ┌───────────────┐        ┌────────────────┐   ┌──────────────────┐   ┌──────────────┐
  │ Source        │        │ Subject Record │   │  Ledger Engine   │   │ Citation Gate│
  │ Adapters      ├──────► │ (reported side)│──►│  (the JOIN)      ├──►│  (SOLE minter│──► read API
  │ (§6 seam)     │        └────────────────┘   │                  │   │  of Citation)│
  └───────────────┘        ┌────────────────┐   │  emits GATE-     │   └──────────────┘
  ┌───────────────┐        │ Pathway Library│──►│  REQUESTS only   │        ▲
  │ Account Model │ ······►│ (expected side)│   └──────────────────┘        │
  │ (manager→subj)│  scopes every read/write above                          │
  └───────────────┘                                                   (no other module
                                                                       reaches this arrow)
```

| Module | Owns | May NOT do |
|---|---|---|
| **Source Adapters** | Turning each external source class into `Source` + `ReportedState`/`Pathway` records; **stamping the confidence tier**. | Compute gaps; emit output. |
| **Account Model** | The `manager → subject(s)` primitive; scoping every query by stewardship. | Hold medical content. |
| **Subject Record** | The reported/done state for one subject. | Hold expected rails; infer new states. |
| **Pathway Library** | The declarative rails (expected side). | Know about any specific subject. |
| **Ledger Engine** | The **join**: match rails against reported states, detect gaps, produce `GateRequest`s. | Construct a `Citation`; write prose. |
| **Citation Gate** | The **sole** constructor of `Citation`. | Originate content — it can only *assemble* what it is handed. |

The critical boundary is the last arrow: **`Citation`'s constructor is package-private to the Gate.**
The Ledger Engine cannot new-up a Citation; it can only hand the Gate a `GateRequest` (§3). The
compiler/type-checker enforces this, so no future feature — including a doctor-facing one — can grow
a side path that emits advice.

---

## 3. Ownership of the citation invariant (the core requirement)

**Owner:** the **Citation Gate**, a single module with a single public function.

```
# The ONLY public entry point that yields anything renderable.
Gate.render(request: GateRequest, viewer: StewardshipContext) -> Citation

GateRequest = {                 # what the Ledger Engine is allowed to ask for
  source_ref     : source_id     # MUST resolve to a stored Source
  state_ref      : state_id?     # MUST resolve to a stored ReportedState, or be ABSENT
  relation       : CitationRelation
}
```

How the invariant is **structurally** enforced (not by convention):

1. **Sealed constructor.** `Citation` is constructible only inside the Gate's module. Every other
   module that wants an output must call `Gate.render`. There is no second door.

2. **The Gate cannot originate.** `render` takes only *references* (`source_id`, `state_id?`). It
   **looks them up** in the stores and copies their fields. It has **no text parameter, no template
   engine, no LLM call, no advice vocabulary.** If a reference does not resolve to a real stored
   record, the Gate raises — it cannot fabricate a Source or a State to fill a gap.

3. **State is never inferred.** The Gate accepts a `ReportedState` only by id, only if it already
   exists in the Subject Record. It has no path to synthesize one. "Never infers state" is therefore
   a property of *there being no code that can*, not a promise.

4. **Advice cannot be originated.** The three `CitationRelation` values are the whole output
   grammar. `NO_PLAN` is the strongest thing the system can say about an open process — and it
   resolves, in rendering, to *"there is a source-recognized open process and no governing rail:
   ask your doctor,"* which is a **pointer to the human authority, not a recommendation**. The Gate
   literally has no way to name a course of action.

5. **Provenance is welded on.** `render` copies `source.confidence_tier` into the Citation. A
   Citation without a resolvable Source cannot be built; a Source without a tier cannot be ingested
   (§6). So **tier + provenance are inseparable from every emitted item** by construction (exit
   criterion 4).

> One place, one type, one door. Delete the Gate and the system can emit nothing. That is the test
> of ownership.

---

## 4. The `manager → subject(s)` primitive

One abstraction, no special cases for family vs. clinic.

```
Stewardship = {
  manager_id
  subject_id
  role   : enum { SELF, FAMILY, CLINICAL }   # labels the relationship; does NOT branch logic
  scope  : enum { FULL, READ_ONLY }
}
```

- A manager managing **themselves** is `Stewardship(self, self, SELF)` — a one-subject case of the
  same edge, not a separate user type.
- A parent managing three children is **three `Stewardship` rows**. A doctor managing 400 patients
  is **400 `Stewardship` rows**. Identical shape; the only difference is cardinality and the `role`
  label (which is metadata, never a code branch).
- **Every read and write in the system is scoped by resolving a `StewardshipContext`** — the set of
  `subject_id`s a given manager may act on. The Ledger Engine and Gate operate **per subject**;
  multi-subject views are just an iteration over the manager's stewardship set. There is no
  "family module" and no "clinician module."
- **The doctor is not privileged past the boundary.** A `CLINICAL` manager still receives only
  Citations from the Gate. A doctor cannot make the system originate advice on a patient — a doctor's
  own instruction enters the system as a **Source** (`DOCTOR_INSTRUCTION`, tier B), which is then
  cited like any other. This is how the invariant holds "including a doctor user."

---

## 5. Expected vs. Done: the rails, the state, and the join

### 5.1 Expected side — a library of declarative rails

Pathways are **data, not code**. Adding a well-baby schedule or an age/risk screening plan is
authoring a `Pathway` record, not extending the engine.

```
Pathway = {
  pathway_id
  title
  governing_source_id        # the authoritative Source this rail cites (tier A typically)
  applicability : Predicate  # declarative: e.g. age-band, risk flag -> which subjects this rail governs
  steps : [ PathwayStep ]
}

PathwayStep = {
  step_id
  expects       : CodedObservation   # the coded fact that would SATISFY this step
  due_rule      : DueRule            # declarative timing: "by 6 months", "every 12 months", "once"
  citation_source_id                 # the Source that authorizes THIS step (defaults to governing)
}
```

The rail's power is that `expects` and `due_rule` are **declarative and coded** — the same shape for
every pathway. The engine reads them uniformly; it does not contain per-pathway logic.

### 5.2 Done side — subject state

The Subject Record holds the subject's `ReportedState`s (§1.1), each with its `origin_source` and,
transitively, its confidence tier. This is purely *what was reported* — results uploaded, doctor
instructions logged, prescriptions recorded. Nothing here is computed.

### 5.3 The join — one algorithm, produces the ledger

The **Ledger Engine** computes gaps by **joining rails against state**, per subject. It never
enumerates cases per example.

```
for each subject in viewer.stewardship_scope:
  applicable_rails = PathwayLibrary.filter(p -> p.applicability(subject))
  for each rail in applicable_rails:
    for each step in rail.steps:
      match = SubjectRecord.find(subject, satisfies=step.expects, within=step.due_rule)
      if match exists:
         request = GateRequest(step.citation_source_id, match.state_id, SATISFIED_BY)
      else:
         request = GateRequest(step.citation_source_id, ABSENT,        OUTSTANDING)
      ledger.append( Gate.render(request, viewer) )     # <- only the Gate mints the entry

  # open processes with no governing rail -> the nudge
  for each open_process in SubjectRecord.open_processes(subject):
    if no rail governs open_process:
       request = GateRequest(open_process.origin_source, ABSENT, NO_PLAN)
       ledger.append( Gate.render(request, viewer) )     # -> "ask your doctor"
```

The resulting **expected-vs-done ledger** is a list of Citations. Each carries its Source, its
confidence tier, and its relation. **Gaps are `OUTSTANDING` citations; the "no plan" nudge is a
`NO_PLAN` citation.** Because every entry left the Gate, **every entry is provenanced and tiered by
construction** — there is no ledger row that is not a Citation.

Key consequences (mapping to exit criteria):

- Expected and Done are **distinct stores**; gaps are the *result of a join*, never a hand-written
  list (criterion 3).
- A **new pathway** is a new `Pathway` record — **one author's change**, touching nothing in the
  account model, engine, gate, or output (criterion 5).

---

## 6. Day-zero vocabulary (the public seams)

The words the seams are allowed to speak on day one. Anything outside this vocabulary is out of scope
by definition, which is itself a guard on the invariant.

### 6.1 Ingest seam — `SourceAdapter` (one owner per source class)

```
SourceAdapter.ingest(raw) -> { Source, [ReportedState | Pathway] }
```
- Vocabulary: `PUBLIC_GUIDELINE`, `DOCTOR_INSTRUCTION`, `PRESCRIPTION`, `REPORTED_RESULT`.
- Each adapter **must** stamp a `ConfidenceTier` (`A_AUTHORITATIVE`, `B_DIRECTED`, `C_SELF_REPORTED`).
  Ingest without a tier is rejected — this is what makes tier inseparable downstream.
- Adding a **new source type** = adding one adapter that speaks this vocabulary. One owner's change
  (criterion 5). The ledger, accounts, and gate are untouched.

### 6.2 Account seam

```
Accounts.link(manager_id, subject_id, role, scope) -> Stewardship
Accounts.scope(manager_id) -> StewardshipContext
```
- Vocabulary: `manager`, `subject`, `stewardship`, `role {SELF, FAMILY, CLINICAL}`, `scope`.

### 6.3 Pathway authoring seam

```
Pathways.publish(Pathway) -> pathway_id
```
- Vocabulary: `pathway`, `step`, `expects (CodedObservation)`, `due_rule`, `applicability`,
  `governing_source`.

### 6.4 Read seam — the only place outputs appear

```
Ledger.view(manager_id, subject_id?) -> [ Citation ]
```
- Vocabulary: `citation`, `source`, `reported_state`, `relation {SATISFIED_BY, OUTSTANDING,
  NO_PLAN}`, `confidence_tier`.
- **This seam can return nothing but `Citation` values.** It has no `advice`, `recommendation`,
  `suggestion`, or `message` in its vocabulary at all. That absence is the invariant, expressed as a
  public contract.

---

## 7. Explicitly out of the MVP

Named so a reviewer can see the boundary was drawn on purpose:

- **The integrated overview (*המכלול*).** Only Pillar 1 (managing/steering processes) is in. No
  cross-process synthesis, dashboards of dashboards, or holistic health scoring.
- **Any inference of medical state.** No "suspected condition," no risk models, no deriving a state
  the subject did not report. The Gate structurally cannot do it, and no module upstream is built to.
- **Originating advice of any kind.** No treatment suggestions, no "you should…," no ranking that
  adds medical meaning. The only counsel the system gives is *ask your doctor* (the `NO_PLAN`
  citation), which points to a human authority.
- **Unstated future source types.** Wearables, EHR feeds, imaging, labs beyond the reported-result
  channel — each would be a future `SourceAdapter`, deliberately not built now.
- **Reminders / scheduling / messaging channels**, triage severity engines, and billing — adjacent
  product surfaces, none required to prove the shape.
- **Speculative multi-tenant clinical features** (care teams, cross-manager sharing) beyond the
  single `manager → subject(s)` edge.

---

## 8. How the design meets each exit criterion

| # | Requirement | Where it lives |
|---|---|---|
| 1 | Non-advice boundary enforced by architecture | §3 — sealed `Citation`, single `Gate.render`, three-value relation grammar, no text/inference path |
| 2 | `manager → subject(s)` a single primitive | §4 — one `Stewardship` edge; self/family/clinic differ only in cardinality + a metadata label |
| 3 | Expected vs. Done distinct; gaps by join | §5 — separate Pathway Library and Subject Record; one join algorithm, no per-example lists |
| 4 | Provenance + tier travel with every item | §1.2 + §3.5 + §6.1 — tier stamped at ingest, welded into every Citation by the Gate |
| 5 | New pathway / source = one owner's change | §5.1 (Pathway = data) and §6.1 (one adapter); neither touches account/ledger/gate |
| 6 | Scoped to Pillar 1 + MVP sources | §7 — overview, inference, and unstated sources explicitly excluded |
