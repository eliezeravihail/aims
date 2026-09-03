# Blind head-to-head: design-R vs design-S — frozen-rubric scores (judge: fable)

Rubric: `/tmp/aims/experiments/plan-diversity/judge/rubric.md` (M1–M8, 0–5, M1/M3/M5 load-bearing).
Contestants read in full; every score below cites a concrete structural fact in the named design.
No assumption about authorship is made or used.

## Score matrix

| Metric | design-R | design-S | Leader |
|---|---:|---:|---|
| M1 — Citation invariant: one structural chokepoint | 5 | 5 | tie |
| M2 — `manager → subject(s)` as a single primitive | 5 | 4 | R |
| M3 — Expected vs reported; generic join | 5 | 4 | R |
| M4 — Provenance + tier inseparable | 5 | 5 | tie |
| M5 — Change locality (new pathway / new source type) | 5 | 4 | R |
| M6 — Seam vocabulary and domain types | 5 | 5 | tie |
| M7 — Scope discipline | 5 | 4 | R |
| M8 — Responsibility placement / non-anemic model | 5 | 4 | R |
| **Total (secondary)** | **40** | **35** | **R** |

---

## Per-metric justifications

### M1 — Citation invariant: one structural chokepoint — R: 5, S: 5 (tie)

**design-R — 5.** The 5-anchor is met on every clause by named mechanisms. `Citation` (§4) has a
module-private constructor in `Ledger` and requires both a `SourceRef` and a `ReportedBasis`;
`ReportedBasis` is a closed sum (`Fulfilled | Absent | OpenUnplanned`) mintable only by
`Record.evaluate`, so a citation is constructive *evidence* the join ran. `LedgerEntry` is
sealed, carries `citation` as a non-optional field, and is "the ONLY type Surface renders";
`Surface`'s read dependency is exactly `Ledger.view` (lock 3), its `Record`/`Accounts` access is
write-only. No free-text recommendation field exists (§3, "two deliberate absences"), and R goes
one lock beyond the anchor: `LangText` has exactly two constructors — `quoted(SourceRef, excerpt)`
and `template(key)` — and no `LangText.of(string)`, so even the human-readable rendering layer
cannot author a sentence. The doctor enters as a source, not an output path: their input is stored
as an attested, sourced `ReportedDirective` ("There is no clinician-mode API", §4 lock 3). Nudge
and notification are ledger rows (§7, §9).

**design-S — 5.** Also meets the anchor's every clause. `Citation` (§1.5) is "opaque… constructor
sealed (package-private / internal) to the Ledger module, callable only from the join function";
its two fields `SourceExcerpt` and `ReportedExcerpt` are "BOTH… required & non-null" — a
half-citation is unrepresentable (§3.2). One output path: "the API's read surface returns
`LedgerView` and nothing else; there is no second endpoint family" (§3.3). `LedgerEntry` has no
message field (§1.5 states this as a structural fact); rendering is a closed template set keyed by
`GapKind` whose only variable content is verbatim excerpts. The doctor user "is just a Manager…
a doctor's instruction enters the system as a Source through ingestion like any other" (§3), and
the future notifier "consumes `LedgerView` like any other client; it adds no new output path"
(§5). The one gap versus R — the template constraint lives in the presentation layer as a stated
rule rather than as a text type like R's `LangText` — is above the 5-anchor's requirements, so it
does not lower the score; it is noted as R's deeper margin, not S's deficiency.

### M2 — `manager → subject(s)` as a single primitive — R: 5, S: 4 (R leads)

**design-R — 5.** One relation, one enforcement mechanism. `Grant(principal_id, subject_id,
scope: {View, Report, Administer})` is the only relation; self-management is literally
`Grant(own principal, own subject, Administer)` written at signup (§3). "A doctor with 200
patients: 201 grants. Same rows, same queries, same code path; no `FamilyAccount`, no
`ClinicianPortal` type exists anywhere" (§5). Enforcement is capability-style: every
subject-scoped seam takes a `SubjectHandle` mintable only by `Accounts.authorize` — "a call
without a handle does not type-check". Crucially, the M2/M1 separation the anchor demands is
explicit: "a clinician's higher authority enters via the `SourceKind` of what they report, not
via their account" — there is no role field at all; the scopes are seam treatments with behavior.

