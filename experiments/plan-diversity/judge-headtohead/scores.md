# Head-to-head scoring — "responsible doctor" MVP architecture

Blind evaluation of **design-P** vs **design-Q** against the frozen nine-metric rubric.
Every score rests on a concrete structural fact (a named type, section, or mechanism), never tone.

## Score matrix

| Metric | design-P | design-Q | Leads |
|---|---|---|---|
| M1 — Citation chokepoint enforced by structure | 5 | 5 | tie (P marginally deeper) |
| M2 — `manager → subject(s)` single primitive | 5 | 5 | tie |
| M3 — Expected vs Reported distinct, gaps JOIN-computed | 5 | 5 | tie |
| M4 — Provenance & confidence tier inseparable | 5 | 5 | tie |
| M5 — Add pathway/source = one owner's change | 5 | 5 | tie |
| M6 — Pathway library as generic rails | 5 | 4 | **P** |
| M7 — Scope discipline, no speculative machinery | 5 | 5 | tie |
| M8 — Day-zero seam vocabulary stated & clean | 5 | 5 | tie |
| M9 — Domain model carries behavior / enforces own rules | 5 | 4 | **P** |
| **Total** | **45** | **43** | **P** |

---

## Per-metric justifications

### M1 — Citation chokepoint (source × reported-state; no infer/originate path)
- **design-P — 5.** `sealed Citation` with a **module-private constructor** in module `citation` (§1.5), and `compute_ledger(exps, facts, today) → Ledger` is the *only* exported function returning `Citation` (§3 lock 2); `api`'s subject-medical handlers are typed `Scope → Ledger`, so no other return type can carry subject content. `Citation` has **no free-text field**; to "say" anything you must point at a `SourceRef` and a `StateRef`. The join input is `JoinFact`, a projection that **omits `note`, `document_id`, `recorded_by`** (§3 lock 3), so free text cannot even enter the join; `today` is a parameter and the module imports no clock/HTTP/ML (lock 4); `render` uses a **fixed template per `status`** whose only recommendation verb is the constant "Ask your doctor" (lock 6); `integrity()` re-resolves every ref fail-closed (lock 8). Ten CI-pinned locks.
- **design-Q — 5.** `Citation` is "constructed ONLY by `CitationGateway`" with a package-private constructor and **no `text`/`advice`/`recommendation`/`reason` field** (§1.6); every public seam read returns `[Citation]` (boundary rule 2, signature-scan enforced) and the delivery surface's only import is the gateway (§3.1 leg 1). Rendering is projection: `template_id` selects from a closed catalog whose slots bind only verbatim source labels and referenced-record codes (§3.1 leg 2). `ObservedFact` is a closed structured sum (no free-text channel), and a verb **denylist lint** (`recommend/advise/diagnose/infer/…`) fails the build over the seam surface (§3.1 leg 3). `LedgerEngine` imports no I/O/clock/randomness (boundary rule 4).
- **Verdict:** Tie. Both make advice/inference structurally unrepresentable through a single sealed egress that forces a source and a reported-state reference. P is marginally more exhaustive (JoinFact strips free text at the join's input type, plus fail-closed `integrity()` and a SELECT-only compute role); Q adds a build-time verb denylist P lacks. Net: both clear the "5" bar.

### M2 — `manager → subject(s)` single primitive
- **design-P — 5.** One relation `Grant(manager_id, subject_id, role)` plus an unforgeable `Scope` capability (§4). A scenario table maps self / parent-two-children / doctor-panel / child-with-parent-and-doctor / grown-child-takeover onto **the same edge at different cardinality**; there is explicitly "no `Patient`, `Family`, or `Panel` type." `role` governs write only and "never reaches the join."
- **design-Q — 5.** One relation `Grant(manager_id, subject_id, scope, relation)` is "the entire account model" (§4); self/family/panel/doctor-as-own-subject are the same rows at different cardinality; "multi-subject is never a branch." `relation` is an "open label that changes nothing in logic" and tier is never derived from it.
- **Verdict:** Tie. Both express family and panel as cardinality on one `Grant` edge with no doctor-mode type. P's `Scope` capability vs Q's ordered `scope` are different auth mechanisms (relevant to M9), not to the primitive's singularity.

### M3 — Expected vs Reported distinct, gaps JOIN-computed
- **design-P — 5.** Distinct models: `reported_item` append-only log (§1.2) vs `rails` declarative pathway files (§1.3). `compute_ledger` (§5.2) is shown in full as **two generic loops** — (A) expected-vs-done over `Expectation[]`, (B) open-process-with-no-plan — plus an echo loop; "gaps are never enumerated per pathway ... produced by the same two loops regardless of which pathways are loaded." Coverage property test `|done ∪ upcoming ∪ due ∪ overdue| == |exps|` (§5.4).
- **design-Q — 5.** Distinct modules: `PathwayLibrary` (rails = data) vs `ReportedStore` (subject state), "distinct by construction" (§5). `join : (Pathways, SubjectFacts, [ReportedState]) → [LedgerItem]` is pure/total, with a classify table (matched→DONE, unmatched-in-window→EXPECTED, past-window→GAP, open-no-plan→NUDGE). "Gaps are the output of the join, never enumerated per example."
- **Verdict:** Tie. Both keep the two sides in separate stores and derive gaps from a single generic join. P shows fuller join pseudocode and a coverage invariant; Q states the classify relation compactly. Equivalent structurally.

### M4 — Provenance & confidence tier inseparable from every item
- **design-P — 5.** `SourceRef` is a sealed sum and `tier: SourceRef → Tier` is a **total, exhaustive** match ("a new source variant fails to compile until its tier is defined", §1.4). The only output type `Citation` has fields `source`, `tier = tier(source)`, and the reported `attestation` — "there is no citation without a source; the type has no optional source field" (§5.3). Pathway schema **requires** `authority` and every item's `locator`, so provenance can't be missing. Tiers are "categorical, not blended."
- **design-Q — 5.** `ConfidenceTier` assigned "BY source class in one file, never by the engine" (§1.1); `RailStep.source_ref` is `NON-NULL`, `LedgerItem` is "invalid without a `source_ref` (type-level)", and `Citation.source_ref` is `NON-NULL` with `tier` "copied, never recomputed" (§1.6, §5.2). Check: `citation.tier == referencedSource.tier` for every item.
- **Verdict:** Tie. Both make a non-null source and a source-keyed tier a structural component of every emitted item. P enforces completeness via an exhaustive `tier()` that won't compile; Q via single-file assignment plus non-null FKs at three levels. Q surfaces the lower of two differing tiers (a min, not a blend); P separates tier from attestation. Both satisfy "enumerated, keyed to source class."

### M5 — Adding a pathway or source type is one owner's change
- **design-P — 5.** Locality table (§2): new pathway/guideline = "one new dir under `rails/library/` (+ goldens). **Zero code.**" (owner `rails`); new **source type** = one `sources` change (a `SourceRef` variant + its `tier()` row, which "won't compile until added," + a compiler function) (owner `sources`). "`citation`, `access`, and `api` appear in none of the first three rows."
- **design-Q — 5.** Two open registries (§2): new source type lands in **SourceRegistry + Ingestors only**; new pathway in **PathwayLibrary only**; core `LedgerEngine`/`CitationGateway` "almost never" change. Explicitly argues the split because a source-ingester and a library-author are "**different owners**" (exit-5 rationale).
- **Verdict:** Tie. Both localize each addition to one owner and keep join/gate/account untouched. Q's explicit two-registry split names the two distinct owners the brief implies; P keeps both source-facing concerns in one `sources` module but still one owner per change. Equivalent.

### M6 — Pathway library as generic rails, not one worked example
- **design-P — 5.** The pathway grammar names three condition-neutral `Schedule` forms — `at_age{from,to} | every{period,from_age} | after{trigger: MatchRule, within}` (§1.3) — and §5.1 shows each compiling to a concrete `Window` (the `after` form emits "one Expectation **per fact** matching `trigger`"). This demonstrably covers the three structurally different brief examples: well-baby (`at_age` immunisations), age/sex screening (`every`), and a **med-refill / follow-up cadence** (`after{trigger,within}`). Ships **two** pathway instances day-zero (well-baby + adult screening) through "the same loader, same evaluator, no pathway-specific code."
- **design-Q — 4.** `RailStep` is genuine data (`expects`, `gate: Predicate`, `cadence: Cadence`, §1.5) in a grammar of "age/sex ranges, prior-item recency, interval arithmetic," and §5.1 asserts well-baby and colon-screening are "the *same act*." But `cadence` stays abstract and the two named examples are both age/interval-shaped (the more similar two of the brief's three); the med-refill/follow-up cadence is modeled as a `Source` claim (`Directive`/`Dispense` with `DoseSchedule`, §1.3) rather than as a library rail schedule form. The abstraction is real but its generality across a *structurally* different third pathway type is asserted, not decomposed into rail primitives the way P's `after{trigger}` form is.
- **Verdict:** **P leads.** P exhibits three distinct schedule primitives that map one-to-one onto the brief's three example pathway shapes; Q's rail cadence is less decomposed and its follow-up cadence lives outside the pathway library.

### M7 — Scope discipline: no speculative machinery
- **design-P — 5.** §7 explicitly excludes Pillar 2/המכלול (no table/route/placeholder), all inference (suspicion/risk/abnormality/trend/credibility-blend), OCR/NLP, EHR/FHIR/HL7, terminology service, notifications, consent/identity flows, persisted ledger, adherence/interactions, and "any ML/LLM including for just wording." Footprint: two persisted stores, one file library, seven modules, two shipped pathways.
- **design-Q — 5.** §7 excludes Pillar 2 ("no aggregation entity by intent"), inference ("unbuildable, not merely disallowed" — the rail grammar is too weak and `Origin` has no `SYSTEM`), plugin runtime, rich RBAC/consent, EHR/FHIR/NLP, scheduling/notifications, persisted ledger, and free-text authoring. The seam is "a contract, not a plugin runtime" shipping a fixed day-zero trio.
- **Verdict:** Tie. Both name overview/inference/future-sources out of scope and tie every built component to a stated MVP requirement. (P carries an audit-only `ledger_snapshot` table that is a hair beyond need; Q keeps the ledger purely derived — a marginal leanness edge for Q that does not move the score.)

### M8 — Day-zero public-seam vocabulary stated and clean
- **design-P — 5.** §6 lists the full seam vocabulary living in `vocab`: `ItemKind`, reserved fact codes, `Process action`, `Origin.kind`, `Attestation`, `Role`, `SourceRef` kinds, `Tier`, `Citation status`, `StateRef` kinds, `Predicate` ops, `Schedule` forms, `MatchRule`, `Duration/Date/Code`, and the pathway file keys. HTTP seam returns domain types (`Manager`, `Subject`, `Grant`, `ItemId`, `Ledger`); "codes are opaque `system:code`," no DB row or vendor type leaks.
- **design-Q — 5.** §6 lists nouns (`Manager`…`Citation`, `Ledger`, `ConfidenceTier`, `Provenance`), the closed `Origin`/`Source.kind`/`ConfidenceTier`/`ReportedState.kind`/`Citation.relation`/`scope` sets, the template catalog, open vocabularies (`code`, `pathway_id`), public verbs (`grant`/`report`/`ingest`/`publish_pathway`/`view_ledger`), and a **permanently-absent verb denylist**. Only domain types cross seams.
- **Verdict:** Tie. Both give an explicit day-zero vocabulary section of domain types with no implementation/vendor type in a public signature. P is more exhaustive (grammar ops, file-format keys); Q's absent-verb list is a distinctive clean touch. Both at the "5" bar.

### M9 — Domain model carries behavior / enforces its own rules
- **design-P — 5.** Invariant-bearing types enforce themselves: `Citation` cannot be built invalid (sealed private constructor), `tier()` is owned by `SourceRef`, `compute_ledger` computes its own gaps, and the pathway evaluator answers "what is expected." Authorization is a **capability, not a habit**: every `reported` method and ledger read takes an unforgeable `Scope` (constructible only by `access.open`), so "a handler that forgets to authorize **fails to compile**" (§3 lock 10). `integrity()` self-validates every reference before render. Tell-don't-ask throughout.
- **design-Q — 4.** Strong type-level enforcement — `Origin` with **no `SYSTEM` member** makes system-authored state unrepresentable (§1.1), `ReportedStore.write` rejects `origin=SYSTEM`/null author (behavior on the store), `Citation`'s private constructor and non-null `source_ref` (§1.6), refuse-never-coerce in the gateway (§3.5). But authorization is an **ask**: `authorized(actor, subject, needed_scope) = ∃ Grant(...)` evaluated in one middleware (§4), a check a handler can omit, rather than an unforgeable capability the type system demands — a step less tell-don't-ask than P's `Scope`. Several other guarantees ride on fitness tests / lint rather than the types.
- **Verdict:** **P leads.** Both are non-anemic and push invariants into types (Q's `Origin`-without-`SYSTEM` is exemplary), but P encodes authorization as a compile-time capability while Q verifies it in a middleware function; on the tell-don't-ask axis the rubric names, P's types own more of their own enforcement.

---

## Overall reading

**Per-metric picture.** The two designs are level on seven of nine metrics, all at the ceiling, and P leads on two (M6, M9). Both are mature synthesized designs that satisfy every exit criterion structurally, not by convention.

**Load-bearing axes (M1, M3, M4, M5 — the non-negotiables).** On all four the designs are **level at 5/5**. Neither fails a non-negotiable:
- M1: both route all output through a single sealed, source×state-forcing constructor with no free-text field and no alternate emit path.
- M3: both keep expected and reported in separate stores and derive gaps from one generic pure join.
- M4: both make a non-null source and a source-keyed enumerated tier a structural component of the sole output type.
- M5: both localize a new pathway and a new source type to one owner each, leaving the core untouched.

**Where the difference turns.** Only on the two secondary axes:
- **M6 (pathway generality):** P exhibits three distinct schedule primitives (`at_age`/`every`/`after`) that map onto the brief's three example pathway shapes, including the med-refill/follow-up cadence as a first-class rail form; Q's rail `cadence` is less decomposed and its two named examples are both age/interval-shaped, with follow-up modeled outside the pathway library.
- **M9 (self-enforcing model):** P makes authorization an unforgeable `Scope` capability that fails to compile if omitted, where Q checks authorization in middleware; P's types own slightly more of their own enforcement.

**Verdict.** **design-P is the stronger design**, but narrowly and on secondary ground. On every load-bearing axis the two are indistinguishable — a tie on the requirements that, per the rubric, a design cannot afford to lose. P's edge is confined to M6 and M9: a more demonstrably generic pathway grammar and a more capability-based (rather than middleware-checked) enforcement of its invariants. Totals (45 vs 43) echo this but are a secondary glance; the honest reading is *level on what matters most, P ahead on two refinement axes*. Q's distinctive strengths — the `Origin`-without-`SYSTEM` unrepresentability and the seam verb denylist — are real and keep it a co-equal on the core boundary; they simply don't offset P's M6/M9 advantages.
