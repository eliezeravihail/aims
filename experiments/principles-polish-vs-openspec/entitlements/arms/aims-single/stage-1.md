# Entitlements — Stage 1 architecture (aims-single arm)

**Question answered:** may user U perform action A on resource R? → **allow / deny**.
**Stage-1 model:** each user holds one or more roles; each role grants a set of permissions, a permission
being an (action, resource) pair; **U may A on R iff any of U's roles grants (A,R), otherwise deny.**

This is a **design only** — components, responsibilities, seams, the rule each owns, and the reasoning.
Concrete Python signatures are given because a design objective must be *buildable* (a Worker could start
sprint 1 from it); no method bodies beyond the one-line decision core whose shape *is* an invariant.

Produced by aims: plan phase (objective + filed records) + the one mandatory design review-and-revise
round. Durable records filed in the project tree: `goals.md`, `base-dependencies.md`, `dependencies.md`,
`architecture.md`, `decisions/0001-substrate.md`, `decisions/0002-decision-core-and-ownership.md`.

---

## 1. Substrate

Python 3.11+, **standard library only, no framework** (`decisions/0001`). The product is a pure decision
function over supplied data; the pervasiveness test selects only the language. Frozen dataclasses, `enum`,
and `typing.Protocol` are the tools used to keep the seam vocabulary typed and the core pure. Any transport
or storage backend is a *confined adapter* behind the data port — never part of the substrate.

> Substrate note: aims makes the substrate a **mandatory user-ask**. This run is non-interactive (frozen
> spec, no answer channel), so the ask could not execute; the Guide chose the substrate and recorded the
> deviation transparently in `decisions/0001` rather than pretend the ask happened. The component
> boundaries and rule-ownership below are language-independent and survive a different substrate choice.

## 2. Components and the rule each owns

Three components, and the discipline that carries the value: **each of the three rules an authorization
system rests on has exactly one home** (`decisions/0002`).

### 2.1 Domain value objects — the vocabulary (`model.py`)

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class UserId:    value: str
@dataclass(frozen=True)
class RoleId:    value: str
@dataclass(frozen=True)
class Action:    name: str
@dataclass(frozen=True)
class Resource:  id: str

@dataclass(frozen=True)
class Permission:                 # the atom a role grants; the (A,R) pair-equality lives here
    action: Action
    resource: Resource

@dataclass(frozen=True)
class Role:
    id: RoleId
    granted: frozenset[Permission]

    def grants(self, action: Action, resource: Resource) -> bool:
        """OWNS the permission-match rule: this role grants (A,R) iff the exact pair is in its set."""
        return Permission(action, resource) in self.granted
```

- **`Permission`** owns **exact (A,R)-pair equality** — the frozen dataclass makes both coordinates part
  of identity, so a grant of (A, R′) matches a query (A, R) only when R′ == R (and symmetrically for the
  action). Matching one coordinate is not a match.
- **`Role`** owns the **permission-match rule** via `grants(action, resource)` — a Tell-Don't-Ask
  predicate: callers ask the role, they do not pull its set and decide outside it. The role is also the
  grant-container and the assignment unit the spec names, so it carries an identity (`RoleId`).
- `UserId`, `Action`, `Resource` are **seam vocabulary**: typed identifiers at the public API so three
  positional string arguments cannot be transposed silently (connascence of position → of name/type).

### 2.2 Data port — where entitlement data comes from (`store.py`)

```python
from typing import Iterable, Protocol

class EntitlementStore(Protocol):
    def roles_for(self, user: UserId) -> Iterable[Role]:
        """OWNS subject-resolution: the roles this user holds, hydrated with their grants.
        An unknown user yields no roles (never raises) — a valid subject with zero entitlements."""
```

- Owns the **subject-resolution rule** (user → held roles). It is the **ports-&-adapters boundary**: the
  decision core depends on this *interface*, adapters implement it. It yields the published domain type
  `Role`, never storage rows — the core cannot couple to a backend.
- A reference `InMemoryEntitlementStore` (stdlib only) implements it for tests and small deployments,
  holding the two data-model relations — *assignments* (user → role ids) and *role definitions* (role id →
  grant set) — and hydrating them into `Role`s. A real deployment supplies a DB/config/remote adapter with
  no change to the core (`dependencies.md`).
- **Unknown user returns empty, does not raise.** An unknown subject is a legitimate *deny*, not invalid
  input; fail-fast (§1) governs malformed input, not a valid subject who happens to hold nothing.

### 2.3 Decision core — the combination rule (`service.py`)

```python
class AuthorizationService:
    def __init__(self, store: EntitlementStore) -> None:
        self._store = store

    def may(self, user: UserId, action: Action, resource: Resource) -> bool:
        """OWNS the decision-combination rule and nothing else: U may A on R iff ANY held role grants it.
        True = permitted. This is the single home a later combination-policy change would reopen."""
        return any(role.grants(action, resource) for role in self._store.roles_for(user))
