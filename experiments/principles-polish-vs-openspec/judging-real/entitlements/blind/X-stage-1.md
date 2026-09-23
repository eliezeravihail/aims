# Design X — stage 1



<!-- file: proposal.md -->

# Proposal

## Why

Callers need one authoritative answer to the question "may user U perform action A on resource R?".
Without that answer, each caller writes its own role checks, and those checks drift apart. Stage 1
starts with the simplest model that answers the question: users hold roles, roles grant permissions.

## What Changes

- Introduce an **entitlement model**. It holds users, roles, and permissions. A permission is an exact
  `(action, resource)` pair. Each user is assigned one or more roles, and each role grants a set of
  permissions. The model is validated as a whole before it can be queried.
- Introduce an **access decision**. Given `(user, action, resource)`, it answers **allow** when any
  of the user's roles grants exactly `(action, resource)`, and **deny** in every other case (deny by
  default).
- Expose both as an in-process Python library API (Python 3.11+, standard library only, single process,
  no persistence, network, or UI, as `substrate.md` requires).

Assumptions made instead of asking the product owner (recorded again in design.md):

- Actions and resources are opaque identifiers matched exactly and case-sensitively. There are no
  wildcards, resource hierarchies, or action implications.
- Unknown users, actions, and resources are denied. They are not errors.
- A role assignment that names an undefined role is a data error. It is rejected when the model is
  built, not silently ignored at decision time.
- There are no deny rules. Only grants exist, so "any role grants" is the entire rule.

## Capabilities

### New Capabilities

- `entitlement-model`: defines users, roles, `(action, resource)` permissions, role assignments, and
  role grants, plus the validation rules a model must pass before it can be queried.
- `access-decision`: the allow/deny answer to "may U perform A on R?" over a validated entitlement model.

### Modified Capabilities

None. The project has no existing specs.

## Impact

- New Python package with a library entry point. There are no existing code, APIs, or dependencies to
  affect.
- No new runtime dependencies (standard library only).


<!-- file: specs/access-decision/spec.md -->

# Spec Delta

## Purpose

Answers the single question "may user U perform action A on resource R?" with allow or deny, evaluated
against a validated entitlement model, denying by default.

## ADDED Requirements

### Requirement: Allow when any assigned role grants the exact permission
The service SHALL answer **allow** for `(user, action, resource)` if and only if at least one role
assigned to that user grants the permission `(action, resource)`.

#### Scenario: Single role grants
- **WHEN** `alice` is assigned `editor`, `editor` grants `(write, doc-42)`, and the service is asked whether `alice` may `write` `doc-42`
- **THEN** the answer is allow

#### Scenario: Grant comes from one of several roles
- **WHEN** `alice` is assigned `viewer` and `editor`, only `editor` grants `(write, doc-42)`, and the service is asked whether `alice` may `write` `doc-42`
- **THEN** the answer is allow

### Requirement: Deny by default
The service SHALL answer **deny** in every case not covered by the allow rule. This includes a user who
is not in the model, and an action or resource that no role mentions.

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

### Requirement: Answer is exactly allow or deny
The service SHALL return one of exactly two outcomes, allow or deny. The outcome SHALL NOT be a value
that could be mistaken for the other (for example, a truthy or falsy non-boolean).

#### Scenario: Outcome type
- **WHEN** any well-formed question is asked
- **THEN** the result is either allow or deny and nothing else

### Requirement: Malformed questions are rejected, never allowed
If the user, action, or resource in a question is not a non-empty string, the service SHALL raise an
error that identifies the invalid argument. It SHALL NOT answer allow.

#### Scenario: Empty action
- **WHEN** the service is asked whether `alice` may perform action `""` on `doc-42`
- **THEN** an invalid-request error is raised and no allow is returned

### Requirement: Decisions are deterministic and side-effect free
For a given model and question, the service SHALL always return the same answer. Asking a question SHALL
NOT modify the model.

#### Scenario: Repeated question
- **WHEN** the same question is asked twice against the same model
- **THEN** both answers are identical


<!-- file: specs/entitlement-model/spec.md -->

# Spec Delta

## Purpose

Defines the data the entitlements service decides from: users, the roles assigned to them, and the
`(action, resource)` permissions each role grants, together with the rules a model must satisfy before
it can be queried.

## ADDED Requirements

### Requirement: Permission is an exact action-resource pair
A permission SHALL be identified by the pair `(action, resource)`. Action and resource SHALL each be a
non-empty string. They SHALL be compared exactly and case-sensitively, with no wildcard, prefix,
hierarchy, or implication semantics.

