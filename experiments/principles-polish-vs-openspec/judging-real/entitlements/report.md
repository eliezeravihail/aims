# Entitlements: blind design judgment (X vs Y)

Scored with `rubric/assessment-form.md` (one row per principle, rows 1–17), using sub-checks from `rubric/design-principles.md` and the severity, weight and aggregation rules in `rubric/measurement.md`. Where the form and `measurement.md` disagree, `measurement.md` wins, because the form says `measurement.md` is canonical. The one case of this is the global cap: the headline grade is uncapped and is reported with the gate. The form's capped figure is shown next to it.

Row score = `round(10 × passed / applicable)`, then limited by the ceiling for the worst failed item: S1→8, S2→7, S3→5, S4→2. Weight: none or S1 ×1, S2 ×2, S3 ×4, S4 ×8. The precondition class follows the principles document: all of §1 correctness, §5 one-owner, and a §0/§5 seam leak. A failed precondition is S4.

**Rows marked N/A for all four designs** (the same applicable set for every design, as `measurement.md` requires):
- **Row 15, testability:** "code-leaning (N/A on a pure design document)".
- **Row 16, performance:** no performance requirement is stated.
- **Row 17, security:** there is no trust boundary. This is an in-process library called by trusted code. Deny-by-default is scored under row 13 and one owner of the decision under row 9, so nothing is lost and nothing is counted twice.

## Step 0: the fixed inventory (taken from `product/`, not from the designs)

### Stage 1

**Rules (R)**
- **R1:** a permission is an exact (A, R) pair.
- **R2:** a role grants a set of permissions.
- **R3:** a user is assigned one or more roles, and those roles are defined.
- **R4:** allow if and only if some assigned role grants (A, R).
- **R5:** otherwise deny.

**Change axes (X)**
- **X1:** entitlement data changes (roles, grants and assignments added or removed).
- **X2** (plausible unstated variant): the decision rule gains cases, such as precedence or effects.

**Acceptance cases (C)**
- **C1:** a single role grants → allow.
- **C2:** one of several roles grants → allow.
- **C3:** no role grants → deny.
- **C4:** unknown user → deny, with no error.
- **C5:** same action, different resource → deny.
- **C6:** different action, same resource → deny.
- **C6b:** a duplicate grant is idempotent.

### Stage 2 (adds to the above)

**Rules (R)**
- **R6:** a grant carries an effect, allow or deny, and a deny from any held role overrides any allow.
- **R7:** a grant on a group applies beneath it, and a deny anywhere on the path wins.
- **R8:** a grant applies only inside `[from, to)`, evaluated at a supplied `now`.
- **R9:** stage-1 answers are unchanged when the new features are absent.

**Change axes (X)**
- **X3:** a new effect or precedence rule.
- **X4:** multi-parent hierarchy (plausible unstated variant).

**Acceptance cases (C)**
- **C7:** a deny from another role beats an allow.
- **C8:** a group grant reaches a descendant.
- **C9:** a descendant grant reaches neither up nor across to siblings.
- **C10:** a descendant deny narrows a group allow.
- **C11:** an ancestor deny beats a descendant allow.
- **C12:** a grant outside its window does not apply.
- **C13:** the window boundaries are `[from, to)`.
- **C14:** an expired deny does not block.
- **C15:** R9 holds.

---

## 1. D1: first-round design (stage 1)

### X-stage-1

| # | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | Tell-Don't-Ask / LoD | Y | **7** | S1 | Items: TDA ✗, LoD ✓, no message chains ✓ (2/3). The decision pulls each role's grant set out of the model and tests membership outside the role: "`ALLOW if any(wanted in model.grants_of(r) for r in model.roles_of(user)) else DENY`". The role has no behaviour ("EntitlementModel … data, with no policy"). Affects R4. This is local: one line. |
| 2 | Interface calibration / concept fit | Y | 10 | — | The lookups are total and minimal: "Both are **total**: an unknown key returns an empty frozenset". Invalid models cannot be represented: "No partially built model can escape". |
| 3 | Interface segregation | Y | 10 | — | "the decision only calls `roles_of` and `grants_of`". |
| 4 | Primitive obsession | Y | **7** | S2 | Items: Permission typed ✓, outcome typed ✓, identifiers typed ✗ (2/3 → 7). "`UserId`, `RoleId`, `Action`, `Resource` are `str` aliases". Their stated rule (non-empty) has no type to own it, so it is checked in two places: in the builder ("ids, actions, and resources are non-empty `str`") and in `check` ("validate request args (non-empty str)"). The public seam `check(user, action, resource)` takes three strings that can be passed in the wrong order. |
| 5 | Anemic domain model | Y | 10 | — | The factory owns the construction invariants: "Owns every entitlement-model validation rule". Exact-pair identity is owned by `Permission` value equality ("frozen … compared by exact value"). The pulled-state issue is scored under row 1, not here. |
| 6 | Cohesion / coupling / OCP | Y | 10 | — | "Dependencies point one way: building -> model <- decision". X2 has a single home: "Later rules … will change `Decision` and leave the data store alone" (D6). |
| 7 | Leaky abstractions / errors | Y | 10 | — | "`ModelValidationError`: bad data … `InvalidRequestError`: bad question … lets a caller distinguish". |
| 8 | SRP / God object | Y | 10 | — | Four modules, each with a single "Owns:" line (model, building, decision, errors). |
| 9 | One unforgeable owner | Y | 10 | — | R4/R5 are "The rule, in full" in `check`. Validation happens "in exactly one place" (D2). R1 is owned by `Permission` equality. |
| 10 | DRY | Y | 10 | — | The duplicated non-empty check is referenced from row 4 and not deducted again. |
| 11 | Naming & failure | Y | 10 | — | Each issue "carries a location (for example `assignments['alice']`)". "The `TypeError` message says what to do". |
| 12 | YAGNI / subtractive | Y | **8** | S1 | Items: no speculative seams ✓, every type pays ✗, no pattern abuse ✓, no dead code ✓, no lazy class ✓ (4/5). `Decision(Enum)` is a two-value enum that owns no product rule. Its one guard (`__bool__` raises) only blocks a hazard the enum itself creates, and the design concedes "A `bool` would also be safe but carries no vocabulary." |
| 13 | Functional correctness | Y | 10 | — | Every C case has a scenario (C1–C6b). Fails fast: "a model that assigns an undefined role SHALL be rejected as a whole". Edge cases covered: empty role, user with no roles, duplicates, case sensitivity, mutation after build. |
| 14 | State & side effects | Y | 10 | — | "Copies caller collections into frozensets". `MappingProxyType`. The decision "never mutates anything". |
| 15–17 | — | N/A | — | — | See the note at the top. |

### Y-stage-1

| # | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | Tell-Don't-Ask / LoD | Y | 10 | — | `any(role.grants(action, resource) for role in self._store.roles_for(user))`: the decision asks the role, not its set. |
| 2 | Interface calibration / concept fit | Y | 10 | — | The port "yields the published domain type `Role`, never storage rows". |
| 3 | Interface segregation | Y | 10 | — | `EntitlementStore` has one method, `roles_for`. |
| 4 | Primitive obsession | Y | 10 | — | `UserId`, `Action`, `Resource` and `Permission` are frozen value types. The result is `bool` for a one-bit decision. |
| 5 | Anemic domain model | Y | 10 | — | `Role.grants` "OWNS the permission-match rule". |
| 6 | Cohesion / coupling / OCP | Y | 10 | — | "the decision core depends on this *interface*". X2 has one home: "This is the single home a later combination-policy change would reopen." |
| 7 | Leaky abstractions / errors | Y | 10 | — | Ports speak domain types. By contract nothing raises ("never raises"). The missing failure vocabulary for invalid data is scored under row 13. |
| 8 | SRP / God object | Y | 10 | — | Three components, one rule each (§2.1–2.3). |
| 9 | One unforgeable owner | Y | 10 | — | "combination in `may`, match in `Role`/`Permission`, resolution in the port". |
| 10 | DRY | Y | 10 | — | No duplicated rule. |
| 11 | Naming & failure | Y | **8** | S1 | Items: intention-revealing ✓, one word per concept ✗, failure speaks the consumer's concept ✓ (with a reference to row 13), least astonishment ✓ (3/4). The three identifier wrappers name the same slot three different ways: `UserId: value: str`, `Action: name: str`, `Resource: id: str`. |
| 12 | YAGNI / subtractive | Y | 10 | — | "does **not** pre-build a combination-strategy seam, a matching-strategy seam…". The store port serves X1, because data is read on every call. |
| 13 | Functional correctness | Y | **2** | **S4** | Items: C cases ✓, interactions ✓, contracts ✓, edges ✓, fail fast ✗, trust inside ✓ (5/6 → 8, capped at 2). No rejection rule exists at the only point where data enters. The in-memory store is described as "holding the two data-model relations — *assignments* (user → role ids) and *role definitions* (role id → grant set) — and hydrating them into `Role`s". An assignment that names an undefined role id (R3) has no stated outcome. **This fails closed** on every natural reading (no `Role` means deny), so no wrong allow results. It is a removable one-clause gap (see the verdict). |
| 14 | State & side effects | Y | 10 | — | Frozen dataclasses. "**Pure core** — `may` depends only on the injected store". |
| 15–17 | — | N/A | — | — | |

