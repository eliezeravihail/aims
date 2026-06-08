# ADR-0021: Per-node requirements are user-sourced and surfaced at edit time
Status: proposed
Date: 2026-06-08
Supersedes: —
Superseded by: —

## Context

In long sessions, a change that fixes one thing silently regresses a
constraint the user cares about elsewhere. ADR-0008 gave each node a
`## Invariants & gotchas` section ("what must not break when editing"), but
two gaps remained: (1) those bullets read as observed code facts, not as a
stated **contract**, and consolidation could rewrite them by mining diffs;
(2) nothing put a node's constraints in front of the model at the moment its
code is edited — they only appeared at prompt time via the memory injector
(`templates/hooks/prompt-submit.sh`), and only when the prompt happened to
reference the file.

The user's framing sharpened the requirement: a *requirement* is **user
intent**, which lives with the user — it cannot be reverse-engineered from
code (reading code yields behavior, not intent). So requirements must be
captured from the user, recorded only on confirmation, and never fabricated.

## Decision

We refine ADR-0008's third section: rename `## Invariants & gotchas` →
`## Requirements & invariants`. It leads with user-recorded requirements and
keeps invariants/gotchas (code facts) below. Requirements are **user-sourced
only**: captured when the user states a constraint in-session (or when a file
is about to be edited and a constraint was raised), recorded verbatim only
after the user confirms (the convention lives in CLAUDE.md "Requirements
capture"). Every existing node is seeded uniformly — "no requirements beyond
CLAUDE.md; re-verify before editing" — rather than fabricating per-node
requirements. `post-edit-marker` surfaces the section as factual context at
edit time (ADR-0020); a change that conflicts with a recorded requirement is
escalated to the user. `consolidate.sh` is forbidden from inventing a
requirement from a diff; `lint.sh` enforces the renamed heading/order but not
content (an empty/seeded section is valid — requirements may be unknown).

This applies to the node body schema and the maintenance/marker tooling; it
does not change storage layout, the DAG model, or the two-phase pipeline.

## Consequences

- ✅ A node's constraints are visible exactly when its code is edited, which is
  where regressions are introduced.
- ✅ Requirements stay trustworthy: user-stated, confirmed, never fabricated.
- ✅ Conflicts surface as an explicit question rather than a silent choice.
- ⚠️ Capture and conflict-detection are model judgment (no reliable bash parse
  of natural-language intent); aims informs, never blocks (ADR-0020).
- ⚠️ The renamed heading must land in lint's `EXPECTED`, the scaffold, the
  consolidation prompt, and all existing nodes together, or lint reports an
  ordering mismatch (informational only).
- 🔒 Rules out auto-deriving requirements from code during consolidation.

## Alternatives considered

- **A separate `## Requirements` section (7 sections)** — rejected: the user
  chose to keep six sections and merge requirements with invariants.
- **A lint check that the requirements section is non-empty / has a real
  bullet** — rejected: an unknown/seeded requirement set is a valid state;
  enforcing content would punish honesty and flag fresh nodes.
- **Mine requirements from code/ADRs during consolidation** — rejected: that
  fabricates intent the user never stated.

## Verification

- `bash .claude/memory/lint.sh` is clean with every node carrying
  `## Requirements & invariants` (heading/order enforced in
  `templates/memory/lint.sh`).
- `bash tests/requirements.sh` covers `fm_section`, the seed scaffold, and
  `post-edit-marker` surfacing requirements at edit time.
- Editing a tracked source file injects the node's requirements: see
  `templates/hooks/post-edit-marker.sh` (the `reqblock` path).