**design-S — 4.** The primitive itself is right: `Manager`/`Subject`/`Grant` with self, family,
and doctor as "the same three rows… with different cardinalities" (§4); subjects are not accounts
and a later signup "becomes a Manager holding a `Self` grant to their existing Subject — no
migration"; `AccessGrant` is a capability token mintable only by `Accounts.authorize`, required
by File and Ledger seams. The deduction is a concrete structural fact: `Grant.relation:
⊕{Self, Family, Clinician}` (§1.1) stores the family-vs-doctor social distinction inside the
relation. S itself declares it "a label only — no code path switches on it in the MVP". It is not
the 3-anchor (no mode switch changes behavior), but the doctor/family distinction does exist in
the relation as a dead discriminator, kept "so the day the product needs them, Accounts is the one
owner" — the very distinction the 5-anchor wants absent from the manager type. R shows the field
is unnecessary; S carries it. 4.

### M3 — Expected vs reported; gap computed by a generic join — R: 5, S: 4 (R leads)

**design-R — 5.** Distinct sides: `Rails` (`PathwayDef` with `eligibility: Predicate` in a closed
grammar + `StepRule` schedules) and `Record` (append-only reported journal); the `Ledger` owns one
join whose key is stated exactly: "`(ActivityCode, occurred_on ∈ window)` and nothing else" (§7),
where `ActivityCode` is a closed, versioned registry — a shared code vocabulary, precisely the
anchor's "stated matching key". The ledger states are the join's enumerated outcomes: the closed
`LedgerStatus` enum `DONE | DUE | OVERDUE | NO_PLAN | UNMATCHED_REPORT` maps 1:1 onto the join
pseudocode's arms. "No plan" is a join outcome with *mechanical, owned* coverage semantics:
openness is declared by exactly two authorities (a `ReportedOpenProcess` report, or a rail's
`opens_process` list), and coverage is defined by the declaring authority's own data — a rail's
`plan_domain` list or a directive's reporter-declared `resolves` link — "never a system guess".
Items the registry cannot express are stored `UNCODED` and surface as `UNMATCHED_REPORT`, never
fuzzily matched. Nothing in the join names any pathway.

**design-S — 4.** Distinct sides ("Rails knows nothing about what was done; File knows nothing
about what is expected. They meet only inside this function", §5) and a generic join in one
screen of pseudocode, with a stated matching key for steps: `Matcher` = "kind + `ClinicalCode`
(+ value constraints)" within `due_window`, over a typed `ClinicalCode {system, code}`. `NoPlan`
is produced inside the join loop, so it is a join outcome, not a sibling feature. The deduction:
the no-plan branch's own matching semantics are hand-waved where R's are mechanical. The join
calls `covered(open, expected, reported)` (§5) which is never defined; §3 unpacks it as "(a) no
rail whose applicability fires **and covers it**, and (b) no subsequent `DoctorInstruction` item
**matching it**" — but neither "covers" nor how an instruction "matches" an open item (by code?
by kind? by reporter link?) is given a key, so this part of the join cannot actually run as
specified. That is the 3-anchor's "matching vocabulary… hand-waved" applied to one branch of an
otherwise fully specified join → 4. A secondary fact: in S the expected side is fed *only* by
`Rails.expected_items` from `PathwayDefinition`s; a `DoctorInstruction`'s own dated step never
becomes an `ExpectedItem` (it only closes `NoPlan` gaps), so an instructed-but-overdue follow-up
cannot appear as `Due/Overdue` — R covers this with `Record.DirectiveSource` promoting
`ReportedDirective.steps` into expectations.

### M4 — Provenance and confidence tier inseparable — R: 5, S: 5 (tie)

