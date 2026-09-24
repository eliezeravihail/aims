# Design Y — stage 2

# Entitlements — Stage 2 architecture (the-method-single arm)

**Change:** three capabilities now combine in one decision — (1) **explicit deny** (a grant is allow or
deny; a deny on any held role overrides any allow — deny wins); (2) **resource inheritance** (resources
nest; a grant on a group applies beneath it unless a more specific descendant says otherwise; a deny
anywhere on the path still wins); (3) **time-bounded grants** (a grant may carry `[from, to)`; outside it
it does not apply; the decision is relative to a supplied `now`). The Stage-1 answer is unchanged where
these are absent.

Run per the-method by **consulting the Stage-1 records** (`goals.md`, `architecture.md`, `decisions/0002`) and
re-running plan → build → the one mandatory design review-and-revise round. New/updated records:
`decisions/0003-stage2-precedence.md` (supersedes 0002's combination portion), updated `architecture.md`
and `goals.md`.

---

## 1. The decision core after the change (`service.py`)

```python
class AuthorizationService:
    def __init__(self, store: EntitlementStore, hierarchy: ResourceHierarchy) -> None:
        self._store = store
        self._hierarchy = hierarchy

    def may(self, user: UserId, action: Action, resource: Resource, now: Instant) -> bool:
        """OWNS the decision-combination rule (deny-absolute, then existential allow, then default deny).
        True = permitted. The single home the Stage-1 design designated for a combination change."""
        path = frozenset(self._hierarchy.ancestors(resource))          # resource itself + its ancestors
        applicable = [g
                      for role in self._store.roles_for(user)
                      for g in role.grants_applicable(action, path, now)]
        return _resolve(applicable)


def _resolve(grants: list[Grant]) -> bool:
    """The precedence rule, one named home: any DENY wins; else any ALLOW; else closed-by-default DENY."""
    if any(g.effect is Effect.DENY for g in grants):
        return False
    return any(g.effect is Effect.ALLOW for g in grants)
```

**Why this is the whole precedence rule.** Because "a deny anywhere on the path still wins over an allow,"
a deny is never subordinate to a more-specific allow, and the only way a descendant "says otherwise" to an
inherited allow is by being a deny — already covered by deny-wins. So over the full input space the
outcome is: any applicable deny ⇒ deny; else any applicable allow ⇒ allow; else deny — **distance never
changes it** (`decisions/0003`). The resolver therefore ranks nothing by specificity; it is a two-predicate
fold, not an ordering. (This is the Stage-2 hard decision, and the single most valuable thing the mandatory
review round bought — see §4.)

## 2. The data model after the change (`model.py`, `store.py`)

```python
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, Optional, Protocol, AbstractSet

Instant = int            # supplied 'now' and window bounds share one comparable time type (epoch/seconds)

class Effect(Enum):      # NEW — a real sum type: it BRANCHES precedence (deny wins). Not a labelled bool.
    ALLOW = auto()
    DENY = auto()

@dataclass(frozen=True)
class Window:            # NEW — owns time-validity; half-open [from, to)
    frm: Instant
    to: Instant
    def contains(self, now: Instant) -> bool:
        return self.frm <= now < self.to      # now == frm applies; now == to does not

@dataclass(frozen=True)
class Grant:             # NEW — the atom a role now grants; owns its own applicability
    effect: Effect
    target: Permission                        # the (Action, Resource-coordinate) pair — Stage-1 value object, reused
    window: Optional[Window] = None           # None == always valid

    def applies(self, action: Action, path: AbstractSet[Resource], now: Instant) -> bool:
        return (self.target.action == action
                and self.target.resource in path                     # inheritance: coordinate on R's path
                and (self.window is None or self.window.contains(now)))

@dataclass(frozen=True)
class Role:              # EXTENDED — grant-container now holds Grants, not bare Permissions
    id: RoleId
    granted: frozenset[Grant]
    def grants_applicable(self, action: Action, path: AbstractSet[Resource], now: Instant) -> Iterable[Grant]:
        return (g for g in self.granted if g.applies(action, path, now))

class EntitlementStore(Protocol):             # SURVIVED unchanged in responsibility (user -> held roles)
    def roles_for(self, user: UserId) -> Iterable[Role]: ...

class ResourceHierarchy(Protocol):            # NEW port — owns the resource path; symmetric to the store
    def ancestors(self, resource: Resource) -> Iterable[Resource]:
        """resource itself, then its parent group, up to a root. A flat resource yields just [resource].
        Unknown resource yields just [resource] (no ancestors) — closed by default is preserved."""
```

`UserId, RoleId, Action, Resource, Permission` are the Stage-1 value objects, unchanged.

## 3. The three rules and their owners (after the change)

| Rule | Owner | Change vs Stage 1 |
|---|---|---|
| A grant applies to (A, R, now) | `Grant.applies` (window via `Window.contains`) | NEW (grants now carry effect + time; resource matches on path) |
| Which roles a user holds | `EntitlementStore` port | UNCHANGED |
| The resource path R belongs to | `ResourceHierarchy` port | NEW seam |
| How applicable grants combine | `AuthorizationService.may` + `_resolve` | EXTENDED in place: OR → deny-absolute-then-allow |

**Invariants (build holds by construction):** deny-absolute over the path; time filters *before*
precedence (an expired deny does not block, an expired allow does not permit); closed-by-default preserved
(`_resolve([]) is False`; unknown user/resource degrade to deny); Stage-1 behavior is the reduction when
deny/hierarchy/windows are absent.

## 4. The mandatory review-and-revise round (design objective)

One measure → return-findings → revise cycle ran (`review.md`, `decisions/0011`). What the passes changed:

- **§1 full-input-space trace + subtractive pass — cut the specificity ordering (the load-bearing find).**
  The first pass, following the spec's wording literally, built a *specificity-ranked* resolver: annotate
  each applicable grant with its distance from `R`, sort, let the most specific win, and break ties by
  deny. Tracing the full input space against "a deny anywhere on the path **still** wins" showed the
  ranking never changes the boolean outcome (any deny ⇒ deny at every distance; else any allow ⇒ allow;
  else deny). The distance annotation and the sort are therefore **value-correct ceremony** — machinery
  that pays for nothing (§7 subtractive; §4 concept-fit: an ordering modelling a computation that is
  really a two-predicate fold). **Revised** to the `_resolve` fold above; the correctness derivation is
  recorded in `decisions/0003` so the omission is a proven decision, not an oversight.
- **§4 concept-fit — `Effect` is a genuine sum type, not the Stage-1 labelled bool.** Confirmed keeping it:
  unlike the Stage-1 *decision result* (cut to `bool` because it owned no rule), `Effect` on a grant
  **branches** the precedence and is forced by the explicit-deny feature. The Stage-1 cut and this addition
  are consistent — the earlier cut was about the *result*, not about all two-valued types.
- **§1 boundary — half-open window.** Pinned `frm <= now < to` (now == frm applies; now == to does not) as
  an explicit `Window.contains` contract with its own tests, rather than leaving the boundary implicit.
- **§5 calibrate / §0 seam — hierarchy as a port, not a `Resource.parent` field.** Confirmed: nesting is
  administered data; putting `parent` on the value object would bake mutable data into the type that
  crosses the seam. The new `ResourceHierarchy` port mirrors `EntitlementStore`.
- **Compatibility re-measure.** Verified the Stage-1 reduction structurally (no deny + flat path + no
  windows ⇒ existential OR over coordinate == R). Design read **met** after the one round; no S3/S4 open.

## 5. SURVIVAL

Per Stage-1 component — did each survive, extend, reopen, or get discarded?

| Stage-1 element | Verdict | Detail |
|---|---|---|
| `AuthorizationService.may` (combination owner) | **SURVIVED + EXTENDED in place** | Still the sole home of combination; body OR → deny-absolute-then-allow; signature gains `now` and a `hierarchy` collaborator. The change landed at exactly the designated seam — **nothing outside this owner had to change to gain deny-precedence.** |
| `EntitlementStore` port (subject-resolution) | **SURVIVED unchanged** | `roles_for(user)` responsibility and signature intact; only the payload type inside `Role` changed. |
| `Role` (grant-container) | **EXTENDED; predicate reopened** | Concept survived (still the assignment unit / grant-container); `granted` type `frozenset[Permission]` → `frozenset[Grant]`; predicate `grants(a, r) -> bool` **reopened** to `grants_applicable(a, path, now) -> Iterable[Grant]` (must yield effect-carrying grants and honor path + time — a bare bool can no longer express the answer). |
| `Permission` ((A,R) pair) | **SURVIVED, reused** | Now the `target` inside a `Grant`; unchanged as a value object. |
| Decision result `bool` | **SURVIVED** | The decision is still one bit; `may` still returns `bool`. The Stage-1 subtractive cut of a `Decision` enum held — and was *vindicated*: the sum type Stage 2 needed (`Effect`) belongs on the grant, not the result. |
| `Action`, `Resource`, `UserId`, `RoleId` | **SURVIVED unchanged** | `Resource` gains a hierarchy *around* it via the new port, but the type itself is untouched (parent-of stayed out of the value object). |
| Invariant: closed-by-default | **SURVIVED** | `_resolve([]) is False`; unknown user/resource still deny. |
| Invariant: exact-pair match | **EXTENDED** | Exact *action* match preserved; *resource* match widened from `== R` to `∈ ancestors(R)` (inheritance). |
| Stage-1 combination (existential OR) | **SUPERSEDED, but as a reduction** | `decisions/0002`'s OR is superseded by `0003`'s deny-absolute rule, of which the OR is the special case when deny/hierarchy/time are absent — so Stage-1 behavior is *contained*, not broken. |

**New components** (each tied to a present Stage-2 force, none speculative): `Effect` (explicit-deny),
`Window` + `Instant` (time-bounds), `Grant` (grants now carry effect + time), `ResourceHierarchy` port
(inheritance), `_resolve` (a named private home for the extended precedence — **not** a pluggable Strategy;
one policy in scope).

**Discarded:** the `Role.grants(a, r) -> bool` predicate and the `granted: frozenset[Permission]`
representation (replaced, not merely extended).

**Did the features slot in, or force the decision core open?** They **forced the decision core open** — the
combination rule genuinely changed (OR → deny-absolute) and the signature grew (`now`, hierarchy). But it
opened at **precisely the one seam Stage 1 designated as the combination's single owner**, and *only*
there: no caller, no adapter, and no other rule-owner had to change to absorb deny-precedence. The data
model extended cleanly behind the surviving `EntitlementStore` port plus one new symmetric port. This is
the payoff of the Stage-1 ownership decision — the blast radius of a semantics change equalled its one
owner. The one interface casualty was `Role`'s predicate (a bool could no longer carry an effect), which is
an honest consequence of the data model itself changing shape, not a mislocated rule.

**Was anything reopened that good Stage-1 design should have avoided?** No — and notably, the Stage-1
*restraint* (no combination Strategy, no specificity machinery, `Decision` cut to bool, hierarchy kept out
of `Resource`) is what made the extension land as *addition at seams* rather than rework. Pre-building any
of those in Stage 1 would have been speculative machinery the review would have cut; not building them cost
one predicate-signature change here. The subtractive bet paid.

## 6. Cost

| | Stage 1 | Stage 2 |
|---|---|---|
| Plan passes (objective + records filed) | 1 | 1 (delta-discovery; consulted Stage-1 records) |
| Build passes (design produced) | 1 | 1 |
| Mandatory design **revise rounds** | 1 (measure → revise → re-measure) | 1 (measure → revise → re-measure) |
| Key revise-round yield | cut `Decision` enum → `bool`; fix `grants` field/method name clash | cut specificity-ordering → two-predicate fold (proven non-outcome-affecting) |
| New/changed root records | goals, base-dependencies, dependencies, architecture, ADR 0001, ADR 0002 | ADR 0003 (supersedes 0002 combination); architecture + goals updated |
| Companions anchored | 0 (design-only; no source files yet) | 0 |
| Approx word count (deliverable) | ~1600 words | ~1850 words |

Total across both stages: **2 design revise rounds** (the method mandate — one per design objective, not
open-ended), **0 correctness (S4) findings left open**, and the semantics change of Stage 2 confined to its
single Stage-1-designated owner.
