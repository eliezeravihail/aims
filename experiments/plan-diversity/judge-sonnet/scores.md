# Scores — "Responsible Doctor" MVP architecture judging

Rubric: `/tmp/aims/experiments/plan-diversity/judge-sonnet/rubric.md` (frozen before reading contestants).
Contestants are anonymized; no claim is made about how each was produced.

## Matrix (0–5 per cell)

| Metric | design-1 | design-2 | design-3 | design-4 |
|---|---|---|---|---|
| M1 Citation-chokepoint enforcement | 5 | 4 | 5 | 4 |
| M2 `manager→subject(s)` unforked primitive | 5 | 5 | 5 | 5 |
| M3 Expected/reported separation + generic join | 5 | 4 | 5 | 5 |
| M4 Provenance/confidence structurally inseparable | 5 | 4 | 5 | 5 |
| M5 Extensibility — one owner's change | 4 | 5 | 5 | 5 |
| M6 Scope discipline (no speculative build) | 5 | 5 | 5 | 5 |
| M7 Domain model carries real behavior | 4 | 3 | 4 | 4 |
| M8 Day-zero vocabulary clarity | 5 | 4 | 5 | 4 |
| **Total (/40)** | **38** | **34** | **39** | **37** |

---

## M1 — Citation-chokepoint enforcement

**design-1 (5).** `cite` module: `Citation` has a **private constructor** exported only within `cite`; a **CI dependency test** (ArchUnit/dependency-cruiser) fails the build if `egress` imports anything but `cite`; the `citation` table has NOT NULL `source_id`/`locator_id`, **no text column**, and a **DB trigger** rejecting a commit with zero `citation_basis` rows (§3.1). Three independent mechanical layers (type visibility + CI test + schema/trigger) are named.

**design-2 (4).** `Mint.project(Finding) -> Citation` is stated as the **sole constructor** (§3, point 1: "Citation has no public constructor"), with a closed `relation` enum with no `RECOMMEND` member and a fixed constant table for system-authored connective text. This is real enforcement, but only one mechanical layer is named (constructor visibility + runtime refusal-to-originate checks) — no CI/architecture test or DB-level constraint is described the way design-1 and design-3 name explicitly.

**design-3 (5).** `CitationGateway`'s constructor is "package-private... no other module references it," backed by **five explicit enumerated "boundary rules (each an enforceable fitness test)"** (§2): sealed constructor, a signature scan on every public seam's return type, `ReportedStore.write` rejecting `origin=SYSTEM`, a purity constraint on `LedgerEngine` (no I/O/clock/randomness), and single-writer of `tier`. Additionally, `Origin` is an enum **with no `SYSTEM` member at all** (§1.1) — a type-level guarantee independent of gateway discipline. §3.1 also names a **denylist lint over the seam surface** that fails the build on a banned verb.

**design-4 (4).** `Gateway.cite(request, viewer)` is the sole public entry point with a "sealed, module-private constructor" and explicit `require` pseudocode (source must resolve, state must resolve or be a typed `Absence`) (§3.1). A second independent leg is named — "one writer of state," the Ingestion Port (§3.2). Two real mechanisms, but neither a CI/architecture test nor a schema-level trigger is described to back them mechanically, unlike design-1/design-3.

**Leader: design-1 and design-3** (tied) — both name three-plus independent, differently-typed enforcement mechanisms (constructor + automated build-time check + schema/enum-level guarantee), not just constructor discipline.

---

## M2 — `manager → subject(s)` unforked primitive

**design-1 (5).** `mandate(manager_id, subject_id, basis, ...)`; `basis ∈ {SELF, FAMILY, CLINICAL}` is explicitly "an audit label only — **no code path branches on it**" (§1.1). §4: "These are three **cardinalities of one table**. No screen, query, or rule enumerates them." No role gates which report kinds a manager may write — the purest zero-branch claim of the four.

**design-2 (5).** `ManagerLink(manager, subject, role, scope)`; explicitly "There is no separate 'family account' or 'doctor account' type" (§1.1). `role`/`scope` "tune permissions... they do **not** create a second entity or a second code path" (§4) — though `role` does gate which `SourceType` a link may ingest (a permission branch on the same table, not a separate entity).

**design-3 (5).** `Grant(manager_id, subject_id, scope, relation)`; `relation` is "an **open label that changes nothing in logic**" (§1.2). §4 makes an explicit falsifiable claim: "the family and clinic scenarios exercise the same `AccountService` methods and the same `Grant` table — the code-path diff is empty."

