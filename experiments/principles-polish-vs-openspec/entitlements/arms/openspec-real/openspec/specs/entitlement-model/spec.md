# entitlement-model Specification

## Purpose

Defines the data the entitlements service decides from: users, the roles assigned to them, and the
`(action, resource)` permissions each role grants, together with the rules a model must satisfy before
it can be queried.

## Requirements

### Requirement: Permission is an exact action-resource pair
A permission SHALL be identified by the pair `(action, resource)`. Action and resource SHALL each be a
non-empty string. They SHALL be compared exactly and case-sensitively, with no wildcard, prefix,
hierarchy, or implication semantics.

#### Scenario: Distinct pairs are distinct permissions
- **WHEN** a role grants `(read, doc-42)`
- **THEN** that role does not grant `(write, doc-42)`, `(read, doc-43)`, `(Read, doc-42)`, or `(read, *)`

#### Scenario: Empty identifier rejected
- **WHEN** a model is built containing a permission whose action or resource is an empty string
- **THEN** building the model fails with a validation error that names the offending entry

### Requirement: Roles grant sets of permissions
A role SHALL be identified by a non-empty string and SHALL grant a set of zero or more permissions.
Granting the same permission more than once SHALL have the same effect as granting it once.

#### Scenario: Duplicate grant is idempotent
- **WHEN** a role is defined granting `(read, doc-42)` twice
- **THEN** the model builds successfully and the role grants `(read, doc-42)` exactly once

#### Scenario: Role with no permissions
- **WHEN** a role is defined with no permissions
- **THEN** the model builds successfully and the role grants nothing

### Requirement: Users are assigned roles
A user SHALL be identified by a non-empty string and SHALL be assigned a set of one or more roles. A
user with no role assignments SHALL be indistinguishable from a user that is not in the model.
Assigning the same role more than once SHALL have the same effect as assigning it once.

#### Scenario: User with several roles
- **WHEN** user `alice` is assigned roles `editor` and `viewer`
- **THEN** the model records both assignments for `alice`

### Requirement: Role assignments reference defined roles
Every role named in a user assignment SHALL be defined in the same model. A model that assigns an
undefined role SHALL be rejected as a whole. No partially built model SHALL become queryable.

#### Scenario: Assignment to undefined role
- **WHEN** a model is built in which user `alice` is assigned role `auditor` and no role `auditor` is defined
- **THEN** building the model fails with a validation error naming user `alice` and role `auditor`

#### Scenario: All validation errors reported together
- **WHEN** a model is built with several invalid entries
- **THEN** the validation error lists every invalid entry, not only the first one found

### Requirement: A built model is immutable
Once built, a model SHALL NOT change. To change entitlements, callers SHALL build a new model. Queries
already evaluating against a model SHALL be unaffected by the construction of another model.

#### Scenario: Source data mutated after build
- **WHEN** a model is built from caller-supplied collections and the caller later mutates those collections
- **THEN** decisions made against the built model are unchanged
