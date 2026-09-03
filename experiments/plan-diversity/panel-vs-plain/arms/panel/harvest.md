# Harvest notes — panel composition

## 1. Unanimous spine (all three designs; treated as robust, carried unchanged)

- Ledger is the sole minter of `Citation` and `LedgerEntry` (sealed/module-private constructors);
  Presentation/Surface renders `list[LedgerEntry]` and nothing else — one auditable output path.
- `Citation = (SourceRef × ReportedBasis)`, non-optional on every entry; **tier is a field of the
  provenance value**, so provenance and confidence are inseparable by shape.
- The account primitive is a single `Grant` edge over principals/subjects; self-management is a
  self-grant; family and a doctor's panel differ only in edge count — no special-case types.
- Two expectation producers (declarative rails; reported directives) behind one interface, both
  real on day one; the Ledger is ignorant of which authority produced an expectation.
- Pathways are declarative data validated at load; adding a pathway is a data change.
- The nudge is a join outcome (`NO_PLAN`-class entry) rendered from a fixed template — never
  generated text; `LedgerEntry` has no free-text field.
- Closed activity-code vocabulary as the join key; exact code+window matching, no fuzziness.
- Closed day-zero seam vocabulary; minimal error taxonomy (one type per distinct caller handling);
  no rows/framework/vendor types across seams.
- Out-of-MVP list excluded *structurally* (no reserved hooks): overview, inference, extra source
  types, notifications, consent workflows, authoring tooling, rules engines/plugins.

## 2. Strengths harvested per design

### advisor-clean-code
- **Closed `ActivityCode` registry as the no-inference guarantee**: join = code equality + window
  membership, a pure function; unparseable codes rejected at ingestion with actionable errors.
  → final §2, §3, §4 lock 4.
- **Dependency diet**: DB + thin HTTP + stdlib + one schema-validation step; closed list; nothing
  from it in seam types. → final §1.
- **Non-nullable `source_id` FK** — provenance as a constraint, not a convention. → final §3.
- **Surface read/write asymmetry**: writes via Accounts/Record, subject-output reads only via
  `Ledger.view`; Record/Rails query seams exported to Ledger only. → final §1, §4 lock 3.
- **Static copy table keyed by `LedgerStatus`**; gap citations join the expectation's source with
  *the reported fact that made the step applicable*. → final §4 lock 2, §7.
- **Minimal error taxonomy** (`NotAuthorized`, `RejectedReport` only until a caller branches).
  → final §8 (plus `NotFound`, see harmonization H8).
- **Honest duplication**: rails and directives share no evaluation code — concepts that merely
  rhyme. → final §6.
- One-sentence-reason-per-module discipline and change-scenario probes. → final §7 table.

### advisor-encapsulation
- **Unforgeability chain**: `Citation` constructor private to Ledger; `SourceRef` mintable only at
  authority registration with tier welded in; `ReportedBasis` mintable only by the Record's
  `evaluate` — a valid Citation is *evidence* the join happened. → final §4 locks 1, 4.
- **`SubjectHandle` capability authorization**: no seam accepts a bare `SubjectId`; a forgotten
  authorization does not type-check; scope-typed handles = least privilege by signature. → final §5.
- **"Record, not body" (I2)**: `evaluate` can only answer about the file (`Fulfilled` /
  `Absent(window)`); "the patient hasn't done X" is unphraseable. → final §4 lock 4.
- **`LangText`**: outbound strings constructible only as quoted-attributed source text or reviewed
  template keys — the advice sentence has no constructor. → final §2, §4 lock 2.
- **Storage private per context**: seam readers never learn a column name. → final §3.
- **Rail-declared `opens_process`**: openness of an episode declared in sourced rail data, so the
  nudge doesn't depend on reporter savvy. → final §7.
- **Rule-ownership table discipline** (every stated rule, one owner, one mechanism) — used as the
  composition's internal checklist; the final expresses it through §4's locks and §7's table.

### advisor-genericity
- **Floor/ceiling calibration of `Expectation`**: flat four-field type; recurrence expanded
  upstream inside the guideline producer (a directive would fabricate it; the Ledger never learns
  recurrence exists); rationale reachable via the SourceRef pointer, not a field. → final §6.
- **`ReportedItem` supertype / directive specialization**: no null-cramming of `due`/`steps` onto
  plain reports; only the one authority-consumer sees the subtype; Ledger's done-feed is
  supertype-typed (interface segregation). → final §3.
- **`UNCODED` + `UNMATCHED_REPORT`**: the file may honestly hold what the vocabulary can't code;
  never force-fitted, never interpreted. → final §3, §7 (see harmonization H5).
