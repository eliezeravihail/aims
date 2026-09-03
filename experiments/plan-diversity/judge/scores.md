# Blind scores — "responsible doctor" MVP architectures (design-1..4)

Rubric: `/tmp/aims/experiments/plan-diversity/judge/rubric.md` (frozen before reading any contestant).
Every cell below rests on a named type, section, quoted mechanism, or specific decision in that design.
Authorship is unknown and not speculated on.

## 1. Score matrix (0–5)

| Metric | design-1 | design-2 | design-3 | design-4 |
|---|:-:|:-:|:-:|:-:|
| M1 Citation invariant — one structural chokepoint | **5** | 3 | 4 | 4 |
| M2 `manager → subject(s)` single primitive | **5** | 3 | **5** | 4 |
| M3 Expected vs reported, generic join w/ matching semantics | **5** | 2 | 4 | 4 |
| M4 Provenance + tier inseparable | **5** | 3 | 4 | 4 |
| M5 Change locality (new pathway / new source type) | 4 | 3 | 4 | 4 |
| M6 Seam vocabulary and domain types | **5** | 3 | **5** | 4 |
| M7 Scope discipline | 4 | 4 | 3 | 4 |
| M8 Responsibility placement / domain behavior | **5** | 3 | 4 | 4 |
| *Secondary total (out of 40)* | *38* | *24* | *33* | *32* |

---

## 2. Per-metric justifications

### M1 — Citation invariant: one structural chokepoint

**design-1 — 5.** Module `cite` owns the sole constructor `cite.make(kind, source_id, locator_id, report_ids[])` (§3.2): "There is no parameter of type `string`." Three mechanical layers (§3.1): private constructor; a CI dependency test that fails if `egress` imports anything but `cite` or if a template slot binds to anything but `source_locator.excerpt`, `source.title`, `report.code`, `report.occurred_on`; and schema — `citation.source_id`/`locator_id` NOT NULL FKs, a trigger rejecting a citation with zero `citation_basis` rows, and "no text column" (§1.6). Every citation's reported half is a real `report` row (composite FK `(report_id, subject_id)`), including gaps (basis = the ATTRIBUTE reports that made the rail apply, §5.3 table) and the nudge (basis = the opening INSTRUCTION report, source = that instruction, §3.4). All outward surfaces (API, UI, digest) live in `egress`, which "may import `cite` only" and "nothing imports `egress`" (§2). Doctor input enters as a `report` of kind INSTRUCTION dual-registered as a source (§3.5) — a source to be cited, not an output path. This is the only design where both halves of every emitted citation are required, real records at the schema level.

**design-2 — 3.** The Mint is a sole constructor (`Mint.project(Finding) -> Citation`, §3.1) with a closed `relation` enum. Two structural holes: (a) `Citation.reported_ref : ReportedRef?` is nullable (§1.5), and §5.2 emits `Finding(DUE, source=E.source, reported=none)` while §3.2 states DUE "require[s] both a SourceRef and a ReportedRef" — either DUE citations are rejected or the requirement is not enforced; the design contradicts itself on the reported half. (b) A `REFERRAL` citation "resolves its source to the single fixed boundary constant `ASK_DOCTOR`" (§3.2) — the source half of one output kind is a system constant, not an authoritative `Source`, so that citation is not a `(source × reported-state)` join. Additionally `SourceType.class` includes `RESULT` (§1.2), so a citation's "authoritative" half can be a subject's result. Enforcement is language-visibility only; no schema or architecture test is named.

**design-3 — 4.** `CitationGateway` holds a package-private constructor (§2 boundary rule 1) and `Citation` has "no `text`, `advice`, `recommendation`, or `reason` field" (§1.6); rendering is a closed `template_id` catalog whose only slots are source text and referenced-record codes (§3.1.2); a denylist lint over the seam (§3.1.3); fitness tests enumerated (§2). The strongest non-inference lever of any design: `Origin` has no `SYSTEM` member and `ReportedStore.write` rejects `origin = SYSTEM` (§1.1, boundary rule 3). Deduction: `Citation.state_ref: StateId?` is optional ("present for DONE / GAP-with-partial-state", §1.6), so `EXPECTED` and plain `GAP` citations carry no reported-state reference at all — the emitted value is `(source × nothing)`, and the `EXPECTED_DUE` template's `{state.last}` slot has nothing to bind. Also §5.1 step 4 has the gateway compute an "effective" lower tier — a small judgment inside the chokepoint.

