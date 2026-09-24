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
