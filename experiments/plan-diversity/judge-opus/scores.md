# Scores — "responsible doctor" MVP architecture (blind)

Rubric frozen in `rubric.md`. Nine metrics, 0–5. Every cell rests on a named type, section, or
mechanism in the design under review. All four designs are strong and structurally similar
(single citation chokepoint, `manager→subject` link, generic expected×reported join, tier-by-source);
scores turn on concrete differences in *enforcement depth*, *internal consistency*, and *machinery*.

## Matrix

| Metric | D1 | D2 | D3 | D4 |
|---|:--:|:--:|:--:|:--:|
| M1 Citation chokepoint (non-advice/non-inference by structure) | 5 | 4 | 5 | 4 |
| M2 `manager→subject(s)` single primitive | 5 | 4 | 5 | 5 |
| M3 Expected≠Reported, gaps JOIN-computed | 5 | 5 | 5 | 5 |
| M4 Provenance + confidence tier inseparable | 5 | 4 | 4 | 5 |
| M5 New pathway / source = one owner's change | 5 | 5 | 5 | 5 |
| M6 Pathway library as generic rails | 5 | 4 | 5 | 5 |
| M7 Scope discipline / no speculative machinery | 4 | 5 | 5 | 5 |
| M8 Day-zero public-seam vocabulary | 5 | 5 | 5 | 5 |
| M9 Domain model carries behavior (not anemic) | 5 | 4 | 5 | 4 |
| **Total (/45)** | **44** | **40** | **44** | **43** |

Load-bearing axes for this brief (rubric closing note): **M1, M3, M4, M5**.

---

## M1 — Citation chokepoint (non-advice / non-inference enforced by structure)

**D1 = 5.** Three *independent, build-time-checkable* enforcement legs (§3.1): (a) type visibility —
`Citation` has a private constructor exported only within `cite`; the public seam return type is
`Citation`/`Citation[]`, so "return advice" does not typecheck; (b) a CI dependency test that fails
the build if `egress` imports anything but `cite`, or if a template slot binds to a non-allowed
field; (c) schema — `citation.source_id`/`locator_id` NOT NULL FKs, a trigger rejecting a citation
with zero `citation_basis`, and **no text column** on the citation row, so "even a raw-SQL bypass
cannot store originated prose." The constructor `cite.make(kind, source_id, locator_id, report_ids[])`
"has no parameter of type `string` … cannot be called with a sentence." Inference is barred by a
single-writer `report` plus a *closed* predicate grammar (§1.4) with "no arithmetic over result
values," and a `CHECK (opens_process IS NULL OR kind='INSTRUCTION')` forbidding a RESULT from opening
a process. Deepest backstop of the four (reaches into the persistence layer).

**D2 = 4.** The Projection/Citation Mint is a genuine sole constructor: `Mint.project(Finding)→Citation`
with a package-private/sealed constructor (§3.1), a sealed `relation` enum with no `RECOMMEND` member
(§3.3), and the concrete non-bypass that "the Ledger engine's `Finding` is an internal type and is not
serializable to a client." Strong, but the enforcement is entirely type-level — no CI architecture
test, no denylist lint, and no schema/DB constraint are named; it rests on language visibility alone.
Fewer independent legs than D1/D3.

**D3 = 5.** Sole egress `CitationGateway` with a package-private `Citation` constructor and "no
advice-shaped field" (§3.1). Three independent legs plus extras: single egress + sealed type; rendering
is closed-catalog projection with the fitness test "delete every template that isn't a (source × state)
projection and the system still functions"; a **denylist lint over the seam surface** that fails the
build on `recommend/diagnose/advise/prescribe/infer` (§3.1.3, §6). Its strongest inference move is
type-level: `Origin` "has no `SYSTEM` member … there is no enum value the system is allowed to write"
(§1.1), making state-inference *unrepresentable*. §3.5 "Refuse, never coerce" makes "no valid citation"
a first-class outcome. Five boundary rules are stated as enforceable fitness tests (§2).

