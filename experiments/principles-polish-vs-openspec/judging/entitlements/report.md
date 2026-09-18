# Blind design judgment — Entitlements (X vs Y)

*Blind, structural-only. Format, vocabulary, verbosity, naming ignored; only structural architecture
properties scored. Every load-bearing claim carries a quotation/reference. Sealed mapping (revealed after
scoring): **X = OpenSpec, Y = aims-single**.*

Precondition for this challenge (oracle): ONE-OWNER-PER-RULE (§5) and first-class deny-as-effect (§4). Three
stage-2 traps checked hard: (1) deny-as-absence cram; (2) inheritance in one resolver, not threaded through
call sites; (3) time/precedence coherence (single defined order).

## D1 — First-round quality (stage-1 only)

**Step-0 inventory (identical for both):** R = union rule, default deny, exact-match only, determinism/
order-independence, unknown user denies without leak. Change-axes named (storage backend; combination
policy) are not stage-1 features. Security/trust boundary PRESENT (the product IS the authz boundary) →
§17 applies.

**X-stage-1 profile: 8.5, worst 7, (0,0).** Sub-10 rows: §1 Tell-Don't-Ask = 8/S1 (engine pulls
`permissions_of(role_id)` and tests membership rather than asking the role); §4 primitive obsession = 7/S2
(`decide(user_id, action, resource)` — three positional bare strings, no Action/Resource value object); §5
anemic = 8/S1 (Role is a permission-set holder, match done in engine). One-owner (§9, precondition)
satisfied; correctly defers the grant/effect type (§12 YAGNI clean).

**Y-stage-1 profile: 10, worst 10, (0,0).** `Role.grants(action, resource)->bool` (Tell-Don't-Ask);
UserId/RoleId/Action/Resource/Permission value objects ("three positional string arguments cannot be
transposed silently"); one home per rule (Invariant 5); the mandatory review cut a `Decision` enum to
`bool` and built no combination/effect/time seam — "§7 falsifier: name the Stage-1 axis it serves — none."

**D1 oracle-trap check:** BOTH stage-1 designs decide via `any(...)` over a FLAT permission set with NO
grant/effect type (the oracle's *reopens* shape) and BOTH correctly defer that type (no stage-1 axis needs
it) while naming a single decision owner where the reopen will land (X `decide`, Y `may`). Neither pre-built
a resolver-over-grant abstraction — correctly. Both satisfy the one-owner precondition.

**D1 winner — Y (aims-single).** Both precondition-clean, no S3/S4, both correctly deferred the grant/effect
type. The gap is quality-tier and earned by present forces (survives the §7 tie-break): Y wraps the seam
arguments for transposition safety where X carries three bare strings (§4), and Y's `Role.grants(...)` is
Tell-Don't-Ask where X pulls the set and tests membership in the engine (§1/§5). **X = 8.5, Y = 10.**

## D2 — Change absorption (stage-1 → stage-2)

**Survival (reading = reopened + discarded):**
- **X (OpenSpec) ≈ 2** — reopened: the union rule spec *and* the decision engine ("rewrite of the rule …
  loop replaced by 4-step precedence"); discarded 0.
- **Y (aims) ≈ 2** — reopened/discarded: `Role.grants(a,r)->bool` predicate and the `frozenset[Permission]`
  representation (replaced) — but the **decision-combination owner did NOT reopen**: "Still the sole home of
  combination … nothing outside this owner had to change to gain deny-precedence." The churn is internal to
  the Role/grant data shape; the decision owner was **extended in place**.

Neither rippled to callers/adapters. Crucial contrast: X's decision *rule/engine* is what reopened, partly
because its stage-1 Role was already an anemic data holder with no behavioral predicate to lose
(stability-through-anemia is not, by the rubric, a merit); Y's decision owner absorbed deny-precedence
without reopening.

**Stage-2 filled forms (condensed):** X-stage-2 = **8.5** (worst 7): §12 flags DEAD MACHINERY — an unused
specificity-tagging step plus an inert "Specificity resolves competing allows only" requirement the 4-step
precedence never consumes; §4 = 7 (still positional bare tokens); §5 = 8 (Grant a data record, logic in
engine). Y-stage-2 = **9.9** (worst 8): only an `Instant = int` bare-alias S1 note; §12 exemplary — "cut the
specificity ordering" proving "distance never changes it … machinery that pays for nothing"; `_resolve` is
"the precedence rule, one named home."

**Stage-2 oracle-trap check — BOTH PASS every hard trap:** deny beats a cross-role allow (X "deny beats
allow from another role"; Y `_resolve` any DENY→False); deny is a first-class sum-type effect, no
deny-as-absence cram (X `effect ∈ {ALLOW,DENY}`; Y `Effect` enum "Not a labelled bool"); one resolver owns a
single precedence order time→deny→allow→default (X "Precedence, stated once"; Y `_resolve` single home);
inheritance resolved once, not per call site; time filtered first ("an expired deny does not block"). Only
trap-level difference is minor and favors X: it explicitly REJECTS an empty window `from ≥ to` (fail-fast),
where Y's `Window` degrades safely (contains always false) without rejecting at construction.

**D2 winner — Y (aims-single), narrow.** Correctness on hard traps TIED (both pass all seven); survival
TIED in category (≈2 vs ≈2, zero caller ripple). Tiebreak = structural quality of the absorbed change: Y
removed dead machinery and keeps richer per-rule ownership with the decision owner extended-in-place, where
X ships an unused specificity apparatus and reopened its rule. **X = 8.5, Y = 9.9.**

## Residual tells

Scored blind/structural; these were IGNORED for scoring but are recorded honestly. Anonymization is
imperfect: both files carry the neutral `the-method` token so the label cannot identify the arm, but the
**house styles remain legible** — X reads spec-driven (capability/requirement units, Given/When/Then, change
bundles), Y reads records-driven (goals/architecture/design-note vocabulary, concrete Python signatures, an
explicit narrated review-and-revise round). Bias guard applied: Y's concrete signatures make its structure
easy to verify and its subtractive discipline easy to credit, so each Y claim was verified against cited
text and X was scored on its explicit structural commitments as written, not on the absence of code. The
deeper un-removable bias — D1/D2 are scored against aims' *own* `design-principles.md` — is noted in the
series `results.md`; D2's survival reading is the rubric-free cross-check and it came out **tied**.
