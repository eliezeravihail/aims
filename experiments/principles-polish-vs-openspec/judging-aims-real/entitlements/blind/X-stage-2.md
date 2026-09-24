# Design X — stage 2



<!-- file: proposal.md -->

# Proposal

## Why

Stage 1 can only say yes through an exact role grant. It cannot say no explicitly, cannot grant access to a
whole folder, and cannot limit a grant to a time period. Callers need all three together: revoke one
resource inside a folder that was granted broadly, give a contractor access to `finance` for one quarter,
and trust that an explicit deny always beats an allow.

## What Changes

- **Grants carry an effect.** A role grant is either **allow** or **deny**. Stage-1 `(action, resource)`
  grants are still accepted and mean an unbounded allow.
- **Resources form a hierarchy.** The model gains an optional resource-containment relation. Each resource
  has at most one parent group, for example `doc-42 -> finance -> org-root`. A grant on a group applies to
  every resource beneath it. The hierarchy must be acyclic, and the build rejects it otherwise.
- **Grants may carry a validity window** `[from, to)`. Either bound may be open. A grant applies only at
  instants inside its window.
- **One combined decision rule (deny-overrides).** The applicable grants are the grants that satisfy all
  of these conditions:
  - a role assigned to U holds the grant
  - the grant names action A
  - the grant is on R or on an ancestor of R
  - the grant's window contains `now`

  If any applicable grant is a deny, the answer is **deny**. Otherwise, if any applicable grant is an allow,
  the answer is **allow**. Otherwise the answer is **deny**.
- **The question gains an evaluation instant.** `check(user, action, resource, *, now=None)`. When no `now`
  is supplied, the decision is still made if no time-bounded grant could affect the answer. If one could,
  the question is rejected as malformed. The service never reads the wall clock.
- Stage-1 models and stage-1 questions give exactly the stage-1 answers. There is no breaking change to
  the library surface.

Assumptions made instead of asking the product owner (repeated in design.md):

- "Unless a more specific grant on a descendant says otherwise" combined with "a deny anywhere on the path
  still wins" means that specificity never turns a deny into an allow. A descendant can narrow an ancestor
  allow only by adding a deny. A descendant allow cannot lift an ancestor deny. There is no "closest grant
  wins" rule.
- The hierarchy applies to resources only. Actions stay exact, and roles do not inherit from one another.
- Each resource has at most one parent, so the hierarchy is a forest. A group is itself a resource and can
  be the subject of a question.
- Window bounds and `now` must be timezone-aware datetimes. Instants are compared, not wall-clock readings.
- A deny whose window has not started or has ended does not apply. Nothing survives outside its window.

## Capabilities

### New Capabilities

None. The new behaviour extends the two existing capabilities.

### Modified Capabilities

- `entitlement-model`: grants gain an effect (allow or deny) and an optional validity window. The model
  gains a resource hierarchy. Validation now covers hierarchy cycles, self-parenting, malformed windows,
  and naive datetimes. The "no hierarchy" clause of the exact-pair requirement is replaced.
- `access-decision`: the any-allow rule becomes a deny-overrides rule over the applicable grants, which
  include inherited and time-filtered grants. The question gains an optional evaluation instant, with rules
  for when it is required. Malformed-question and determinism rules are extended to cover it.

## Impact

- `entitlements` package: the model value types grow (`Effect`, `Window`, `Grant`, resource parents).
  `build_model` gains a `parents=` argument and accepts `Grant` entries alongside stage-1 tuples.
  `DecisionService.check` gains a keyword-only `now`. The decision rule moves into a small pure combining
  function.
- Existing callers are source-compatible.
- No new runtime dependencies. `datetime` from the standard library is enough.


<!-- file: specs/access-decision/spec.md -->

# Spec Delta

## MODIFIED Requirements

### Requirement: Allow when any assigned role grants the exact permission
For a question `(user, action, resource)` asked at an evaluation instant, a grant SHALL be
**applicable** if and only if all of these hold:
- a role assigned to the user holds the grant
- the grant's action equals the action
- the grant's resource is the resource or one of its ancestors
- the grant applies at the evaluation instant

The service SHALL answer **allow** if and only if at least one applicable grant is an allow and no
applicable grant is a deny.

#### Scenario: Single role grants
- **WHEN** `alice` is assigned `editor`, `editor` grants `(write, doc-42)`, and the service is asked whether `alice` may `write` `doc-42`
- **THEN** the answer is allow

#### Scenario: Grant comes from one of several roles
- **WHEN** `alice` is assigned `viewer` and `editor`, only `editor` grants `(write, doc-42)`, and the service is asked whether `alice` may `write` `doc-42`
- **THEN** the answer is allow

#### Scenario: Grant on a group applies beneath it
- **WHEN** `doc-42` is in `finance`, `finance` is in `org-root`, `alice`'s role allows `(read, org-root)`, and the service is asked whether `alice` may `read` `doc-42`
- **THEN** the answer is allow