**D4 = 4.** Sole egress `Citation Gateway` with a sealed module-private constructor; `Gateway.cite`
"takes references, never content … no text parameter, no template engine, no LLM call" and REJECTs an
unresolvable `source_ref`/`state_ref` (§3.1) — a strong reference-only chokepoint. Inference is barred
by the single-writer Ingestion Port: "'the system infers state' describes code that does not exist"
(§0, §3.2). Enforcement is "by construction" (sealed ctor + reference resolution + single writer) but,
unlike D1/D3, no CI dependency test, denylist lint, schema constraint, or unrepresentable-enum is named
as a backstop. High 4.

## M2 — `manager → subject(s)` single primitive

**D1 = 5.** One `mandate(manager_id, subject_id, basis, …)` row; `basis ∈ {SELF,FAMILY,CLINICAL}` is
"an audit label only — **no code path branches on it**" (§1.1). `has_mandate` is called in "exactly
two places" (§4). Self is a self-edge, family/clinician are "three cardinalities of one table," and
multiple mandate-holders per subject "falls out for free as extra rows." The role label is fully inert.

**D2 = 4.** One `ManagerLink(manager, subject, role, scope)`; self = `ManagerLink(self, self)`; family
and clinical panels are "the same abstraction at different fan-out" (§4). One entity, one authorization
rule. Docked because `role` is not fully inert: "only a `CLINICIAN` link may attach a `DOCTOR_INSTRUCTION`
source" — capability is gated on the role label directly, the closest any design comes to a
role-conditional path (still one entity, so not a special case).

**D3 = 5.** One `Grant(manager_id, subject_id, scope, relation)`; `scope ∈ {READ<REPORT<MANAGE}` is an
ordered permission carried as data, and `relation ∈ {self, family_member, patient, …}` is "an open
label that changes nothing in logic" (§1.2). Self, family, and a 400-patient panel are stated as pure
cardinality (§4), with the explicit test "the code-path diff is empty." Permission (scope) and label
(relation) are cleanly separated; the label is inert.

**D4 = 5.** One `Link{role, scope}`; role `self|guardian|clinician` is "metadata; **never a code
branch**" and authorization is uniform — "every read and write … authorized by resolving a live `Link`
whose `scope` covers the operation" (§4). Role only tunes *default* scope; "it does not open a second
data path and does not change what the Gateway emits." The clinician's extra capability rides on scope
(a uniform capability check), not on a role branch, so the authorization path stays single.

## M3 — Expected ≠ Reported, gaps JOIN-computed

**D1 = 5.** Distinct modules `pathways` (rails) and `reports` (facts) that "never share a store"
(§5.1). The join (§5.2) is explicit pseudocode with `hits = Facts ∩ step.satisfied_by ∩ within(occ.window)`
described as "a relational join, not a hand-written check," with "no branch on subject, rail, publisher,
or example"; "gaps are the join's residue … never enumerated per example."

**D2 = 5.** Distinct owners `Pathway`/`RailStep` vs `ReportedItem` (§1.3/§1.4); the join is "one function
over `(RailStep.satisfied_by, ReportedItem)`" producing `Finding`s (§5.2). Gaps are computed
(DONE/DUE/GAP). Minor: the open-process→referral case is a *separate* coverage check (§5.3,
`open_process_key`) rather than folded into the main join, but it is still computed, not enumerated.

**D3 = 5.** `PathwayLibrary` (rails=data) vs `ReportedStore` (subject state), meeting only in the pure
`join : (Pathways, SubjectFacts, [ReportedState]) → [LedgerItem]` (§5.1), "total, deterministic, no I/O,"
with a 4-row classification table. "Gaps are the output of the join, never enumerated per example …
adding the well-baby schedule and the colon-screening schedule are the *same act*."

