# Entitlements — Stage 2 (the-method)

> Design only. No implementation code. This is the the-method **change** that lands on top of the
> frozen stage-1 specs. It contains: the updated/added capability specs (new requirements +
> scenarios), a new change bundle (`a-design-doc`, `a-design-doc`, `a-design-doc`), a **SURVIVAL**
> section tracing each stage-1 spec/component, and a **Cost** section.
>
> Change id: **`add-deny-inheritance-and-time`**. Stage-1 specs are treated as frozen input;
> this change edits them by adding and revising requirements, in the the-method style of showing
> the *delta* against the frozen baseline.

---

## Card under design (stage-2 change request)

> The model gains three capabilities combining in **one** decision.
> (1) **EXPLICIT DENY** overrides any allow, even from another role (deny wins).
> (2) **RESOURCE INHERITANCE**: resources nest in groups; a grant on a group applies beneath it
> unless a more specific descendant grant says otherwise; a deny on the path still wins.
> (3) **TIME-BOUNDED GRANTS** carry a validity window `[from, to)`; outside it they don't apply;
> decision uses a supplied `now`.
> Stage-1 simple answer unchanged where features absent.

The hard part is **combination**: a single verdict must fold precedence (deny > allow), the
resource path (specificity), and time (window filtering) together, and still collapse to the
stage-1 union rule when none of the three features is present.

---

# Part 1 — Capability specs after this change (deltas over the frozen baseline)

## Capability: `entitlements-model` (MODIFIED)

**Purpose (unchanged in intent, widened in scope).** Still owns the durable data and its
integrity. Now the data also carries grant **effect** (allow/deny), a **resource hierarchy**,
and a **validity window** on each grant.

### Requirement: Subjects — *survives unchanged*
(Verbatim from stage 1. Users identified by stable `user_id`. Scenario retained.)

### Requirement: Permissions as (action, resource) pairs — *survives unchanged*
(Verbatim from stage 1. A permission is still exactly `(action, resource)`, exact match, both
fields required.)

### Requirement: Roles hold grants (RENAMED from "grant permission sets")
The system must represent a role as a collection of **grants**. A grant is a permission plus
an **effect** and a **validity window**: `Grant { permission, effect ∈ {ALLOW, DENY}, from,
to }`. A grant with `effect = ALLOW` and an unbounded window is exactly a stage-1 grant, so
existing roles keep their meaning.

- **Scenario: stage-1 grant is a special case**
  - **Given** a role `editor` whose only grant is `{ ("write","doc:42"), ALLOW, from=−∞, to=+∞ }`
  - **When** it is compared to a stage-1 `editor` granting `("write","doc:42")`
  - **Then** it grants the same authority at all times.

- **Scenario: a deny grant is representable**
  - **Given** a role `quarantine` with grant `{ ("write","doc:42"), DENY, −∞, +∞ }`
  - **When** the model stores it
  - **Then** the role carries a negative grant on that permission.

### Requirement: Users hold one or more roles — *survives unchanged*
(Verbatim. Many-to-many; referential integrity retained.)

### Requirement: Resource hierarchy (NEW)
The system must let resources nest: each resource MAY declare exactly one parent
**resource group**, forming a forest (no cycles). A grant whose `resource` names a group
applies to that group and, by inheritance, to every descendant resource — subject to the
precedence rules of `access-decision`.

- **Scenario: acyclic nesting**
  - **Given** `doc:42` whose parent is `folder:F`, and `folder:F` whose parent is `space:S`
  - **When** the ancestry of `doc:42` is enumerated
  - **Then** it is `[doc:42, folder:F, space:S]`, most-specific first, and setting `space:S`'s
    parent to `doc:42` is rejected as a cycle.

- **Scenario: root resource**
  - **Given** `space:S` with no parent
  - **When** its ancestry is enumerated
  - **Then** it is `[space:S]`.

### Requirement: Validity window integrity (NEW)
The system must store each grant's window as a half-open interval `[from, to)` with
`from < to` (or an explicit unbounded sentinel on either end), and must reject a window with
`from ≥ to`.

- **Scenario: half-open interval**
  - **Given** a grant with `from = 2026-01-01T00:00Z`, `to = 2026-02-01T00:00Z`
  - **When** `now = 2026-02-01T00:00Z`
  - **Then** the grant is **not** active (upper bound is exclusive).

- **Scenario: empty window rejected**
  - **Given** a grant with `from = to`
  - **When** the model validates it
  - **Then** it is rejected.

---

## Capability: `access-decision` (MODIFIED — the rule is reformulated, superset of stage 1)