**design-4 — 4.** `Gateway.cite(request: GateRequest, viewer)` with `source_ref: SourceRef!` and `reported_ref: ReportedState!` where `ReportedState = Present(ReportedItem) | Absence(expected_step_ref)` is a closed union with "no String" (§1.5, §3.1); both must resolve to stored records or the call is rejected; tier copied not chosen; sealed module-private constructor; every API read returns `Citation`/`Ledger`; a single state writer (Ingestion Port, §3.2). Deductions: (a) `Absence(expected_step_ref)` is a pointer at an instantiated *expected* step, not a reported record, so gap/nudge citations are `(source × reference-to-the-source-side)` — required and typed, but not a reported state; (b) `Citation.rendered: TemplateFill` puts a prose-bearing field on the output type (design-1 has no text column at all); (c) no schema-level or architecture-test enforcement is named beyond constructor visibility.

**Leader: design-1.** It is the only design where the reported half is a required real record for every citation kind and where enforcement exists at type, build, and schema level. design-3 and design-4 both have single sealed gateways but each leaves the reported half optional or non-reported for gap items. design-2's nullable `reported_ref` and constant-as-source `REFERRAL` are the weakest.

### M2 — `manager → subject(s)` as a single primitive

**design-1 — 5.** One relation `mandate(manager_id, subject_id, basis, granted_at, revoked_at?)` (§1.1); `basis ∈ {SELF, FAMILY, CLINICAL}` "is an audit label only — no code path branches on it." `identity.has_mandate` is called in exactly two places, `reports` on write and `cite` on read (§4), so every medical read/write is scoped by the relation. Self is a self-edge; family and clinician are "three cardinalities of one table"; multiple mandate holders per subject "fall out for free as extra rows." `subject` is a record, not a login (covers a baby). The doctor-as-source concept is separate (`report` kind INSTRUCTION → `source`), so the relation carries no clinical trust.

**design-2 — 3.** One `ManagerLink(manager, subject, role, scope[])` (§4) with self = `(self, self)`. Deduction: `role` and `scope[]` "tune ... which SourceTypes the manager may ingest (e.g. only a `CLINICIAN` link may attach a `DOCTOR_INSTRUCTION` source)" (§4). Because every `ReportedItem` "must carry a `source_id`" (§1.4), a family manager cannot record a doctor instruction with its proper source class — the role becomes a behavioral switch, and the brief's reported item "doctor instructions" is blocked for non-clinician managers. The relation thus carries clinical-content gating, not just access.

**design-3 — 5.** One `Grant(manager_id, subject_id, scope, relation)` (§1.2, §4); `scope ∈ {READ < REPORT < MANAGE}` is closed ordered data; `relation` is "an open label that changes nothing in logic"; "Tier is never derived from `relation`." One middleware `authorized(actor, subject, needed_scope) = ∃ Grant(...)` gates every read/write (§4). Self = actor and subject coincide; doctor-as-own-subject is a Grant like any other. Doctor instruction enters as a `DOCTOR_INSTRUCTION` Source via an ingestor (§3.4), not via the grant.

**design-4 — 4.** One `Link{manager_id, subject_id, role, scope}` with `role` "metadata; never a code branch" and `scope: ScopeSet` doing the gating (§1.1, §4); self/guardian/clinician are cardinality on the one edge; `reporter: Link-ref` on every reported item. Deductions: a second discriminator `Party.kind: person | provider` sits beside the Link (§1.1); and `role` "tunes default scope (... a clinician may additionally attach `DOCTOR_INSTRUCTION` sources)" while `reportItem` also "may co-register a Source from a reported doctor instruction" — two entry routes for the same source class, one role-gated and one not.