**D4 = 5.** Pathway Library vs `ReportedItem`s, "never merged at rest … meet only inside the
Reconciliation Engine, on read" (§5.1). Generic 4-step join (§5.2) with an `Absence` *first-class typed
value* so a gap is a well-formed `(source × state)` row. "Because gaps fall out of the join, adding a
new pathway needs no new gap logic."

## M4 — Provenance + confidence tier inseparable

**D1 = 5.** The citation row carries `source_id` (NOT NULL FK), `locator_id` (NOT NULL FK), and a `tier`
copied from the source, plus a trigger requiring ≥1 `citation_basis` (§1.6). Provenance is the most
*granular* of the four — not just a source but a `source_locator` with the verbatim excerpt (the exact
citable position). Tier is "a property of the source, assigned by `sources` at registration, never
computed downstream and never passed by a caller" (§1.2), with a coherent A/B/C ladder. Inseparability
is a schema fact.

**D2 = 4.** `confidence_tier` lives on `SourceType` so it "travels automatically with anything that
references a source," and a `Citation` *is* the source join — "remove them and there is no citation left
to emit" (§3.4). Inseparability is real (required `source_ref`). Docked because it names the fewest
*guards*: no NOT-NULL-at-storage constraint, no "copied, never recomputed" rule, and no equality check —
the guarantee rests on the type being a join, weaker than D1's schema FKs or D3/D4's explicit checks.

**D3 = 4.** Inseparability itself is excellent — non-null `source_ref` on `RailStep`, `LedgerItem`, and
`Citation` ("cannot exist without a non-null `source_ref` … a schema fact, not a convention," §1.5),
tier "copied, never recomputed" with the check `citation.tier == referencedSource.tier` (§5.2). But the
tier *concept it must carry is internally contradictory*: §1.1 declares the total order
`T1_GUIDELINE > T2_DOCTOR_INSTRUCTION > T3_PRESCRIPTION > T4_SELF_REPORT` (guideline outranks a doctor
instruction), while §5.3 states "the same expected step cited from a doctor instruction **outranks** it
cited from a general schedule." The two orderings are opposite. Because confidence-tier is the thing
that must travel with every flag, a self-contradiction in its ordering is a concrete defect on this
load-bearing axis — docked one point. (D1/D2/D4 all order the individualized clinician directive above
the population guideline, consistently.)

**D4 = 5.** `source_ref: SourceRef!` and `reported_ref: ReportedState!` are required on `Citation`;
`authorizing_source_ref` is NON-NULL on `ExpectedStep`; "an instantiated step whose `source_ref` does
not resolve is rejected before it reaches the join," and the Gateway stamps `confidence_tier` as a
non-optional field copied from the resolved source (§5.3). Tier is a coherent ordered set
(`clinician_directive > guideline > self_reported > uncoded`) consistent with §5.3's "doctor instruction
outranks a general schedule," and it even adds the `uncoded` tier for un-codable items.

## M5 — New pathway / source type = one owner's change

**D1 = 5.** Change table (§7): a new public pathway = "one rail document + one guideline registration in
`sources`," leaving ledger/identity/cite/egress/reports untouched; a new source *type* = "one
`sources.kind` enum value + one tier rule." A rail is data; "the ledger join, the citation constructor,
the mandate check, and the egress templates are written once and do not change when content changes."
Most detailed and honest change map of the four.

**D2 = 5.** "Adding a pathway = inserting rows" in the library, "touches nothing else" (§1.3); a new
source type = a `SourceType` registry row (§1.2); "join & Mint untouched" (§8). Clean, if the least
detailed.

**D3 = 5.** The sharpest *structural rationale* for exit 5: two separate open registries because "a new
source and a new pathway each [must] be one owner's change — and they are **different owners** (a source
ingester vs. a clinical library author)" (§2). `LedgerEngine`/`CitationGateway` "range over the closed
spine, not example content," so they "change almost never." Owner-separation is a first-class design
driver.