### D1 profiles

| design | weighted grade | worst | (#S3, #S4) | gate | form-capped figure |
|---|---|---|---|---|---|
| X-stage-1 | **9.27** (139/15) | 7 | (0, 0) | CLEAR | 8.5 |
| Y-stage-1 | **6.86** (144/21) | 2 | (0, 1) | BLOCKED | 5.0 |

**D1 winner: no clear advantage.** On the literal grade, X leads. That lead comes entirely from one item: Y's unspecified validation of dangling role ids. That item fails closed, and one sentence in the store adapter would fix it, so it is exactly the removable local blemish that must not decide the verdict.

With that item neutralised, Y scores 9.86 and X 9.27. What remains is:
- Y's typed identifiers and tell-style `Role.grants`,
- against X's string ids (S2), its labelled-bool enum (S1) and its pull-and-test (S1),
- with X's real advantage, full data validation and error vocabulary, now counting only as passes.

The two cores are structurally the same: one pure owner of an `any(...)` rule, a value-typed exact pair, and deny-by-default built into the structure. That is too thin a margin to call either way.

---

## 2. D2: change absorption

### Survival classification (stage-2 design compared against stage-1)

**X**

| stage-1 element | verdict | evidence |
|---|---|---|
| `Permission` | survived | "`Permission` is unchanged." |
| `EntitlementModel` (component) | extended | Gains `lineage` and `grants_for`. "The model still owns only immutability, indexing, and the 'absent means empty' convention." |
| `roles_of(user)` / `assignments` index | survived | "`roles_of(user)` is unchanged." |
| `grants` index `Mapping[RoleId, frozenset[Permission]]` | **reopened** | Shape changed to "`grants: Mapping[RoleId, Mapping[Permission, frozenset[Grant]]]`". |
| `grants_of(role)` seam | **reopened** | Was the decision's lookup. Now "kept for compatibility … returns the role's permissions that have an ALLOW grant with no window … It is not used by the decision." |
| `build_model` | extended | "gains a `parents=` argument and accepts `Grant` entries alongside stage-1 tuples". |
| `DecisionService.check` (decision rule owner) | **reopened** | Stage 1 "Owns: request validation, the any-role-grants rule". Stage 2 "owns steps 1-3" and "delegates to `combining.deny_overrides`". The rule body is replaced and the combination responsibility moves out. The signature change is compatible (`now=None`). |
| `Decision` | survived (relocated) | "`Decision` moves there from `decision.py` … still re-exported from the package root". |
| errors | extended | "Stage 2 adds `EvaluationInstantRequired(InvalidRequestError)`". |
| public surface | extended | Re-exports the new names. "Existing callers are source-compatible." |

**X: reopened + discarded = 3** (the `grants` index, `grants_of`, `DecisionService.check`), with 0 discarded. Every reopen sits behind a compatible public surface: "The stage-1 test suite must pass unmodified as the compatibility gate."

**Y**

| stage-1 element | verdict | evidence |
|---|---|---|
| `UserId`, `RoleId`, `Action`, `Resource` | survived | "the Stage-1 value objects, unchanged". |
| `Permission` | survived | Reused as `target: Permission`. |
| `Role` (component) | extended | "EXTENDED — grant-container now holds Grants". |
| `Role.granted: frozenset[Permission]` | **reopened** | Now `granted: frozenset[Grant]`. |
| `Role.grants(action, resource) -> bool` | **discarded** | "Discarded: the `Role.grants(a, r) -> bool` predicate". Replaced by `grants_applicable(action, path, now)`. |
| `EntitlementStore.roles_for` port | survived | The signature is intact. Every adapter must now build `Grant`s, because the `Role` shape changed. |
| `InMemoryEntitlementStore` | extended (implicitly) | Not mentioned in stage 2, but it must now hydrate `Grant`s. |
| `AuthorizationService.may` + constructor | **reopened** | Went from `__init__(store)` / `may(user, action, resource)` to `__init__(self, store, hierarchy)` / `may(self, user, action, resource, now: Instant)`. The body is replaced and the public signature changes incompatibly: `now` is required. The design's claim that "no caller … had to change" is contradicted by this signature, and the classification follows the signature. |
| `bool` result | survived | "`may` still returns `bool`". |

**Y: reopened + discarded = 3** (`Role.granted`, `Role.grants`, `may`). One of these is the public entry point, which every caller uses. The `Role` constructor change also reaches every store adapter.

Both designs match the hidden survival oracle in the same way. Each had `any(...)` over flat permissions with no effect type, so the core had to reopen. Each also had a single decision owner, so precedence had a place to land.

**D2 winner on survival: X, narrowly.** The counts are equal (3 vs 3), but X's reopens are all internal and stage-1 callers stay source-compatible. Y's reopens include the public `may` signature and the adapter-facing `Role` constructor.

### X-stage-2

| # | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | Tell-Don't-Ask / LoD | Y | **7** | S1 | Carried over from stage 1, now with three pulls: candidates come from `grants_for(role, Permission(action, r))`, the time test is `window is None or window.contains(now)`, and effects come from `g.effect for g in in_force`. `Grant` has no behaviour (2/3). |
| 2 | Interface calibration / concept fit | Y | **8** | S1 | Illegal states representable ✗ (4/5). `Window(valid_from: datetime \| None, valid_until: datetime \| None)` allows both bounds to be `None`, which is a second spelling of `window=None`. Validation only checks "When both bounds are present, `from < to`". Under D4, a `Window(None, None)` candidate makes a call without `now` raise `EvaluationInstantRequired` for a grant that is always valid. The failure is loud and fails closed. |
| 3 | Interface segregation | Y | 10 | — | The decision uses `roles_of`, `lineage` and `grants_for`. The unused `grants_of` is scored under row 12. |
| 4 | Primitive obsession | Y | **7** | S2 | Identifiers are still `str` aliases (carried over). `datetime` (timezone-aware) ✓, `Effect` ✓, `Window` ✓, `Grant` ✓ (5/6 → 8, capped at 7). |
| 5 | Anemic domain model | Y | 10 | — | `Window.contains` owns being "in force at t": "belongs to the value it describes". See row 1. |
| 6 | Cohesion / coupling / OCP | Y | 10 | — | "`combining` imports `Effect` … and `Decision` …, and nothing else". X3 lands only in `combining`. X4: "neither `combining` nor `decision` would change". |
| 7 | Leaky abstractions / errors | Y | 10 | — | "A caller that already catches `InvalidRequestError` needs no changes". The subtype has a distinct handling. |
| 8 | SRP / God object | Y | 10 | — | `check` orchestrates steps 1–3. `combining` owns step 4. `building` owns validation and precomputed lineage. |
| 9 | One unforgeable owner | Y | 10 | — | "This function is the whole answer to 'who wins'". The hierarchy rule: "that choice lives in this one line". |
| 10 | DRY | Y | 10 | — | `Effect` and `Decision` are distinct concepts (D6), not duplication. |
| 11 | Naming & failure | Y | 10 | — | `lineage` is named accurately. The data-dependent failure when `now` is missing is a documented trade-off that is loud and fails closed (D4), and it is not counted. |
| 12 | YAGNI / subtractive | Y | **6** | S1 | Every type pays ✗, no dead code ✗ (3/5). (a) The labelled-bool `Decision` is carried over, plus a new module that exists only to host it: "`outcome` is a new leaf module: `Decision` moves there … so that both `decision` and `combining` can use it". (b) A dead accessor: "`grants_of(role)` is kept for compatibility … It is not used by the decision". It also still lists a permission that the same role denies. |
| 13 | Functional correctness | Y | 10 | — | Every C case has a scenario, including "Deny on an ancestor beats an allow on the descendant" (C11) and "Expired deny no longer overrides" (C14). Fails fast on cycles, naive datetimes and empty windows. |
| 14 | State & side effects | Y | 10 | — | "The service holds no state beyond the model reference, and it never reads the clock." |
| 15–17 | — | N/A | — | — | |

### Y-stage-2

| # | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | Tell-Don't-Ask / LoD | Y | 10 | — | `role.grants_applicable(action, path, now)` → `g.applies(...)`. |
| 2 | Interface calibration / concept fit | Y | 10 | — | `Effect` is a real sum type on the grant, and the grant is `Grant(effect, target: Permission, window)`. The hierarchy is "a port, not a `Resource.parent` field". The inverted-window state is scored under row 13. |
| 3 | Interface segregation | Y | 10 | — | Two single-method ports. |
| 4 | Primitive obsession | Y | **7** | S2 | Time typed ✗ (5/6 → 8, capped at 7). "`Instant = int` … (epoch/seconds)" appears in `Window(frm: Instant, to: Instant)` and in `may(..., now: Instant)`. The unit and epoch are only stated in a comment, and there are two ints that can be swapped. |
| 5 | Anemic domain model | Y | 10 | — | `Grant` "owns its own applicability". `Window.contains`. |
| 6 | Cohesion / coupling / OCP | Y | 10 | — | New `ResourceHierarchy` port. `_resolve` is the single place X3 lands. |
| 7 | Leaky abstractions / errors | Y | 10 | — | The ports speak domain types. |
| 8 | SRP / God object | Y | 10 | — | Applicability, path and precedence each have their own home (§3 table). |
| 9 | One unforgeable owner | Y | 10 | — | "`_resolve` … The precedence rule, one named home". |
| 10 | DRY | Y | 10 | — | No duplicated rule. |
| 11 | Naming & failure | Y | **5** | S1 | Intention-revealing ✗, one word per concept ✗ (2/4). `frm` is an abbreviation. `ancestors(resource)` returns "resource itself, then its parent group", which is more than the ancestors. The value/name/id split is carried over. |
| 12 | YAGNI / subtractive | Y | 10 | — | Each new type is tied to a stage-2 force. "`_resolve` … **not** a pluggable Strategy". |
| 13 | Functional correctness | Y | **2** | **S4** | Fail fast ✗ (5/6, capped at 2). Neither new data structure has an owner for its integrity. `Window` has no `frm < to` rule, so for an inverted **deny** window "`return self.frm <= now < self.to`" is never true. The deny silently drops and any allow wins, which **fails open**. `ResourceHierarchy` promises "up to a root", but no component is named to reject cycles, so a cycle makes the path walk never terminate. Every C case passes, e.g. "time filters *before* precedence". |
| 14 | State & side effects | Y | 10 | — | Frozen dataclasses. `may` is pure. |
| 15–17 | — | N/A | — | — | |

### D2 form profiles

| design | weighted grade | worst | (#S3, #S4) | gate | form-capped figure |
|---|---|---|---|---|---|
| X-stage-2 | **9.00** (135/15) | 6 | (0, 0) | CLEAR | 8.5 |
| Y-stage-2 | **6.59** (145/22) | 2 | (0, 1) | BLOCKED | 5.0 |

**D2 winner on the stage-2 form: X.** Unlike stage 1, Y's S4 here is not a blemish I can neutralise. It fails open in an authorization product: a mistyped deny window silently becomes an allow. It also affects both data structures the change introduced, and no component owns their integrity. X has a component for exactly this job ("the decision never needs to know that a hierarchy could be malformed").

For transparency: if that one item were fixed, Y would score 9.27 against X's 9.00. So X wins on this form only because of the S4, and every X deduction is S1 or S2.

---

## 3. Correctness traps (from `spec-and-oracle.md`)

| trap | X | Y |
|---|---|---|
| **1. Deny as absence** | **Avoided.** "`Effect(Enum)`: `ALLOW` and `DENY`". Precedence has one owner: `deny_overrides`. | **Avoided.** "`class Effect(Enum)` … a real sum type: it BRANCHES precedence". Precedence has one owner: `_resolve`. |
| **2. Inheritance threaded through call sites** | **Avoided.** Lineage is precomputed in the model and used on one line of `check`: "that choice lives in this one line". | **Avoided.** `path = frozenset(self._hierarchy.ancestors(resource))` sits only in `may`, and the match sits in `Grant.applies`. |
| **3. Time check scattered / precedence undefined** | **Avoided.** Step 3 (time) runs strictly before step 4 (combine): "Allow and deny are symmetric with respect to time". It also closes the case where `now` is missing: "(c) Ignore windowed grants when `now` is absent … fails open" was rejected. | **Avoided.** "time filters *before* precedence (an expired deny does not block, an expired allow does not permit)". The trap is avoided, but a related gap remains: an unvalidated inverted deny window is silently lost (row 13). |

**Specificity.** Both designs make the same argument (X D1; Y §1): because "a deny anywhere on the path still wins", specificity can never change a two-valued outcome, so neither design ranks grants by depth. The oracle's "resolve specificity first" and "a deny on the path still wins" can only both hold if specificity has no effect on the outcome, which is what both designs conclude. This does not tell the designs apart.

The remaining oracle items are the same for both designs: `now` is supplied (X: "The service never reads the wall clock"; Y: `now: Instant` parameter), and only grants carry windows.

---

## 4. Residual tells and controls

- **Method guess.** Before scoring I guessed X = OpenSpec and Y = aims at 97%. The rubric is aims' own document (it cites `skills/aims-guide`), and Y uses its vocabulary: §-numbers, "subtractive pass", "concept-fit", "a boolean with a label". That is capture risk (a) in `measurement.md`, and it favours Y. Controls:
  - I did not credit Y's review, SURVIVAL or Cost sections.
  - I classified Y's `may` as *reopened*, against its own label "SURVIVED + EXTENDED".
  - Every Y pass cites a signature or a type, not a self-description.
  - I applied "a two-value enum that is a boolean with a label" to X because the rubric says so, not because Y said it. It is weighted ×1.
- **Length and format.** X is about 3 times longer and in SHALL/scenario format, which reads as rigorous. Controls:
  - I credited scenarios only for the rules they fix.
  - I searched X's larger surface for faults, and found the `grants_of` shim and `Window(None, None)`.
  - I faulted Y's omissions only where an R/C item implies the missing rule (R3, R8, R7).

  The asymmetry this leaves is why I ran a blemish check on each verdict.
- **Severity class and "local blemish".** Literally, the rubric makes every §1 fail-fast gap S4. I kept the literal scores, then tested each verdict with the removable items neutralised:
  - D1 flipped, so I report no clear advantage.
  - The stage-2 form did not flip in substance, because that gap fails open and covers every new data structure.

  This judgment call (fails closed = blemish, fails open = substantive) decides both verdicts, so you can re-rule it if you disagree.
- **Instrument conflicts.**
  - The form (rows 1–17) and the principles (§0–§14) are numbered differently. I scored the form rows and drew sub-checks from the matching principle items.
  - The form's caps contradict `measurement.md`'s "no global cap". I report both, with the uncapped figure as the headline.
- **Oracle ambiguity on specificity.** Noted above. It affects X and Y in the same way.