**design-R — 5.** Tier and provenance are one value by construction: `SourceRef` has "**no tier
parameter**" — its factory computes the tier internally via the single total mapping
`ConfidenceTier.of(kind)`, so "tier and provenance are one value, never split" (§2), and the
factory is invocable only by `Record` and `Rails`, the two modules that register authorities.
Inseparability is then transitive shape, not rule: tier is a field of `SourceRef`, `SourceRef` a
required field of `Citation`, `Citation` a required field of every `LedgerEntry` (§4 lock 1); "the
Ledger physically cannot assign a tier because no tier-accepting constructor is visible to it"
(§7). The nudge is the same shape: `NO_PLAN` is a `LedgerEntry` whose citation joins the declaring
authority against the open report. The enum is closed and named (`DIRECTED > GUIDELINE`), with the
tier count justified by the number of distinct downstream treatments. Adding a source kind touches
`ConfidenceTier.of`, which lives in the vocabulary kernel beside `SourceKind` — not in the ledger
— so the 3-anchor's "adding a source type touches the ledger" does not apply.

**design-S — 5.** The mapping lives with the source in the most literal sense: `tier_of(class)`
is owned by the **Sources** module, "the ONLY place tiers are assigned" (§1.2), and tier is "never
stored as an independent, editable field anywhere else… a citation's tier can never drift from its
source". Both join inputs are born provenanced: `ReportedItem.source_id` is "REQUIRED — no orphan
facts" (§1.3, enforced by constructor), and `ExpectedItem.source_id` is "inherited from the
definition — an expected item is born citing its source" (§1.4). The `Citation` constructor
requires a `SourceExcerpt` (which carries id, class, and derived tier) and a `ReportedExcerpt`,
both non-null; "the mint *copies* provenance through, it never assigns it" (§5). The `NoPlan`
nudge is the same `LedgerEntry` shape, its citation being "(the source of the opening item × the
opening item itself)". `ConfidenceTier` is a closed, ordered, named enum. Every 5-anchor clause is
met by a named mechanism.

### M5 — Change locality — R: 5, S: 4 (R leads)

**design-R — 5.** The design explicitly walks both mandated changes and shows the untouched
components, in a dedicated table (§7 "Change scenarios"). New pathway: "Rails: one new
`PathwayDef` data file (+ any new registry codes, reviewed)" — Ledger, Accounts, Record, Surface,
all other rails untouched; "Adding a pathway is adding a reviewed data file; no code change" (§6).
New source kind: one `SourceKind` member + one line in `ConfidenceTier.of` (both in the vocabulary
kernel, a reviewed vocabulary change — not the join, not the ledger) + one `ExpectationProducer`
implementation in the module that backs it, with "`Citation`, `LedgerEntry`, join logic, Accounts,
Surface — all compile untouched". The interface the adapter fills is stated (`ExpectationProducer`
→ `Expectation` with `SourceRef` carrying its own tier), which is exactly the 5-anchor's "one
adapter behind a stated source interface emitting the common… type (with its own tier)".

**design-S — 4.** Both changes are walked with owners: new pathway = "adding one
`PathwayDefinition` record… Nothing else changes anywhere" (§1.4); new source type = "one change
in Sources: a new `SourceClass` variant, its tier, and its adapter", with "Rails, File, Ledger,
and Accounts see only the generic `Source` / `ReportedItem` / `PathwayDefinition` types and are
untouched" (§1.2) — genuinely one module in the plain case, arguably tighter than R's
vocabulary+module pair. The deduction is a concrete latent coupling R avoids: S maintains
*parallel classification enums* — `SourceClass ⊕{PublicGuideline, DoctorInstruction, Prescription,
SubjectSelfReport}` owned by Sources (§1.2) and `ReportedItem.kind ⊕{Result, DoctorInstruction,
Prescription, Demographic}` owned by File (§1.3), with Rails' `Matcher` matching on "kind +
`ClinicalCode`" (§1.4). A source type whose items are a new *kind* (e.g. a new instruction-like
class) therefore touches Sources (class + tier + adapter), File (the `kind` enum), and rail
`Matcher` data — three owners — and the design does not walk this case. R has no such parallel
pair: `SourceKind` is the sole classification and report subtypes are behavioral
(`ReportedDirective`, `ReportedOpenProcess`), not per-source. Locality is shown for the easy case
and unexamined for the coupled one → 4 (between the 3-anchor's partially-asserted locality and
the clean 5).