**D4 = 5.** §7 table: a new pathway = one `Pathway` in the Pathway Library; a new source class = "one
class + one adapter that normalizes to canonical `Source`/`ReportedItem` and registers a tier." Because
Reconciliation and the Gateway "see only canonical abstractions," the change "does not scatter across
the ledger, the account model, and the output layer."

## M6 — Pathway library as generic rails

**D1 = 5.** The rail grammar is the most fully specified: a *closed* predicate/matcher grammar (§1.4)
with enumerated atoms (`attr` comparisons, `reported`/`not_reported`, `report_kind`/`code`/`refers_to`
equality, comparators, ISO-8601 durations) and "no arithmetic over result values." Crucially,
INSTRUCTION/PRESCRIPTION sources are *compiled into the same rail schema* (one-step instruction rails),
so a guideline schedule, a well-baby schedule, and a doctor instruction all populate one rail model —
genuine genericity, and the closure doubles as the non-inference guarantee.

**D2 = 4.** `RailStep` is data with `applies_when`/`cadence`/`expects`/`satisfied_by` (§1.3), and "a
pathway is pure data." Docked because the grammar is sketched via a few example predicates
(`age_between`, `sex_is`, `has_risk_flag`; `once`/`every`/`by_age`) rather than a stated closed set, and
because the expected side is *less unified*: doctor instructions are `Source`s that "authorize or satisfy
individual steps but do not define general expectations," and the open-process case rides a separate
`open_process_key` rather than the same rail — so a structurally different (instruction-driven) pathway
does not slot into the same `RailStep` shape as cleanly as in D1/D3/D4.

**D3 = 5.** Rails are "pure data in a small declarative grammar (age/sex ranges, prior-item recency,
interval arithmetic) — **deliberately too weak to express 'looks like diabetes'**" (§1.5), a strong
statement that the abstraction is generic yet bounded. `code` is a namespaced open string so "new
clinical concepts need no schema migration." A `RailStep` carries `expects`/`gate`/`cadence`/
`plan_required`/`source_ref`.

**D4 = 5.** `ExpectedStep` is condition-neutral: `applicability` predicate + `cadence`
(`once|every|at(age)|conditional`) + `window` + `satisfied_by` [match_key] (§1.3), "pure data." Dual-role
registration (§1.4) folds a doctor instruction into the same step model as a Source authorizing a step,
so guideline and instruction pathways share one rail abstraction.

## M7 — Scope discipline / no speculative machinery

**D1 = 4.** §8 excludes the overview, inference, and future sources thoroughly, and none of those is
built. Docked because D1 carries the most *beyond-MVP apparatus* of the four for the same invariant set:
`content_hash` on every source, full row immutability with `superseded_by` pointers [A], `source_locator`
excerpt objects, same-transaction dual-registration, and a nightly recompute job (§1, §5.5). These serve
audit/verifiability but exceed what any stated exit criterion requires — D2/D3/D4 meet the same
guarantees with less machinery.