#### Scenario: Grant on a descendant does not apply upward
- **WHEN** `doc-42` is in `finance`, `alice`'s only grant allows `(read, doc-42)`, and the service is asked whether `alice` may `read` `finance`
- **THEN** the answer is deny

#### Scenario: Group grant does not reach siblings outside the group
- **WHEN** `doc-42` is in `finance`, `doc-7` is in `hr`, `alice`'s role allows `(read, finance)`, and the service is asked whether `alice` may `read` `doc-7`
- **THEN** the answer is deny

### Requirement: Deny by default
The service SHALL answer **deny** in every case not covered by the allow rule. This includes each of
these cases:
- a user who is not in the model
- an action or resource that no applicable grant mentions
- a case where the only matching grants are outside their validity windows

#### Scenario: Role lacks the permission
- **WHEN** `bob` is assigned `viewer`, `viewer` grants only `(read, doc-42)`, and the service is asked whether `bob` may `write` `doc-42`
- **THEN** the answer is deny

#### Scenario: Permission on a different resource
- **WHEN** `bob`'s roles grant `(read, doc-42)` and the service is asked whether `bob` may `read` `doc-43`
- **THEN** the answer is deny

#### Scenario: Unknown user
- **WHEN** the service is asked about user `mallory`, who is not in the model
- **THEN** the answer is deny, and no error is raised

#### Scenario: Another user's role does not leak
- **WHEN** `alice`'s role grants `(write, doc-42)`, `bob` does not hold that role, and the service is asked whether `bob` may `write` `doc-42`
- **THEN** the answer is deny

#### Scenario: Only grant has expired
- **WHEN** `carol`'s only grant allows `(read, finance)` with window `[2026-01-01T00:00Z, 2026-04-01T00:00Z)`, and the service is asked at `2026-05-01T00:00Z` whether `carol` may `read` `finance`
- **THEN** the answer is deny

### Requirement: Malformed questions are rejected, never allowed
The service SHALL raise an error that identifies the invalid argument in each of these cases, and SHALL
NOT answer allow:
- the user, action, or resource is not a non-empty string
- a supplied evaluation instant is not a timezone-aware datetime
- no evaluation instant is supplied and the answer depends on one, as defined by the evaluation-instant
  requirement

#### Scenario: Empty action
- **WHEN** the service is asked whether `alice` may perform action `""` on `doc-42`
- **THEN** an invalid-request error is raised and no allow is returned

#### Scenario: Naive evaluation instant
- **WHEN** the service is asked a question with an evaluation instant that has no timezone
- **THEN** an invalid-request error is raised that identifies the evaluation instant

### Requirement: Decisions are deterministic and side-effect free
For a given model, question, and evaluation instant, the service SHALL always return the same answer.
The service SHALL NOT consult a clock or any other ambient state. Asking a question SHALL NOT modify the
model.

#### Scenario: Repeated question
- **WHEN** the same question is asked twice against the same model at the same evaluation instant
- **THEN** both answers are identical

#### Scenario: Time passing does not change an answer
- **WHEN** a question is asked with evaluation instant `2026-02-01T00:00Z`, and the same question with the same instant is asked again after a time-bounded grant's window has ended in real time
- **THEN** both answers are identical

## ADDED Requirements

### Requirement: Explicit deny overrides allow
If any applicable grant is a deny, the service SHALL answer **deny**. This SHALL hold even when another
applicable grant is an allow, including in each of these cases:
- the allow comes from a different role
- the allow is on a more specific resource
- the allow is on a less specific resource

#### Scenario: Deny from another role wins
- **WHEN** `alice` holds `editor`, which allows `(write, doc-42)`, and `alice` also holds `contractor`, which denies `(write, doc-42)`, and the service is asked whether `alice` may `write` `doc-42`
- **THEN** the answer is deny

#### Scenario: Deny on a descendant narrows a group allow
- **WHEN** `doc-42` is in `finance`, `alice`'s roles allow `(read, finance)` and deny `(read, doc-42)`, and the service is asked whether `alice` may `read` `doc-42` and whether `alice` may `read` `doc-43`, which is also in `finance`
- **THEN** the answer for `doc-42` is deny and the answer for `doc-43` is allow

#### Scenario: Deny on an ancestor beats an allow on the descendant
- **WHEN** `doc-42` is in `finance`, `alice`'s roles deny `(read, finance)` and allow `(read, doc-42)`, and the service is asked whether `alice` may `read` `doc-42`
- **THEN** the answer is deny

#### Scenario: Deny for a different action does not interfere
- **WHEN** `alice`'s roles allow `(read, doc-42)` and deny `(write, doc-42)`, and the service is asked whether `alice` may `read` `doc-42`
- **THEN** the answer is allow

#### Scenario: A deny alone is not an allow
- **WHEN** `alice`'s only grant denies `(read, doc-42)` and the service is asked whether `alice` may `read` `doc-43`
- **THEN** the answer is deny

