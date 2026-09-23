# Judging report: entitlements, designs X and Y

Judge disposition: YAGNI / simplicity. I looked hardest for types, layers and seams that no stated requirement pays for.
Instrument: `rubric/assessment-form.md` (rows 1–17). Its rows, sub-checks, severity and profile follow `rubric/measurement.md`.
Row numbers below are **form** rows. Form row 13 is *functional correctness*; it is not design-principles §13, which covers performance.
Scope of evidence: for X, the architecture is `design.md`. `proposal.md`, `specs/` and `tasks.md` are method artifacts. I used them only where they state what the design promises, and never to credit structure. For Y, the whole file is the architecture record. I did not read `goals.md`, which Y cites but which is not in the blind set.

---

## Step 0: fixed inventory (from the product cards and the hidden spec; the same for every design)

**Rules (R)**
- R1: allow iff any of U's roles grants (A,R).
- R2: otherwise deny (default deny).
- R3: users hold roles; roles hold (action, resource) permissions.
- R4 (stage 2): an explicit deny from any of U's roles overrides any allow.
- R5 (stage 2): a grant on a group applies beneath it, and a deny anywhere on the path wins.
- R6 (stage 2): a grant applies only inside its window `[from,to)`, judged against a *supplied* now.
- R7 (stage 2): stage-1 answers are unchanged where the new features are absent.

**Change axes (X)**
- X1: effects and precedence (deny).
- X2: resource hierarchy.
- X3: time validity.
- X4 (plausible unstated variant): a different model source or reload.

**Acceptance cases (C)**
- Stage 1:
  - C1: a single role grants → ALLOW.
  - C2: one of several roles grants → ALLOW.
  - C3: the role lacks the action → DENY.
  - C4: unknown user → DENY.
  - C5: same action on another resource → DENY.
  - C5b: malformed question → error, never ALLOW.
- Stage 2:
  - C6: role X allows and role Y denies → DENY.
  - C7: allow on `finance` plus deny on `doc-42` → DENY for doc-42, ALLOW for sibling doc-43.
  - C8: deny on `finance` plus allow on `doc-42` → DENY (card: "a deny anywhere on the path still wins").
  - C9: an expired deny plus a permanent allow → ALLOW.
  - C10: an in-window deny beats an allow.
  - C11: the window end is exclusive.
  - C12: now is supplied and the clock is never read.
  - C13: instants are compared as instants (the design-principles §1 "time" edge).

**Applicability** (the same for all four designs)
- Rows 1–14 apply.
- Row 15 (testability) is N/A: it is code-leaning, and these are pure designs.
- Row 16 (performance) is N/A: no performance requirement is stated.
- Row 17 (security) is N/A: the product states no trust boundary (in-process library, single process). Failing closed is scored in row 13.

### Fixed sub-checks per row (the same list for every design; score = round(10 × passed / applicable), then min(score, ceiling))

| row | sub-checks |
|---|---|
| 1 TDA/LoD | a. the rule runs in, or is told to, the holder of its data · b. no reach-through chains · c. one call on one object yields the answer · d. no module reads another's private fields |
| 2 calibration / concept fit | a. inbound seam types are generic and complete · b. outbound type is exactly the domain answer · c. concept fit (no inert stand-in) · d. peers share one altitude |
| 3 ISP | a. no client depends on methods it does not use · b. core importable without the edges · c. construction and query are not forced onto one client beyond need |
| 4 primitive obsession | a. rule-bearing concepts are typed internally · b. no anonymous clump at a public seam where a named type is due · c. identifiers have one owned rule · d. time is a typed value (N/A at stage 1) |
| 5 anemic model | a. the central object owns the decision behaviour (no service over a data bag) · b. value types own their own rules · c. invariants are enforced where the data is created |
| 6 cohesion / coupling / OCP | a. no feature envy · b. no shotgun surgery for a foreseen change · c. acyclic dependencies, pointing to the stable side · d. OCP: the foreseen change extends at a seam |
| 7 leaky abstractions | a. boundary types are domain or stdlib types · b. own error types, one per handling · c. representation hidden · d. implementation exceptions translated |
| 8 SRP | a. one reason to change per module or class · b. no God object · c. functions do one thing at one altitude |
| 9 one owner | a. each stated rule has one home · b. all paths funnel through it · c. model invariants have one construction path |
| 10 DRY | a. one home per fact · b. no duplicated validation · c. no wrong abstraction forcing unrelated things together · d. no parallel representations of one concept |
| 11 naming / failure | a. intention-revealing names · b. errors in the consumer's terms · c. no surprising API behaviour · d. failures are loud, never a silent allow |
| 12 YAGNI / subtractive | a. every module answers to a stated requirement (no invented edge or feature) · b. no hook for an unrevealed change · c. no guard, type or rule that owns nothing present · d. no dead or retained-unused code · e. minimal granularity (no lazy module or class) |
| 13 correctness | stage 1: C1, C2, C3+C5, C4, C5b (5 checks) · stage 2: C6, C7 (down only), C8, C9–C11, C12, R7, C13 (7 checks) |
| 14 state | a. model immutable, inputs copied · b. queries pure (no clock or global state) · c. replacement is atomic (no torn reads) · d. no global mutable state |