**Leaders: design-1 and design-3.** Both make the relation label inert and put the access check in one stated place. design-4 is close but adds `Party.kind` and a role-tuned route. design-2's role gates which source classes can exist, which breaks the brief's reported-instruction case for family managers.

### M3 — Expected vs reported: distinct sides, generic join with matching semantics

**design-1 — 5.** Expected = `rail` documents in `pathways` (§1.4) with a **closed** predicate/matcher grammar (`attr`, `reported`/`not_reported`, `report_kind`/`code`/`refers_to_report_id`, `eq/gte/lt`, ISO-8601 durations); reported = `report` rows in `reports` (§1.3). The join (§5.2) is written out: `hits = Facts ∩ step.satisfied_by ∩ within(occ.window)`, occurrences from `anchor + due + repeat`, four outcomes `DONE/EXPECTED/NO_PLAN/OVERDUE`, "no branch on subject, rail, publisher, or example." The join key is the closed item-code vocabulary owned by `reports` (§6). The no-plan case is a join outcome: an INSTRUCTION with `opens_process = true` compiles to a one-step rail satisfied only by a later report whose `refers_to_report_id` points back (§1.4, §5.4). Uniquely, subject-specific sources (instructions/prescriptions) are mechanically brought onto the expected side by the "instruction-rail compiler" (§1.4).

**design-2 — 2.** Sides are distinct (`Pathway`/`RailStep` vs `ReportedItem`, §1.3–1.4) and a join is sketched (§5.2). But the matching semantics are absent: `satisfied_by` is "the match rule joining `expects` to a real `ReportedItem` (§5)", and §5 only says `matches = ReportedItems where satisfied_by(E.step, item)`; `expects` is "a `ReportedItem.kind`" — a five-member enum (`RESULT`, ...) that cannot distinguish a colonoscopy from an HbA1c; no code vocabulary exists anywhere. The join's `else: (not yet due — no finding)` branch emits nothing once a due window has closed, so an overdue step vanishes (there is no OVERDUE outcome). Open-process coverage is a separate check in §5.3 keyed on `open_process_key`, not a join outcome. Instruction/prescription sources have no rail (`Pathway.backing_source_type_id` is GUIDELINE-backed only), so a doctor's "repeat in 3 months" never becomes expected.

**design-3 — 4.** Expected lives in `PathwayLibrary` (`RailStep{expects: ActionCode|ProcessCode, gate: Predicate, cadence, plan_required, source_ref}`), reported in `ReportedStore` (`ObservedFact` variants incl. `ProcessOpen` and `PlanMarker`, §1.4–1.5). Join key stated: "`ObservedFact.code = step.expects` within `cadence`", codes being "the join key shared by `RailStep.expects` and `ObservedFact.code`" (§6). Classification table has four outcomes including `NUDGE_ASK_DOCTOR` for `plan_required`/`ProcessOpen` with no `PlanMarker` (§5.1) — the nudge is a join outcome over reported facts. Deduction: the join signature is `join : (Pathways, SubjectFacts, [ReportedState])` — `Source` is not an input, so the `Directive{code, issued_for, window}` and `Dispense` claims defined in §1.3 never reach the expected side; no mechanism turns a doctor instruction into a rail step.

**design-4 — 4.** `ExpectedStep{applicability, cadence, window, satisfied_by: [match_key], requires_plan, authorizing_source_ref}` vs `ReportedItem{code, code_space, ...}` (§1.3–1.4); a stated matching rule, "code equality within a time window — a lookup, never clinical reasoning" (§0); a four-step join with a status table and typed `Absence(step)` (§5.2). Deductions: the `OPEN_NO_PLAN` condition "`requires_plan`, open, past window, no plan on file" uses two predicates the model never defines — nothing marks a step "open" (no `opens_process`/`ProcessOpen` fact) and no reported kind is designated as a "plan"; and the instruction→expected link is asserted ("simultaneously a recorded fact and an authorized expected step", §1.4) but join step 1 selects `ExpectedStep` only from the library, so no mechanism instantiates a subject-specific step from an instruction.