### Requirement: Time-bounded grants apply only inside their window
The service SHALL evaluate every grant's window against the evaluation instant of the question. Grants
whose windows do not contain the instant SHALL be ignored. This SHALL apply equally to allows and denies.

#### Scenario: Allow inside window
- **WHEN** `carol`'s role allows `(read, finance)` with window `[2026-01-01T00:00Z, 2026-04-01T00:00Z)`, and the service is asked at `2026-02-15T12:00Z` whether `carol` may `read` `finance`
- **THEN** the answer is allow

#### Scenario: Allow at the exclusive end
- **WHEN** the same grant is evaluated at `2026-04-01T00:00Z`
- **THEN** the answer is deny

#### Scenario: Expired deny no longer overrides
- **WHEN** `alice`'s roles allow `(read, doc-42)` without a window and deny `(read, doc-42)` with window `[2026-01-01T00:00Z, 2026-02-01T00:00Z)`, and the service is asked at `2026-03-01T00:00Z` whether `alice` may `read` `doc-42`
- **THEN** the answer is allow

#### Scenario: Deny inside its window overrides
- **WHEN** the same model is asked at `2026-01-15T00:00Z`
- **THEN** the answer is deny

### Requirement: Evaluation instant is supplied by the caller
The service SHALL accept an optional evaluation instant with each question. When an instant is
supplied, every grant's window SHALL be evaluated against it. When no instant is supplied, the service
SHALL proceed as follows:
- It SHALL answer normally if none of the grants that match the user, action, and resource or an
  ancestor carries a validity window.
- It SHALL reject the question with an invalid-request error if any such grant carries a validity
  window.

The service SHALL NOT substitute the current time.

#### Scenario: Stage-1 question needs no instant
- **WHEN** a model has no time-bounded grants and the service is asked, without an evaluation instant, whether `alice` may `write` `doc-42`
- **THEN** the service answers exactly as stage 1 would

#### Scenario: Unrelated time-bounded grant does not require an instant
- **WHEN** a model contains a time-bounded grant only for `(read, hr)`, and the service is asked, without an evaluation instant, whether `alice` may `write` `doc-42`
- **THEN** the service answers without error

#### Scenario: Relevant time-bounded grant requires an instant
- **WHEN** `carol`'s role allows `(read, finance)` with a validity window, and the service is asked, without an evaluation instant, whether `carol` may `read` `doc-42` in `finance`
- **THEN** an invalid-request error is raised that identifies the missing evaluation instant, and no allow is returned


<!-- file: specs/entitlement-model/spec.md -->

# Spec Delta

## MODIFIED Requirements

### Requirement: Permission is an exact action-resource pair
A permission SHALL be identified by the pair `(action, resource)`. Action and resource SHALL each be a
non-empty string. They SHALL be compared exactly and case-sensitively. There SHALL be no wildcard, prefix,
or action-implication semantics. A resource SHALL relate to another resource only through the explicit
resource hierarchy declared in the model. Resource names SHALL NOT imply containment.

#### Scenario: Distinct pairs are distinct permissions
- **WHEN** a role grants `(read, doc-42)` and the model declares no hierarchy
- **THEN** that role does not grant `(write, doc-42)`, `(read, doc-43)`, `(Read, doc-42)`, or `(read, *)`

#### Scenario: Names do not imply hierarchy
- **WHEN** a role grants `(read, finance)`, resource `finance/doc-42` exists, and the model declares no parent for `finance/doc-42`
- **THEN** that role does not grant `(read, finance/doc-42)`

#### Scenario: Empty identifier rejected
- **WHEN** a model is built containing a permission whose action or resource is an empty string
- **THEN** building the model fails with a validation error that names the offending entry

### Requirement: Roles grant sets of permissions
A role SHALL be identified by a non-empty string and SHALL hold a set of zero or more grants. A grant
SHALL consist of the following parts:
- a permission `(action, resource)`
- an effect, which is either **allow** or **deny**
- an optional validity window

A grant given only as a permission SHALL mean an allow with no window. Two grants SHALL be the same grant
when their permission, effect, and window are all equal. Holding the same grant more than once SHALL have
the same effect as holding it once. A role MAY hold both an allow and a deny for the same permission, and
the model SHALL accept this.

#### Scenario: Duplicate grant is idempotent
- **WHEN** a role is defined granting `(read, doc-42)` twice
- **THEN** the model builds successfully and the role grants `(read, doc-42)` exactly once

#### Scenario: Role with no permissions
- **WHEN** a role is defined with no permissions
- **THEN** the model builds successfully and the role grants nothing

#### Scenario: Plain permission is an unbounded allow
- **WHEN** a role is defined with the plain permission `(read, doc-42)`
- **THEN** the role holds an allow grant for `(read, doc-42)` with no validity window

