# Judging report: entitlements, designs X and Y

Judge disposition: **invariant ownership**. Instrument: `rubric/assessment-form.md` (17 rows), with sub-checks taken from
`rubric/design-principles.md` items and aggregated by `rubric/measurement.md`. I scored structure only: the types,
owners, seams, rules and cases each design specifies. I gave no credit for principle vocabulary, trace tables or
length.

---

## 0. Step 0: fixed inventory (from the product cards, identical for every design)

**R: rules and invariants**
- R1: allow iff at least one of U's roles grants (A, R).
- R2: otherwise deny (default deny).
- R3: a permission is an `(action, resource)` pair.
- R4: user → roles; role → set of permissions.
- *Stage 2 adds:*
  - R5: a grant's effect is allow **or** deny. An explicit deny overrides any allow, including one from another role.
  - R6: a group grant applies to every descendant, and a deny anywhere on the path wins.
  - R7: a window `[from, to)` means the grant does not apply outside it. The decision is made against a *supplied* now.
  - R8: stage-1 answers are unchanged where the new features are absent.

**X: change axes**
- X1: entitlement data is replaced over time.
- X2 (plausible unstated variant): the grant-matching or combining rule gains a case.
- *After stage 2:*
  - X3: the precedence rule changes.
  - X4: the hierarchy allows multiple parents.
  - X5: windows become recurring.

**C: acceptance cases**
- C1: a single role grants → allow.
- C2: one of several roles grants → allow.
- C3: no role grants → deny.
- C4: unknown user → deny.
- C5: other action on the same resource → deny.
- C6: same action on another resource → deny.
- *Stage 2:*
  - C7: a deny from role Y beats an allow from role X.
  - C8: a group allow is inherited.
  - C9: a descendant deny narrows a group allow.
  - C10: an ancestor deny beats a descendant allow.
  - C11: an expired deny does not apply.
  - C12: an allow outside its window → deny.
  - C13: `t == to` is excluded.
  - C14: a feature-free model gives the stage-1 answers.

**Applicability (identical for all four designs)**
- Row 16 (performance) is N/A: no requirement is stated.
- Row 17 (security boundary) is N/A: the product states none, and "fail closed" is scored under row 13.
- Row 15 is scored only on its design-level item ("verifiable by construction"). The other §12 items are code-leaning
  and so N/A.
- Row 14's "no clock read" item applies at stage 2 only.
- Row 9(c) ("a rule gaining a case is absorbed in its owner") applies at stage 2 only.
- Row 10(b) (the aware-instant rule has one home) applies at stage 2 only.

**Sub-check legend.** Row score = `round(10 × passed / applicable)`, capped by the ceiling of its worst failure (S1→8,
S2→7, S3→5, S4→2).

**One defect, one row.** Each defect is deducted once, in the most specific row. Where another row's item points at
the same defect, that item is marked *ref* and counted as passed there, not deducted again.

| row | sub-checks |
|---|---|
| 1 | a) the decision tells domain objects rather than pulling their state; b) no message chains (LoD); c) outside callers need not pull state to decide; d) value objects answer questions about themselves |
| 2 | a) seam types calibrated (floor/ceiling); b) only published types cross seams; c) concept fit (effect ≠ decision; deny ≠ absence); d) peers at one altitude |
| 3 | a) no client depends on unused methods; b) public surface minimal per client |
| 4 | a) concepts with rules are typed; b) illegal states unrepresentable (invariant lives in the type); c) one representation per meaning; d) public seam uses typed values for concepts with rules; e) immutable by default |
| 5 | a) the entity holding the data owns the behaviour over it (not data bag + manager); b) value types carry their rules; c) no pure data class for a concept whose rule lives elsewhere |
| 6 | a) cohesion; b) acyclic dependencies pointing to the core; c) each foreseeable X-item extends at a seam; d) no shotgun surgery or feature envy |
| 7 | a) representation hidden, only the intended operations public; b) errors are boundary vocabulary, one type per handling; c) only published types cross seams; d) edges do not reach into core internals |
| 8 | a) one responsibility per component; b) no God object; c) functions do one thing |
| 9 | a) each stated rule (R) has one owner; b) all intended paths funnel through it; c) a rule that gains a case is absorbed in its owner, with no parallel path; d) representation evolution has one owner |
| 10 | a) identifier rule has one home; b) aware-instant rule has one home; c) decision logic is not duplicated; d) no wrong abstraction |
| 11 | a) intention-revealing names; b) failure speaks the consumer's concept; c) least astonishment of public results; d) one word per concept |
| 12 | a) every type answers a present force; b) no speculative generality; c) no guards against callers that don't exist; d) edges limited to what the chosen entry point needs |
| 13 | a) every specified case; b) contracts stated; c) edge and boundary coverage, including time; d) fail fast; e) defensive at the edge, trusting inside; f) every X×R interaction traced |
| 14 | a) immutable values; b) functional core, no clock read; c) no global mutable state; d) concurrency-safe replacement |
| 15 | a) every decision reachable by isolated tests, with its inputs (model, now) injected |