#### Scenario: Distinct pairs are distinct permissions
- **WHEN** a role grants `(read, doc-42)`
- **THEN** that role does not grant `(write, doc-42)`, `(read, doc-43)`, `(Read, doc-42)`, or `(read, *)`

#### Scenario: Empty identifier rejected
- **WHEN** a model is built containing a permission whose action or resource is an empty string
- **THEN** building the model fails with a validation error that names the offending entry

### Requirement: Roles grant sets of permissions
A role SHALL be identified by a non-empty string and SHALL grant a set of zero or more permissions.
Granting the same permission more than once SHALL have the same effect as granting it once.

#### Scenario: Duplicate grant is idempotent
- **WHEN** a role is defined granting `(read, doc-42)` twice
- **THEN** the model builds successfully and the role grants `(read, doc-42)` exactly once

#### Scenario: Role with no permissions
- **WHEN** a role is defined with no permissions
- **THEN** the model builds successfully and the role grants nothing

### Requirement: Users are assigned roles
A user SHALL be identified by a non-empty string and SHALL be assigned a set of one or more roles. A
user with no role assignments SHALL be indistinguishable from a user that is not in the model.
Assigning the same role more than once SHALL have the same effect as assigning it once.

#### Scenario: User with several roles
- **WHEN** user `alice` is assigned roles `editor` and `viewer`
- **THEN** the model records both assignments for `alice`

### Requirement: Role assignments reference defined roles
Every role named in a user assignment SHALL be defined in the same model. A model that assigns an
undefined role SHALL be rejected as a whole. No partially built model SHALL become queryable.

#### Scenario: Assignment to undefined role
- **WHEN** a model is built in which user `alice` is assigned role `auditor` and no role `auditor` is defined
- **THEN** building the model fails with a validation error naming user `alice` and role `auditor`

#### Scenario: All validation errors reported together
- **WHEN** a model is built with several invalid entries
- **THEN** the validation error lists every invalid entry, not only the first one found

### Requirement: A built model is immutable
Once built, a model SHALL NOT change. To change entitlements, callers SHALL build a new model. Queries
already evaluating against a model SHALL be unaffected by the construction of another model.

#### Scenario: Source data mutated after build
- **WHEN** a model is built from caller-supplied collections and the caller later mutates those collections
- **THEN** decisions made against the built model are unchanged


<!-- file: design.md -->

# Design

## Context

This is a greenfield repository. The only fixed ground is `substrate.md`: Python 3.11+, the standard
library only, a single process, and no persistence, network, database, or UI. See proposal.md for why
the change exists and specs/ for the behaviour it must have. The model is RBAC in its simplest form:
users hold roles, roles grant exact `(action, resource)` pairs, and any grant allows.

## Goals / Non-Goals

**Goals:**
- A decision rule small enough to check by inspection: a pure function over immutable data.
- Invalid entitlement data is caught once, when the model is built, so the decision path never has to
  defend against it.
- Failing closed is structural. The only way to produce allow is to find a matching grant.

**Non-Goals:**
- Wildcards, resource hierarchies, action implication, role inheritance, deny rules, conditions, and
  attributes. None of these were asked for (see Assumptions).
- Explaining decisions (which role matched), auditing, and caching.
- Loading from files, storing models, or runtime administration APIs. The caller supplies the data in
  memory. No stage has asked for anything else.
- Concurrency control beyond what immutability already gives.

## Architecture

```
            caller
              |
              |  build_model(roles=..., assignments=...)        check(user, action, resource)
              v                                                           |
   +----------------------+   produces   +----------------------+  reads  |
   |  Model building      | -----------> |  EntitlementModel    | <-------+----+
   |  (validation lives   |              |  (immutable, indexed |              |
   |   here only)         |              |   data; no rules)    |     +-------------------+
   +----------------------+              +----------------------+     |  Decision         |
              |                                     ^                 |  (the allow rule; |
              v                                     |                 |   deny default)   |
   ModelValidationError                     Permission, ids           +-------------------+
                                                                               |
                                                                  Decision.ALLOW / DENY
                                                                  InvalidRequestError
```

Dependencies point one way: building -> model <- decision. Model depends on nothing. Errors form a leaf
module that everything may import. Decision never imports building.

### Components and what each owns

**1. Model (`entitlements/model.py`): the data, with no policy**
- Value types: `UserId`, `RoleId`, `Action`, `Resource` are `str` aliases.
  `Permission` is `@dataclass(frozen=True, slots=True)` with fields `action` and `resource`, so it is
  hashable and compared by exact value.