**Leader: design-1.** Only design-1 states a closed grammar, a closed join key, all four outcomes, and a mechanism that puts instructions on the expected side. design-3 and design-4 have a real join key but leave the subject-specific expected side unwired (design-4 also leaves "open"/"plan" undefined). design-2 has no join key at all.

### M4 — Provenance and confidence tier inseparable from every item

**design-1 — 5.** Tier is "a property of the source, assigned by `sources` at registration, never computed downstream and never passed by a caller" via one policy table (§1.2); `cite.make` "copies `tier` from the source — the caller cannot pass a tier" (§3.2); `citation.source_id`, `locator_id`, `tier` are NOT NULL on the row (§1.6). The A/B/C ladder distinguishes a document-backed directive (A) from a relayed one (C) by `document_ref` presence, so the tier reflects evidence. Provenance is section-level (`source_locator.locator` + verbatim `excerpt`). The nudge cites the opening instruction's own source and locator (§5.3 table), so it carries provenance and tier like any other kind. `rail.source_id` is required ("A rail with no source cannot exist", §1.4).

**design-2 — 3.** Tier lives on `SourceType.confidence_tier` "so the tier is a property of provenance" (§1.2) and `ExpectedItem` is "born already carrying its `Source` and `confidence_tier`" (§5.1) — good mechanism. Deductions: the `REFERRAL` citation's source is the constant `ASK_DOCTOR` (§3.2), which has no `SourceType` and hence no tier — the nudge item is the one item without real provenance or tier; and `RESULT` is a `SourceType` at T3 (§1.2), so a result (a reported fact per the brief) can stand as the provenance half.

**design-3 — 4.** Tier "lives only on `Source`, is assigned only by `SourceRegistry` by source class, and is copied, never recomputed" (§5.2); `RailStep.source_ref` NON-NULL (§1.5); `LedgerItem` "invalid without a `source_ref` (type-level)" and `Citation.source_ref` NON-NULL (§1.6); a stated check `citation.tier == referencedSource.tier`. Deductions: §5.1 step 4 has the gateway "surface the lower tier as effective confidence" when sources differ — a tier computation outside the registry, contradicting "never recomputed"; and `ConfidenceTier` includes `T4_SELF_REPORT` while `Source.kind` has no self-report member and `ReportedState` carries no tier — a tier no source can produce.

**design-4 — 4.** `confidence_tier` "is derived only from `source_class`, at ingest, immutable thereafter" (§1.2); `authorizing_source_ref` bound to each step at authoring, an unresolvable ref "rejected before it reaches the join", and the Gateway stamps tier as "a non-optional field" (§5.3). Deductions: the ladder (§5.3) includes `self_reported` ("a `ReportedItem` standing on no clinical source") and `uncoded`, but `Citation.confidence_tier` is "copied from `source_ref`" which "MUST resolve to an ingested Source" and no `source_class` maps to those tiers — two of four tiers are unproducible by the stated rule; and a guardian-relayed instruction co-registers a `DOCTOR_INSTRUCTION` Source (§1.4) receiving `clinician_directive`, so the tier does not distinguish evidenced from relayed provenance.

**Leader: design-1.** Its tier ladder is both source-owned and evidence-sensitive, and the nudge carries real provenance. design-3 and design-4 have source-owned tiers but each declares a tier member no source can produce. design-2's nudge has no provenance.

### M5 — Change locality: new pathway / new source type

**design-1 — 4.** §7 is an explicit table of touched vs untouched modules for five changes. New pathway = "one rail document + one guideline registration in `sources`"; ledger, identity, cite, egress, reports untouched. New source type = "one `sources.kind` enum value + one tier rule (+ a compiler entry in `pathways` if it carries steps)". Deduction: item codes are a closed list owned by `reports` (§6), so a new pathway needing a new screening code touches `reports` as well as `pathways` and `sources` (three registries), and a step-bearing source type touches `pathways` as well as `sources`.