---

## 1. D1: first-round design (stage 1)

### X-stage-1

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 10 | — | b, d pass: no chains; `Permission` equality answers identity. a *ref* §5 (the decision pulls `roles_of`/`grants_of`). c *ref* §7. |
| 2 | Interface / calibration / concept fit | Y | 10 | — | The seam is `check(user, action, resource) -> Decision`. `Decision(Enum): ALLOW, DENY` is a domain outcome, not a bool (D4). The published types are `build_model`, `Permission` and `Decision`. |
| 3 | ISP | Y | 10 | — | `DecisionService` uses only `roles_of`/`grants_of`. Surface width *ref* §7. |
| 4 | Primitive obsession / types | Y | 7 | S2 | **b fails.** `EntitlementModel` stores `assignments: Mapping[UserId, frozenset[RoleId]]` by *name*, and it "does not validate. It trusts that the builder established its invariants", while it is re-exported publicly ("Re-exports `build_model`, `EntitlementModel`, …"). A dangling assignment to an undefined role is therefore representable, and the invariant is held by `building`, not by the type. The intended path does funnel through `build_model`, so this is S2, not S4. a, c, d, e pass (`Permission` is `frozen=True, slots=True`). 4/5 = 8, capped at 7. |
| 5 | Anemic domain model | Y | 7 | S2 | **a fails.** "Model (`entitlements/model.py`): the data, with no policy"; the rule sits in a separate manager, `ALLOW if any(wanted in model.grants_of(r) for r in model.roles_of(user))`. b, c pass. 2/3 = 7. |
| 6 | Cohesion / coupling / OCP | Y | 10 | — | "Dependencies point one way: building -> model <- decision". X2 lands in `Decision`/`Permission`, both inside the core. |
| 7 | Leaky abstractions | Y | 7 | S2 | **a fails.** The public model exposes its representation: "`assignments` … `grants` … wrapped in `types.MappingProxyType`" plus "Read-only queries: `roles_of(user)` … `grants_of(role)`". Any caller can re-derive the grant rule outside `check`. b pass (`ModelValidationError` vs `InvalidRequestError`, "Keeping them separate lets a caller distinguish"); c, d pass. 3/4 = 8, capped at 7. |
| 8 | SRP / God object | Y | 10 | — | There are four small components, each with an "Owns:" line. |
| 9 | Rule enforcement: one owner | Y | 10 | — | R1/R2 have one owner, `DecisionService.check` ("The rule, in full"), and every query path funnels through it. |
| 10 | DRY | Y | 7 | S2 | **a fails.** The identifier rule is stated in two modules. `building` owns "ids, actions, and resources are non-empty `str`", and `decision` owns "validate request args (non-empty str) else raise InvalidRequestError". No shared owner is named, so the two can drift. c, d pass. 2/3 = 7. |
| 11 | Naming and failure | Y | 10 | — | "`Decision.__bool__` raises `TypeError`, so `if service.check(...)` cannot silently treat DENY as truthy". Errors name the location (`assignments['alice']`). |
| 12 | Size / YAGNI | Y | 10 | — | No CLI and no loader: "nothing calls for a CLI". Every type has a force. |
| 13 | Functional correctness | Y | 10 | — | C1–C6 appear as spec scenarios. Request validation runs before lookup ("validate request args … else raise"). Unknown user → deny via the total `roles_of`. Every validation error is collected. |
| 14 | State discipline | Y | 10 | — | Immutable model with defensive copies; "a check in progress always sees one consistent model". |
| 15 | Testability | Y | 10 | — | `check` is a pure function over an injected model. |
| 16 | Performance | N/A | | | |
| 17 | Security | N/A | | | |

