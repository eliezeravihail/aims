# Design

## Context

Stage 1 is described in `openspec/changes/archive/2026-09-23-entitlements-decision-service/design.md`.
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