**design-2 — 3.** Pathway = "inserting rows" in the library, source type = "one registry change" in `SourceType` (§1.2–1.3); the join "does not change" (§5.2). Deductions: locality is asserted, not walked (§8 is a one-line pointer table); `ManagerLink.scope[]` "tune[s] ... which SourceTypes the manager may ingest" (§4), so a new source type also touches account scope; and because no matching vocabulary exists (M3), a new pathway's `satisfied_by` cannot be verified to work without touching engine code.

**design-3 — 4.** Two named open registries with a per-module "Changes when…" column (§2): new source type → "SourceRegistry + Ingestors — here only"; new pathway → "PathwayLibrary — here only"; codes are an open namespaced vocabulary so a new pathway needs "no schema change" (§6); `Ingestor.parse(raw) → (ReportedState[], Source)` is the stated seam contract. Deduction: a new source type also touches the shared `Origin` enum in the provenance spine (§1.1) and possibly `SourceClaim` variants (§1.3), and the walk-through is by table rather than by tracing a concrete change through the untouched modules.

**design-4 — 4.** §7 walks both changes: new pathway = "one new `Pathway` (predicate + steps + guideline source)"; new source class = "one class + one adapter that normalizes to canonical `Source`/`ReportedItem` and registers a tier"; "the join works on `code`, the Gateway on references — neither is aware of `source_class`." Deduction: the day-zero code space's owner is not named (§0 only says "a small day-zero code space"), and a new class that needs a new `ReportedItem.kind` or `confidence_tier` member touches those closed enums, which the design does not address.

**Leaders: design-1, design-3, design-4 (tie).** All three isolate the join, account model, and egress from both changes; each has one extra registry a change may touch. design-2 asserts locality but its account-level source gating and missing join key make it unverifiable.

### M6 — Seam vocabulary and domain types

**design-1 — 5.** §6 lists a closed enumeration per owning module: identity, source (`kind`, `tier ∈ {A,B,C}`, `locator`, `excerpt`, `version`), report (`kind`, `asserted_by`, `opens_process`, `refers_to_report_id`), a namespaced closed item-code list, the full rail grammar atoms and comparators, ledger status, citation shape, and the four HTTP endpoints with `Citation[]` as the only medical response shape. A denylist of words "absent from every seam, type, and template" is bound to the architecture test. The predicate/matcher grammar is fully closed (§1.4). Deduction noted but not scored down: ids are bare `id` columns rather than typed id types.

**design-2 — 3.** A nouns/verbs table (§6) with typed refs on `Citation` (`SourceRef`, `ReportedRef`, `SubjectRef`) and closed `Relation`/`ConfidenceTier` enums. Deductions: the seam carries untyped `Source.payload`, `ReportedItem.value`, `ManagerLink.scope[]`, and `RailStep.satisfied_by` with no grammar; there is no code vocabulary at all — the join key (the most load-bearing seam value) is undefined.

**design-3 — 5.** Typed ids and refs throughout (`SubjectId`, `SourceId`, `StateId`, `ActorId`, `DocumentId`, `TemplateId`, §1); closed enumerations for `Origin`, `Source.kind`, `ConfidenceTier`, `ReportedState.kind`, `Citation.relation`, `Grant.scope`, and the template catalog (§6); open vocabularies (`ActionCode`/`ProcessCode`/`MedicationCode`) explicitly typed and named as the join key; seam verbs with signatures; a denylist lint. Deduction noted: codes are "namespaced strings" (open), so the join key has a type name but no registry.

**design-4 — 4.** `SourceRef`, `Link-ref`, `ScopeSet`, the closed union `ReportedState = Present | Absence`, and enumerated enums (§6); verbs with signatures (`reportItem(link, item) -> ReportedItem`, `getTrackingFile(link, subject) -> Ledger`). Deductions: `Predicate`, `Cadence`, `Window` are named but their grammar is not stated (cadence atoms only); `Source.payload` and `ReportedItem.value?` are untyped; the code space is "LOINC-like" by assumption without an owner or list.