#### Scenario: Allow and deny for the same permission coexist
- **WHEN** a role is defined with both an allow and a deny for `(read, doc-42)`
- **THEN** the model builds successfully and the role holds both grants

## ADDED Requirements

### Requirement: Resources may be arranged in a hierarchy
The model SHALL accept a resource hierarchy that assigns each resource at most one parent resource, called
its group. The ancestors of a resource SHALL be its parent, its parent's parent, and so on, up to a
resource that has no parent. A resource SHALL NOT need to be declared anywhere to be asked about. A
resource with no declared parent SHALL have no ancestors. A group SHALL itself be a resource: it can be
granted on, have a parent, and be the subject of a question. The hierarchy SHALL be optional. A model
that declares no hierarchy SHALL behave as in stage 1.

#### Scenario: Ancestor chain
- **WHEN** the model declares `doc-42` in `finance` and `finance` in `org-root`
- **THEN** the ancestors of `doc-42` are `finance` and `org-root`, in that order

#### Scenario: Undeclared resource has no ancestors
- **WHEN** the model declares a hierarchy that does not mention `doc-99`
- **THEN** `doc-99` has no ancestors and no error is raised

### Requirement: Resource hierarchy is validated
Building a model SHALL fail with a validation error in each of these cases:
- a hierarchy entry names an empty child or parent
- a resource is its own parent
- the hierarchy contains a cycle of any length
- a resource is given more than one distinct parent

The error SHALL name the offending resources. These errors SHALL be reported together with all other
validation errors in the model.

#### Scenario: Cycle rejected
- **WHEN** a model is built declaring `a` in `b`, `b` in `c`, and `c` in `a`
- **THEN** building the model fails with a validation error naming the cycle `a`, `b`, `c`

#### Scenario: Self-parent rejected
- **WHEN** a model is built declaring `finance` in `finance`
- **THEN** building the model fails with a validation error naming `finance`

### Requirement: Grants may carry a validity window
A grant MAY carry a validity window `[from, to)`. Either bound MAY be absent, and an absent bound SHALL
be unbounded on that side. A grant SHALL apply at instant `t` if and only if all of these hold:
- `from` is absent, or `from <= t`
- `to` is absent, or `t < to`

Bounds SHALL be timezone-aware instants. They SHALL be compared as instants, independent of the timezone
in which each one is written. A grant with no window SHALL apply at every instant.

#### Scenario: Window is half-open
- **WHEN** a grant has window `[2026-01-01T00:00Z, 2026-04-01T00:00Z)`
- **THEN** it applies at `2026-01-01T00:00Z` and at `2026-03-31T23:59:59Z`, and does not apply at `2026-04-01T00:00Z` or at `2025-12-31T23:59:59Z`

#### Scenario: Open-ended window
- **WHEN** a grant has window `[2026-01-01T00:00Z, unbounded)`
- **THEN** it applies at every instant from `2026-01-01T00:00Z` onward

#### Scenario: Bounds in different timezones
- **WHEN** a grant's window ends at `2026-04-01T02:00+02:00`
- **THEN** it does not apply at `2026-04-01T00:00Z`

### Requirement: Validity windows are validated
Building a model SHALL fail with a validation error in each of these cases:
- a window bound is not a timezone-aware datetime
- both bounds are present and `from` is not strictly before `to`

The error SHALL name the role and grant, and SHALL be reported together with all other validation errors
in the model.

#### Scenario: Naive bound rejected
- **WHEN** a model is built with a grant whose window starts at a datetime that has no timezone
- **THEN** building the model fails with a validation error naming that role and grant

#### Scenario: Empty window rejected
- **WHEN** a model is built with a grant whose window has `from` equal to `to`
- **THEN** building the model fails with a validation error naming that role and grant


<!-- file: design.md -->

# Design

## Context

Stage 1 is described in `the-method/changes/archive/2026-09-23-entitlements-decision-service/design.md`.
It has four parts:
- An immutable, normalised `EntitlementModel` that holds user->roles and role->permissions. Its lookups
  are total.
- `build_model`, the only place where validation happens. It reports every error at once.
- `DecisionService.check`, which validates the question and applies an any-grant rule.
- A two-valued `Decision` enum whose truthiness is disabled.

The constraints from `substrate.md` still apply: Python 3.11+, the standard library only, and an
in-process library. See proposal.md for the motivation and specs/ for the behaviour.

Stage 2 changes the rule from "any grant allows" to "collect the grants that apply, then combine them".
That split is the organising idea of this design:

```
question (user, action, resource, now?)
    |
    v
[1 validate request] -- bad --> InvalidRequestError
    |
    v
[2 gather candidates]   roles_of(user) x lineage(resource) x grants_for(role, (action, r))
    |                   (model lookups only; no policy)
    v
[3 place in time]       drop grants whose Window does not contain `now`
    |                   (no `now` and a windowed candidate --> EvaluationInstantRequired)
    v
[4 combine]             deny-overrides: any DENY -> DENY; else any ALLOW -> ALLOW; else DENY
    |
    v
Decision.ALLOW / Decision.DENY
```

