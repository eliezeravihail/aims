# access-decision Specification

## Purpose

Answers the single question "may user U perform action A on resource R?" with allow or deny, evaluated
against a validated entitlement model, denying by default.

## Requirements

### Requirement: Allow when any assigned role grants the exact permission
The service SHALL answer **allow** for `(user, action, resource)` if and only if at least one role
assigned to that user grants the permission `(action, resource)`.

#### Scenario: Single role grants
- **WHEN** `alice` is assigned `editor`, `editor` grants `(write, doc-42)`, and the service is asked whether `alice` may `write` `doc-42`
- **THEN** the answer is allow

#### Scenario: Grant comes from one of several roles
- **WHEN** `alice` is assigned `viewer` and `editor`, only `editor` grants `(write, doc-42)`, and the service is asked whether `alice` may `write` `doc-42`
- **THEN** the answer is allow

### Requirement: Deny by default
The service SHALL answer **deny** in every case not covered by the allow rule. This includes a user who
is not in the model, and an action or resource that no role mentions.

#### Scenario: Role lacks the permission
- **WHEN** `bob` is assigned `viewer`, `viewer` grants only `(read, doc-42)`, and the service is asked whether `bob` may `write` `doc-42`
- **THEN** the answer is deny

#### Scenario: Permission on a different resource
- **WHEN** `bob`'s roles grant `(read, doc-42)` and the service is asked whether `bob` may `read` `doc-43`
- **THEN** the answer is deny

#### Scenario: Unknown user
- **WHEN** the service is asked about user `mallory`, who is not in the model
- **THEN** the answer is deny, and no error is raised

#### Scenario: Another user's role does not leak
- **WHEN** `alice`'s role grants `(write, doc-42)`, `bob` does not hold that role, and the service is asked whether `bob` may `write` `doc-42`
- **THEN** the answer is deny

### Requirement: Answer is exactly allow or deny
The service SHALL return one of exactly two outcomes, allow or deny. The outcome SHALL NOT be a value
that could be mistaken for the other (for example, a truthy or falsy non-boolean).

#### Scenario: Outcome type
- **WHEN** any well-formed question is asked
- **THEN** the result is either allow or deny and nothing else

### Requirement: Malformed questions are rejected, never allowed
If the user, action, or resource in a question is not a non-empty string, the service SHALL raise an
error that identifies the invalid argument. It SHALL NOT answer allow.

#### Scenario: Empty action
- **WHEN** the service is asked whether `alice` may perform action `""` on `doc-42`
- **THEN** an invalid-request error is raised and no allow is returned

### Requirement: Decisions are deterministic and side-effect free
For a given model and question, the service SHALL always return the same answer. Asking a question SHALL
NOT modify the model.

#### Scenario: Repeated question
- **WHEN** the same question is asked twice against the same model
- **THEN** both answers are identical