**Purpose (unchanged).** Still answers `may U do A on R?`. The verdict is still `ALLOW|DENY`,
but the query now carries `now`, and the rule folds effect precedence, resource specificity,
and time.

### Requirement: Decision query shape (REVISED)
The system must accept a query `(user_id, action, resource, now)` and return `ALLOW` or `DENY`.
The `now` is supplied by the caller (the engine reads no clock).

- **Scenario: now is an input, not ambient**
  - **Given** identical `(user, action, resource)` evaluated with two different `now` values
  - **When** decided
  - **Then** each verdict depends only on its supplied `now`; the engine consults no wall clock.

### Requirement: Consider only active grants (NEW — time filter runs first)
The system must, before applying any precedence rule, discard every grant whose window does
not contain `now` (i.e. keep grant iff `from ≤ now < to`).

- **Scenario: expired grant ignored**
  - **Given** the only grant that would allow `("read","doc:42")` has window
    `[2025-01-01, 2025-06-01)` and `now = 2026-09-18`
  - **When** decided
  - **Then** that grant contributes nothing and (absent others) the verdict is `DENY`.

- **Scenario: not-yet-valid grant ignored**
  - **Given** an allow grant with `from` in the future relative to `now`
  - **When** decided
  - **Then** it does not apply.

### Requirement: Collect grants along the resource path (NEW)
The system must gather, from all roles the user holds, every **active** grant whose
`resource` equals the queried resource **or any of its ancestors**, tagging each with its
**specificity** = the distance from the queried resource to the grant's resource (0 = the
resource itself, 1 = its parent, …). Action must still match exactly.

- **Scenario: inherited allow**
  - **Given** `folder:F` is granted `("read", ALLOW)` and `doc:42`'s parent is `folder:F`,
    with no grant directly on `doc:42`
  - **When** `("read","doc:42")` is queried
  - **Then** the folder grant applies at specificity 1.

### Requirement: Deny wins across everything (NEW — top precedence)
The system must return `DENY` if **any** active grant collected along the path (at any
specificity, from any role) has `effect = DENY` for the queried action. An explicit deny
overrides every allow, including allows from other roles and more-specific allows.

- **Scenario: deny beats allow from another role**
  - **Given** role `editor` allows `("write","doc:42")` and role `quarantine` denies
    `("write","doc:42")`, both active
  - **When** the user (holding both) queries `("write","doc:42")`
  - **Then** the verdict is `DENY`.

- **Scenario: deny on an ancestor beats a specific allow**
  - **Given** `space:S` denies `("read", ...)`, `doc:42` (a descendant) allows `("read", ...)`,
    both active
  - **When** `("read","doc:42")` is queried
  - **Then** the verdict is `DENY` — a deny on the path wins regardless of specificity.

### Requirement: Specificity resolves competing allows only (NEW — below deny)
The system must, **when no applicable deny exists**, decide allow vs. deny by the
**most specific** applicable grant: among collected allow grants, the one at the smallest
specificity distance governs; a more specific ALLOW overrides a less specific absence, and a
more specific grant "wins" over ancestor grants of the opposite... — but since deny already
short-circuits above, at this stage only allows remain, so *any* remaining active allow on the
path yields `ALLOW`.

- **Scenario: descendant allow under a silent ancestor**
  - **Given** no deny anywhere on the path, `folder:F` grants nothing, `doc:42` allows
    `("read", ...)`
  - **When** `("read","doc:42")` is queried
  - **Then** `ALLOW`.

- **Scenario: ancestor allow inherited by silent descendant**
  - **Given** no deny on the path, `folder:F` allows `("read", ...)`, `doc:42` is silent
  - **When** `("read","doc:42")` is queried
  - **Then** `ALLOW` (inheritance), because the closest applicable grant is the ancestor allow
    and nothing more specific contradicts it.

> **Precedence, stated once:** (1) drop grants outside `[from,now,to)`; (2) if any active DENY
> is on the path for the action → `DENY`; (3) else if any active ALLOW is on the path → `ALLOW`;
> (4) else `DENY` (default deny, unchanged). Specificity only matters when *both* an allow and a
> deny could apply — and rule (2) already resolves that in deny's favor — so within a single
> effect, presence anywhere on the path suffices. This keeps the model total and unambiguous.

### Requirement: Default deny — *survives unchanged*
(Verbatim from stage 1. No applicable active grant ⇒ `DENY`; unknown user ⇒ `DENY`, no leak.)

### Requirement: Collapse to stage-1 answer when features absent (NEW — compatibility guard)
The system must, for any query where no deny grants exist, no resource has a parent, and all
grants are unbounded, return exactly the stage-1 union-rule verdict.

