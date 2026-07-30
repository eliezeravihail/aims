---
id: 31
title: "aims adopts the Capsa capsule format as its storage layer"
status: accepted
date: 2026-07-29
supersedes: null
superseded_by: null
discussion_ref: null
tags: [partially-supersedes-0005, partially-supersedes-0007, partially-supersedes-0008, partially-supersedes-0028]
---

## Context

aims proved the artifact discipline — ADRs, plans, and a self-maintaining
memory tree — but stored it in a bespoke layout (`docs/adr/`, `docs/plans/`,
`docs/memory/`) with a hand-rolled node schema (decisions 0007, 0008, 0028).
Capsa (the owner's separate standard, `capsa_version 0.2.0`) is the clean,
passive, schema-backed generalization of exactly that discipline: a single
`.capsa/` capsule holding `decisions/`, `plans/`, `insights/{code,dev,design}/`,
`charter.md`, and a `capsule.yaml` manifest — with a stdlib-only validator.

Capsa's own decision 0002 chose *not* to fork aims ("aims stays as-is"); that
was Capsa's scoping decision. This is the independent, reverse decision by
*aims*: adopt Capsa as its own format because aims itself becomes far cleaner
and better-organized on it.

## Decision

aims stores its management truth as a conforming Capsa 0.2.0 capsule at
`.capsa/`. The mapping is: ADRs → `decisions/`, plans → `plans/`, memory-tree
nodes → `insights/` (code-anchored nodes → `insights/code/` carrying
`code_globs`; historical breadcrumbs → `insights/dev/`), CLAUDE.md's project
conventions → `charter.md`. Capsa is passive data; **aims is the active
self-maintenance layer on top of it** — precisely the role Capsa's README
reserves for such a tool. aims' hooks/scripts read and write the capsule
instead of the old `docs/` layout (Phase B).

## Consequences

- ✅ One schema-validated home; the vendored `validator/validate.py` checks
  conformance mechanically. Cleaner, portable, tool-agnostic.
- ✅ aims gains Capsa's richer primitives when needed (requirements, issues,
  dependencies/licensing, releases, the verification block) — absent until
  used, never an error.
- ⚠️ The bespoke node schema (0008/0028) is superseded by Capsa insights;
  its structured fields (`related`, `external_refs`) flatten into insight
  bodies/tags. Durable facts are preserved in prose.
- ⚠️ Status-enum nuance ("amended by NNNN", "partial") that Capsa's
  decision enum does not model is preserved as `tags` and `superseded_by`.
- 🔒 Rules out aims' bespoke `docs/adr|plans|memory` layout going forward.

## Alternatives considered

- **Keep the bespoke layout** — rejected: Capsa is the same discipline,
  cleaner and standardized; maintaining a parallel private schema is waste.
- **Migrate data only, keep tooling on `docs/`** — rejected as the end
  state: it would leave two homes (violates Capsa §1.4 single-home); done
  only as a transient Phase-A window before the Phase-B tooling retarget.