### M6 — Seam vocabulary and domain types — R: 5, S: 5 (tie)

**design-R — 5.** §8 is a normative, closed list: kernel types (`PrincipalId`, `SubjectId`,
`ActivityCode`, `RiskFlagCode`, `SourceKind`, `ConfidenceTier`, `SourceRef`, `ReportRef`,
`DateWindow`, `LedgerStatus`, `LangText`) plus the public types (`Grant`, `SubjectHandle`,
`SubjectProfile`, `ReportedItem` supertype, `Attestation`, `Expectation`, `Citation`,
`ReportedBasis`, `LedgerEntry`); "All ids are distinct nominal types, never bare strings";
closed tier and status enums; the foundational set is declared as a small closed list (ISO-8601
stdlib types, UTF-8 only as `LangText`, JSON at the HTTP edge); the dependency diet (§1) is
closed and barred from seams; errors are one type per distinct handling (`NotAuthorized`→403,
`RejectedReport`→422, `NotFound`→404) with "no further subtype… until a caller demonstrably
branches on one". Seam bindings are concrete: Rails/Record export query seams to the Ledger only;
`Predicate` "never crosses a seam"; "a seam reader never learns a column name."

**design-S — 5.** §6 is likewise a normative closed set tied to named seams ("API ↔ Ledger,
Ledger ↔ Rails/File, anything ↔ Sources/Accounts"): opaque id types (`ManagerId`…`StepKey`,
"never bare strings"), opaque `AccessGrant`, opaque `Citation`, closed enums (`SourceClass`,
`ConfidenceTier`, `GapKind`, `CodeSystem`, item `kind`) each with a named extension owner;
typed `ClinicalCode` rather than a bare code string; foundational primitives declared (ISO
dates, JSON at the API edge, "no ORM, HTTP-framework, or vendor type is ever a parameter or
return at a seam"); error vocabulary of four types each tied to a distinct caller handling, with
implementation exceptions translated at the seam. The key concepts the 3-anchor worries about
(subject id, tier, source) are all typed, not primitives. Both designs meet every 5-anchor
clause; R's `LangText` (typed outbound text) is a margin above the anchor, not a gap in S.

### M7 — Scope discipline — R: 5, S: 4 (R leads)

**design-R — 5.** Exclusions are *shape* exclusions: "no interface, enum slot, nullable column,
or reserved hook exists 'for when we add it'" (§9), and the body bears this out — the overview,
inference ("no cell an inference could live in", §3), FHIR/HL7, notification delivery, real code
systems (LOINC/SNOMED deferred), pathway tooling, rules/plugin engines are all absent from the
structure, not stubbed. The only interface with multiple implementations, `ExpectationProducer`,
is justified by two producers that both ship day one, with "no plugin registry and no dynamic
discovery — a hand-maintained list of two" (§6). The dependency diet is closed (§1). Every
structure present traces to a brief force (`RiskFlagCode` to the brief's "age/risk-based"
screening; `LangText` to exit criterion 1; `resolves`/`plan_domain` to the nudge).

**design-S — 4.** Core scope is right (Pillar 1 only, §0; §7 excludes overview, inference,
interop, push, consent — "no hooks left 'just in case'"). But two structures contradict that
claim with the 3-anchor's exact pattern, "reserves fields… 'for later'": (1) `Grant.relation ⊕
{Self, Family, Clinician}` is by S's own words a field no MVP code path reads, kept because "the
field exists so the day the product needs them, Accounts is the one owner that changes" (§1.1) —
a reserved-for-later slot the brief scores against; (2) `CodeSystem ⊕{LOINC, ATC, Local}` (§1.3)
builds real clinical code systems into the day-zero seam vocabulary, which nothing in the MVP's
two source classes requires (a local registry suffices — R explicitly defers LOINC/ATC as
post-MVP). Neither is an overview or inference engine (so nowhere near the 0-anchor), but both
are pre-built structure for unstated futures → 4.

### M8 — Responsibility placement, non-anemic model — R: 5, S: 4 (R leads)

**design-R — 5.** Each concept owns its rule, and the ownership is stated: the pathway decides
its own applicability and expansion ("The pathway knows its own rules — nothing outside Rails
ever opens a definition", §6); the source declares its tier at `SourceRef` construction; the
Record owns matching over itself ("the Record decides matching… and mints the `ReportedBasis`.
Callers never interpret raw rows", §7) so the Ledger owns only orchestration of the
reconciliation; the citation's completeness is enforced by its own constructor; `Accounts` owns
"the ONLY authorization question in the system" (§5); `Surface` "owns zero rules" with "no branch
on `SourceKind` and no branch on manager type" (§8). Types carry behavior, not just fields — the
vocabulary table has a "Rules it owns" column per type (`ActivityCode.parse`, `DateWindow`'s
ordering rule, `LangText`'s constructors). None of the 3-anchor misplacements is present.

**design-S — 4.** Modules are split by concept with the single reason to change stated per module
in a table (§2: "Who may act for whom", "The join of expected × reported, spoken only in
citations", etc.), Tell-Don't-Ask is an explicit boundary rule ("API asks `Ledger.view(grant,
as_of)`, never 'give me the expected items and the file so I can join them myself'"), and key
types own rules (the `ReportedItem` constructor enforces source-required and verbatim-content;
`Citation` is sealed; `AccessGrant` is a required argument, not middleware). Two placement facts
cost the point: (1) the rule deciding when an open process counts as *planned* — a load-bearing
domain rule — exists only as the undefined helper `covered(open, expected, reported)` inside the
join pseudocode (§5), with no owner stating its semantics (contrast R, where coverage is owned by
the declaring authority's own data: `plan_domain` / `resolves`); (2) `opens_process: bool` is a
File-owned field whose value is decided by Sources' ingest adapters ("stated BY the source…
carried through ingestion", §1.3), i.e. one module's semantics are written by another's adapters
— workable but a soft edge in ownership. These are the 3-anchor's "key rules misplaced" in
miniature, on one rule rather than systemically → 4.

---

## Overall reading

**Per-metric picture first.** The two designs are level on M1, M4, and M6: both seal the
`Citation` constructor inside the Ledger, make both halves of the citation required and
independently mintable only by the authoritative side, leave no free-text field an advice
sentence could occupy, route the doctor's authority through source ingestion rather than a
privileged account path, weld tier to source through a single source-owned mapping, and publish
a closed, typed, seam-bound day-zero vocabulary with handling-driven error types. On the
architecture's single most important property — the structurally enforced non-advice boundary —
there is nothing to choose between them.

**Where it turns.** design-R leads on five metrics, and two of them are load-bearing:

- **M3 (load-bearing):** R's join is fully mechanical end to end — a closed `ActivityCode`
  registry as the stated join key, and NO_PLAN coverage defined by the declaring authority's own
  data (`plan_domain`, reporter-declared `resolves`). S's join is equally generic for steps but
  leaves its `covered()` predicate — the exact rule that decides whether a nudge fires —
  undefined, and S's expected side cannot express a doctor-instructed future step at all
  (instructions only close gaps, never open expectations), which R's `DirectiveSource` handles.
- **M5 (load-bearing):** both walk the two mandated changes, but S's parallel classification
  enums (`SourceClass` in Sources, `kind` in File, `Matcher` keyed on kind in Rails data) leave a
  three-owner path for the very change class the seam exists for; R has one classification and an
  explicit untouched-components table for six change scenarios.
- **M2, M7, M8:** the same root cause — S carries small speculative or unowned structure
  (the dead `Grant.relation` label, day-zero LOINC/ATC, the unowned coverage rule) where R
  resolves each with an explicit mechanism or an explicit absence.

**Total (secondary glance):** design-R 40, design-S 35.

**Verdict.** **design-R is the stronger design.** Not because S is weak — S is a sound,
tightly-scoped architecture that meets the citation invariant as structurally as R does — but
because R closes exactly the seams S leaves soft: the no-plan coverage rule is owned and
mechanical rather than an undefined helper, doctor directives participate in the expected side,
the account primitive carries no dormant role discriminator, and both mandated change walks
terminate in provably untouched components. The head-to-head turns on the load-bearing axes M3
and M5, with M2/M7/M8 confirming the same pattern.
