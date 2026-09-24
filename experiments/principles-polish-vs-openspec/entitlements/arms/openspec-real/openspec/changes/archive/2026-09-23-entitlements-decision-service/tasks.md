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