- **Tier count = number of distinct downstream treatments** (two: DIRECTED, GUIDELINE), not one per
  source kind. → final §2.
- **Declared-only `SubjectProfile` ceiling** with closed `RiskFlagCode` registry; richer profile
  would require inference and is therefore excluded by type. → final §3.
- **Closed predicate/schedule grammar** calibrated to exactly the two MVP rail families; extension
  is an in-Rails change because `Predicate` never crosses a seam. → final §3, §7 table.
- **Tolerance as a Ledger constant**, not a per-pathway knob. → final §4 lock 4, §7.
- **Code lists governed as vocabulary** (reviewed, versioned), not freely edited data. → final §2.

## 3. Harmonizations (both strengths hold, adapted)

- **H1 — Tier derivation × tier inseparability × tier count.** clean-code's single
  `ConfidenceTier.of(kind)` function + encapsulation's tier-welded-into-`SourceRef` + genericity's
  two-tier calibration: the `SourceRef` factory takes no tier parameter and computes it internally
  via the one total mapping; `SourceKind` stays three-membered for provenance/display, tier is
  two-membered (prescription and instruction share the `DIRECTED` treatment).
- **H2 — Capability handles × "only Accounts knows managers" × role-gating.** The `SubjectHandle`
  (encapsulation) *is* how clean-code's "downstream modules never heard of a manager" is achieved
  without per-call `authorize` discipline. Scope count calibrated by genericity's
  one-member-per-distinct-treatment rule: exactly three scopes, one per seam kind that exists
  (View→ledger read, Report→record write, Administer→grant management).
- **H3 — Matching ownership × matching triviality.** Encapsulation's tell-don't-ask
  (`Record.evaluate` mints the basis; callers never interpret rows) holds, *and* the algorithm
  inside it is clean-code's trivially auditable pure function (code equality + window + genericity's
  single tolerance constant). Ownership from one design, algorithm from the others — no dilution of
  either.
- **H4 — Gap-citation content.** clean-code/genericity cite the reported facts that made the step
  applicable; encapsulation cites the file's searched-and-empty window (record-not-body phrasing).
  Composed: `Absent(applicability_basis, searched_window)` carries both; glue field
  `Expectation.applicability_basis` (see §5) makes the Record able to mint it.
- **H5 — Reject-at-ingestion vs. store-`UNCODED`.** Genuine conflict, harmonized by splitting the
  cases: a *mistyped/unrecognized* code is rejected with an actionable error (clean-code — no
  silent free text, no later fuzzy match), while an item the registry *genuinely cannot express*
  may be stored `UNCODED` by the reporter's explicit choice and surfaces only as
  `UNMATCHED_REPORT` (genericity — the tracking file stays complete and honest). Both anti-
  inference stances hold at full strength; neither policy is averaged.
- **H6 — The three reported "roles" × no-null subtyping.** clean-code's
  `EVIDENCE/DIRECTIVE/OPEN_PROCESS` role enum is realized through genericity's supertype/subtype
  mechanism: plain `ReportedItem` (evidence), `ReportedDirective` (dated steps), and
  `ReportedOpenProcess` (openness, optional plan-domain) — same three-way semantics, zero nullable
  cram.
- **H7 — Two nudge triggers, one rule.** Openness is *declared, never inferred*, by exactly two
  authorities mirroring the two expectation producers: the reporter (attested
  `ReportedOpenProcess` — clean-code's OPEN_PROCESS) or rail data (`opens_process` list —
  encapsulation's flag). Coverage is mechanical and owned by the declaring authority (rail
  `plan_domain`; reporter-declared `resolves` link). Genericity's "open directive" trigger is
  subsumed: a directive too vague to fill `Expectation`'s fields *is* a `ReportedOpenProcess`
  (its unmeetable floor/ceiling is the signal genericity's own method predicts).
- **H8 — Error taxonomy.** clean-code's `NotAuthorized` + `RejectedReport` merged with genericity's
  `NotFound`; three types, each with a demonstrably distinct caller handling (403/422/404) —
  clean-code's "no subtype until a caller branches" rule kept as the governing test.
- **H9 — Explicit tables × storage privacy.** clean-code's one-owner-per-table and non-null
  provenance FK hold *inside* each module's private storage (encapsulation's rule that no row type
  or column name crosses a seam). Constraint enforcement and seam opacity are compatible layers.

## 4. Decided conflicts (chosen over rejected, with reasons)

