# Entitlements — Stage 1 (OpenSpec)

> Design only. No implementation code. Produced with the OpenSpec spec-driven method:
> capability specs (`openspec/specs/`) plus a change bundle (`proposal.md`, `design.md`,
> `tasks.md`). This file collects, in prose, what those artifacts would contain for the
> stage-1 change **`add-authorization-core`**. Once accepted, the specs below are **FROZEN**;
> stage 2 arrives as a separate change against them.

---

## Card under design

> Design a service and data model answering: may user **U** perform action **A** on
> resource **R**? (allow/deny). At stage 1: each user has one or more roles; each role
> grants a set of permissions, a permission being an **(action, resource)** pair; U may
> perform A on R if **any** of U's roles grants (A,R), else **deny**.

---

# Part 1 — `openspec/specs/` (capability specifications)

Two capabilities are affected. Each is the authoritative, deployed-state description of
*what the system does* once the stage-1 change lands. They are written independently of any
single change so later changes edit them in place.

## Capability: `entitlements-model`

**Purpose.** Define the durable data the authorization system reasons over: the actors
(users), the bundles of authority (roles), the atomic units of authority (permissions), and
the assignment edges between them. This capability owns *shape and integrity*, not decisions.

### Requirement: Subjects
The system SHALL represent each authorization subject as a **user** identified by a stable,
unique `user_id` that never encodes authority of its own.

- **Scenario: distinct users are distinct subjects**
  - **Given** two users created with `user_id = "u_alice"` and `user_id = "u_bob"`
  - **When** the model is queried for either id
  - **Then** each resolves to its own subject record and neither inherits the other's roles.

### Requirement: Permissions as (action, resource) pairs
The system SHALL represent a **permission** as an ordered pair `(action, resource)`, where
`action` is a verb token (e.g. `read`, `write`, `delete`) and `resource` is an identifier of
the thing acted upon. A permission SHALL carry no subject and no grant semantics of its own —
it is a *type of authority*, not a *holding* of it.

- **Scenario: a permission is only its two coordinates**
  - **Given** a permission `("read", "doc:42")`
  - **When** it is compared to another permission
  - **Then** the two are equal if and only if both `action` and `resource` are equal.

- **Scenario: action and resource are both required**
  - **Given** an attempt to define a permission with an empty `action` or empty `resource`
  - **When** the model validates it
  - **Then** the definition is rejected and no partial permission is stored.

### Requirement: Roles grant permission sets
The system SHALL represent a **role** as a named collection that grants a **set** of
permissions. Granting the same permission twice SHALL have no additional effect (set
semantics — grants are idempotent, unordered, and duplicate-free).

- **Scenario: a role grants a set**
  - **Given** a role `editor` that grants `("read","doc:42")` and `("write","doc:42")`
  - **When** the same `("read","doc:42")` is granted again
  - **Then** the role still grants exactly those two permissions.

### Requirement: Users hold one or more roles
The system SHALL allow each user to be assigned **one or more** roles. Assignment is a
many-to-many edge: a role MAY be held by many users and a user MAY hold many roles.

- **Scenario: multi-role user**
  - **Given** user `u_alice` assigned roles `editor` and `auditor`
  - **When** her effective authority is enumerated
  - **Then** it is the union of the permission sets of `editor` and `auditor`.

- **Scenario: referential integrity**
  - **Given** an attempt to assign a user a role id that does not exist
  - **When** the model validates the assignment
  - **Then** the assignment is rejected and the user's role set is unchanged.