```

- Owns the **decision-combination rule** — the existential OR — and is its *only* home. No caller and no
  adapter re-derives "any held role → allow".
- **Closed by default, structurally.** `any(...)` over an empty or all-non-granting set is `False`; there
  is no path that yields `True` without a granting role. Unknown user, no roles, and empty grant sets all
  deny *by the shape of the function*, not by a special-cased branch.
- **Idempotent OR.** `any` short-circuits; the same (A,R) granted by two held roles yields a single allow,
  never a double-count or error.
- **Pure functional core.** `may` is a pure function of what the store returns; the store is its only
  (injected) edge — unit-testable with the in-memory adapter.

### 2.4 The seam map

```
caller ──may(UserId, Action, Resource)──▶ AuthorizationService     [owns: combination / OR + default-deny]
                                                │
                                     roles_for(UserId)  (port)
                                                ▼
                                        EntitlementStore            [owns: subject-resolution]
                                          (in-memory | DB | remote adapter)
                                                │ yields Role(s)
                                                ▼
                                     Role.grants(Action, Resource)  [owns: permission-match]
                                                │ uses
                                                ▼
                                     Permission  ((A,R) pair equality)
```

## 3. Invariants (build must hold these by construction)

1. **Closed by default** — no path returns allow without a granting role (structural, via `any` + deny
   fall-through).
2. **Exact-pair match** — both action and resource must equal; one-coordinate match denies.
3. **Existential, idempotent combination** — one granting role suffices; duplicates change nothing.
4. **Pure core** — `may` depends only on the injected store; no ambient state, no I/O in the core.
5. **One owner per rule** — combination in `may`, match in `Role`/`Permission`, resolution in the port;
   none re-derived elsewhere.

## 4. Buildability — exit criteria mapped to tests (test-first)

Each Stage-1 exit criterion is a decision the Worker writes a failing test for first (the *deliverable is
the design*; these are the tests it must be buildable against):

| Criterion | Test |
|---|---|
| No roles → deny | user with `[]` roles ⇒ `may` is False |
| Roles all empty-granted → deny | roles with empty `granted` ⇒ False |
| Unknown user → deny | user absent from store ⇒ store returns empty ⇒ False (no raise) |
| One of several roles grants → allow | 3 roles, only one grants (A,R) ⇒ True |
| Resource must match | role grants (A, R2), query (A, R), R2≠R ⇒ False |
| Action must match | role grants (A2, R), query (A, R), A2≠A ⇒ False |
| Duplicate grant → single allow | two roles both grant (A,R) ⇒ True, once |
| Combination has one home | only `may` contains the OR; grep/inspection: no re-derivation |
| Match has one home | only `Role.grants`/`Permission` decide a pair match |
| Core is pure/injectable | `may` tested against `InMemoryEntitlementStore`, no I/O |

## 5. The mandatory review-and-revise round (design objective)

aims never reads a `design` objective as met on its first pass; one measure → return-findings → revise
cycle is mandatory (`review.md`, `decisions/0011`). It ran. What the passes changed:

- **Subtractive pass (§7) — cut the decision-result enum.** The first pass modelled the result as
  `class Decision(Enum){ALLOW, DENY}` and `may(...) -> Decision`. The subtractive pass asks *what present
  force requires this*: a two-value enum here owns no rule — it is "a boolean with a label" (the canonical
  ceremony the pass names). No Stage-1 force distinguishes it from `bool`. **Revised to `-> bool`**
  (True = permitted). Kept: `Action`, `Resource`, `UserId` value objects — these earn their place by a
  *present* force (transposition safety at the three-argument public seam), and `Permission` is a genuine
  value object (a pair used as a set member / match key). `RoleId` kept: the role is an identified,
  assignable entity in the data model (two roles with identical grants stay distinct), though the decision
  core never reads it — force recorded, not deleted.
- **Naming pass (§3) — one word per concept.** The first pass named both the field and the predicate
  `grants`, a field/method collision. **Revised:** field `granted: frozenset[Permission]`, predicate
  `grants(action, resource) -> bool`.
- **Concept-fit pass (§4).** No decomposition-as-movement mismatch: the model is a membership test plus an
  existential quantifier — each element is the kind of thing it is. `may` returning `bool` is the honest
  shape of a one-bit decision. No inert members. Pass clean.
- **Interface-calibration check (§5).** Considered narrowing the port to yield raw grant sets
  (`Iterable[frozenset[Permission]]`) since `may` never reads `RoleId`. **Kept `Role`** — it is the
  domain's grant-container and assignment unit (a present concept), and §0 says speak the published domain
  type at a seam; stripping it to bare sets would be under-modelling the data model the spec names, not
  calibration.

Re-measure after revision: all ten decision criteria structurally satisfiable; §1 correctness, §5
one-owner, §0/§11 core-purity hold by construction; no S3/S4 finding open. Design read **met** after the
one round. (Full scored profile withheld here per the build-time projection; shown when comparing arms.)

## 6. What was deliberately NOT built (subtractive discipline, §7 / `goals.md` non-goals)

The Stage-1 spec names only role → permission with existential combination. The design builds exactly that.
It does **not** pre-build a combination-strategy seam, a matching-strategy seam, resource structure, a
grant "effect", or any time concept — no Stage-1 force requires them, and a seam serving no present change
axis is over-build (§7 falsifier: name the Stage-1 axis it serves — none). The combination rule's single
home (`may`) is where such a change would land *if and when* it arrives. This restraint is a deliberate
bet that honest ownership beats speculative generality — the survival test of that bet is Stage 2.