- **D1 — No separate Sources context** (encapsulation's `Sources` store rejected; genericity's
  "Sources is a seam, not a store" chosen; clean-code's provenance-in-Record kept). Reason: a store
  module whose job is re-keying provenance already carried by Record (directives, item sources) and
  Rails (guideline provenance) has no independent reason to change, and it adds a registration
  round-trip for every directive. The strength it protected — unforgeable `SourceRef` with welded
  tier — is preserved by sealing the `SourceRef` factory to the two registering modules (H1);
  the change-axis ("new source kind = one owner") is preserved per the final §7 table.
- **D2 — Closed `ActivityCode` registry over `ConceptCode(scheme, code, display)`**
  (encapsulation's multi-scheme code type rejected). Reason: no MVP consumer branches on scheme;
  the scheme indirection is capacity for LOINC/ATC futures the brief scores as speculative; two of
  three designs and the join-exactness argument favor the closed registry. LOINC mapping is in the
  out-of-MVP list in all three.
- **D3 — Scopes over roles** (genericity's `owner/caregiver/clinician` grant role rejected;
  encapsulation's `{View, Report, Administer}` scopes chosen). Reason: scopes name what a seam
  mechanically checks (one treatment each — genericity's own calibration rule); roles name social
  categories the data model must never branch on (genericity itself requires role to never change
  data model or output path). The force behind role-gating — clinician authority — is served
  without it: authority tier comes from the reported item's `SourceKind`, and accountability from
  `Attestation`, not from the reporter's account category.
- **D4 — SubjectProfile owned by Record, not Identity** (genericity placed demographics/risk flags
  in Identity). Reason: they are *reported medical state*; medical state must have exactly one door
  (encapsulation lock 4), and Accounts' single reason to change is who-acts-for-whom (clean-code's
  one-sentence rule). Two axes vs. one, and the losing placement weakens the invariant.

## 5. Glue elements authored (connective tissue only, each justified)

- **`Expectation.applicability_basis: [ReportRef | profile-fact refs]`** — joins clean-code /
  genericity's gap-citation content ("the reported fact that made the step apply") with
  encapsulation's rule that only the Record mints a `ReportedBasis`: producers attach the refs they
  consumed; `evaluate` validates them and mints `Absent(applicability, window)`. No new capability
  — it routes existing data across an existing seam.
- **`ReportedDirective.resolves: ReportRef?` and rail `plan_domain: [ActivityCode]`** — the
  mechanical coverage rules H7 needs so "no plan covers it" is computable without judgment. Each is
  a declaration by the same authority that declared the openness (reporter / rail); no system
  guessing is introduced.
- **`SourceRef` factory sealed to Record + Rails** — the minimal mechanism that keeps
  encapsulation's unforgeability after D1 removed the central Sources minter.
- **`UNMATCHED_REPORT` citation shape** `(item's own source × Fulfilled(item))` — genericity left
  the source half vague ("attestation_as_basis"); clean-code's non-null source FK supplies a real
  source for every item, so the entry satisfies the same citation invariant with no exception case.

## 6. Subtractive pass (cut, with the absent force named)

- **`Nudge` enum (one member)** — cut: `NO_PLAN` status + fixed template already carry the token;
  a one-member enum with no branching consumer fails genericity's own dead-vocabulary test.
- **`matchPredicate` field on steps/expectations** (encapsulation) — cut: the join key is fixed at
  (code, window); a predicate slot is a general mechanism with exactly one instantiation.
- **Grant role enum** — cut per D3.
- **Separate Sources store** — cut per D1.
- **Multi-scheme `ConceptCode`** — cut per D2.
- **Per-pathway match tolerance knob** — cut (genericity's own argument): one Ledger constant until
  a real pathway demonstrates the need.
- **`open: bool` on directives** — cut: an active directive's expectations are horizon-filtered;
  vague "open" directives are `ReportedOpenProcess` (H7); no remaining consumer of the flag.
- Everything retained in the final names its force in place (each lock, scope, status, and subtype
  is tied to a brief requirement or an exit criterion in §§2–7 of the final).

## 7. Gap notes (perceived gaps in all three designs — flagged, not silently patched)

- **G1 — Cross-manager subject identity.** All three make multi-manager access "just another
  grant," but none says how a second manager (a doctor, given a parent already registered the
  child) *finds or links to* the existing Subject rather than creating a duplicate. Duplicate
  subject records would silently split the tracking file. Needs a linking/invitation decision
  before build; not designed here.
- **G2 — Pathway version transition.** Rails carry a `version` field in two designs, but none
  states the rule for in-flight expectations when a rail is revised. The compute-on-read ledger
  makes this mostly self-healing (next view uses the new version), but "which version does an
  older `SourceRef` display" needs a one-line policy at build time.
- **G3 — Handle lifetime/transport.** `SubjectHandle` is specified as "opaque, short-lived" but no
  design states its lifetime relative to a request or how the Surface carries it; an
  implementation-time decision, noted so it is not invented ad hoc.
