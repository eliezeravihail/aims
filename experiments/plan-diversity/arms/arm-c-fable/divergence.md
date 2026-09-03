# Divergence map — where the three candidates split, and why the synthesis chose as it did

The three arms (minimal / extensible / verifiable) agree on far more than they disagree. The agreements
below are the robust core the synthesis kept without argument; the ten axes after are the real
architectural decision points, where the design biases genuinely pulled apart.

## What all three agree on (kept wholesale)

- **Citation is the single, sealed output type**, one owning module, private constructor, no free-text
  field; the non-advice boundary is enforced by *construction*, not convention.
- **`manager → subject(s)` is one join edge**; self, family, and a doctor's panel are cardinalities, not
  types. Subject has no login and no medical columns.
- **Pathways are declarative data files, version/revision-pinned, never DB rows or code.**
- **Reported state is append-only; corrections supersede, never edit** — so every state pointer is stable.
- **A doctor instruction is structurally the same shape as a rail item** — the one abstraction that lets
  the ledger treat guideline and clinician expectations identically.
- **Expectations/ledger/citations are derived, never stored as truth**, recomputed from
  `(rails, reports, today)` with `today`/`as_of` a parameter → replayable.
- **The compute path cannot infer**: closed grammar, only calendar arithmetic, predicates over reported
  facts only; "open process" is declared by a report, never detected.
- **Tier is a function of the source (not the login); tier + provenance travel with every item; no blended
  score.** Same out-of-MVP list (overview, inference, OCR, EHR/FHIR, notifications, terminology, LLM).

---

## The ten divergence axes

### 1. Granularity of the reported-item grammar
- **minimal:** 4 kinds (`attribute · done · instruction · prescription`) — specificity pushed into `code`.
- **extensible:** closed 6-kind grammar (`fact · result · event · instruction · prescription · process`).
- **verifiable:** ~10 typed `ItemKind`s (dob, sex, lab_result, vaccination, diagnosis, referral, …).

**Chosen: extensible's closed six, with verifiable's typed payloads.** minimal's four collapse too much
(`done` lumps a lab result with a visit, hiding the reported `flag` the nudge rule needs). verifiable's ten
are checkable but bake specific clinical concepts into the enum, so an `imaging_done` needs a `vocab`
change. The six-kind grammar is the sweet spot: it is *stable and source-type-agnostic* (the ledger never
learns source types) yet each kind carries a typed, schema-validated payload. It wins because it satisfies
criterion 5 (new clinical concept = new `code`, not a new kind) **and** criterion 3 (the join stays generic).

### 2. How an "open process" arises
- **minimal:** a `follow_up_required` bool on a `done` entry + `re` links.
- **extensible:** an explicit `process` report with `action: opens|closes|plansFor`.
- **verifiable:** a `vocab.opens_process` table over other kinds (`referral`→true, `lab_result`→true iff
  reported `flag==abnormal`, …).

**Chosen: extensible's explicit `process` report.** All three avoid *inference*, but verifiable's
`opens_process` table makes the vocabulary itself draw clinical linkages ("abnormal lab ⇒ open matter"),
and minimal's bool buries the process inside a `done` row. An explicit `process{opens}` item is the purest
form of "declared by a report, never detected": a human states the matter is open, and the no-plan nudge is
a clean join over two reports. verifiable's abnormal-flag idea survives only as a **UI prompt** to file a
process, never as a system judgment.

### 3. Is `Source` a materialized row?
- **minimal:** no — source = the pathway's citation block or the entry itself.
- **extensible:** yes — a first-class immutable `Source` table; personal sources *minted* from
  instruction/prescription reports and linked both ways.
- **verifiable:** no — `SourceRef` is a sum type; `tier()` is a total function over it.

**Chosen: verifiable's sealed `SourceRef` sum type, no table.** extensible's `Source` table forces a
**dual write** (the report *and* a minted source) and a second source of truth for the same clinician fact.
A sum type resolved to either a pinned pathway revision or the reported item by id is leaner, avoids the
dual write, and — the decisive point — makes `tier()` an **exhaustive match** the compiler completes,
turning criterion 4 ("citation inseparable from source") and criterion 5 ("new source type is one change")
into compile-time guarantees rather than runtime discipline.

### 4. Strength of the invariant enforcement mechanism
- **minimal:** private constructor + SELECT-only DB handle + one route (capability-absence).
- **extensible:** sealed type + module-boundary lint + one contract test.
- **verifiable:** sealed type + AST call-site test + `JoinFact` projection that strips note/document/who +
  `integrity()` fail-closed re-resolution + the INV-1..13 suite.

**Chosen: verifiable's stack, plus minimal's SELECT-only role as defense-in-depth.** This is verifiable's
home turf and the brief measures the invariant *structurally*, so the strongest checkable enforcement wins.
The `JoinFact` projection is strictly stronger than "SELECT-only": it blocks the join from even *reading*
free text, documents, or the reporter's identity, closing inference channels a read-only DB role leaves
open. minimal's SELECT-only role is kept underneath because it is cheap and real.