- **Scenario: feature-free query is stage-1 identical**
  - **Given** a model with only unbounded ALLOW grants and a flat resource space
  - **When** any `(user, action, resource, now)` is decided
  - **Then** the verdict equals the stage-1 `decide(user, action, resource)` verdict.

### Requirement: Determinism (REVISED to include the new inputs)
The system must make the verdict a pure function of `(model, query including now)`,
independent of the order roles, grants, or path nodes are examined.

- **Scenario: order independence with mixed effects**
  - **Given** a path bearing both allow and deny grants across several roles
  - **When** evaluated in any traversal order
  - **Then** the verdict is identical (because deny short-circuits set-wise, not order-wise).

---

# Part 2 — Change bundle: `add-deny-inheritance-and-time`

## a-design-doc — why + what

**Why.** Three real needs the frozen positive-union model cannot express: security teams must
*revoke* an action even when some role still allows it (deny); administrators must grant on a
*container* and have it flow down while still overriding per item (inheritance); and access
must be *temporary* (time windows). Each is common; together they define most real RBAC/ABAC
policy. They must combine in one verdict, not three separate checks.

**What.**
- Extend `entitlements-model`: grants gain `effect ∈ {ALLOW,DENY}` and a window `[from,to)`;
  resources gain an optional parent forming an acyclic hierarchy.
- Reformulate `access-decision` as a four-step precedence: time-filter → deny-wins →
  allow-present → default-deny; `now` becomes a query input; resource path is walked
  most-specific to root.
- Preserve stage-1 behavior exactly when the three features are absent (compatibility guard
  requirement).

**Non-goals (kept out to bound the change):** wildcard/pattern permissions; deny at a chosen
specificity *overriding* a more specific allow (we take the strict "deny always wins" reading
the card states); role-level (as opposed to grant-level) time windows; relative/recurring
schedules; delegation.

## a-design-doc — technical design, component structure, decisions

**Component structure (delta).**

```
  query (U, A, R, now)         +----------------------------+
  -------------------------->  |       access-decision      |
                               |  1 time-filter (now)       |
                               |  2 collect along R's path  |----+
                               |  3 deny-wins / allow / deny |    | reads
                               +----------------------------+    v
                                        pure reads          +----------------------+
                                                            |   entitlements-model |
                                                            |  grants{effect,window}|
                                                            |  resource hierarchy   |
                                                            +----------------------+
```

New/changed model reads the engine needs: `ancestry(resource) → [resource, …, root]` and
`active_grants_for(user, action, resource_in_path, now)`. Both pure.

**Evaluation algorithm (prose, no code).** Given `(U,A,R,now)`:
1. Compute `path = ancestry(R)` (most specific first).
2. From every role U holds, collect grants whose `action = A`, whose `resource ∈ path`, and
   whose window contains `now`. Tag each with `specificity = index of its resource in path`.
3. If the collected set contains **any** DENY → return `DENY`.
4. Else if it contains **any** ALLOW → return `ALLOW`.
5. Else → return `DENY` (default deny).

Steps 3–4 make deny strictly dominate; step 2's time filter makes windows irrelevant unless a
grant is currently active; the flat/unbounded/allow-only case reduces to "is the exact pair
granted by any role", i.e. stage 1.

**Key decisions (ADRs this change files).**

- **D6 — Deny is unconditional dominance.** The card says "deny wins … even from another role"
  and "a deny on the path still wins." We therefore do *not* let a more specific allow beat a
  less specific deny. Specificity governs among allows and among denies but never lets allow
  overturn deny. *Rationale:* the card's wording is explicit and this is the fail-safe reading.
- **D7 — Effect+window live on the grant, not the role or the assignment.** A grant becomes
  `{permission, effect, from, to}`. *Rationale:* smallest change; a stage-1 grant is the
  `{ALLOW, unbounded}` special case, so the compatibility guard is structural, not bolted on.
- **D8 — Resource hierarchy is a forest of parent pointers, acyclic, single-parent.**
  *Rationale:* single-parent keeps "the path" a line, so specificity is a total order and the
  precedence rule is unambiguous; multi-parent DAGs would reopen the tie-break question.
- **D9 — `now` is an explicit query parameter; the engine reads no clock.** *Rationale:*
  determinism (D3 extended) and testability; the same model+query+now always yields the same
  verdict, and callers control the evaluation instant.
- **D10 — Half-open windows `[from,to)`.** *Rationale:* adjacent windows tile without overlap
  or gap; the boundary case is unambiguous.
- **D11 — Compatibility is a first-class requirement, not an accident.** The "collapse to
  stage-1" requirement is testable on its own so future changes cannot silently break the base
  case.