**design-4 (5).** `Link{role, scope}` with `role ∈ {self, guardian, clinician}` tuning only default `scope`; "does **not** open a second data path and does **not** change what the Gateway emits" (§4). Same permission-gating pattern as design-2 (clinician role required to attach `DOCTOR_INSTRUCTION` sources).

**Leader: tie, all four.** Each names one relation table used identically for self/family/clinician with cardinality, not type, as the only difference. design-1's is the strictest (literally zero role-based branching anywhere in the write path); design-2/3/4 gate only *which source class* a role may attach, still on the same table — a permission nuance, not a special-cased abstraction, so all four satisfy the criterion equally.

---

## M3 — Expected/reported separation + generic join

**design-1 (5).** `Rails(subject)` (from `pathways`) and `Facts(subject)` (from `reports`) are stated as never sharing a store (§5.1). The join (§5.2) is literal pseudocode with the explicit claim: "The function has **no branch on subject, rail, publisher, or example**." The matcher grammar is stated **closed** (no arithmetic over result values, no free-form expressions) (§1.4), which is what makes "computed, not inferred" a grammar property rather than a promise.

**design-2 (4).** `Pathway`/`RailStep` vs `ReportedItem` are separately owned (§1.3/§1.4) and joined by one function (§5.2: "The join is one function... the join code does not change"). However, `Source.class` includes a `RESULT` class (§1.2 table) and **every `ReportedItem` must carry a `source_id`** (§1.4: "nothing enters state unattributed") — so a subject's own reported result is modeled as requiring an authoritative-artifact `Source` registration, blurring the brief's "authoritative source" vs "reported state" dichotomy that the other three keep strictly to `{GUIDELINE, INSTRUCTION, PRESCRIPTION}` on the `Source` side.

**design-3 (5).** `PathwayLibrary` and `ReportedStore` are named as physically separate modules (§2 table) with `LedgerEngine` stated to be "pathway- and source-**agnostic**." The join is shown as a typed pure function `join: (Pathways, SubjectFacts, [ReportedState]) → [LedgerItem]` (§5.1) with an explicit non-inference argument: "code equality... is a lookup, not a clinical inference" (§3.2).

**design-4 (5).** `ExpectedStep` (Pathway Library) vs `ReportedItem` are stated "**never merged at rest**; they meet only inside the Reconciliation Engine, on read" (§5.1). The 4-row classification table (§5.2) is generic over any instantiated step, with the explicit claim "adding a new pathway needs no new gap logic — the same engine consumes any rail."

**Leader: design-1, design-3, design-4** (tied) — each keeps `Source`/authoritative strictly to guideline/instruction/prescription classes and shows the join as a genuinely rail-agnostic function; design-2's universal `source_id` requirement on every `ReportedItem` (including results) is a concrete structural blur of the two families.

---

## M4 — Provenance/confidence structurally inseparable

**design-1 (5).** `citation` table: `source_id`/`locator_id` **NOT NULL FK**, `tier` copied from source ("the caller cannot pass a tier" — §3.2), `citation_basis ≥ 1` enforced by DB trigger. Tier is a literal, required column on the emitted row itself.

**design-2 (4).** `Citation.source_ref: SourceRef` is required, and `confidence_tier` lives on `SourceType`, reached through `source_ref` (§1.2/§1.5). §3 point 4 argues inseparability in prose ("remove them and there is no citation left to emit"), but unlike the other three, **`Citation` itself has no `tier`/`confidence_tier` field** — the comment "`SourceRef → a real Source (+ its confidence_tier)`" leaves ambiguous whether the tier is materialized on the emitted value or only reachable by a further lookup.

**design-3 (5).** `Citation.tier: ConfidenceTier // copied from the referenced Source, never recomputed` is a literal field (§1.6); `RailStep.source_ref` is stated `NON-NULL`; §5.2 adds an explicit consistency check: "`citation.tier == referencedSource.tier` for every emitted item."

**design-4 (5).** `Citation.confidence_tier: ConfidenceTier` is a literal field, "copied from source_ref; inseparable" (§1.5); §5.3 states "an instantiated step whose `source_ref` does not resolve is rejected **before it reaches the join**, so an uncited expectation can never reach the ledger" — provenance is checked upstream of emission, not only at the gateway.

**Leader: design-1, design-3, design-4** (tied) — all three materialize `tier` as a literal, non-optional field on the emitted `Citation` object itself; design-2 leaves tier reachable only via a dereference through `source_ref`, a real (if minor) structural gap against "confidence tier travels with every item."

---

## M5 — Extensibility: new pathway or source type is one owner's change