Severity maps to ceiling and weight as follows: none → 10, ×1; S1 → 8, ×1; S2 → 7, ×2; S3 → 5, ×4; S4 → 2, ×8.

---

## 1. D1: first-round design

### X-stage-1

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 10 | — | Callers make one call: `svc.check("bob", "write", "doc-42")`. There are no chains. The pull of `roles_of`/`grants_of` into `DecisionService` is charged in row 5 and not deducted again here. |
| 2 | Calibration / concept fit | Y | 10 | — | `roles: Mapping[str, Iterable[tuple[str, str]]]` in, `class Decision(Enum): ALLOW, DENY` out. Deny-as-absence is the right concept at stage 1 ("There are no deny rules"). |
| 3 | ISP | Y | 10 | — | A caller depends only on `check`. There are no edges. |
| 4 | Primitive obsession | Y | 10 | — | `Permission` is `@dataclass(frozen=True, slots=True)`. The id aliases are `str`, and one rule (non-empty `str`) governs them (row 10 notes where that rule is written). |
| 5 | Anemic model | Y | **7** | S2 | 2/3. Sub-check a fails. The model is by design "**the data, with no policy**… It does not validate", and the rule lives in a separate service that pulls the model's state: `ALLOW if any(wanted in model.grants_of(r) for r in model.roles_of(user)) else DENY`. That is a data bag plus a manager, and it is the design's organising split (D6), not a one-off, so it is S2. (b holds: `Permission` owns identity. c holds: the builder is the sole creator.) |
| 6 | Cohesion / OCP | Y | 10 | — | "Dependencies point one way: building -> model <- decision." The feature envy is charged in row 5. |
| 7 | Leaky abstractions | Y | **8** | S1 | 3/4. Sub-check c fails. The public, re-exported `EntitlementModel` exposes its normalised indexes (`assignments: Mapping[...]`, `grants: Mapping[...]`) and `roles_of`/`grants_of` to every caller. They exist only for `decision.py`, and they invite a second implementation of R1 outside it. Errors are the module's own types: `ModelValidationError` / `InvalidRequestError`. |
| 8 | SRP | Y | 10 | — | Five small modules, each named for one concern (model / building / decision / errors / surface). |
| 9 | One owner | Y | 10 | — | `build_model` is "the only entry to a model", and the any-grant rule sits only in `check`. |
| 10 | DRY | Y | **8** | S1 | 3/4. Sub-check b fails. The identifier rule is written twice. `build_model` enforces "ids, actions, and resources are non-empty `str`" and `check` enforces "validate request args (non-empty str) else raise InvalidRequestError". The two are identical as specified, so no reproducing divergence exists; it is a knowledge duplication only, hence S1. |
| 11 | Naming / failure | Y | 10 | — | `Decision.__bool__` raises "so `if service.check(...)` cannot silently treat DENY as truthy". Failures are loud. |
| 12 | YAGNI | Y | 10 | — | a: "There is no CLI… nothing calls for a CLI", and there is no file format. b: the `DecisionService`/model split (D6) serves axis X1, which stage 2 later used, so by the §7 falsifier it is earned. c: `ValidationIssue` is earned by "lists every invalid entry", and `__bool__` by the truthiness trap. d, e: nothing is dead or lazy. |
| 13 | Correctness | Y | 10 | — | 5/5. Cases C1–C5b are all satisfied by `any(...)` over total lookups ("an unknown key returns an empty frozenset"). The empty-action case raises. |
| 14 | State | Y | 10 | — | "wrapped in `types.MappingProxyType` over private dict copies". The check is pure. A check "always sees one consistent model". |
| 15 | Testability | N/A | — | — | code-leaning; N/A on a design |
| 16 | Performance | N/A | — | — | nothing stated |
| 17 | Security | N/A | — | — | no trust boundary stated |