Each step answers exactly one of the three new questions:
- **Which grants concern this resource?** Step 2 answers this. It is where the hierarchy is used.
- **Which grants are in force?** Step 3 answers this, using time.
- **What do the grants in force add up to?** Step 4 answers this, using effect and precedence.

## Goals / Non-Goals

**Goals:**
- Keep the combining rule in one pure function over a set of effects, so it can be checked against a
  truth table by inspection.
- Keep the model free of policy. The hierarchy and windows are data with total lookups, as in stage 1.
- Make "fail closed" structural for the new features as well:
  - the service never reads a clock
  - a missing instant is never silently treated as "ignore windowed grants", because that could drop a
    deny
  - the only path to ALLOW is an in-force allow with no in-force deny
- Keep every stage-1 model and question working, with the same answers and no source changes.

**Non-Goals:**
- Most-specific-wins or other precedence schemes, priorities, and ordered rules.
- Multiple parents per resource (a DAG), role inheritance, action hierarchies, and wildcards.
- Recurring windows (for example "weekdays 9-17"), time zones as policy, and reading the clock.
- Explaining decisions (which grant decided). This is still deferred. See Risks.
- Incremental updates to the model. Models are still rebuilt wholesale.

## Architecture

```
                    +-------------+
                    |  errors     |  (leaf: EntitlementsError, ModelValidationError,
                    +-------------+   InvalidRequestError, EvaluationInstantRequired)
                          ^
        +-----------------+-----------------------+
        |                 |                       |
+---------------+   +-------------+       +----------------+      +-------------+
| building      |-->| model       |<------| decision       |----->| combining   |
| (validation,  |   | (values,    |       | (orchestrates  |      | (deny-      |
|  cycle check, |   |  indexes,   |       |  steps 1-3,    |      |  overrides) |
|  lineage      |   |  lineage)   |       |  calls step 4) |      +-------------+
|  precompute)  |   +-------------+       +----------------+             |
+---------------+         ^                       |                      v
                          |                       +-------------> +-------------+
                          +-------------------------------------- | outcome     |
                                (Effect lives in model)           | (Decision)  |
                                                                  +-------------+
```

The dependencies point one way. `combining` imports `Effect` from `model` and `Decision` from `outcome`,
and nothing else. `outcome` is a new leaf module: `Decision` moves there from `decision.py`, so that both
`decision` and `combining` can use it without an import cycle. It is still re-exported from the package
root, so the public path does not change.

### 1. Model (`entitlements/model.py`): data, with no policy

The model gains the following value types. All of them are frozen, slotted, and hashable.

- `Effect(Enum)`: `ALLOW` and `DENY`. Like `Decision`, `__bool__` raises. A grant's effect is a
  different concept from a decision's outcome, even though the two have the same members. See D6.
- `Window(valid_from: datetime | None, valid_until: datetime | None)` has one method,
  `contains(t) -> bool`, which implements the half-open `[from, to)` rule. The definition of "in force
  at t" belongs to the value it describes, and it is a one-liner.
- `Grant(permission: Permission, effect: Effect = ALLOW, window: Window | None = None)`. The default
  values make a stage-1 permission the same as `Grant(permission)`.
- `Permission` is unchanged.

`EntitlementModel` gains or changes the following items:
- `grants: Mapping[RoleId, Mapping[Permission, frozenset[Grant]]]`. It is indexed by permission, so
  collecting candidates costs one lookup for each (role, resource on the path) pair, instead of a scan
  of the role's grants.
- `lineage(resource) -> tuple[Resource, ...]` returns `(resource, parent, ..., root)`. It is **total**:
  an undeclared resource returns `(resource,)`. The builder precomputes lineages for every declared
  resource. At query time the method is a dictionary lookup with a fallback, so the model never walks a
  structure that might contain a cycle.
- `grants_for(role, permission) -> frozenset[Grant]` is total, and returns an empty set when there is
  nothing to return.
- `roles_of(user)` is unchanged.
- `grants_of(role)` is kept for compatibility. It now returns the role's permissions that have an ALLOW
  grant with no window, which is its stage-1 meaning. It is not used by the decision.

The model still owns only immutability, indexing, and the "absent means empty" convention.

### 2. Model building (`entitlements/building.py`): the only entry to a model

```python
build_model(*, roles: Mapping[str, Iterable[tuple[str, str] | Grant]],
               assignments: Mapping[str, Iterable[str]],
               parents: Mapping[str, str] = {}) -> EntitlementModel
```

Public helpers make the data easy to read:
`allow(action, resource, *, valid_from=None, valid_until=None) -> Grant` and the matching `deny(...)`.