- `EntitlementModel` is immutable and holds two normalised indexes:
  - `assignments: Mapping[UserId, frozenset[RoleId]]`
  - `grants: Mapping[RoleId, frozenset[Permission]]`

  Both are wrapped in `types.MappingProxyType` over private dict copies.
- Read-only queries: `roles_of(user) -> frozenset[RoleId]` and `grants_of(role) -> frozenset[Permission]`.
  Both are **total**: an unknown key returns an empty frozenset. This one rule is the reason an
  unknown user needs no special case anywhere else.
- Owns: immutability and the "absent means empty" convention. It does not validate. It trusts that
  the builder established its invariants.

**2. Model building (`entitlements/building.py`): the only entry to a model**
- Sketch: `build_model(*, roles: Mapping[str, Iterable[tuple[str, str]]], assignments: Mapping[str, Iterable[str]]) -> EntitlementModel`
- Owns every entitlement-model validation rule from the spec:
  - ids, actions, and resources are non-empty `str`
  - every assigned role is defined
  - duplicates collapse (set semantics)
  - users whose assignment list is empty are dropped (they are indistinguishable from absent users)
- Collects **all** issues before failing. It then raises a single
  `ModelValidationError(issues: tuple[ValidationIssue, ...])`, where each issue carries a location
  (for example `assignments['alice']`) and a message. No partially built model can escape.
- Copies caller collections into frozensets. This is why mutating the source afterwards has no effect.

**3. Decision (`entitlements/decision.py`): the rule**
- `class Decision(Enum): ALLOW, DENY`. `Decision.__bool__` raises `TypeError`, so
  `if service.check(...)` cannot silently treat DENY as truthy. Callers write
  `== Decision.ALLOW` or use `decision.allowed`.
- Sketch: `class DecisionService: __init__(model: EntitlementModel)` and
  `check(user, action, resource) -> Decision`
- The rule, in full:
  ```
  validate request args (non-empty str) else raise InvalidRequestError
  wanted = Permission(action, resource)
  ALLOW if any(wanted in model.grants_of(r) for r in model.roles_of(user)) else DENY
  ```
- Owns: request validation, the any-role-grants rule, and deny by default. It holds no state beyond
  the model reference, and it never mutates anything.

**4. Errors (`entitlements/errors.py`)**
- `EntitlementsError` is the base, with two subclasses:
  - `ModelValidationError`: bad data, raised at build time
  - `InvalidRequestError`: bad question, raised at check time

  Keeping them separate lets a caller distinguish "the policy data is broken" from "my call was wrong".
  Neither is ever an allow.

**5. Public surface (`entitlements/__init__.py`)**
- Re-exports `build_model`, `EntitlementModel`, `Permission`, `DecisionService`, `Decision`, and the
  errors. Everything else is internal. There is no CLI. The substrate allows a local function API, and
  nothing calls for a CLI.

### Typical use

```python
model = build_model(
    roles={"editor": [("read", "doc-42"), ("write", "doc-42")], "viewer": [("read", "doc-42")]},
    assignments={"alice": ["editor"], "bob": ["viewer"]},
)
svc = DecisionService(model)
svc.check("bob", "write", "doc-42")   # Decision.DENY
```

To change entitlements, build a new model and construct a new `DecisionService`, or hand the new one
to callers. Because models are immutable, a check in progress always sees one consistent model.

## Decisions

**D1. Keep the model normalised (user->roles, role->permissions). Do not flatten it to
user->permissions.**
The check costs O(number of roles the user holds) set lookups, which is trivially fast at any scale a
single in-memory process holds. The flattened index would give an O(1) check, but it duplicates role
data per user and hides roles. That makes changes to a role's grants rewrite every holder's entry.
Rejected for stage 1. It can be added later inside `EntitlementModel` without touching `Decision`,
because the decision only calls `roles_of` and `grants_of`.

**D2. Validate at build time, in exactly one place. Keep the decision path free of validation.**
The alternative is to tolerate bad data at check time, for example by skipping undefined roles. That
hides data errors that would otherwise surface loudly and spreads defensive checks through the hot
path. Building up front gives a single source of truth for the model's invariants.

**D3. An unknown user, action, or resource is a deny, not an error.**
To an access-decision service, "never heard of them" is the ordinary negative case. Raising here would
push every caller into error handling for a routine answer. Malformed input, meaning an empty or
non-string identifier, *is* an error, because it indicates a caller bug rather than a policy fact.

**D4. Use a two-valued `Decision` enum with truthiness disabled, not a bare `bool`.**
The enum names the domain outcome. The disabled `__bool__` closes the trap where a default `Enum`
member is always truthy, which would make DENY read as allowed. A `bool` would also be safe but carries
no vocabulary. This is a small cost for a security-relevant return value.