**Profile X-1:** weights are 11×1 + 2 + 1 + 1 = 15, and Σ = 110 + 14 + 8 + 8 = 140.
**grade = 9.33 · worst = 7 · (#S3,#S4) = (0,0) · gate = CLEAR**

### Y-stage-1

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 10 | — | `role.grants(p)` is told. `_Role` is "Called only from `decide`, which never reads `permissions` itself". |
| 2 | Calibration / concept fit | Y | 10 | — | The §2.1 table shows `decide(user: str, action: str, resource: str)` in and `Decision`, "two members, no reason", out. `_Role` has no inert `name` field. |
| 3 | ISP | Y | 10 | — | The public surface is exactly `{decide}`, and "`import entitlements` never loads json". |
| 4 | Primitive obsession | Y | 10 | — | `_Permission` and `_Role` are internal types. The identifier rule has one owner, `_identifier`. The seam pair `(str, str)` is the card's own concept, and X uses the same pair. |
| 5 | Anemic model | Y | 10 | — | `EntitlementModel` "owns the grant rule". `_Role.grants` owns role-level membership. |
| 6 | Cohesion / OCP | Y | 10 | — | `__main__ → cli → json_file → model` is acyclic and points to the core. |
| 7 | Leaky abstractions | Y | 10 | — | "`_Permission`, `_Role` and the internal maps never" cross a seam. `ValueError` is translated "with `raise … from`". |
| 8 | SRP | Y | 10 | — | There is one core module, argued from one change reason, plus two edges. |
| 9 | One owner | Y | 10 | — | §7 "Where each rule lives" gives one owner per rule. The constructor is "the only way to make one". |
| 10 | DRY | Y | 10 | — | `_identifier` is used by "constructor and `decide`, the only two entries of raw strings". |
| 11 | Naming / failure | Y | 10 | — | Messages speak the caller's concept: "`action must be a non-empty string, got ''`". |
| 12 | YAGNI | Y | **6** | S2 | 3/5. **a fails (S2):** two edge modules plus `__main__`, a JSON file format, a duplicate-key hook and CLI exit-code semantics ("A7 — a repeated key in the model file is rejected", "A8 — CLI exit codes: 0 allow, 1 deny, 2 error"). No stage card asks for any of these. The substrate only *permits* "a small CLI"; nothing requires it. The core is untouched, so the cost is local rather than structural: S2. **c fails (S1):** there is defensive machinery against a threat nobody stated in an in-process library. It includes "The threat is a subclass whose `__eq__`/`__hash__` could make a question match a grant", normalization via `str.__str__`, and phase-1 step 4 ("two keys that normalize to the same exact string… are rejected"). `StrEnum` members already hash and compare as their strings, so the normalization only pays against a hostile `str` subclass. (b, d, e pass. There is "no `ModelSource` protocol today", no holder, and `_Role` owns the role clause, which counts as small but earned.) |
| 13 | Correctness | Y | 10 | — | 5/5. The §3.4 case table covers C1–C5. The question is parsed before lookup, so `decide("nobody", "", "doc")` "must raise". |
| 14 | State | Y | 10 | — | The model is immutable through `__slots__` and `MappingProxyType`. There are "No torn reads, by construction". |
| 15 | Testability | N/A | — | — | code-leaning |
| 16 | Performance | N/A | — | — | nothing stated |
| 17 | Security | N/A | — | — | no stated boundary. The CLI file input is self-introduced and is scored under row 12. |

**Profile Y-1:** weights are 13×1 + 2 = 15, and Σ = 130 + 12 = 142.
**grade = 9.47 · worst = 6 · (#S3,#S4) = (0,0) · gate = CLEAR**

**D1 verdict: no clear advantage.**
- Y leads on grade by 0.14. X has the better worst chapter (7 against 6).
- The two designs fail opposite halves of the simplicity question:
  - X has the leaner scope: no CLI, no file format, no anti-subclass machinery. But its core is a data bag with public getters and a separate decision service.
  - Y has the tighter core: one object owns the rule, and nothing is exposed. But it adds two unrequested edges and a hostile-input rule set.
- Sensitivity: if Y's edges are graded S1 (the substrate does sanction "a small CLI"), Y-1 = 9.71. If X's anemic split is graded S1, X-1 = 9.50.
- The lead flips with a single severity call, so it is noise, not an advantage.

---

## 2. D2: change absorption

### Survival classification

**X (stage-1 names → stage 2)**

| stage-1 component / seam | class | evidence |
|---|---|---|
| `EntitlementModel` + its query seam to the decision (`roles_of`/`grants_of`) | **reopened** | The stored index changes from `grants: Mapping[RoleId, frozenset[Permission]]` to "`grants: Mapping[RoleId, Mapping[Permission, frozenset[Grant]]]`". The decision now uses new queries `grants_for`/`lineage`. `grants_of` "now returns the role's permissions that have an ALLOW grant with no window… It is not used by the decision." |
| `DecisionService` (`decision.py`) | **reopened** | Stage 1: "Owns: request validation, the any-role-grants rule, and deny by default". Stage 2: "The service owns steps 1-3" and "The decision rule moves into a small pure combining function". |
| `Decision` enum | **reopened** (trivial, module boundary only) | "`Decision` moves there from `decision.py`" into the new `outcome.py`. |
| `Permission` | survived | "`Permission` is unchanged." |
| id aliases (`UserId`, `RoleId`, …) | survived | still used (`RoleId` in the new index) |
| `build_model` / `building.py` (and the build seam) | extended | "gains a `parents=` argument and accepts `Grant` entries alongside stage-1 tuples"; the new checks are "added to the stage-1 rules" |
| `check(user, action, resource)` seam | extended | "gains a keyword-only `now`"; "Existing callers are source-compatible." |
| `errors.py` | extended | "Stage 2 adds `EvaluationInstantRequired(InvalidRequestError)`" |
| `__init__` surface | extended | "Re-export `Effect`, `Window`, `Grant`, `allow`, `deny`…" |

**X reopened + discarded = 3 + 0 = 3.** Two of these are substantive (the model and the decision service). The third is a trivial relocation.

**Y (stage-1 names → stage 2)**

| stage-1 component / seam | class | evidence |
|---|---|---|
| `_Permission` | **discarded** | "`_Permission` is removed." |
| `_Role` + the `decide → _Role.grants` internal seam | **reopened** | "`_Role.grants(permission) -> bool` becomes `_Role.effects(action, lineage, instant) -> frozenset[_Effect]`" |
| `EntitlementModel.decide` (and the question seam) | **reopened** | "The grant rule's single owner, `decide`, is split into three owners". The seam also changes: "A stage-1 call `decide(u, a, r)` now raises Python's `TypeError`". |
| `json_file.load_model` | **reopened** (small) | "This supersedes one stage-1 loader duty… that check moves into `_parse_grant`" |
| `model.py` core module | extended | "The core grows from about 100 to about 230 lines", still one module |
| `_identifier` | survived | "unchanged (A4)" |
| constructor seam | extended | `parents: Mapping[str, str] = _NO_PARENTS` is optional, and the pair form is kept |
| `Decision` | survived | "unchanged (A5)" |
| errors | survived | "(unchanged set)" |
| `cli.main` | extended | "gains: --now"; it now owns the wall-clock default |
| `__main__`, `__init__` | survived | "(unchanged)", "`__all__` unchanged" |

**Y reopened + discarded = 3 + 1 = 4.** Three of these are substantive (`_Permission`, `_Role`, `decide`). The fourth is a small duty move in the loader.

The hidden spec's survival oracle puts **both** designs in the "**Reopens**" class. Both answered stage 1 with `any(...)` over flat permissions and had no grant or effect type. Both had to reopen the decision core. X's count is lower by one, and X kept every stage-1 call source-compatible, while Y's `decide` seam broke stage-1 callers.
**D2 winner on survival: X (narrow).** Per measurement.md this is weak corroboration only.

### X-stage-2

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 10 | — | There is one call, `svc.check(..., now=...)`. The pull of `roles_of` × `lineage` × `grants_for` is charged in row 5. |
| 2 | Calibration / concept fit | Y | 10 | — | Deny is a first-class value: `Effect(Enum): ALLOW, DENY`, separate from `Decision` (D6: "A grant *says* deny, and a decision *is* deny"). |
| 3 | ISP | Y | 10 | — | A caller needs only `build_model`, the `allow`/`deny` helpers, and `check`. |
| 4 | Primitive obsession | Y | 10 | — | `Grant(permission, effect, window)`, `Window(valid_from, valid_until)`, and aware `datetime`. |
| 5 | Anemic model | Y | **7** | S2 | 2/3. Sub-check a fails, and the split persists: "The model still owns only immutability, indexing, and the 'absent means empty' convention". `DecisionService` orchestrates gather → time → combine over model lookups. (b holds: "`Window`… has one method, `contains(t)`".) |
| 6 | Cohesion / OCP | Y | 10 | — | A precedence change touches only `combining`. "Moving to multiple parents… neither `combining` nor `decision` would change." |
| 7 | Leaky abstractions | Y | **8** | S1 | 3/4. Sub-check c fails; this is the same exposure as stage 1, now wider. The public model exposes `grants_for`, `lineage`, `roles_of`, `grants_of` and the nested `grants` index. |
| 8 | SRP | Y | 10 | — | Each step has one owner (D2: "three steps with three owners"). |
| 9 | One owner | Y | 10 | — | Precedence: `deny_overrides` is "the whole answer to 'who wins'". Reach: `lineage`. In force: `Window.contains`. Validation: `build_model`. |
| 10 | DRY | Y | **8** | S1 | 3/4. Sub-check b fails, as in stage 1, and now extends to time as well. `build_model` checks "Each window bound must be `None` or an aware `datetime`" and `check` checks "`now` must be `None` or an aware `datetime`". |
| 11 | Naming / failure | Y | **8** | S1 | 3/4. Sub-check c fails, and the design says so itself: "whether a call without `now` succeeds depends on the data". **Repro:** `alice` holds `finance-reader` (a permanent allow on `finance`), and `check("alice","read","doc-43")` → ALLOW. Adding `allow("read","finance", valid_from=…, valid_until=…)` to a second role alice holds makes the same call raise `EvaluationInstantRequired`. It is loud and never an allow, so S1. |
| 12 | YAGNI | Y | **6** | S1 | 3/5. **e fails:** `combining.py` is a module for one three-line function, and `outcome.py` is a leaf module that exists only because of that split ("`Decision` moves there… so that both `decision` and `combining` can use it without an import cycle"). The *function* owns precedence and is earned; the two modules are ceremony. **d fails:** `grants_of(role)` is "kept for compatibility… It is not used by the decision". This is a greenfield design with no external callers, and the retained accessor now reports permissions that a deny overrides (a role with `allow` and `deny` on (read, doc-42) lists (read, doc-42)). |
| 13 | Correctness | Y | **2** | **S4** | 6/7 (the sub-check score of 9 is capped at 2). C6–C12 and R7 pass: the spec scenarios "Deny from another role wins", "Deny on an ancestor beats an allow on the descendant", "Expired deny no longer overrides", "Allow at the exclusive end"; "the service never reads the clock"; "every stage-1 `check` call returns the stage-1 answer". **C13 fails.** `Window.contains(t)` compares the caller's datetimes as stored ("implements the half-open `[from, to)` rule"). The only normalization is the awareness check. Python compares two aware datetimes that share a `tzinfo` by **wall time**, ignoring the fold and offset, which breaks X's own requirement "compared as instants, independent of the timezone". **Repro:** role `r` = `allow("read","doc", valid_from=datetime(2026,10,1,tzinfo=Berlin), valid_until=datetime(2026,10,25,2,30,fold=1,tzinfo=Berlin))`; alice holds `r`; `check("alice","read","doc", now=datetime(2026,10,25,2,45,fold=0,tzinfo=Berlin))`. The instant is 00:45Z and the window ends at 01:30Z, so the grant is in force and the **correct answer is ALLOW**. X as written evaluates `2:45 < 2:30` on wall time and returns **DENY**. Verified in CPython: `start<=now<to` → `False`; UTC-normalized → `True`. The fold also runs the other way: a deny window ending at 02:30 fold=0, asked at 02:15 fold=1, is dropped by instant but kept by wall time, and ALLOW becomes DENY. This is local and fixable with one line (normalize to UTC at build and at check time), but it is a precondition item, so the tier is S4. |
| 14 | State | Y | 10 | — | "The service holds no state beyond the model reference, and it never reads the clock." (The `parents: Mapping[str, str] = {}` default is only read by the builder and is copied, so no shared-state hazard is shown and nothing is charged.) |
| 15 | Testability | N/A | — | — | code-leaning |
| 16 | Performance | N/A | — | — | nothing stated |
| 17 | Security | N/A | — | — | no boundary stated |

**Profile X-2:** weights are 8×1 + 2 + 3×1 + 1 + 8 = 22, and Σ = 80 + 14 + 24 + 6 + 16 = 140.
**grade = 6.36 · worst = 2 · (#S3,#S4) = (0,1) · gate = BLOCKED** (because of the row-13 fold defect).
*Sensitivity:* with the one-line UTC fix, row 13 = 10 and the grade is **8.80**, worst 6, (0,0), CLEAR.

### Y-stage-2

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 10 | — | `decide` tells `role.effects(...)`, and "`decide` never reads `grants`". |
| 2 | Calibration / concept fit | Y | 10 | — | `_Effect` is distinct from `Decision` ("Reusing `Decision`… would be the value-correct cram"). `_ALWAYS` is a genuine (−∞, +∞) interval, not a stand-in. |
| 3 | ISP | Y | 10 | — | "The public surface of `EntitlementModel` is exactly `{decide}`", and `__all__` is unchanged. |
| 4 | Primitive obsession | Y | **7** | S2 | 3/4. Sub-check b fails. The in-code grant seam is a string-keyed dict: `Mapping[str, object]` with keys `"action"`, `"resource"`, `"effect"`, `"from"`, `"to"` and the effect spelled `"deny"`. The design concedes the cost: "a misspelled key is caught when the model is built, not by a type checker". The stated reason ("the same vocabulary as the file") comes from the unrequested file edge. This is a public-seam data clump, local to one seam: S2. |
| 5 | Anemic model | Y | 10 | — | `_Window.contains`, `_Grant.applies`, `_Hierarchy.lineage` and `_combine` each own their own rule. |
| 6 | Cohesion / OCP | Y | 10 | — | The table "Each foreseeable change reopens exactly one owner" (precedence → `_combine`, validity → `_Window`). |
| 7 | Leaky abstractions | Y | 10 | — | "No new public type is added." Cycles, windows and effects map to the existing `InvalidModelError`. |
| 8 | SRP | Y | 10 | — | The core is one module with a stated falsifier. `decide` has four steps at one altitude. |
| 9 | One owner | Y | 10 | — | `_combine` is "the only code in the package that produces a `Decision` value". Reach has "one home" in `_Hierarchy.lineage`. |
| 10 | DRY | Y | 10 | — | `_instant` is "the one owner of 'a supplied instant'". The grant-key list moves into the core because "Two copies of the key list would be duplicated knowledge". |
| 11 | Naming / failure | Y | **8** | S1 | 3/4. Sub-check c fails: "A stage-1 call `decide(u, a, r)` now raises Python's `TypeError`". **Repro:** the stage-1 model `roles={"editor":[("read","doc-42")]}, assignments={"alice":["editor"]}` with `decide("alice","read","doc-42")` → `TypeError` (stage 1 returned ALLOW). With `now=` supplied, every stage-1 answer is preserved (§9.6). This is a loud break, argued from "decision is made relative to a supplied now", so S1. |
| 12 | YAGNI | Y | **6** | S2 | 3/5. **a fails (S2):** the unrequested edges grow with the new features. `--now` is added, "When `--now` is absent, the CLI passes `datetime.now(timezone.utc)`" (A15), and ISO text parsing (A13), wire names (A11) and `parents` are added to the file. **c fails (S1):** there is still hostile-input machinery that pays nothing present: "Subclass neutrality. A `datetime` subclass cannot bring its own comparison into the rule", the overflow rule A16, and an AST fitness test forbidding `Decision.ALLOW` outside `_combine`. The UTC normalization in `_instant` is **not** charged, because it is load-bearing: it is exactly what avoids X's row-13 defect. Small is not unearned. |
| 13 | Correctness | Y | 10 | — | 7/7. Traced in §9: C6 "{ALLOW, DENY} → DENY"; C7 "doc-42 ∉ L(doc-43)"; C8 "deny org-root + allow doc-42 → DENY"; C9/C10 "an expired deny… → ALLOW"; C11 "`t1 < t1` false"; C12 "the only clock read… sits in the imperative shell"; R7 §9.6; C13: `_instant` "Normalizes the value to an exact `datetime` in UTC". The fold repro above gives ALLOW (correct). |
| 14 | State | Y | 10 | — | "hierarchy and the grants are fields of **one** immutable object". `_NO_PARENTS` is a `MappingProxyType`. |
| 15 | Testability | N/A | — | — | code-leaning |
| 16 | Performance | N/A | — | — | nothing stated |
| 17 | Security | N/A | — | — | no stated boundary |

**Profile Y-2:** weights are 11×1 + 2 + 1 + 2 = 16, and Σ = 110 + 14 + 8 + 12 = 144.
**grade = 9.00 · worst = 6 · (#S3,#S4) = (0,0) · gate = CLEAR**

**D2 winner on the stage-2 form: Y.**
- As reported: 9.00 CLEAR against 6.36 BLOCKED.
- The removable-blemish rule does not change this. With X's fold defect fixed, Y still leads, 9.00 against 8.80, so the verdict does not depend on the S4; only the margin does.
- On structure alone the lead is narrow. Y's core is richer (no service over a data bag, nothing exposed). X's is leaner in scope, but Y pays for its unrequested CLI and file edges and for the string-keyed grant seam those edges justify.
- If Y's edges were graded S1, Y-2 would be 9.20; still Y.

**D2 winner on survival: X (narrow).** The winner on the stage-2 form is **Y**.

---

## 3. Correctness traps (spec-and-oracle.md)

| trap | X | Y |
|---|---|---|
| **1. Deny-as-absence cram** | **Avoided at stage 2.** "`Effect(Enum)`: `ALLOW` and `DENY`… A grant's effect is a different concept from a decision's outcome." At stage 1 X answered with `any(...)` ("There are no deny rules"), so it had to reopen the decision core, as the oracle predicts. This is allowed: the substrate forbids building for unrevealed stages. | **Avoided at stage 2.** "Deny is a first-class effect, not a missing allow. `_Effect.DENY` is a value that a grant carries." At stage 1 Y also used `any(...)` ("Deny is the absence of any grant… there is no deny machinery") and reopened `decide`, as predicted. |
| **2. Inheritance threaded through call sites** | **Avoided.** Reach is resolved in one place: "The hierarchy semantics… are exactly the choice to iterate over `lineage(resource)`… and that choice lives in this one line". Lineage is precomputed per resource, and grants are *not* expanded. | **Avoided.** "`lineage(R)` owns reach", with "The fallback lives here and not in `decide`". Expanding grants is explicitly rejected ("destroys grant identity"). |
| **3. Time check scattered / precedence undefined** | **Avoided.** Time is one step before the combiner, symmetric for allow and deny: "[3 place in time] drop grants whose Window does not contain `now`" and then "[4 combine]". The spec reads "This SHALL apply equally to allows and denies". The precedence order is defined: relevance, then time, then deny-overrides. (The separate instant-comparison defect is reported in row 13 with its repro. It is not scattering: it gives a wrong in-force answer for allow and deny alike.) | **Avoided.** "`_Grant.applies`… action == a ∧ resource ∈ lineage ∧ window.contains(t)", with "one path for both effects (B5 by construction)"; `_combine` is the sole precedence owner. |

**Oracle cross-check on specificity.**
- The oracle's first answer ("most specific resource wins; at the same level, deny beats allow") conflicts with its own third answer ("a deny on the path still wins over an allow") and with the stage card the designers saw ("A deny anywhere on the path still wins over an allow").
- The only input that separates the readings is: deny (read, finance), allow (read, doc-42), ask about doc-42.
- **Both X and Y return DENY.** X: "Deny on an ancestor beats an allow on the descendant". Y: "deny org-root + allow doc-42 → DENY".
- DENY is the card's answer. The oracle is self-contradictory on this input, so **no failure is claimed for either design**. Their outputs are identical, so the question cannot affect the ranking.
- The other oracle answers are met by both designs: the default is deny; `now` is supplied (X: optional, never the clock; Y: required); only grants carry windows.

**Failures reported, with reproductions**
- **X-2, row 13 (S4).** DST-fold instant comparison.
  - Input: `valid_until=datetime(2026,10,25,2,30,fold=1,tzinfo=ZoneInfo("Europe/Berlin"))`, `valid_from=datetime(2026,10,1,tzinfo=same)`, `now=datetime(2026,10,25,2,45,fold=0,tzinfo=same)`.
  - X returns **DENY**; the correct answer is **ALLOW** (00:45Z < 01:30Z). Verified in CPython.
- **X-2, row 11 (S1, not a correctness failure).** A data-dependent `EvaluationInstantRequired`. The repro is in the row. The output is an error, never a wrong allow.
- **Y-2, row 11 (S1, not a correctness failure).** `decide("alice","read","doc-42")` → `TypeError`, where stage 1 returned ALLOW. With `now=` supplied, the output is correct.
- No other correctness failure was found in either design, and none is claimed.

---

## 4. Residual tells and how I controlled for them

- **Method guess.** Before scoring, I recorded X = OpenSpec and Y = aims at 97% confidence. I scored against the fixed sub-check list above, applied identically to every design, and cited only specified structure.
- **Rubric home advantage.** The rubric is aims' own instrument (its paths point to `aims-guide`), and Y recites its vocabulary: "concept fit", "Tell-Don't-Ask", "falsifier", "§13 of the principles". measurement.md itself warns of "vocabulary capture". Controls:
  - I credited Y only where the structure holds, for example "the public surface is exactly `{decide}`" and a single `_combine` producer.
  - I charged Y where its self-justification did not buy a present force. Examples: the str/datetime-subclass defences, the JSON/CLI edges, and the string-keyed grant seam, which Y argues for at length.
- **Length.** Y is about 30% longer. Length was never charged. Only named unrequested modules and rules were charged (row 12). X's proposal/spec/task artifacts were not credited as structure.
- **One asymmetry.** I quoted X's spec ("compared as instants, independent of the timezone") to show that X promised what it fails at. The row-13 finding stands without it: the product card requires a window "relative to a supplied now", and design-principles §1 names "time" as an edge. The reproduction is concrete and verified.
- **My own disposition.**
  - YAGNI pushed me to grade Y's unrequested edges S2 rather than S1. I reported both sensitivities (D1: Y-1 9.47 → 9.71; D2: Y-2 9.00 → 9.20). Neither changes a verdict.
  - The same lens made me look hard at X's `DecisionService`. By the registered §7 falsifier it serves axis X1, so I did not charge it as over-build. It is charged once as anemic (row 5), not again as YAGNI.
- **Removable blemish.** X-2's S4 is a one-line fix. I reported it as the rubric requires (gate BLOCKED) and gave the fixed-state grade (8.80), so the stage-2 verdict visibly does not rest on it.
- **Numbering.** The form's row 13 is functional correctness, while design-principles §13 is performance. Row 16 (performance) is N/A for all four designs, so Y's remark about "§13 of the principles" did not affect any score.
