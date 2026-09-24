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