**design-1 (4).** §7's own change-table is candid about a partial exception: adding a **new source *type*** lists "one `sources.kind` enum value + one tier rule **(+ a compiler entry in `pathways` if it carries steps)**" — i.e., a source type that itself defines expectation steps (guideline-like) requires touching *two* owners (`sources` and `pathways`), by the design's own text.

**design-2 (5).** §1.3: "Adding a pathway = inserting rows here. It touches nothing else." §1.2: "Adding a class = one registry change" to `SourceType`. The module table (§2) restates both as isolated single-owner changes with no stated exception.

**design-3 (5).** §2 gives the most explicit rationale for the exit criterion's exact wording: "exit 5 asks that a *new source* and a *new pathway* each be **one owner's** change — and they are **different owners**... Splitting them keeps each change local to its owner." Two registries (`SourceRegistry`, `PathwayLibrary`) are named specifically to satisfy this criterion, with no stated cross-owner exception.

**design-4 (5).** §7's explicit table: new pathway touches only `Pathway Library`, "Ledger engine, account model, Gateway, seam operate on canonical `ExpectedStep` — **unchanged**"; new source class touches only `Sources+Ingestion`, "the join works on `code`, the Gateway on references — **neither is aware of `source_class`**." No stated cross-owner exception.

**Leader: design-2, design-3, design-4** (tied) — each states a clean one-owner change with no admitted exception; design-1 is the only design whose own extensibility table names a case (a source type that carries pathway steps) that scatters into a second owner.

---

## M6 — Scope discipline (no speculative build)

**design-1 (5).** §8 explicitly excludes the overview, any inference (tying it to the schema: "the `opens_process` CHECK forbids a result triggering follow-up"), advice beyond the fixed nudge, document understanding/OCR, external integrations, clinician tooling, consent workflows, scheduling, and multi-guideline conflict resolution (11 named exclusions) — none built.

**design-2 (5).** §7 excludes the overview, "any inference of medical state," advice origination, source reconciliation/dedup, EHR/lab/pharmacy integrations, notification infra, localization, and cross-subject analytics — none built.

**design-3 (5).** §7 excludes the overview, an inference/suspicion engine ("`Origin` has no `SYSTEM` member — inference is **unbuildable**, not merely disallowed"), advice origination, and notably **its own extensibility mechanism**: "A hot-loadable adapter/pack plugin runtime... would be speculative" — the design deliberately trims a *more capable version of its own extension point* rather than building it "for later."

**design-4 (5).** §8 excludes the overview, an inference/suspicion engine, advice generation, unstated future source types, cross-subject analytics, scheduling/notifications, **and specifically "Auto-coding of uncoded sources"** — a concrete NLP/inference vector named and closed off ("Uncoded items surface at the lowest tier and never auto-match").

**Leader: tie, all four** — none of the four builds a component for the overview, inference, or unstated sources; all four devote a dedicated section to naming exclusions. design-3 and design-4 each name one additional, more specific self-imposed cut (a plugin runtime; auto-coding) beyond the generic overview/inference exclusions common to all four, but this is a matter of granularity, not a different verdict.

---

## M7 — Domain model carries real behavior (anemic-model check)

**design-1 (4).** `cite.make(kind, source_id, locator_id, report_ids[]) -> Citation` (§3.2) is shown as an explicit 5-step validation/construction procedure owned by the `cite` module (resolve source, resolve locator, resolve+check reports share a subject, copy tier, persist). This is a real invariant-enforcing constructor. But the join/ledger logic is explicitly framed as "a pure function" (§5.2) rather than a method owned by a `Ledger` type, and most other rules are phrased as "rules owned by `reports`" (a module, not an object) rather than object methods.

**design-2 (3).** `Mint.project(Finding) -> Citation` is described in three prose bullets (§3) rather than an inline procedure; no comparable step-by-step construction pseudocode is shown for it or for any other type. The Ledger engine is "a pure join `expected × reported → Finding[]`" (§2 table) — again a function, not a type with owned behavior. Of the four, this design shows the least concrete "this type does X" evidence.

**design-3 (4).** §2 names five numbered, individually-owned "boundary rules (each an enforceable fitness test)" tied to specific modules/types (e.g. rule 5: "Only `SourceRegistry` may set `tier`"), which is a concrete (if terse) statement of owned behavior per module. `LedgerEngine`'s purity is explicitly asserted as a constraint on the type itself (§2 rule 4), and §5.3 states a checkable invariant (`citation.tier == referencedSource.tier`) as a property the type must hold.

