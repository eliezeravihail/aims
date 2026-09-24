# Spec Delta

## MODIFIED Requirements

### Requirement: Allow when any assigned role grants the exact permission
For a question `(user, action, resource)` asked at an evaluation instant, a grant SHALL be
**applicable** if and only if all of these hold:
- a role assigned to the user holds the grant
- the grant's action equals the action
- the grant's resource is the resource or one of its ancestors
- the grant applies at the evaluation instant

The service SHALL answer **allow** if and only if at least one applicable grant is an allow and no
applicable grant is a deny.

#### Scenario: Single role grants
- **WHEN** `alice` is assigned `editor`, `editor` grants `(write, doc-42)`, and the service is asked whether `alice` may `write` `doc-42`
- **THEN** the answer is allow

#### Scenario: Grant comes from one of several roles
- **WHEN** `alice` is assigned `viewer` and `editor`, only `editor` grants `(write, doc-42)`, and the service is asked whether `alice` may `write` `doc-42`
- **THEN** the answer is allow

#### Scenario: Grant on a group applies beneath it
- **WHEN** `doc-42` is in `finance`, `finance` is in `org-root`, `alice`'s role allows `(read, org-root)`, and the service is asked whether `alice` may `read` `doc-42`
- **THEN** the answer is allow

#### Scenario: Grant on a descendant does not apply upward
- **WHEN** `doc-42` is in `finance`, `alice`'s only grant allows `(read, doc-42)`, and the service is asked whether `alice` may `read` `finance`
- **THEN** the answer is deny

#### Scenario: Group grant does not reach siblings outside the group
- **WHEN** `doc-42` is in `finance`, `doc-7` is in `hr`, `alice`'s role allows `(read, finance)`, and the service is asked whether `alice` may `read` `doc-7`
- **THEN** the answer is deny

### Requirement: Deny by default
The service SHALL answer **deny** in every case not covered by the allow rule. This includes each of
these cases:
- a user who is not in the model
- an action or resource that no applicable grant mentions
- a case where the only matching grants are outside their validity windows

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

#### Scenario: Only grant has expired
- **WHEN** `carol`'s only grant allows `(read, finance)` with window `[2026-01-01T00:00Z, 2026-04-01T00:00Z)`, and the service is asked at `2026-05-01T00:00Z` whether `carol` may `read` `finance`
- **THEN** the answer is deny

### Requirement: Malformed questions are rejected, never allowed
The service SHALL raise an error that identifies the invalid argument in each of these cases, and SHALL
NOT answer allow:
- the user, action, or resource is not a non-empty string
- a supplied evaluation instant is not a timezone-aware datetime
- no evaluation instant is supplied and the answer depends on one, as defined by the evaluation-instant
  requirement

#### Scenario: Empty action
- **WHEN** the service is asked whether `alice` may perform action `""` on `doc-42`
- **THEN** an invalid-request error is raised and no allow is returned

#### Scenario: Naive evaluation instant
- **WHEN** the service is asked a question with an evaluation instant that has no timezone
- **THEN** an invalid-request error is raised that identifies the evaluation instant

### Requirement: Decisions are deterministic and side-effect free
For a given model, question, and evaluation instant, the service SHALL always return the same answer.
The service SHALL NOT consult a clock or any other ambient state. Asking a question SHALL NOT modify the
model.

#### Scenario: Repeated question
- **WHEN** the same question is asked twice against the same model at the same evaluation instant
- **THEN** both answers are identical

#### Scenario: Time passing does not change an answer
- **WHEN** a question is asked with evaluation instant `2026-02-01T00:00Z`, and the same question with the same instant is asked again after a time-bounded grant's window has ended in real time
- **THEN** both answers are identical

## ADDED Requirements

### Requirement: Explicit deny overrides allow
If any applicable grant is a deny, the service SHALL answer **deny**. This SHALL hold even when another
applicable grant is an allow, including in each of these cases:
- the allow comes from a different role
- the allow is on a more specific resource
- the allow is on a less specific resource

