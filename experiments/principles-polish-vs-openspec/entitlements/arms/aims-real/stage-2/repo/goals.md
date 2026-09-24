---
title: "goals"
date: 2026-09-23
---
## Primary goal
A decision service that answers one question: **may user U perform action A on resource R?** — allow or deny.

## Use scenarios
- Stage 1 model: each user is assigned one or more roles; each role grants a set of permissions, a permission
  being an `(action, resource)` pair. U may perform A on R iff **any** of U's roles grants `(A, R)`; otherwise deny.
- Stage 2 (product change, 2026-09-23): a grant is an **allow** or an explicit **deny**; a deny for (A, R) from
  any of U's roles overrides any allow. Resources form a hierarchy; a grant on a group applies to everything
  beneath it, and a deny anywhere on the path wins. A grant may carry a validity window `[from, to)`; the
  decision is made relative to a supplied "now". Stage-1 answers are unchanged where these features are absent.
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
- **A4 — identifiers are opaque, exact, case-sensitive, non-empty strings.** No wildcards, no action
  implication (`write` does not imply `read`). (Stage 2 adds a *resource* hierarchy — B2; actions stay flat.)
- **A5 — the answer is allow/deny only.** No explanation of which role granted it.
- **A6 — the model has set semantics.** A repeated assignment or grant is the same as one.

## Stage-2 product assumptions (same standing instruction; recorded 2026-09-23)
- **B1 — deny wins everywhere on the path.** "A more specific grant says otherwise" can only make a
  group-allowed resource denied; a more specific allow never beats a deny on an ancestor. DENY if any in-force
  deny from any of U's roles covers (A, R) via R or an ancestor; else ALLOW if any in-force allow does; else DENY.
- **B2 — the hierarchy is a tree**, part of the supplied model: at most one parent per resource; a group is itself
  a resource (askable, may have a parent). Cycles and self-parents are rejected at build. A resource not in the
  hierarchy is its own root. Inheritance flows down only.
- **B3 — windows are half-open `[from, to)`**, either bound optional, no window = always in force. Datetimes must
  be timezone-aware (naive → error, in model and question); comparison is by instant; `from >= to` is a model error.
- **B4 — "now" is supplied on every question**; the library never reads the clock. The CLI may default it to the
  wall clock.
- **B5 — windows apply to allow and deny alike.** Roles, assignments and the hierarchy are not time-bounded.

## Non-goals
- Administration API, persistence, network service, audit log, caching layers.
- Wildcards, action hierarchy, role inheritance, multiple parents, recurring windows, conditions/attributes,
  tenants, explanations — not revealed; not built for. (Explicit deny and resource hierarchy moved into scope at
  stage 2.)
