# Spec Delta

## MODIFIED Requirements

### Requirement: Permission is an exact action-resource pair
A permission SHALL be identified by the pair `(action, resource)`. Action and resource SHALL each be a
non-empty string. They SHALL be compared exactly and case-sensitively. There SHALL be no wildcard, prefix,
or action-implication semantics. A resource SHALL relate to another resource only through the explicit
resource hierarchy declared in the model. Resource names SHALL NOT imply containment.

#### Scenario: Distinct pairs are distinct permissions
- **WHEN** a role grants `(read, doc-42)` and the model declares no hierarchy
- **THEN** that role does not grant `(write, doc-42)`, `(read, doc-43)`, `(Read, doc-42)`, or `(read, *)`

#### Scenario: Names do not imply hierarchy
- **WHEN** a role grants `(read, finance)`, resource `finance/doc-42` exists, and the model declares no parent for `finance/doc-42`
- **THEN** that role does not grant `(read, finance/doc-42)`

#### Scenario: Empty identifier rejected
- **WHEN** a model is built containing a permission whose action or resource is an empty string
- **THEN** building the model fails with a validation error that names the offending entry

### Requirement: Roles grant sets of permissions
A role SHALL be identified by a non-empty string and SHALL hold a set of zero or more grants. A grant
SHALL consist of the following parts:
- a permission `(action, resource)`
- an effect, which is either **allow** or **deny**
- an optional validity window

A grant given only as a permission SHALL mean an allow with no window. Two grants SHALL be the same grant
when their permission, effect, and window are all equal. Holding the same grant more than once SHALL have
the same effect as holding it once. A role MAY hold both an allow and a deny for the same permission, and
the model SHALL accept this.

#### Scenario: Duplicate grant is idempotent
- **WHEN** a role is defined granting `(read, doc-42)` twice
- **THEN** the model builds successfully and the role grants `(read, doc-42)` exactly once

#### Scenario: Role with no permissions
- **WHEN** a role is defined with no permissions
- **THEN** the model builds successfully and the role grants nothing

#### Scenario: Plain permission is an unbounded allow
- **WHEN** a role is defined with the plain permission `(read, doc-42)`
- **THEN** the role holds an allow grant for `(read, doc-42)` with no validity window

#### Scenario: Allow and deny for the same permission coexist
- **WHEN** a role is defined with both an allow and a deny for `(read, doc-42)`
- **THEN** the model builds successfully and the role holds both grants

## ADDED Requirements

### Requirement: Resources may be arranged in a hierarchy
The model SHALL accept a resource hierarchy that assigns each resource at most one parent resource, called
its group. The ancestors of a resource SHALL be its parent, its parent's parent, and so on, up to a
resource that has no parent. A resource SHALL NOT need to be declared anywhere to be asked about. A
resource with no declared parent SHALL have no ancestors. A group SHALL itself be a resource: it can be
granted on, have a parent, and be the subject of a question. The hierarchy SHALL be optional. A model
that declares no hierarchy SHALL behave as in stage 1.

#### Scenario: Ancestor chain
- **WHEN** the model declares `doc-42` in `finance` and `finance` in `org-root`
- **THEN** the ancestors of `doc-42` are `finance` and `org-root`, in that order

#### Scenario: Undeclared resource has no ancestors
- **WHEN** the model declares a hierarchy that does not mention `doc-99`
- **THEN** `doc-99` has no ancestors and no error is raised

### Requirement: Resource hierarchy is validated
Building a model SHALL fail with a validation error in each of these cases:
- a hierarchy entry names an empty child or parent
- a resource is its own parent
- the hierarchy contains a cycle of any length
- a resource is given more than one distinct parent

The error SHALL name the offending resources. These errors SHALL be reported together with all other
validation errors in the model.

#### Scenario: Cycle rejected
- **WHEN** a model is built declaring `a` in `b`, `b` in `c`, and `c` in `a`
- **THEN** building the model fails with a validation error naming the cycle `a`, `b`, `c`

#### Scenario: Self-parent rejected
- **WHEN** a model is built declaring `finance` in `finance`
- **THEN** building the model fails with a validation error naming `finance`

### Requirement: Grants may carry a validity window
A grant MAY carry a validity window `[from, to)`. Either bound MAY be absent, and an absent bound SHALL
be unbounded on that side. A grant SHALL apply at instant `t` if and only if all of these hold:
- `from` is absent, or `from <= t`
- `to` is absent, or `t < to`

Bounds SHALL be timezone-aware instants. They SHALL be compared as instants, independent of the timezone
in which each one is written. A grant with no window SHALL apply at every instant.

#### Scenario: Window is half-open
- **WHEN** a grant has window `[2026-01-01T00:00Z, 2026-04-01T00:00Z)`
- **THEN** it applies at `2026-01-01T00:00Z` and at `2026-03-31T23:59:59Z`, and does not apply at `2026-04-01T00:00Z` or at `2025-12-31T23:59:59Z`

#### Scenario: Open-ended window
- **WHEN** a grant has window `[2026-01-01T00:00Z, unbounded)`
- **THEN** it applies at every instant from `2026-01-01T00:00Z` onward

#### Scenario: Bounds in different timezones
- **WHEN** a grant's window ends at `2026-04-01T02:00+02:00`
- **THEN** it does not apply at `2026-04-01T00:00Z`

### Requirement: Validity windows are validated
Building a model SHALL fail with a validation error in each of these cases:
- a window bound is not a timezone-aware datetime
- both bounds are present and `from` is not strictly before `to`

The error SHALL name the role and grant, and SHALL be reported together with all other validation errors
in the model.

#### Scenario: Naive bound rejected
- **WHEN** a model is built with a grant whose window starts at a datetime that has no timezone
- **THEN** building the model fails with a validation error naming that role and grant

#### Scenario: Empty window rejected
- **WHEN** a model is built with a grant whose window has `from` equal to `to`
- **THEN** building the model fails with a validation error naming that role and grant