**Leaders: design-1 and design-3.** design-1 has the most complete closed enumerations and grammar tied to concrete endpoints; design-3 has the most complete typed-id/ref vocabulary. design-4 names types but leaves grammars open; design-2 leaves the join key undefined.

### M7 — Scope discipline against the frozen brief

**design-1 — 4.** §8 excludes overview, inference, document understanding, integrations, clinician tooling, scheduling, conflict resolution, authoring UI, billing, multi-tenancy. Speculative residue: an "optional external-code slot left empty at day zero" on every item code (§6) and a `superseded_by` audit pointer on citations (§5.5) — reserved-for-later structure; a daily digest is defensible as the brief's "proactive" surface.

**design-2 — 4.** §7 excludes overview, inference, integrations, notifications, analytics, and "new source classes ... not needed by the MVP." Speculative residue: `RESULT` as a `SourceType` class (the brief lists results as reported items, not sources) and the `SourceType` registry with an `owner` field — a generic runtime registry rather than the two mandated seams.

**design-3 — 3.** §7 excludes overview, inference, plugin runtime, RBAC ceremony, integrations, notifications. Speculative residue exceeds the others: `Origin.RESULT_INGEST` and "ingest connector" as an author (§1.1) model a result feed the brief does not state (results are subject-reported); `Dispense{schedule: DoseSchedule}`, `MedTaken`, and `MEDICATION_STATUS` (§1.3–1.4) model medication adherence, beyond "prescription as a reported item"; `T4_SELF_REPORT`/`SELF_ATTESTATION` exist with no source that produces them; and the open code vocabulary is explicitly built so it "maps to a standard terminology later."

**design-4 — 4.** §8 excludes overview, inference, advice, future source types, analytics, scheduling, auto-coding, identity provider. Speculative residue: `Party.kind: person | provider` introduces a provider entity the brief does not ask for; the `uncoded` tier plus `code_space` and "LOINC-like" codes pre-commit to an external terminology shape; `listGaps` is a second read verb over the same `Citation` list.

**Leaders: design-1, design-2, design-4 (tie).** Each carries one or two reserved-for-later structures. design-3 carries adherence modelling and a result-ingest origin that the brief does not call for.

### M8 — Responsibility placement and domain-model behavior

**design-1 — 5.** The §2 module table states what each module "Owns" with one reason to change: `sources` owns the `kind → tier` policy; `pathways` owns rail documents, the closed grammar, `applicable_rails(subject_facts)` and the instruction-rail compiler (the pathway side decides applicability); `reports` owns the fact table and the code list; `ledger` owns only the pure join; `cite` owns the constructor and the citation tables; `identity` owns `has_mandate`; `egress` renders. Write authority is exclusive per module ("no module except `sources` may write a `Source`; no module except `reports` may write a `ReportedItem`; `ledger` writes neither"). The dual object (instruction = report + source) is handled by one stated same-transaction hook rather than by two modules each knowing the other's schema.

**design-2 — 3.** Modules are split by concept (§2), but behavior concentrates in the Ledger engine and Mint: the engine evaluates `applies_when` (§5.1) and separately runs the open-process coverage check (§5.3); the Mint owns the relation enum *and* the rendering constant table (§2); the Account module knows source classes ("which SourceTypes the manager may ingest", §4) — a cross-concept coupling. Entities (`Person`, `Source`, `RailStep`, `ReportedItem`) are field tables with no stated behavior of their own.

**design-3 — 4.** A per-module "Changes when…" column (§2) gives each module one reason to change; `PathwayLibrary` owns "evaluating rails"; `SourceRegistry` alone sets tier (boundary rule 5); `ReportedStore` enforces its own `origin ≠ SYSTEM` rule; `LedgerEngine` is pure with "no I/O, clock, or randomness" (rule 4). Deductions: the gateway computes an "effective" lower tier (§5.1 step 4) — tier logic outside the registry; and `RailStep.on_open_no_plan: NUDGE_ASK_DOCTOR` is a per-step field whose only allowed value is a constant — dead data on every step.