**Profile X-stage-1:** grade = (11×10 + 4×7×2) / (11 + 8) = 166/19 = **8.74**, worst **7**, (#S3,#S4) = **(0,0)**, gate **CLEAR**.

### Y-stage-1

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 10 | — | `any(role.grants(p) for role in self._roles_of.get(u, frozenset()))`: `decide` tells each `_Role`. "`decide`, which never reads `permissions` itself". |
| 2 | Interface / calibration / concept fit | Y | 10 | — | The seam calibration table gives floor and ceiling. Strings are used at the seam because "a caller passing the wrong type would get a **silent deny**". |
| 3 | ISP | Y | 10 | — | "public surface is exactly `{decide}`". |
| 4 | Primitive obsession / types | Y | 10 | — | "A user maps to **resolved role objects, not role names**, so once built the model cannot represent an assignment to an undefined role". `_Permission` and `_Role` are frozen value types. |
| 5 | Anemic domain model | Y | 10 | — | `EntitlementModel` owns the grant rule; `_Role.grants` owns membership; `_Permission` owns identity. |
| 6 | Cohesion / coupling / OCP | Y | 10 | — | "Dependencies (acyclic, pointing to the core)". The core imports no I/O. X2 lands in `_Role`/`_Permission`. |
| 7 | Leaky abstractions | Y | 10 | — | "No `roles_of`, `users`, iteration, `__eq__`, `to_dict`, `explain`". Errors are translated "once" at each boundary. The loader "deliberately does **not** check leaf values … owned by the core". |
| 8 | SRP / God object | Y | 10 | — | Core and edges are split, and each type owns one clause (the §7 table). |
| 9 | Rule enforcement: one owner | Y | 10 | — | "Its constructor is the only way to make one". Validation runs in `__init__`, "no second constructor, no `validate()` to forget". The rule is owned by `decide` alone, and the CLI reaches it "through the same `decide`". |
| 10 | DRY | Y | 10 | — | One `_identifier` serves both boundaries: "constructor and `decide`, the only two entries of raw strings". |
| 11 | Naming and failure | Y | 7 | S2 | **c fails.** `class Decision(enum.Enum): ALLOW = "allow"; DENY = "deny"` has no truthiness guard, and every Enum member is truthy. Repro: `if model.decide("bob", "read", "doc-42"):` where bob has no roles. `decide` returns `Decision.DENY`, which is truthy, so the caller's allow-branch runs. The correct result is that the branch is not taken. X closed exactly this hole. a, b, d pass. 3/4 = 8, capped at 7. |
| 12 | Size / YAGNI | Y | 8 | S1 | **c fails.** It guards against callers that do not exist: "two keys that normalize to the same exact string (possible only with a `str` subclass whose `__eq__`/`__hash__` kept them apart …) are rejected", plus a threaded stress test for a structural guarantee. d passes: the substrate lets the design choose "a library with a small CLI", and the JSON edge is what that CLI needs. 3/4 = 8. |
| 13 | Functional correctness | Y | 10 | — | The "Why every stated case needs no branch" table covers C1–C6. "`decide("nobody", "", "doc")` must raise, not return DENY". |
| 14 | State discipline | Y | 10 | — | "`__slots__` … `__setattr__`/`__delattr__` raise"; "No torn reads, by construction". |
| 15 | Testability | Y | 10 | — | `decide` is a pure query. |
| 16 | Performance | N/A | | | |
| 17 | Security | N/A | | | |

**Profile Y-stage-1:** grade = (13×10 + 8×1 + 7×2) / (13 + 1 + 2) = 152/16 = **9.50**, worst **7**, (#S3,#S4) = **(0,0)**, gate **CLEAR**.

### D1 verdict: **Y**

Y wins on the dimension this judge weights most. Every invariant lives in the type that holds it:
- Y resolves role names to `_Role` objects, so a dangling role cannot be represented.
- Y's single validating constructor is the only path to a model.
- Y has one `_identifier` owner.

X splits the invariant (in the builder) from the data (in a public, non-validating model). X also exposes the
representation and states the identifier rule twice.

**Robustness check.** I removed each design's removable local blemishes:
- X: the duplicated identifier rule.
- Y: the truthy `Decision` and the YAGNI guards.

Y then scores 10.0 and X scores 9.0, so the verdict does not flip. X's remaining S2s are structural: the anemic model,
the exposed representation, and a dangling reference that the representation allows.

---

## 2. D2: change absorption (stage 1 → stage 2)

### Survival classification

Rule used: a component whose responsibility or interface changed is **reopened**; one that disappeared is
**discarded**. Internal seams are counted with the component whose interface changed, and public seams are listed
separately.

**X**

| Stage-1 component / seam | Class | Evidence |
|---|---|---|
| `EntitlementModel` (and the decision→model accessor seam) | **reopened** | Representation retyped: "`grants: Mapping[RoleId, Mapping[Permission, frozenset[Grant]]]`". Accessor meaning changed: "`grants_of(role)` … now returns the role's permissions that have an ALLOW grant with no window … It is not used by the decision". New `lineage`, `grants_for`. |
| `DecisionService.check` (owner of the rule) | **reopened** | Stage 1: "The rule, in full … ALLOW if any(...)". Stage 2: "The service owns steps 1-3", and the rule moves out to `combining.deny_overrides`. |
| `Permission` | survived | "`Permission` is unchanged." |
| `Decision` | survived (moved) | "`Decision` moves there from `decision.py` … the public path does not change". |
| `build_model` / building | extended | "gains a `parents=` argument and accepts `Grant` entries alongside stage-1 tuples". |
| errors | extended | "adds `EvaluationInstantRequired(InvalidRequestError)`". |
| public seam `check(user, action, resource)` | extended | "gains a keyword-only `now`" (optional); "Existing callers are source-compatible". |
| public seam `build_model(roles, assignments)` | extended | D7: "every stage-1 `build_model` call builds an equivalent model". |

**X: reopened + discarded = 2** (EntitlementModel; DecisionService.check).

**Y**

| Stage-1 component / seam | Class | Evidence |
|---|---|---|
| `_Permission` | **discarded** | "`_Grant` — NEW, replaces stage-1 `_Permission`"; "`_Permission` is removed". |
| `_Role` | **reopened** | "`_Role.grants(permission) -> bool` becomes `_Role.effects(action, lineage, instant) -> frozenset[_Effect]`". |
| `EntitlementModel.decide` (rule owner and public seam) | **reopened** | "The grant rule's single owner, `decide`, is split into three owners". The seam also breaks: "A stage-1 call `decide(u, a, r)` now raises Python's `TypeError`". |
| `json_file` edge | **reopened** | Its responsibility shrank: "Grant-key validation moves from `json_file` into the core (`_parse_grant`)". |
| `_identifier` | survived | "unchanged (A4)". |
| `Decision`, errors, `__main__` | survived | "`Decision` … unchanged (A5)"; "Errors — … (unchanged set)". |
| `EntitlementModel.__init__` | extended | "The stage-1 two-phase contract is kept, and the new inputs slot into it"; `parents` is optional. |
| `cli` | extended | "gains: --now". |

**Y: reopened + discarded = 4** (`_Permission` discarded; `_Role`, `decide`, `json_file` reopened).

**Oracle reading.** Neither stage-1 design had a grant/effect abstraction: both answered with `any(...)` over a flat
permission set. Both therefore reopened the decision core, exactly as the survival oracle predicts. Y's count is
higher for two reasons:
- Its finer stage-1 owners (`_Permission` equality as the match rule, `_Role.grants -> bool`) each encoded a clause
  that stage 2 changed.
- It chose a breaking `now` seam where X chose an optional one.

**D2 winner on survival: X (2 vs 4).** Per `measurement.md`, survival is weak corroboration and does not lead the
comparison.

### X-stage-2 form

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 8 | S1 | **b fails.** The service reaches through each grant to its window and decides the "no window" case itself: "the service keeps the grants where `window is None or window.contains(now)`". a *ref* §5, c *ref* §7, d pass (`Window.contains`). 3/4 = 8. |
| 2 | Interface / calibration / concept fit | Y | 10 | — | D6: "`Effect` and `Decision` are separate enums … A grant *says* deny, and a decision *is* deny". Deny is an effect, not an absence. |
| 3 | ISP | Y | 10 | — | The decision uses `roles_of`, `lineage` and `grants_for`. Surface width *ref* §7. |
| 4 | Primitive obsession / types | Y | 6 | S2 | **b fails.** The window invariant sits in the builder, not the type. `Window(valid_from, valid_until)` "has one method, `contains(t)`", and `from < to` plus awareness are checked only in `build_model`, while `Window`/`Grant` are public ("Re-export `Effect`, `Window`, `Grant`"). The stage-1 dangling-`RoleId` representation is carried over. **c fails.** "Always in force" has two representations: `Grant(..., window: Window \| None = None)` and a valid `Window(None, None)`. Repro: `roles={"r": [Grant(Permission("read","doc-42"), window=Window(None, None))]}`, `assignments={"alice": ["r"]}`, then `check("alice","read","doc-42")` with no `now`. Step 3 says "If `now` is `None` and any candidate has a window, the service raises `EvaluationInstantRequired`", so the call raises instead of returning **ALLOW** (the grant is unbounded, and "A grant with no window SHALL apply at every instant"). The two spellings are also distinct set members, which breaks set semantics. a, d, e pass. 3/5 = 6. |
| 5 | Anemic domain model | Y | 3 | S2 | **a fails.** "Keep the model free of policy. The hierarchy and windows are data". **c fails.** `Grant(permission, effect, window)` is a pure data class; its applicability (action, lineage, window) is computed in `DecisionService` steps 2–3. b passes: `Window.contains`. 1/3 = 3. |
| 6 | Cohesion / coupling / OCP | Y | 10 | — | "`combining` imports `Effect` from `model` and `Decision` from `outcome`, and nothing else". X3 lands in `combining` only; X4 in `lineage` only ("neither `combining` nor `decision` would change"). |
| 7 | Leaky abstractions | Y | 5 | S3 | **a fails, and is worse than at stage 1.** The public model still exposes `grants` (now retyped), `lineage`, `grants_for` and `roles_of`. It also keeps a public accessor whose meaning now contradicts the rule: "`grants_of(role)` … returns the role's permissions that have an ALLOW grant with no window … It is not used by the decision". Repro: `roles={"r": [allow("read","doc-42"), deny("read","doc-42")]}`, `assignments={"alice": ["r"]}`. `model.grants_of("r")` returns `{Permission("read","doc-42")}`, while `check("alice","read","doc-42")` returns **DENY**. A stage-1 caller using that public accessor now reads "granted" where the decision is deny. b, c, d pass. 3/4 = 8, capped at 5. |
| 8 | SRP / God object | Y | 10 | — | Each step has a named owner: gather, time and combine. |
| 9 | Rule enforcement: one owner | Y | 10 | — | R5 precedence is owned by `deny_overrides` alone ("This function is the whole answer to 'who wins'"). R6 reach is "exactly the choice to iterate over `lineage(resource)` … in this one line". R7 is step 3 and applies to both effects. d *ref* §7. |
| 10 | DRY | Y | 5 | S2 | **a fails** (carried from stage 1). **b fails.** The "aware instant" rule is stated twice: the builder checks "Each window bound must be `None` or an aware `datetime`, where `tzinfo` is set and `utcoffset()` is not `None`", and `check` checks "`now` must be `None` or an aware `datetime`". c, d pass. 2/4 = 5. |
| 11 | Naming and failure | Y | 8 | S1 | **c fails.** The public contract depends on the data, and the design says so itself: "a caller that worked yesterday can fail after someone adds a windowed grant". It is loud and fail-closed, so S1. a, b, d pass (`Decision`/`Effect` `__bool__` raise). 3/4 = 8. |
| 12 | Size / YAGNI | Y | 10 | — | `outcome.py` exists because "so that both `decision` and `combining` can use it without an import cycle"; `grants_of` is kept for stage-1 public callers. |
| 13 | Functional correctness | Y | 2 | S4 | **c fails: a time edge case that fails open.** See §3 for the reproducing input. X promises bounds are "compared as instants, independent of the timezone in which each one is written", but it compares the caller's raw aware datetimes in `Window.contains`. Python compares two aware datetimes that share a `tzinfo` object by wall time, ignoring `fold`, so an in-force deny across a DST fold is dropped and the answer is **ALLOW** instead of **DENY**. a, b, d, e, f pass: C7–C14 appear as scenarios, including "Expired deny no longer overrides" and "Deny on an ancestor beats an allow on the descendant". 5/6 = 8, capped at 2. |
| 14 | State discipline | Y | 10 | — | "The service holds no state beyond the model reference, and it never reads the clock". |
| 15 | Testability | Y | 10 | — | `now` is injected, and `deny_overrides` "can be checked against a truth table". |
| 16 | Performance | N/A | | | |
| 17 | Security | N/A | | | |

**Profile X-stage-2:** grade = (8×10 + 8 + 8 + 6×2 + 3×2 + 5×2 + 5×4 + 2×8) / (8+1+1+2+2+2+4+8) = 160/28 = **5.71**,
worst **2**, (#S3,#S4) = **(1,1)**, gate **BLOCKED** (row 13c).

*Sensitivity check.* With the one-line S4 fixed (normalise instants to UTC), row 13 = 10 and the grade is 154/21 =
**7.33**, CLEAR.

### Y-stage-2 form

| § | principle | applies | score | sev | finding + citation |
|---|---|---|---|---|---|
| 1 | TDA / LoD | Y | 10 | — | "`decide` never reads `grants` (Tell-Don't-Ask)". The chain `decide → _Role.effects → _Grant.applies → _Window.contains` tells at each hop. |
| 2 | Interface / calibration / concept fit | Y | 10 | — | "`_Effect` … **It is not `Decision`**". `_ALWAYS = _Window(None, None)` is the genuine (−∞, +∞) interval, used for every grant. `now: datetime` is keyword-only, required and aware. |
| 3 | ISP | Y | 10 | — | "The public surface of `EntitlementModel` is exactly `{decide}`". |
| 4 | Primitive obsession / types | Y | 7 | S2 | **d fails.** At the in-code public seam, a grant is a stringly mapping: `roles: Mapping[str, Iterable[tuple[str, str] \| Mapping[str, object]]]`, with `"effect": "deny"` and `"from"/"to"` as dict keys. The design concedes "a misspelled key is caught when the model is built, not by a type checker". It is one localised clump, caught at the single owner, so S2. a, b, c, e pass: `_Window.__post_init__` makes "an empty or inverted window **cannot be represented**", `_Hierarchy` "cannot hold a cycle", and a grant "gets `_ALWAYS`, never `None`". 4/5 = 8, capped at 7. |
| 5 | Anemic domain model | Y | 10 | — | `_Grant.applies`, `_Role.effects`, `_Hierarchy.lineage` and `_Window.contains` each own their clause. |
| 6 | Cohesion / coupling / OCP | Y | 10 | — | Its change table maps each foreseeable change to one owner: X3 → `_combine`, X4 → `_Hierarchy`, X5 → `_Window`. Dependencies are unchanged and acyclic. |
| 7 | Leaky abstractions | Y | 10 | — | "There is no `lineage`, `roles_of`, `explain` or iteration". "No new public type is added". Each `ValueError` is translated once per boundary. |
| 8 | SRP / God object | Y | 10 | — | Each private type "owns one rule". `_parse_grant` is separate from the constructor. |
| 9 | Rule enforcement: one owner | Y | 10 | — | `_combine` is "the **only code in the package that produces a `Decision` value**", and an AST fitness test pins that. The window lives in every grant: "B5 … holds **by construction**". The new cases are absorbed in the existing constructor phases: "The stage-1 rule absorbs the new case unchanged". |
| 10 | DRY | Y | 10 | — | `_instant` is "the one owner of 'a supplied instant'", used at both entries. The key list is "Two copies … would be duplicated knowledge" and moves to `_parse_grant`. |
| 11 | Naming and failure | Y | 7 | S2 | **c fails.** The truthy `Decision` is carried over ("`class Decision(enum.Enum): # unchanged (A5)`"). Repro as at stage 1: `if model.decide("bob","read","doc-42", now=T):` runs the allow-branch for `Decision.DENY`. a, b, d pass. 3/4 = 8, capped at 7. |
| 12 | Size / YAGNI | Y | 8 | S1 | **c fails.** More guards against callers that do not exist: "`datetime` subclass as `now` behaves like its plain value", "`datetime.min`/`max` with an offset → a clean error", "a 10 000-deep chain", and normalized-key collisions for `str` subclasses. a, b, d pass. 3/4 = 8. |
| 13 | Functional correctness | Y | 10 | — | `_instant` "**Normalizes** the value to an **exact `datetime` in UTC**", so the DST-fold case is handled ("a DST-fold instant … answers by instant"). C7–C14 are traced in §9.1–9.6. Validation runs before lookup ("`decide("nobody", "read", "x", now=naive)` raises"). |
| 14 | State discipline | Y | 10 | — | "the library never reads the clock"; the only clock read is in `cli`. Hierarchy and grants sit in "**one** immutable object". |
| 15 | Testability | Y | 10 | — | `now` is a value ("every test would need a fake" is avoided). |
| 16 | Performance | N/A | | | |
| 17 | Security | N/A | | | |

**Profile Y-stage-2:** grade = (12×10 + 7×2 + 7×2 + 8×1) / (12+2+2+1) = 156/17 = **9.18**, worst **7**,
(#S3,#S4) = **(0,0)**, gate **CLEAR**.

### D2 verdicts

- **On survival: X** (2 reopened or discarded, vs 4 for Y).
- **On the stage-2 form: Y**: 9.18 / worst 7 / (0,0) / CLEAR, against X's 5.71 / worst 2 / (1,1) / BLOCKED.
  - The verdict does not rest on X's single S4. With it fixed, X reaches 7.33 and still has an anemic
    `Grant` + manager, a builder-held window invariant, two spellings of "no window", and a public accessor with a
    stale meaning.
  - Y's deductions are local: a stringly grant seam, the truthy enum, and over-guarding.
- Y reopened more owners, but each owner it reopened was one clause of the rule, and the result has one owner per
  rule that cannot be bypassed. X reopened fewer, but kept its invariants outside the types that hold them.

---

## 3. Correctness traps (spec-and-oracle.md)

| Trap | X | Y |
|---|---|---|
| **1. Deny as absence** | **Avoided.** "`Effect(Enum)`: `ALLOW` and `DENY` … A grant's effect is a different concept from a decision's outcome"; "A deny alone is not an allow" scenario. Stage 1's `any(...)` core was reopened, as the oracle requires. | **Avoided.** "`_Effect.DENY` is a value that a grant carries"; `_combine` names the explicit and absence cases as separate branches. The stage-1 line "Deny is the absence of any grant" was explicitly superseded (§13.3). |
| **2. Inheritance threaded through call sites** | **Avoided.** Lineage is computed once per model ("The builder precomputes lineages", which expands the path, not the grants) and consumed in one line: "that choice lives in this one line". | **Avoided.** "`lineage(R)` owns reach … The fallback lives here and not in `decide`". It explicitly rejects "Expanding grants down to descendants at build time". |
| **3. Time check scattered / precedence undefined** | **Structurally avoided.** Step 3 filters every candidate, allow and deny alike, before `deny_overrides` ("This SHALL apply equally to allows and denies"), and precedence has one defined order. **But the time predicate itself is wrong at a DST fold** (below). | **Avoided.** "the window is a field of every `_Grant`, and `applies` has one path for both effects". There is one `_combine`, and time is compared in UTC. |

**Specificity note (no differential).** The oracle says "most specific wins; … a deny on the path still wins". The
card says "A deny anywhere on the path still wins over an allow". With only two effects, "deny anywhere wins" makes
specificity unable to change any outcome. Both designs state this reading and pin it with the same case: X in D1
("A descendant allow cannot lift an ancestor deny"), Y in §9.2 ("deny org-root + allow doc-42; ask doc-42 → DENY").
They answer identically, so I report no failure for either.

### Reproducing inputs for every reported failure

1. **X §13c: DST fold fails open (S4).**
   ```python
   berlin = ZoneInfo("Europe/Berlin")               # cached: the same tzinfo object every call
   model = build_model(
       roles={"staff":  [allow("read", "doc-42")],
              "freeze": [deny("read", "doc-42",
                              valid_from=datetime(2026,10,25,0,0, tzinfo=berlin),           # 22:00Z Oct 24
                              valid_until=datetime(2026,10,25,2,30, fold=1, tzinfo=berlin))]}, # 01:30Z
       assignments={"alice": ["staff", "freeze"]})
   DecisionService(model).check("alice", "read", "doc-42",
                                now=datetime(2026,10,25,2,45, fold=0, tzinfo=berlin))         # 00:45Z
   ```
   - Validation passes: both bounds are aware, and `from < to` by wall time.
   - The instant 00:45Z is inside the deny window [22:00Z, 01:30Z), so the **correct answer is DENY**.
   - X's `Window.contains` evaluates `now < valid_until` on the same `tzinfo`. Python then compares the base wall
     times, 02:45 < 02:30, which is False. The deny is dropped, and `deny_overrides({ALLOW})` returns **ALLOW**.
   - This contradicts X's own requirement: "compared as instants, independent of the timezone in which each one is
     written".
   - Y normalises both values through `_instant` to 00:45Z and 01:30Z and returns DENY.

2. **X §4c: two spellings of "no window" (S2).**
   - Input: `Grant(Permission("read","doc-42"), window=Window(None, None))`, then
     `check("alice","read","doc-42")` with no `now`.
   - X raises `EvaluationInstantRequired`. The correct result is ALLOW, because the grant has no bounds.

3. **X §7a: stale public `grants_of` (S3).**
   - Input: role `r = [allow("read","doc-42"), deny("read","doc-42")]`.
   - `model.grants_of("r")` returns `{Permission("read","doc-42")}`, while `check` returns DENY.
   - The accessor reports a grant that the decision overrides.

4. **Y §11c (both stages): truthy `Decision` (S2).**
   - Input: `if model.decide("bob","read","doc-42", now=T): serve()`, where bob has no grants.
   - `Decision.DENY` is truthy, so `serve()` runs. The correct behaviour is that it does not run.

Every other finding in the forms is a structural quality finding, not an output failure.

---

## 4. Residual tells and controls

- **Method guess and vocabulary capture.** My pre-scoring guess (GUESS.md) was X = OpenSpec, Y = aims, and the rubric
  is Y's own principle set. Y cites it by section ("design-principles §4") and uses its words ("Tell-Don't-Ask",
  "concept fit", "Falsifier", "present force").
  - *Control:* I credited only specified mechanisms. For example, I credited `_Window.__post_init__` rejecting
    `start >= end`, not the phrase "cannot be represented". I credited `_combine` being the sole producer of
    `Decision`, not the word "owner".
  - I deducted Y wherever its structure fell short, whatever its prose said: the truthy `Decision` (a hole X
    closed), a stringly grant seam, and over-guarding.
  - I gave X its genuine wins: the `__bool__` guard, `Effect` kept separate from `Decision`, the survival count, and
    a compatible `now`.
- **Length and trace tables.** Y is about 30% longer and traces far more cases. Row 13 was decided only by a
  demonstrable wrong output with an input, which cut against the shorter design. I did not credit Y's trace tables
  as correctness evidence; Y's row 13 = 10 rests on the `_instant` normalisation mechanism.
- **Process markers.** Y's front matter says "revised after one mandatory review round" and "panel-merged". X's
  `the-method/changes/archive/...` path and its proposal/spec/tasks scaffolding are workflow artifacts. The substrate
  says method outputs are "stripped before the architecture is judged", so I ignored both as evidence.
- **Disposition bias.** Invariant-ownership favours Y's validate-in-constructor style over X's builder/model split,
  which is a legitimate pattern. *Control:* X's split was scored S2 (quality), not S4 (§9 one-owner), because X's
  *intended* path does funnel through `build_model`. The principles treat one-owner as "a design intent, not a
  language-enforced guard".
- **The single large swing.** X's row-13 S4 is one fixable time-comparison defect weighted ×8. I report X's stage-2
  grade both with it (5.71, BLOCKED) and without it (7.33, CLEAR). The D2 form verdict is Y either way, so a
  removable local blemish does not decide it.
- **Y's breaking `now` seam.** Y makes `now` required, so stage-1 three-argument calls raise `TypeError`. X keeps
  `now` optional. I did not score Y's choice as a correctness failure: no wrong answer results, and the card says
  "relative to a supplied now". It is counted where it structurally belongs, as part of Y's `decide` reopen in the
  survival tally.