This module owns these validation rules, which are added to the stage-1 rules. It still collects every
issue before it raises a single `ModelValidationError`.
- Grant fields must have the correct types. The effect must be an `Effect`.
- Each window bound must be `None` or an aware `datetime`, where `tzinfo` is set and `utcoffset()` is not
  `None`. When both bounds are present, `from < to` must hold.
- Hierarchy entries must be non-empty strings, a resource must not be its own parent, and there must be no
  cycles. A `Mapping` already guarantees that each child has only one parent. If a later input format
  allows duplicates, "more than one distinct parent" becomes a builder check.
- Cycle detection walks each chain with a visited set. It reports each cycle once, as its members in
  order, and names every resource on it.

After validation passes, the builder freezes the lineage table: a map of each declared resource to its
tuple.

### 3. Decision (`entitlements/decision.py`): orchestration

```python
class DecisionService:
    def __init__(self, model: EntitlementModel): ...
    def check(self, user: str, action: str, resource: str, *,
              now: datetime | None = None) -> Decision: ...
```

The service owns steps 1-3.

1. **Validate the request.** This covers the stage-1 string checks, plus: `now` must be `None` or an
   aware `datetime`. The service raises `InvalidRequestError` with the argument name otherwise.

2. **Gather candidates.** The candidates are
   `{g for role in roles_of(user) for r in lineage(resource) for g in grants_for(role, Permission(action, r))}`.

   This is pure lookup. The hierarchy semantics ("a grant on a group applies beneath it") are exactly
   the choice to iterate over `lineage(resource)` instead of `(resource,)`, and that choice lives in
   this one line.

3. **Place in time.**
   - If `now` is given, the service keeps the grants where `window is None or window.contains(now)`.
   - If `now` is `None` and any candidate has a window, the service raises `EvaluationInstantRequired`,
     which is a subclass of `InvalidRequestError`.
   - Otherwise, all candidates are in force.

4. The service delegates to `combining.deny_overrides(g.effect for g in in_force)`.

The service holds no state beyond the model reference, and it never reads the clock.

### 4. Combining (`entitlements/combining.py`): the precedence rule, alone

```python
def deny_overrides(effects: Iterable[Effect]) -> Decision:
    # any DENY -> DENY; else any ALLOW -> ALLOW; else DENY (default)
```

This function is the whole answer to "who wins". It is the security-critical rule and also the rule most
likely to be revised by product. It sees only effects: no resources, depths, roles, or times. The
function is order-insensitive, so it does not care where on the path, or in which role, a grant came
from. That property is exactly the spec's "a deny anywhere on the path, from any role, wins".

### 5. Errors (`entitlements/errors.py`)

Stage 2 adds `EvaluationInstantRequired(InvalidRequestError)`. A caller that already catches
`InvalidRequestError` needs no changes. A caller that wants to tell "you forgot `now`" apart from other
invalid requests can catch the subclass.

### Typical use

```python
model = build_model(
    roles={
        "finance-reader": [allow("read", "finance")],
        "contractor":     [allow("read", "finance",
                                 valid_from=datetime(2026, 1, 1, tzinfo=UTC),
                                 valid_until=datetime(2026, 4, 1, tzinfo=UTC))],
        "restricted":     [deny("read", "doc-42")],
    },
    assignments={"alice": ["finance-reader", "restricted"], "carol": ["contractor"]},
    parents={"doc-42": "finance", "doc-43": "finance", "finance": "org-root"},
)
svc = DecisionService(model)
svc.check("alice", "read", "doc-43")                    # ALLOW (inherited from finance)
svc.check("alice", "read", "doc-42")                    # DENY  (explicit deny wins)
svc.check("carol", "read", "doc-43", now=feb_15)        # ALLOW (inside window)
svc.check("carol", "read", "doc-43")                    # raises EvaluationInstantRequired
```

## Decisions

**D1. Precedence is plain deny-overrides, not most-specific-wins.**
The brief says two things: "unless a more specific grant on a descendant says otherwise" and "a deny
anywhere on the path still wins over an allow". Read together, a descendant can override an inherited
allow only by denying, and deny-overrides already produces that result. A most-specific-wins rule with
deny as the tie-breaker would let a descendant allow lift an ancestor deny, which contradicts the second
sentence. Deny-overrides also has no notion of depth, so the combiner stays a function of effects only.
The assumption is recorded in proposal.md, and the "Deny on an ancestor beats an allow on the
descendant" scenario checks it.

**D2. Keep three steps with three owners: relevance (hierarchy), time, and combining.**
One alternative was to fold windows and the hierarchy into the model, as `effective_grants(user, action,
resource, now)`. That puts policy into the data layer and makes the combiner impossible to test alone.
Another alternative was to put everything inside `check`. That works today, but every future precedence
change would then touch lookup code. The split costs one small module (`combining`) and one leaf
(`outcome`).

**D3. The hierarchy is a single-parent map, and lineages are precomputed at build time.**
The example in the brief is a chain, `doc-42 -> finance -> org-root`, so a forest is the simplest model
that fits it. Precomputing lineages brings three benefits:
- the cycle check and the lineage walk happen in one place
- query-time cost is O(depth) lookups with no risk of looping
- the decision never needs to know that a hierarchy could be malformed

