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