**design-4 — 4.** An "Owns / May NOT do" table (§2) gives each module a stated responsibility and prohibition (e.g. Sources "may not know any subject's expected/done status"; Pathway Library "may not know any specific subject"). Deduction: tier stamping has two owners — the Ingestion Port "stamps provenance + tier" (§2 diagram) while Sources "owns ... confidence-tier mapping" (§2 table) and §5.3 says the ladder is "owned in one place (Sources module)"; and the Gateway both constructs citations and owns rendering templates.

**Leader: design-1.** Its ownership table is the most explicit, and write authority is exclusive per module. design-3 and design-4 each have one misplaced piece of logic (gateway tier arithmetic; two tier-stamp owners). design-2 concentrates behavior in the engine and Mint over anemic tables.

---

## 3. Per-metric leaders (summary)

| Metric | Leader(s) | Why (one line) |
|---|---|---|
| M1 | design-1 | Only design with both citation halves required as real records at type + build + schema level. |
| M2 | design-1, design-3 | Inert relation label; one stated access check; doctor-as-source kept separate. |
| M3 | design-1 | Closed grammar, closed join key, four outcomes, instruction-rail compiler; others leave the subject-specific expected side unwired. |
| M4 | design-1 | Source-owned, evidence-sensitive tier; nudge carries real provenance; NOT NULL on the row. |
| M5 | design-1, design-3, design-4 | All isolate join/account/egress; each has one extra registry touched. |
| M6 | design-1, design-3 | Closed enumerations + grammar tied to endpoints (1); typed ids/refs throughout (3). |
| M7 | design-1, design-2, design-4 | design-3 carries adherence modelling and a result-ingest origin beyond the brief. |
| M8 | design-1 | Explicit per-module ownership with exclusive write authority. |

---

## 4. Overall reading

The per-metric picture is primary. The three load-bearing axes are M1, M3, and M5 (exit criteria 1, 3, 5).

- **design-1** leads or ties on every metric and leads outright on the three load-bearing ones. Its structural advantage is consistent: every guarantee it claims is carried by a named type, an enum, a NOT NULL/FK/trigger, or a build test, and it is the only design that mechanically brings doctor instructions/prescriptions onto the expected side (the instruction-rail compiler) rather than asserting it. Its two soft spots are M5 (a new pathway can touch three registries: rail, source registration, item-code list) and M7 (an external-code slot and audit pointer reserved for later).
- **design-3** is the clear second. It ties for the lead on M2 and M6 (typed vocabulary, inert grant label, `Origin` with no `SYSTEM` member is the strongest non-inference lever in the field). It loses ground where types are declared but not wired: an optional `state_ref` on gap citations (M1), `Source` absent from the join's inputs so `Directive`/`Dispense` claims never become expectations (M3), a tier (`T4_SELF_REPORT`) no source can produce (M4), and scope residue — adherence modelling and a result-ingest origin (M7, its lowest score).
- **design-4** is a consistent 4 across the board — no axis is weak, none leads. The typed `Absence` union is a good move for M1, but "open" and "plan on file" are never defined (M3), two tiers are unproducible by its own copy rule (M4), and tier stamping has two owners (M8).
- **design-2** trails on every metric. The decisive structural facts: a nullable `reported_ref` with a self-contradiction on DUE (M1), a nudge whose source half is a system constant (M1, M4), no join key at all and an overdue step that disappears once its window closes (M3), and role-gated source classes that block a family manager from recording a doctor instruction (M2).

**Secondary total** (design-1 38, design-3 33, design-4 32, design-2 24) agrees with the per-metric picture; no contestant wins a total while losing a load-bearing axis. The one caution: design-3's total is close to design-4's, but design-3's lowest score (M7, scope) is on a non-load-bearing axis, while its load-bearing scores (M1 4, M3 4, M5 4) match design-4's — so the ordering 1 > 3 ≥ 4 > 2 holds on the load-bearing axes as well as on the total.