### 5. Does the account edge carry a role, and does role set tier?
- **minimal:** no role column; tier rises only with an attached document ("authority is the document, not
  the login").
- **extensible:** `role: self|guardian|clinician` **sets a `clinician-entered` attestation tier above
  document** — trusting login = clinician.
- **verifiable:** `role: owner|delegate`, affects **write perms only**, never reaches the join; attestation
  is `document|self_entered`.

**Chosen: verifiable's write-only role + minimal's document-not-login tier stance.** extensible's
clinician-entered tier requires trusting an unverified login — and extensible itself ships no identity
proofing, so that tier would be dishonest. Making a doctor's undocumented word outrank a documented
self-report also *reintroduces the special-casing the brief forbids*. Deriving attestation purely from
"document attached?" keeps "doctor is not special" structurally true and the tier honest.

### 6. The extensibility seam for new source types
- **minimal:** none — a new source is "just another pathway file" or an ad-hoc ingester.
- **extensible:** a full **Source Adapter** contract (`accepts/ingest(rawItem)/tierOf/snippet`) + registry.
- **verifiable:** a new `SourceRef` variant + `tier()` row (exhaustive match forces it) + a compiler fn.

**Chosen: verifiable's compiler-per-source.** extensible's adapter is the most infrastructure and it is
partly *speculative* (criterion 6 penalizes this): `accepts(rawItem)`/`ingest(rawItem)` anticipate raw-input
parsing the MVP explicitly does not do (no OCR; the manager transcribes). verifiable achieves the same
one-owner locality with far less machinery, and the exhaustive `tier()` *forces* completeness at compile
time. The robust *idea* behind extensible's adapter — "a closed report grammar so the ledger never learns
source types" — is kept (axis 1); only its runtime apparatus is dropped.

### 7. The ledger status / citation-kind enum
- **minimal:** `done|upcoming|due|overdue|no_plan` (5).
- **extensible:** adds `superseded` (6).
- **verifiable:** `Done|ExpectedOpen|AskDoctor|Recorded` (4) — collapses upcoming/due/overdue, adds a
  `Recorded` **echo** so every subject view is `Citation[]`.

**Chosen: a merged seven** (`done·upcoming·due·overdue·no_plan·recorded·superseded`). Keep the finer
upcoming/due/overdue (minimal/extensible) because they are meaningful pure clock outcomes and the window
travels in the citation anyway. Keep `superseded` (extensible/verifiable) — it is what append-only needs.
Adopt verifiable's **`recorded` echo**, the strongest single idea here: it means even the plain "my items"
list is `Citation[]`, so *no* route can carry subject content that skipped the gate — directly hardening
criterion 1. Templates key per status, so the finer enum costs nothing.

### 8. Codes and terminology
- **minimal:** a closed `codes.yaml` registry; every code must be listed.
- **extensible / verifiable:** opaque `system:code`, string equality, no terminology service.

**Chosen: opaque `system:code`.** minimal's central registry couples *every new code* to edits in one
shared file — mild but real friction against criterion 5. Opaque namespaced codes make "a new lab test is
just a new code" literally true; an optional labels file is display-only and never gates matching.

### 9. Golden fixtures per pathway
- **Only verifiable** ships `fixtures/*.facts.json` + `*.ledger.json` goldens, CI-blocking.

**Chosen: adopt it.** It is the mechanism that makes "a new pathway is one owner's change" *safe*: the
owner ships goldens, CI proves the addition changed nothing else. Cheap, and it turns criterion 5 from a
claim into a test.

### 10. The authorization primitive
- **minimal:** `assert_grant(...)` as the first line of every handler (runtime, habitual).
- **extensible:** "is there a Custody edge?" queried per call (runtime).
- **verifiable:** an unforgeable `Scope` capability, constructed only in `access`; every repo method takes
  `Scope`, so a handler that forgets authorization **fails to compile**.

**Chosen: verifiable's `Scope`.** Compile-time enforcement beats a runtime assert that a new endpoint can
forget. It makes criterion 2's enforcement checkable, matching how the invariant itself is enforced.

---

## The through-line

The synthesis is **verifiability-first in enforcement** (sealed type, `Scope`, `JoinFact` projection,
exhaustive `tier()`, `integrity()`, goldens, the INV suite) built on **extensibility-first bones** (the
closed six-kind grammar and the explicit `process` kind that keep the ledger source-type-agnostic), with
**minimal's honesty checks** kept where they cut speculation (no `Source` table, no adapter runtime, no
role-based tier, SELECT-only as defense-in-depth). Each pick is the option that made a brief exit-criterion
*structural* rather than *trusted* — which is exactly what the brief says it measures.