Moving to multiple parents (a DAG) later would change `lineage` into a set of ancestors. Because
deny-overrides ignores order, neither `combining` nor `decision` would change.

**D4. `now` is optional, the service never reads the clock, and a missing `now` fails only when it
matters.** Four options were considered:
- **(a) Require `now` on every call.** This breaks every stage-1 caller, and the brief says the stage-1
  answer is unchanged where the new features are absent.
- **(b) Default to `datetime.now(UTC)`.** This breaks determinism, which is a stage-1 requirement, and
  makes tests depend on time.
- **(c) Ignore windowed grants when `now` is absent.** This fails open, because it would drop a
  time-bounded deny.
- **(d) Raise only when a candidate grant has a window.** This is the chosen option. It is compatible,
  deterministic, and closed.

The trade-off is that whether a call without `now` succeeds depends on the data. Callers who have any
time-bounded policy should always pass `now`, and the package docs say so. "Candidate" means the grant
matched the user's roles, the action, and the lineage. The rule is deliberately not "matters to the
outcome", which would require evaluating hypothetical instants. The rule is simple, predictable, and
never produces an allow.

**D5. Windows are half-open and aware-only, and are validated at build time.**
Comparing a naive datetime with an aware one raises `TypeError` in Python. Comparing two naive datetimes
is ambiguous across zones. Rejecting naive bounds in `build_model`, and a naive `now` in `check`, keeps
that failure out of the decision path. It fits D2 of stage 1: validate once, where the data enters. A
half-open window lets consecutive windows meet exactly, with no overlap and no gap.

**D6. `Effect` and `Decision` are separate enums.**
A grant *says* deny, and a decision *is* deny. The two are different concepts, and their domains could
diverge later, for example if a combining algorithm gained a "not applicable" result internally.
Keeping them separate also stops code from returning a grant's effect directly as the answer, which
would skip the combining step.

**D7. The stage-1 input shape stays valid.**
`roles=` accepts a mix of bare `(action, resource)` tuples and `Grant` objects. A tuple means
`Grant(Permission(a, r))`, which is an unbounded allow. `parents` defaults to empty. So every stage-1
`build_model` call builds an equivalent model, and every stage-1 `check` call returns the stage-1
answer.

## Assumptions (product questions answered by default)

- A descendant allow never lifts an ancestor deny (D1).
- The hierarchy applies to resources only. Actions are exact, and roles do not inherit.
- A resource has at most one parent. Undeclared resources are roots with no ancestors, and asking about
  them is not an error.
- A group is a resource, so grants on it apply to the group itself as well as beneath it.
- Windows are `[from, to)`, either bound may be open, and bounds must be timezone-aware. An empty or
  inverted window is a data error, not "never applies".
- Allow and deny are symmetric with respect to time: an out-of-window deny does not apply.
- A role may hold both an allow and a deny for the same permission. The deny wins whenever both are in
  force. This is not a data error.

## Risks / Trade-offs

- [Deny-overrides with inheritance makes a broad deny on a group impossible to punch through for one
  child] -> This is the intended semantics per the brief. A future "exception" feature would be a
  product decision and would change only `combining`, or add a new effect.
- [The no-`now` error depends on the data, so a caller that worked yesterday can fail after someone adds
  a windowed grant] -> The failure is a loud, typed error and never an allow. The guidance is to always
  pass `now` once any time-bounded policy exists.
- [Callers cannot see *why* a request was denied, which gets harder with inheritance and time] ->
  Explanation is deferred. The step pipeline makes it cheap to add later: steps 2 and 3 already
  materialise the grant set that an explanation would report.
- [Deep hierarchies with many roles cost O(roles x depth) lookups per check] -> This is negligible at
  in-memory scale. A per-(user, action) flattening is possible behind the model without touching
  `combining`.
- [Moving `Decision` to `outcome.py` changes an internal import path] -> The package root still
  re-exports it, and stage 1 declared only the root as public.

## Migration Plan

This change is additive and in-process. Existing `build_model` and `check` calls are unchanged. The
stage-1 test suite must pass unmodified as the compatibility gate. To roll back, revert the change;
there is no persisted state.


<!-- file: tasks.md -->

# Tasks

## 1. Leaf modules

- [ ] 1.1 Move `Decision` from `decision.py` into a new leaf module, `outcome.py`, and keep its re-export from `entitlements/__init__.py`. Verify that the unmodified stage-1 test suite passes.
- [ ] 1.2 Add `EvaluationInstantRequired(InvalidRequestError)` to `errors.py`. Verify with a unit test that it is caught by `except InvalidRequestError` and by `except EntitlementsError`.

## 2. Model value types and indexes

