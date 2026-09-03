# Blind judging — "Responsible Doctor" MVP architecture — Design R vs Design S

Scored against the frozen rubric at `/tmp/aims/experiments/plan-diversity/judge-sonnet/rubric.md`,
using the brief at `/tmp/aims/experiments/plan-diversity/brief/brief.md`. Contestants are anonymized;
no claim is made about how either was produced.

## Score matrix (0–5 per metric)

| Metric | R | S | Leader |
|---|---|---|---|
| M1. Citation-chokepoint enforcement | 5 | 5 | tie |
| M2. `manager → subject(s)` unforked primitive | 5 | 4 | **R** |
| M3. Expected/reported separation, generic join | 5 | 5 | tie |
| M4. Provenance/tier inseparable from output | 5 | 5 | tie |
| M5. Extensibility — one owner's change | 4 | 5 | **S** |
| M6. Scope discipline — no speculative build | 5 | 4 | **R** |
| M7. Domain model carries real behavior | 5 | 5 | tie |
| M8. Day-zero vocabulary named | 5 | 5 | tie |
| **Total** | **39/40** | **38/40** | R by 1 |

---

## Per-metric justifications

### M1 — Citation-chokepoint enforcement — R: 5, S: 5 (tie)

**R (5):** `Citation` and `LedgerEntry` have "module-private constructors; the only way to obtain
instances is `Ledger.view(handle) -> list[LedgerEntry]`" (§4, lock 1). Its two components are each
minted by exactly one other privileged site: `SourceRef` "invocable only by `Record` and `Rails`"
and `ReportedBasis` "minted ONLY by `Record.evaluate`." `Surface`'s only subject-output dependency
is `Ledger.view`; its access to `Record`/`Accounts` is write-only (§4, lock 3). The design states
explicitly this holds for a doctor user too ("no clinician-mode API").

**S (5):** `Citation` is "declared in the shared vocabulary as an *opaque* type; its constructor is
sealed (package-private/internal) to the Ledger module, callable only from the join function" (§3.1).
The API's read surface "returns `LedgerView` and nothing else; there is no second endpoint family
that could emit medical content" (§3.3). Both halves (`SourceExcerpt`, `ReportedExcerpt`) are
required non-null at that one constructor. Identical structural guarantee to R, stated with equal
rigor and an explicit doctor-user carve-out ("a doctor is just a Manager... no privileged path").

Both name one sealed mint with no alternate construction site; scored identically.

### M2 — `manager → subject(s)` as one unforked primitive — R: 5, S: 4

**R (5):** `Accounts.Grant(principal_id, subject_id, scope: {View, Report, Administer})` is the
entire relation. "Self-management = `Grant`(own principal, own subject, `Administer`)" — the same
row type for self, family, and clinician cases, distinguished only by cardinality: "A person alone:
one self-grant. A parent with three children: four grants. A doctor with 200 patients: 201 grants.
Same rows, same queries, same code path" (§5). The design states explicitly: "There are no roles
('caregiver', 'clinician') — the data model never branches on who a manager socially is." No field
on `Grant` carries a role/relation label at all.

**S (4):** Also one `Grant` row per manager-subject pair used identically for self/family/clinician
in the join and query logic, and explicitly "no code path switches on it in the MVP" — a genuinely
unforked primitive in terms of behavior. But `Grant` itself is defined as `{manager_id, subject_id,
relation: ⊕{Self, Family, Clinician}, granted_at}` (§1.1) — a role-specific enum bolted directly onto
the shared manager↔subject edge to distinguish the very cases the brief says must not be
distinguished. The rubric's 5-bar requires "nothing role-specific is bolted onto the subject or
manager entity to distinguish them"; S's own text concedes the field's purpose is exactly that
distinction, deferred rather than absent: "(Assumption: differentiated permissions per relation are
post-MVP; the field exists so the day the product needs them...)" (§1.1). The primitive is still
single and unforked in *code*, but not in *data shape* — hence 4, not 5.

### M3 — Expected/reported separation with a generic join — R: 5, S: 5 (tie)