**D5. Construct the model from in-memory Python mappings. Do not use a file format.**
The substrate rules out persistence. A JSON or YAML loader would be an adapter onto `build_model`, and
it can be added later without changing any component above.

**D6. Keep the decision and the model as separate components, rather than adding a method on the
model.**
The model owns data shape. The decision owns policy. Later rules, whatever they turn out to be, will
change `Decision` and leave the data store alone, or the other way round. The seam costs one class.

## Assumptions (product questions answered by default)

- Matching is exact and case-sensitive, and identifiers are opaque. There is no trimming or
  normalisation.
- There are only grants. Nothing can be explicitly denied, so role order and conflicts cannot arise.
- A role that grants nothing is valid. A user who has no roles is treated as unknown, which means deny.
- A role assigned to a user but never defined is invalid data, and the whole model is rejected.
- Roles may exist without being assigned to anyone. That is valid.
- Models are replaced wholesale. There are no incremental grant or revoke operations.

## Risks / Trade-offs

- [A large, frequently changing policy is rebuilt wholesale on every change] -> This is acceptable for
  stage 1 in-memory sizes. Incremental builders can be added behind `build_model` without changing the
  decision path.
- [Callers forget to swap in the new service after rebuilding] -> A later stage can add a holder with
  an atomic reference swap if runtime reload becomes a requirement. It is not built now.
- [Disabled `__bool__` surprises callers] -> The `TypeError` message says what to do, and it is
  documented in the package docstring.
- [Exact matching is too rigid once resources multiply] -> The data growth is deliberate. Wildcards
  or hierarchies change the decision semantics and need a product decision first.


<!-- file: tasks.md -->

# Tasks

## 1. Package scaffolding

- [ ] 1.1 Create the `entitlements/` package (`__init__.py`, `model.py`, `building.py`, `decision.py`, `errors.py`) and a `tests/` directory. Verify that `python -c "import entitlements"` succeeds and that `python -m unittest discover tests` runs with zero tests and no errors.

## 2. Errors and model types

- [ ] 2.1 Implement the error hierarchy in `errors.py` (`EntitlementsError`, `ModelValidationError` carrying `ValidationIssue` items, `InvalidRequestError`). Verify with unit tests that both errors are subclasses of `EntitlementsError` and that `ModelValidationError` exposes every issue it was given.
- [ ] 2.2 Implement `Permission` (frozen, slotted, hashable) and `EntitlementModel` with read-only mappings and total `roles_of` / `grants_of`. Verify with unit tests that exact equality holds, that `(read, doc-42) != (Read, doc-42)`, that unknown keys return empty frozensets, and that the mappings reject assignment.

## 3. Model building and validation

- [ ] 3.1 Implement `build_model(roles=..., assignments=...)` with set semantics and defensive copies. Verify with unit tests covering the entitlement-model spec scenarios for duplicate grants, roles with no permissions, users with several roles, and source collections mutated after the build.
- [ ] 3.2 Add validation that collects all issues: empty or non-string ids, actions, and resources, and assignments to undefined roles. Verify with unit tests covering the "Empty identifier rejected", "Assignment to undefined role", and "All validation errors reported together" scenarios, and that no model is returned on failure.
- [ ] 3.3 Document `build_model` input shape and validation rules in its docstring. Verify that `help(entitlements.build_model)` shows them.

## 4. Access decision

- [ ] 4.1 Implement `Decision` (ALLOW/DENY, `allowed` property, `__bool__` raising `TypeError` with guidance). Verify with unit tests that `bool(Decision.DENY)` raises and that `Decision.ALLOW.allowed` is `True`.
- [ ] 4.2 Implement `DecisionService.check` (request validation, then the any-role-grants rule, deny by default). Verify with unit tests covering every access-decision spec scenario: single role, one of several roles, role lacks the permission, different resource, unknown user, no leakage across users, empty action raising `InvalidRequestError`, and a repeated question giving an identical answer.
- [ ] 4.3 Document `DecisionService.check` and the `Decision` truthiness rule in docstrings. Verify that `help(entitlements.DecisionService.check)` shows them.

## 5. Public API

- [ ] 5.1 Re-export the public surface from `entitlements/__init__.py` and write the package docstring with the usage example from design.md. Verify with a test that imports only from `entitlements` and runs the example end to end, asserting `Decision.DENY` for bob writing doc-42 and `Decision.ALLOW` for alice.

## 6. Integration check

- [ ] 6.1 Run the full suite. Verify that `python -m unittest discover tests` passes on Python 3.11 with no third-party packages installed.