**design-4 (4).** `Gateway.cite(request, viewer)` (§3.1) is shown with explicit `require`/assignment pseudocode (comparable in concreteness to design-1's `cite.make`), and a second locus of owned behavior is named separately: the Ingestion Port is "the *only* write path into medical state" (§2 table, "may NOT" column) — giving this design two distinct type/module-owned behavior loci rather than one.

**Leader: design-1, design-3, design-4** (tied) — each shows at least one concrete, procedural, module-owned construction/validation routine (not just a schema); design-2's equivalent is stated only as prose contract points with no comparable procedural detail.

---

## M8 — Day-zero vocabulary clarity

**design-1 (5).** §6 lists closed enumerations per owning module (`basis`, `kind`×2, `tier`, `asserted_by`, `opens_process`, item-code namespace, rail predicate atoms, ledger `status`, citation `kind`) **and** an explicit denylist of banned words ("recommend, advise, suggest, should, diagnose, suspected, abnormal, likely, risk score, predict, infer, Advice, Recommendation") stated to be enforced by "the same architecture test that binds template slots (§3.1)" — tied to a mechanical check.

**design-2 (4).** §6 gives a clean nouns table and a verbs table with one closed enum (`ConfidenceTier: T1/T2/T3`, `Relation: DUE|DONE|GAP|REFERRAL`). No denylist of banned terms is stated, and no code/predicate-grammar vocabulary is enumerated the way design-1/design-3 do.

**design-3 (5).** §6 enumerates closed sets for `Origin` (no `SYSTEM`), `Source.kind`, `ConfidenceTier` (a **total order**, not just a set), `ReportedState.kind`, `Citation.relation`, `Grant.scope`, plus explicit **open** vocabularies (`ActionCode`/`ProcessCode`/`MedicationCode`) so growth is pre-declared as unconstrained-by-schema. A separate "Verbs permanently absent (denylist lint over the seam)" list is given, tied back to the build-failing lint of §3.1.

**design-4 (4).** §6 lists nouns, enums (`role`, `source_class`, `kind`, `status`, `confidence_tier`, `ReportedState`), and verbs, plus a prose denylist ("The seam may not speak: advice, recommendation, diagnosis, suggestion, assessment..."). No automated enforcement (lint/CI) is named for this list, unlike design-1/design-3.

**Leader: design-1 and design-3** (tied) — both pair the vocabulary listing with a stated build-time/lint enforcement mechanism and an explicit denylist of banned terms; design-3 additionally distinguishes closed vs. open vocabularies (where new codes may land without a schema change) most explicitly of the four.

---

## Overall reading

**The per-metric picture is primary.** design-3 and design-1 are the strongest pair on the mechanisms that make the non-advice/citation invariant *structural* rather than conventional (M1, M4, M8) — both name a build-time or schema-level backstop (a CI dependency test / DB trigger for design-1; a denylist lint / a `SYSTEM`-less `Origin` enum for design-3) in addition to constructor discipline, where design-2 and design-4 rely on constructor discipline plus runtime checks alone. design-2 is comparatively the weakest of the four on the core citation/provenance mechanics (M1, M3, M4, M7): its `Citation` type has no literal `tier` field (M4), its `Source` model absorbs `RESULT` as a source class and forces every `ReportedItem` to carry a `source_id` (M3, blurring the authoritative/reported split the brief asks to keep distinct), and its constructor's invariants are stated only in prose without comparable procedural detail (M7). design-1 is, conversely, the only design whose own extensibility table admits a case where a change scatters across two owners (M5) — the one criterion where design-2, design-3, and design-4 all show a clean single-owner claim with no stated exception.

All four are tied on M2 (single `manager→subject(s)` relation, cardinality-only difference) and M6 (no built overview/inference/speculative material) — these two exit criteria are met uniformly across the field.

**Secondary glance — totals:** design-3 = 39/40, design-1 = 38/40, design-4 = 37/40, design-2 = 34/40.

**Total vs. load-bearing axes:** design-3 both leads the total and ties for the lead on every load-bearing axis (M1, M2, M3, M4, M5 — the five criteria the brief states as exit conditions), so there is no total/axis divergence for the leader. design-1 is the case worth flagging: its total (38) is second-highest and close to design-3's, but it is the sole design that scores below the other three specifically on M5 (extensibility = one owner's change, exit criterion 5) — a load-bearing axis where its own text admits a two-owner exception. A reader selecting on total alone would not see that design-1 is uniquely weaker, by its own account, on one of the six criteria the brief itself names as an exit condition.