**D2 = 5.** The leanest design — "five nouns carry the whole product" (§1); §7 cleanly excludes the
overview, inference, EHR/lab integrations, and unbuilt source classes ("the *mechanism* to add them
exists … no such content is pre-built"). Nothing speculative is constructed.

**D3 = 5.** §7 explicitly excludes the overview and any inference ("`Origin` has no `SYSTEM` member —
inference is unbuildable"), and uniquely names and rejects a speculative *plugin runtime*: "the seam is
a *contract*, not a plugin runtime … more adapters now would be speculative," shipping "a fixed trio."
Its extra apparatus (append-only, golden/fitness tests) is testing discipline serving the in-scope
invariant, not runtime features.

**D4 = 5.** §8 counts overview, inference, auto-coding/NLP, extra source types, and cross-subject
analytics as out and builds none; "Each is a future adapter (§7), deliberately not pre-built." The only
modest additions (a `Party` layer, an `uncoded` tier) serve in-scope needs.

## M8 — Day-zero public-seam vocabulary

**D1 = 5.** The most exhaustive seam vocabulary (§6): closed enumerations per module, a namespaced item-
code list with an empty external-code slot, the full rail grammar atoms, citation kinds, *and* explicit
endpoint signatures (`GET /subjects/{id}/ledger → Citation[]`). A stated denylist of forbidden words
("recommend, advise, diagnose, suspected …") whose absence "is the enforcement." No implementation type
crosses a seam ([A] keeps table DDL out of the model).

**D2 = 5.** §6 nouns + verbs tables in a closed vocabulary; `getLedger` "returns only `Citation[]` …
there is no endpoint that returns advice … because no such type exists to return." Domain types only;
`ConfidenceTier` is an enum, not a bare number. Complete, if less granular than D1/D3.

**D3 = 5.** §6 is the cleanest *closed-vs-open* separation: closed sets (`Origin`, `source_class`,
`ConfidenceTier`, `relation`, template catalog) are "the stable contract," while open vocabularies
(`code`, `pathway_id`) are "where growth is absorbed … no schema change." Verbs listed; a denylist of
words "permanently absent." No implementation type at a seam.

**D4 = 5.** §6 lists nouns, all enums, and verbs; notes `LedgerItem` is internal; states "`Gap` and
`Nudge` are **not** separate types" (a Gap is a `Citation` with a status). Denylist of what "the seam may
not speak." Domain types only.

## M9 — Domain model carries behavior (not anemic)

**D1 = 5.** Invariants live *in the data layer itself*, the strongest anti-anemic signal: `CHECK
(opens_process IS NULL OR kind='INSTRUCTION')` forbids a RESULT opening a process; a trigger rejects a
citation with zero basis; NOT NULL FKs and the absent text column make an invalid citation
unstorable. Rules are explicitly "owned by `reports`," tier owned by `sources`, and `cite.make` enforces
the citation invariant at construction — behavior is co-located with the data it guards, and the schema
rejects illegal states regardless of calling code.

**D2 = 4.** Behavior is real (`Mint.project` refuses to originate; "the Ledger can *compute* a gap; it
cannot *emit* one") but concentrated in two behavior modules (Ledger engine + Mint) over five data
`nouns`; per-type rule ownership is thinner than D1/D3, and invariants like tier-immutability are stated
as properties rather than enforced by the types/stores themselves.

**D3 = 5.** Invariant behavior is distributed to the stores/types that own each rule:
`ReportedStore.write` "rejects `origin = SYSTEM` or null author" (boundary rule 3); "only `SourceRegistry`
may set `tier`; engine and gateway read but never write it" (rule 5); a `RailStep` "cannot exist without
a non-null `source_ref`"; the Gateway *refuses* rather than coerces (§3.5). Enforcement is spread across
the owners rather than pooled in one engine.

**D4 = 4.** Strong behavioral constraints exist — the module table's explicit "May NOT do" column
(Reconciliation "may NOT construct a `Citation`, write prose or state"), the single-writer Ingestion
Port, and reject-before-join (§5.3). But the core domain records (`Party`, `Subject`, `Source`,
`ReportedItem`) are largely data, with the behavior concentrated in Gateway + Reconciliation + Ingestion;
per-type rule ownership is closer to D2 than to D1/D3 (e.g., it does not use `Origin`-without-`SYSTEM`;
inference is barred procedurally by the single writer).

---

## Per-metric leaders

- **M1 (chokepoint):** **D1 and D3 lead.** Both stack multiple independent, build-time-checkable legs
  (D1: private ctor + CI dependency test + schema trigger/no-text-column; D3: sealed type + denylist lint
  + fitness tests + `Origin`-without-`SYSTEM`). D2 and D4 enforce by type/visibility and single-writer
  alone — strong but with no CI/schema/lint backstop.
- **M2 (single primitive):** **D1, D3, D4 lead.** All make the role/relation label inert and multi-subject
  pure cardinality; D2 trails only because `role` directly gates who may attach a `DOCTOR_INSTRUCTION`.
- **M3 (join):** **Four-way tie at 5.** All separate the two sides into distinct stores and compute gaps
  from one generic pure join; D4's first-class `Absence` type and D1's "relational join, not a hand-written
  check" are the crispest, but none enumerates per example.
- **M4 (provenance+tier):** **D1 and D4 lead.** D1 has schema NOT NULL FKs + verbatim-locator granularity;
  D4 has required refs + reject-before-join + a coherent ordered tier. D3 is inseparable but carries a
  self-contradictory tier ordering (§1.1 vs §5.3); D2 names the fewest guards.
- **M5 (one-owner change):** **D3 leads on rationale** (two registries *because* the two changes have
  different owners); D1/D2/D4 all satisfy it, D1 with the most complete change map.
- **M6 (generic rails):** **D1 leads** (fully-specified closed grammar; instructions compiled into the
  same rail schema); D3 and D4 close behind; D2 trails (grammar by example; instructions don't become
  rails; open-process on a side channel).
- **M7 (scope):** **D2, D3, D4 lead** (lean / explicitly anti-speculative); D1 carries the most beyond-MVP
  apparatus (content_hash, immutability, nightly recompute).
- **M8 (vocabulary):** **Four-way tie at 5** — all state an explicit day-zero vocabulary in domain types;
  D1 is the most exhaustive, D3 the cleanest closed-vs-open split.
- **M9 (behavior):** **D1 and D3 lead** — D1 pushes invariants into the schema (CHECK/trigger/NOT NULL);
  D3 distributes rule-enforcement to the owning stores/types. D2 and D4 concentrate behavior in a few
  engine/gateway modules over more data-shaped records.

## Overall reading

The per-metric picture is primary. **D1 and D3 are co-leaders (44 each); D4 is a very close third (43);
D2 is the weakest of a strong field (40).** The four are close because they converge on the same
correct spine (sealed single-egress citation gateway, one `manager→subject` link, a generic pure
expected×reported join, tier-by-source). Differences are in enforcement depth and internal consistency,
not in kind.

**On the load-bearing axes (M1, M3, M4, M5), D1 is the strongest: a clean 5 on all four.** D3 ties D1 on
total but has a load-bearing blemish D1 does not — its confidence-tier ordering contradicts itself
(§1.1 ranks guideline above doctor instruction; §5.3 says the opposite), dropping it to 4 on M4. D3's
only edge over D1 is on a *secondary* axis (M7 scope-minimality: D1 carries more beyond-MVP machinery).
So the total tie resolves, on the axes the brief weights most, in D1's favor — with the honest caveat
that D1 pays for its depth with extra apparatus. If a reviewer values minimality and the elegance of
making inference *unrepresentable* (D3's `Origin`-without-`SYSTEM`) over schema-level defense-in-depth,
D3 is the pick; the two are genuinely a coin-flip apart.

**D4** would be my pick for the cleanest *single* reading of the design: it is a 5 on all four
load-bearing axes except M1, where it loses only for lacking the CI/lint/schema backstops that D1/D3
carry, and it contributes the nicest single idea (the first-class `Absence` type that makes a gap a
well-formed citation). Its 43 is one enforcement-backstop and one behavior-distribution point behind the
leaders.

**D2** is the leanest and most readable, and wins M7 outright, but its minimalism costs it on the axes
that matter here: the thinnest citation-chokepoint enforcement (M1, type-visibility only), a role that
gates capability (M2), the fewest tier-inseparability guards (M4), and the least-unified rail model where
doctor instructions never become rails (M6). No design *fails* a non-negotiable, but D2 sits at the
bottom of a strong pack precisely because it under-invests in structural enforcement.

**Watch-out on totals:** the D1/D3 tie at 44 is exactly the case the rubric flags — equal totals, but D3
loses a load-bearing axis (M4) that D1 holds, while leading only on a secondary one (M7). Read the axes,
not the sum.