- [ ] 2.1 Implement `Effect` (ALLOW/DENY, with `__bool__` raising). Verify with unit tests that `bool(Effect.DENY)` raises `TypeError` and that `Effect.ALLOW != Decision.ALLOW`.
- [ ] 2.2 Implement `Window(valid_from, valid_until)` with `contains(t)` implementing half-open `[from, to)` and open bounds. Verify with unit tests covering the "Window is half-open", "Open-ended window", and "Bounds in different timezones" scenarios.
- [ ] 2.3 Implement `Grant(permission, effect=ALLOW, window=None)` (frozen, slotted, hashable) and the public helpers `allow(...)` and `deny(...)`. Verify with unit tests that `Grant(p) == allow(p.action, p.resource)` and that duplicate grants collapse in a set.
- [ ] 2.4 Extend `EntitlementModel` with the per-role `Permission -> frozenset[Grant]` index, a total `grants_for(role, permission)`, a total `lineage(resource)` backed by a precomputed table, and `grants_of(role)` keeping its stage-1 meaning. Verify with unit tests that an unknown role, permission, or resource returns an empty set or `(resource,)`, and that the mappings reject assignment.

## 3. Model building and validation

- [ ] 3.1 Extend `build_model` so that `roles=` accepts a mix of `(action, resource)` tuples and `Grant` objects, and add `parents=` (default empty). Freeze both into the model, with lineages precomputed. Verify with unit tests covering the "Plain permission is an unbounded allow", "Allow and deny for the same permission coexist", "Ancestor chain", "Undeclared resource has no ancestors", and "Names do not imply hierarchy" scenarios, and that mutating `parents` after the build has no effect.
- [ ] 3.2 Add grant and window validation: grant field types, aware bounds only, and `from < to`. All issues must be collected together with the stage-1 issues. Verify with unit tests covering the "Naive bound rejected" and "Empty window rejected" scenarios, plus one model that mixes a window error with an undefined-role error and reports both.
- [ ] 3.3 Add hierarchy validation: non-empty ids, no self-parent, and cycle detection that reports each cycle once by its members. Verify with unit tests covering the "Cycle rejected" and "Self-parent rejected" scenarios, and a model with two disjoint cycles that reports both.
- [ ] 3.4 Update the `build_model` docstring to cover the grant forms, `allow`/`deny`, `parents`, and window rules. Verify that `help(entitlements.build_model)` shows them.

## 4. Combining rule

- [ ] 4.1 Implement `combining.deny_overrides(effects) -> Decision`. Verify with a truth-table unit test covering {} -> DENY, {ALLOW} -> ALLOW, {DENY} -> DENY, and {ALLOW, DENY} -> DENY, and that the result is the same under any input order.

## 5. Access decision

- [ ] 5.1 Extend `DecisionService.check` with keyword-only `now`, and validate that it is `None` or an aware `datetime`. Verify with unit tests covering the "Naive evaluation instant" scenario and a non-datetime `now`.
- [ ] 5.2 Implement candidate gathering over `roles_of(user)`, `lineage(resource)`, and `grants_for`. Verify with unit tests covering the "Grant on a group applies beneath it", "Grant on a descendant does not apply upward", and "Group grant does not reach siblings outside the group" scenarios.
- [ ] 5.3 Implement the time step: filter candidates by `window.contains(now)`, and raise `EvaluationInstantRequired` when `now` is absent and a candidate is windowed. Verify with unit tests covering the "Allow inside window", "Allow at the exclusive end", "Only grant has expired", "Expired deny no longer overrides", "Deny inside its window overrides", "Stage-1 question needs no instant", "Unrelated time-bounded grant does not require an instant", and "Relevant time-bounded grant requires an instant" scenarios.
- [ ] 5.4 Wire the time step into `deny_overrides`. Verify with unit tests covering the "Deny from another role wins", "Deny on a descendant narrows a group allow", "Deny on an ancestor beats an allow on the descendant", "Deny for a different action does not interfere", and "A deny alone is not an allow" scenarios.
- [ ] 5.5 Verify determinism with unit tests: the same question at the same `now` gives identical answers, and `check` never calls the clock (patch `datetime` to raise if it is read).
- [ ] 5.6 Update the docstrings for `DecisionService.check` and the package. The docstrings must cover `now`, the rule that a clock is never read, and the advice to always pass `now` when time-bounded policy exists. Verify that `help(entitlements.DecisionService.check)` shows this.

## 6. Public API

- [ ] 6.1 Re-export `Effect`, `Window`, `Grant`, `allow`, `deny`, and `EvaluationInstantRequired` from `entitlements/__init__.py`, and add the stage-2 usage example from design.md to the package docstring. Verify with a test that imports only from `entitlements` and runs the example end to end, asserting each commented outcome.

## 7. Integration check

- [ ] 7.1 Run the full suite. Verify that `python -m unittest discover tests` passes on Python 3.11 with no third-party packages installed, and that the stage-1 tests pass unmodified.