#### Scenario: Deny from another role wins
- **WHEN** `alice` holds `editor`, which allows `(write, doc-42)`, and `alice` also holds `contractor`, which denies `(write, doc-42)`, and the service is asked whether `alice` may `write` `doc-42`
- **THEN** the answer is deny

#### Scenario: Deny on a descendant narrows a group allow
- **WHEN** `doc-42` is in `finance`, `alice`'s roles allow `(read, finance)` and deny `(read, doc-42)`, and the service is asked whether `alice` may `read` `doc-42` and whether `alice` may `read` `doc-43`, which is also in `finance`
- **THEN** the answer for `doc-42` is deny and the answer for `doc-43` is allow

#### Scenario: Deny on an ancestor beats an allow on the descendant
- **WHEN** `doc-42` is in `finance`, `alice`'s roles deny `(read, finance)` and allow `(read, doc-42)`, and the service is asked whether `alice` may `read` `doc-42`
- **THEN** the answer is deny

#### Scenario: Deny for a different action does not interfere
- **WHEN** `alice`'s roles allow `(read, doc-42)` and deny `(write, doc-42)`, and the service is asked whether `alice` may `read` `doc-42`
- **THEN** the answer is allow

#### Scenario: A deny alone is not an allow
- **WHEN** `alice`'s only grant denies `(read, doc-42)` and the service is asked whether `alice` may `read` `doc-43`
- **THEN** the answer is deny

### Requirement: Time-bounded grants apply only inside their window
The service SHALL evaluate every grant's window against the evaluation instant of the question. Grants
whose windows do not contain the instant SHALL be ignored. This SHALL apply equally to allows and denies.

#### Scenario: Allow inside window
- **WHEN** `carol`'s role allows `(read, finance)` with window `[2026-01-01T00:00Z, 2026-04-01T00:00Z)`, and the service is asked at `2026-02-15T12:00Z` whether `carol` may `read` `finance`
- **THEN** the answer is allow

#### Scenario: Allow at the exclusive end
- **WHEN** the same grant is evaluated at `2026-04-01T00:00Z`
- **THEN** the answer is deny

#### Scenario: Expired deny no longer overrides
- **WHEN** `alice`'s roles allow `(read, doc-42)` without a window and deny `(read, doc-42)` with window `[2026-01-01T00:00Z, 2026-02-01T00:00Z)`, and the service is asked at `2026-03-01T00:00Z` whether `alice` may `read` `doc-42`
- **THEN** the answer is allow

#### Scenario: Deny inside its window overrides
- **WHEN** the same model is asked at `2026-01-15T00:00Z`
- **THEN** the answer is deny

### Requirement: Evaluation instant is supplied by the caller
The service SHALL accept an optional evaluation instant with each question. When an instant is
supplied, every grant's window SHALL be evaluated against it. When no instant is supplied, the service
SHALL proceed as follows:
- It SHALL answer normally if none of the grants that match the user, action, and resource or an
  ancestor carries a validity window.
- It SHALL reject the question with an invalid-request error if any such grant carries a validity
  window.

The service SHALL NOT substitute the current time.

#### Scenario: Stage-1 question needs no instant
- **WHEN** a model has no time-bounded grants and the service is asked, without an evaluation instant, whether `alice` may `write` `doc-42`
- **THEN** the service answers exactly as stage 1 would

#### Scenario: Unrelated time-bounded grant does not require an instant
- **WHEN** a model contains a time-bounded grant only for `(read, hr)`, and the service is asked, without an evaluation instant, whether `alice` may `write` `doc-42`
- **THEN** the service answers without error

#### Scenario: Relevant time-bounded grant requires an instant
- **WHEN** `carol`'s role allows `(read, finance)` with a validity window, and the service is asked, without an evaluation instant, whether `carol` may `read` `doc-42` in `finance`
- **THEN** an invalid-request error is raised that identifies the missing evaluation instant, and no allow is returned
