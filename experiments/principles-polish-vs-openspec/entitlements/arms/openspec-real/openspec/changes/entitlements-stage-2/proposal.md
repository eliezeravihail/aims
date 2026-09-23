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