**Where the stage-1 seam paid off.** Stage 1 phrased the rule as "is `p` in the *effective
set*." Stage 2 keeps that shape but redefines how the effective set is gathered (path + time)
and adds a precedence fold over it. The engine/model split (D4) meant the storage change and
the rule change are describable independently.

## a-design-doc — ordered checklist (no code)

1. [ ] Amend `entitlements-model`: add `effect` and `[from,to)` to grants; add single-parent
       acyclic resource hierarchy; add window and cycle integrity rules + scenarios.
2. [ ] Amend `access-decision`: add `now` to the query; add time-filter, path-collection,
       deny-wins, and specificity requirements; add the "collapse to stage-1" guard.
3. [ ] Restate the precedence as the canonical 4-step rule; record it once in the spec.
4. [ ] Record ADRs D6–D11 (deny dominance, grant-level effect+window, single-parent forest,
       explicit `now`, half-open windows, compatibility as requirement).
5. [ ] Verify the survival trace (below): confirm each surviving stage-1 requirement is either
       carried verbatim or is a provable special case of a stage-2 requirement.
6. [ ] Define acceptance scenarios: expired/future grants, inherited allow, deny across roles,
       deny on ancestor beating specific allow, feature-free equals stage-1.
7. [ ] Re-freeze the amended specs as the new baseline for any stage 3.

---

## SURVIVAL

Per frozen stage-1 spec / component: **survived / extended / reopened / discarded**, and
whether the change is **additive** or a **rewrite**.

| Stage-1 item | Fate | Additive vs rewrite | Note |
|---|---|---|---|
| `entitlements-model` · Subjects (users) | **survived** | additive | verbatim; untouched. |
| `entitlements-model` · Permission = (action,resource) | **survived** | additive | still the atomic pair; exact match preserved. |
| `entitlements-model` · "Roles grant permission sets" | **extended** | additive (superset) | renamed to "roles hold grants"; a stage-1 grant = `{ALLOW, unbounded}`. No stored meaning lost. |
| `entitlements-model` · Users hold ≥1 role | **survived** | additive | unchanged. |
| `entitlements-model` · Pure reads | **survived** | additive | new reads (`ancestry`, active-grant filter) added, still pure. |
| *(new)* Resource hierarchy | **added** | additive | forest of parent pointers. |
| *(new)* Validity-window integrity | **added** | additive | `[from,to)`, `from<to`. |
| `access-decision` · Query shape | **extended** | rewrite of signature (additive param) | gains `now`; verdict still `ALLOW|DENY`. |
| `access-decision` · Allow on any granting role (union) | **reopened** | rewrite (subsumed) | union survives *within a single effect* but is now step (4) of a precedence fold, no longer the whole rule. Guarded by the "collapse to stage-1" requirement. |
| `access-decision` · Default deny | **survived** | additive | verbatim; now step (5). |
| `access-decision` · Determinism | **extended** | additive | now includes `now`; deny short-circuit keeps order-independence. |
| *(new)* Time filter / path collection / deny-wins / specificity / compatibility guard | **added** | additive | the three requested features + the guard. |
| Component: `entitlements-model` store | **survived (widened)** | additive | same entities plus fields and parent pointers. |
| Component: `access-decision` engine | **reopened** | rewrite of the rule, same interface shape | loop replaced by 4-step precedence over the collected active grants. |
| ADRs D1–D5 | **survived** | additive | D2 (exact match), D3 (set/union), D4 (split), D1/D5 (default deny, binary verdict) all still hold; D6–D11 layer on top, none contradicts D1–D5. |

**Nothing discarded.** No stage-1 requirement was deleted; the only genuine *rewrite* is the
core allow rule, and even that is preserved as a guaranteed special case rather than removed.

## Cost

| Stage | Passes | Approx. words |
|---|---|---|
| Stage 1 (`stage-1.md`) | 1 design pass (specs + bundle, frozen; no rework) | ~1,350 |
| Stage 2 (`stage-2.md`) | 2 passes: (a) delta specs + bundle, (b) survival/precedence reconciliation | ~1,850 |
| **Total** | **3 passes across 2 changes** | **~3,200** |

*Notes.* Stage 2's second pass exists because the three features interact: writing the deny/
specificity requirements forced a single canonical precedence statement and the "collapse to
stage-1" guard, which then had to be checked back against every surviving stage-1 requirement
(the SURVIVAL table). The stage-1 seams (effective-set framing, model/decision split, exact-
match atomic permission) meant the interaction was absorbed as *additive* requirements plus one
localized rule rewrite, rather than a ground-up redesign.
