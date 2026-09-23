---
title: "goals"
date: 2026-09-23
---
## Primary goal
A decision service that answers one question: **may user U perform action A on resource R?** — allow or deny.

## Use scenarios
- Stage 1 model: each user is assigned one or more roles; each role grants a set of permissions, a permission
  being an `(action, resource)` pair. U may perform A on R iff **any** of U's roles grants `(A, R)`; otherwise deny.
- Start-to-result: the host supplies the entitlement model (who holds which role, which role grants which
  permission); a caller asks `(U, A, R)` and receives allow or deny.

## Product assumptions (no product owner reachable; stated per the standing instruction in `substrate.md`)
Each is the simple, sensible reading; a different answer would change behavior, so each is named.
- **A1 — the model is supplied, not administered.** The host hands the service a complete entitlement model
  (in code, or a file for the CLI). There is no grant/revoke/assign API in stage 1; changing entitlements
  means supplying a new model, which replaces the old one whole.
- **A2 — anything unknown is a deny, not an error.** An unknown user, an unknown action or an unknown
  resource answers deny. A malformed question (an empty or non-string identifier) is an error, not a deny.
- **A3 — an inconsistent model is rejected when supplied.** A user assigned to a role the model does not
  define is a load error (fail fast), never a silent deny at query time. A role granting nothing is valid.
  A user with zero roles is valid and is denied everything (same answer as an unknown user).
- **A4 — identifiers are opaque, exact, case-sensitive, non-empty strings.** No wildcards, no resource
  hierarchy, no action implication (`write` does not imply `read`).
- **A5 — the answer is allow/deny only.** No explanation of which role granted it.
- **A6 — the model has set semantics.** A repeated assignment or grant is the same as one.

## Non-goals (stage 1)
- Administration API, persistence, network service, audit log, caching layers.
- Explicit deny rules, wildcards, hierarchies, role inheritance, conditions/attributes, tenants — not revealed; not built for.