**R (5):** `Rails` (`PathwayDef`/`StepRule`, data files, schema-validated) is wholly separate from
`Record` (`ReportedItem` journal). `Ledger.view` joins them by one mechanical key: "`(ActivityCode,
occurred_on ∈ window)` and nothing else" (§7) — the same procedure "for every rail, so gaps are
computed, never enumerated per example." The change table confirms a new pathway is "one new
`PathwayDef` data file" with the join untouched.

**S (5):** `Rails` (`PathwayDefinition`/`StepTemplate`/`Predicate`, data) is wholly separate from
`File` (`ReportedItem` log); "Expected and reported never mix at rest... They meet only inside this
function, at read time" (§5). The join (§5) is a single generic procedure over `expected`/`reported`
lists using `satisfied_by` matching, applicable to any pathway without per-pathway branches.

Both name a genuinely generic, pathway-agnostic diff mechanism owned by one module; tied at 5.

### M4 — Provenance/confidence tier structurally inseparable — R: 5, S: 5 (tie)

**R (5):** `SourceRef = (source_id, SourceKind, tier, label)` — "no tier parameter exists — the
factory computes tier via `ConfidenceTier.of` internally, so tier and provenance are one value,
never split" (§2). `Citation.source: SourceRef` is a required, non-optional field, and `Citation`
itself is a required field of every `LedgerEntry` — "tier is a field of `SourceRef`, `SourceRef` a
field of `Citation`, `Citation` a required field of every entry" (§4, lock 1).

**S (5):** `tier_of(class: SourceClass) -> ConfidenceTier` is "the ONLY place tiers are assigned"
(§1.2), "never stored as an independent, editable field anywhere else." `Citation{source:
SourceExcerpt, reported: ReportedExcerpt}` — "BOTH fields required & non-null. Constructor SEALED
inside Ledger" (§1.5). Tier "is derived from the source at excerpt time via `Sources.tier_of` — one
owner, no drift" (§5).

Both make tier a computed, non-nullable, structurally required component of the sole output type;
tied at 5.

### M5 — Extensibility: one owner's change — R: 4, S: 5

**S (5):** A new source type is explicitly "one change in Sources: a new `SourceClass` variant, its
tier, and its adapter" (§1.2) — all three sub-changes land inside a single named module, `Sources`,
which owns `Source`, `SourceClass`, the tier mapping, *and* the `SourceAdapter.ingest(raw)` interface
together (module table, §2: "`Sources` | ... | `Source`, `SourceClass`, tier mapping, ingest
adapters"). A new pathway is "adding one `PathwayDefinition` record" (§1.4). Both extension axes are
each contained to one module's ownership.

**R (4):** A new pathway is equally clean — "adding a reviewed data file; no code change" (§6). But a
new source *kind* is not contained to one module: the change table lists it as "`SourceKind` member +
one line in `ConfidenceTier.of` (vocabulary, reviewed) + one `ExpectationProducer` implementation in
the module that backs it" (§7) — a vocabulary-kernel edit *plus* a separate new implementation in
whatever module ends up backing the new source. R itself flags that this is deliberately not a
registry: "There is no plugin registry and no dynamic discovery — a hand-maintained list of two"
(§6), and a third source class "forces a new-subtype conversation at this seam." That is a real,
named extension point, but it spans two owners (vocabulary + a producer module) rather than S's
single `Sources` module — hence 4, not 5.

### M6 — Scope discipline: no speculative build — R: 5, S: 4

**R (5):** §9 "Explicitly out of the MVP" excludes the overview, all inference, non-MVP source types,
and states the exclusion is a *shape* exclusion — "no interface, enum slot, nullable column, or
reserved hook exists 'for when we add it.'" A scan of R's types finds no field whose only purpose is
a stated future need; `RiskFlagCode`, `UNCODED`, `ReportedOpenProcess` etc. are all load-bearing for
Pillar-1 behavior today.

**S (4):** §7 "Explicitly out of the MVP" is comparably disciplined for the overview/inference/interop
axes. But `Grant.relation: ⊕{Self, Family, Clinician}` (§1.1) is a field the design's own text says
exists *for a feature not in the MVP*: "the field exists so the day the product needs them [differentiated
permissions]..." — i.e., a reserved hook, which is precisely what the rubric's 0-anchor calls
"padding the architecture with speculative generality 'for later.'" This is a narrow, explicitly
self-admitted instance rather than a systemic pattern (the rest of S's scope discipline, e.g. §7's own
list, is otherwise as tight as R's), so it costs one point rather than more.

### M7 — Domain model carries real behavior — R: 5, S: 5 (tie)

**R (5):** Invariants are attributed to types/modules, not external services: `Citation`'s
constructor is "module-private" and its assembly rule is stated as a type-level fact ("There is no
way to construct one from thin air"); `Record.evaluate` "decides matching... and mints the
`ReportedBasis`" — behavior owned by `Record`, not read out of it by another module; "the pathway
knows its own rules — nothing outside Rails ever opens a definition" (§6).

**S (5):** `ReportedItem`'s source requirement is "enforced by its constructor, not by convention"
(§1.3); `Citation`'s constructor is "sealed... to the Ledger module" (§3.1); `Sources.tier_of` is
the sole tier-computing function, owned by `Sources`; `Ledger.view` is presented as the module's one
owned join operation (§5), consistent with "Tell, Don't Ask" (§2): "API asks `Ledger.view(grant,
as_of)`, never 'give me the expected items and the file so I can join them myself.'"

Both attribute the citation invariant and the gap computation to named owning types/modules with
constructor-enforced rules rather than external "service does X to record" prose; tied at 5.

### M8 — Day-zero vocabulary named — R: 5, S: 5 (tie)

**R (5):** §2 gives an explicit kernel-vocabulary table (Type | Definition | Rules it owns) naming
`PrincipalId`, `SubjectId`, `ActivityCode`, `RiskFlagCode`, `SourceKind` (closed 3-member enum),
`ConfidenceTier` (2-tier ordered enum), `SourceRef`, `DateWindow`, `LedgerStatus` (5-member closed
enum), `LangText`. §8 restates the closed, normative public-seam vocabulary plus a 3-member error
vocabulary.

**S (5):** §6 "Day-zero vocabulary" enumerates the closed domain-type set (`ManagerId`, `SubjectId`,
`SourceId`, ..., `SourceClass`, `ConfidenceTier`, `ClinicalCode`, `Citation`, `GapKind`,
`LedgerEntry`, `LedgerView`), foundational primitives, and a 4-member error vocabulary, explicitly
naming closed enums and their owners ("`SourceClass`, `ConfidenceTier`, `GapKind`, `CodeSystem`...
extending one is a deliberate, versioned vocabulary change with a single owner").

Both give an explicit, closed, named vocabulary list with enum values/shapes as the brief instructs;
tied at 5.

---

## Overall reading

**Per-metric first.** Six of eight metrics are genuine ties (M1, M3, M4, M7, M8, plus the shared
strength of both designs' citation-mint discipline) — both designs independently converge on the same
core solution shape the brief all but dictates: a sealed `Citation` mint owned by one join module,
expected/reported as separate aggregates joined generically, tier welded to source at construction,
and an explicit closed vocabulary section. The two metrics that separate them point in opposite
directions and trace to one structural choice each:

- **M2 and M6 favor R**, and both trace to the *same* fact in S: `Grant.relation: ⊕{Self, Family,
  Clinician}` is a role-labeling field bolted onto the shared manager→subject edge, which S's own
  text says is there for a post-MVP feature. It doesn't fork any code path today, but it is both a
  role-specific field on the primitive the brief demands stay undifferentiated (M2) and a
  self-admitted "for later" hook (M6) — the exact shape both metrics' 0-anchors warn against, present
  here in a mild, single-field form rather than systemically.
- **M5 favors S**, tracing to a different fact: S consolidates a new source type's tier, class, and
  ingestion adapter inside one named module (`Sources`), while R's own change table shows a new source
  kind touching both the shared vocabulary kernel and a separate producer-module implementation —
  R explicitly disclaims a registry ("no plugin registry and no dynamic discovery... a hand-maintained
  list of two"), which is honest about the tradeoff but is measurably less single-owner than S's
  `Sources` module.

**Load-bearing axes.** For this brief, M1 (chokepoint), M3 (generic join), and M4 (tier inseparability)
are the metrics closest to the product's actual non-negotiable ("never infers, never originates
advice") — both designs are equally rigorous there, which is the more important finding than the final
score gap. M2 and M5 are the second-order structural-hygiene axes (how clean is the primitive, how
contained is extension), and they're where the designs actually diverge — in opposite directions,
by the same margin.

**Total as secondary glance:** R 39/40, S 38/40.

**Verdict.** The two designs are essentially level in engineering quality — both fully satisfy the
brief's hard non-advice invariant with equal structural force. R is marginally cleaner on primitive
hygiene and scope discipline (no bolted-on role field anywhere in `Accounts`); S is marginally cleaner
on extension containment (one `Sources` module owns everything about a source type, versus R's split
between vocabulary kernel and producer module). Neither gap reflects a difference in rigor or
seriousness of design — both would pass a structural audit against every exit criterion in the brief.
If forced to pick, R is the very slightly stronger design on balance (39 vs 38), but the honest
reading is a near-tie decided by one field each design happens to add or omit, not by any gap in
how thoroughly either team reasoned through the citation invariant.