### Requirement: Deterministic, side-effect-free reads
The system SHALL expose the model as a set of pure read operations (enumerate a user's roles,
enumerate a role's permissions) that do not mutate state and return the same result for the
same stored model.

- **Scenario: repeated read is stable**
  - **Given** an unchanged model
  - **When** a user's roles are enumerated twice
  - **Then** both reads return identical sets.

---

## Capability: `access-decision`

**Purpose.** Answer the single question the card poses — *may U perform A on R?* — as an
`ALLOW`/`DENY` verdict derived purely from the `entitlements-model`. This capability owns the
*decision rule*, and nothing else.

### Requirement: Decision query shape
The system SHALL expose a decision operation that accepts a **query** `(user_id, action,
resource)` and returns a **verdict** of exactly `ALLOW` or `DENY`.

- **Scenario: well-formed query returns a verdict**
  - **Given** a decision query `("u_alice", "read", "doc:42")`
  - **When** the decision operation is invoked
  - **Then** it returns exactly one of `ALLOW` or `DENY` and mutates nothing.

### Requirement: Allow on any granting role (union rule)
The system SHALL return `ALLOW` if **any** role held by the user grants a permission equal to
`(action, resource)` from the query.

- **Scenario: one role suffices**
  - **Given** `u_alice` holds `editor` (grants `("write","doc:42")`) and `viewer` (grants
    `("read","doc:42")`)
  - **When** she queries `("read","doc:42")`
  - **Then** the verdict is `ALLOW` because `viewer` grants it, regardless of `editor`.

- **Scenario: union across roles**
  - **Given** `u_alice` holds two roles whose union grants `("write","doc:42")`
  - **When** she queries `("write","doc:42")`
  - **Then** the verdict is `ALLOW`.

### Requirement: Default deny
The system SHALL return `DENY` whenever no role held by the user grants a permission equal to
the query pair, including when the user holds no roles or does not exist.

- **Scenario: no grant present**
  - **Given** `u_bob` whose roles grant only `("read","doc:42")`
  - **When** he queries `("delete","doc:42")`
  - **Then** the verdict is `DENY`.

- **Scenario: unknown user denies**
  - **Given** a query for `user_id = "u_ghost"` that is not in the model
  - **When** the decision operation is invoked
  - **Then** the verdict is `DENY` (no error that leaks whether the user exists).

- **Scenario: exact-match only**
  - **Given** a role granting `("read","doc:42")`
  - **When** the user queries `("read","doc:99")` or `("READ","doc:42")`
  - **Then** the verdict is `DENY` (resource and action are matched exactly, no coercion).

### Requirement: Determinism and independence from evaluation order
The system SHALL make the verdict a pure function of `(model, query)` — independent of the
order in which roles or permissions are examined, and stable across repeated evaluation of an
unchanged model.

- **Scenario: order does not change the answer**
  - **Given** the same user, model, and query
  - **When** roles are evaluated in any order
  - **Then** the verdict is identical.

---

# Part 2 — Change bundle: `add-authorization-core`

## proposal.md — why + what

**Why.** There is today no shared, authoritative way to answer "may this user do this to this
thing?" Callers embed ad-hoc checks, which drift and disagree. We need one small, deterministic
service and a data model behind it so every caller gets the same verdict.

**What.** Introduce two capabilities:

- `entitlements-model` — users, roles, permissions `(action, resource)`, user→role and
  role→permission assignment, with integrity rules and pure reads.
- `access-decision` — a `decide(user_id, action, resource) → ALLOW | DENY` operation whose rule
  is *allow iff any held role grants the exact pair, else deny*.

**Explicitly out of scope for stage 1** (recorded so the freeze is honest, not so it is designed
now): explicit deny / negative grants; resource hierarchy or inheritance; time-bounded or
conditional grants; wildcards or pattern matching; delegation; audit logging beyond a verdict.
The decision rule is deliberately a single positive union so later features have a clean,
frozen baseline to extend.

**Success.** A caller submitting `(U, A, R)` receives a stable `ALLOW`/`DENY` that matches the
union rule exactly; the model rejects malformed permissions and dangling assignments.

## design.md — technical design, component structure, decisions

**Component structure.**

```
                +------------------------+
  query (U,A,R) |     access-decision    |  verdict ALLOW/DENY
  ------------->|   (decision engine)    |------------------->
                +-----------+------------+
                            | reads only (pure)
                            v
                +------------------------+
                |    entitlements-model  |
                |  users | roles |       |
                |  permissions | edges   |
                +------------------------+
```

- **entitlements-model** — the state of record. Entities:
  - `User { user_id }`
  - `Permission { action, resource }` — a value object; equality is structural on both fields.
  - `Role { role_id, grants: Set<Permission> }`
  - `UserRole { user_id, role_id }` — the assignment edge (many-to-many).
  It exposes only read operations to the engine: `roles_of(user_id) → Set<role_id>` and
  `permissions_of(role_id) → Set<Permission>`. Writes (create user, define role, grant, assign)
  live here too but are administrative, not on the decision path.

- **access-decision** — a *stateless* engine. `decide(u,a,r)` = form the query permission
  `p=(a,r)`; compute the user's **effective permission set** as the union of
  `permissions_of(role)` over `roles_of(u)`; return `ALLOW` if `p ∈` that set else `DENY`.

**Key decisions (the ADRs this change files).**

- **D1 — Default deny.** Absence of a matching grant is `DENY`, not error and not allow. Unknown
  user ⇒ `DENY` with no existence leak. *Rationale:* safe-by-default; a missing subject is
  indistinguishable from an unauthorized one.
- **D2 — Permission is a pure value pair, exact match only.** No wildcards, no normalization, no
  case folding of `action` or `resource`. *Rationale:* the smallest unambiguous unit; every
  later feature (hierarchy, patterns) becomes an *additive* layer over exact match rather than a
  rewrite of it.
- **D3 — Set/union semantics for grants and for effective authority.** Grants are duplicate-free;
  the verdict is order-independent. *Rationale:* makes the rule a pure function of state, which
  the determinism requirement demands and which stage 2 will need when precedence enters.
- **D4 — Model and decision are separate capabilities.** The engine only reads. *Rationale:*
  the decision rule will change (stage 2) while the storage shape is comparatively stable;
  separating them keeps each change small.
- **D5 — Verdict is binary now.** `ALLOW | DENY` only, with no reason payload. *Rationale:* keep
  the frozen contract minimal; a reason/obligation channel can be added additively if needed.

**Boundaries chosen for the freeze.** The engine consumes an *effective permission set*
abstraction, not the raw role loop. Even though stage 1 needs nothing more than a loop, phrasing
the rule as "is `p` in the effective set" is the seam later precedence rules attach to.

## tasks.md — ordered checklist (no code)

1. [ ] Ratify capability `entitlements-model`: entities `User`, `Permission`, `Role`,
       `UserRole`; set semantics; integrity rules (non-empty action/resource; no dangling
       role reference).
2. [ ] Ratify capability `access-decision`: query `(user_id, action, resource)`, verdict
       `ALLOW|DENY`, the union rule, default deny, exact match, determinism.
3. [ ] Confirm the read interface between them: `roles_of`, `permissions_of` are pure.
4. [ ] Record ADRs D1–D5.
5. [ ] Define the acceptance scenarios (all Given/When/Then above) as the test charter.
6. [ ] Review boundary seams (effective-set abstraction, model/decision split) for
       extensibility without over-building.
7. [ ] **Freeze** the two specs. Any change after this point is a new OpenSpec change bundle.

---

## Freeze marker

Stage-1 specs `entitlements-model` and `access-decision` are **FROZEN** as of acceptance of
change `add-authorization-core`. Stage 2 does not edit this file; it arrives as the separate
change documented in `stage-2.md` and rewrites the specs *there*.
