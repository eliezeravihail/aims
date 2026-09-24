# aims Guide State

## Mode

auto

## Loop cursor

ready-to-choose-next (stage-2 design met; operator scope is design only — stop before implementation)

## Current objective

**Kind:** design

**Objective:** Evolve the stage-1 architecture so that the stage-2 decision — explicit deny overriding allow,
grants inherited down a resource hierarchy, grants bounded by a validity window evaluated at a supplied
"now" — has exactly one owner for the combining rule (deny wins) and one owner for each clause that feeds it
(does a grant apply to this resource? at this instant?), with deny modelled as a first-class effect, the
hierarchy consistent by construction, and every stage-1 answer preserved where the new features are absent.

**Hard decision at its core:** where the precedence rule lives once three independent dimensions (roles ×
ancestor path × time) feed one decision; how deny is represented so it can outrank an allow from any role at
any level; who owns the resource hierarchy and its invariants (tree, acyclic); how "now" crosses the seam.

**Why now:** a newly received product change (stage 2); stage-1 design (DESIGN.md, decisions/0002) explicitly
names `decide` and the role clause as the owner a deny/hierarchy stage would reopen.

**Exit criteria:**
- [x] Buildable: Python 3.11 stdlib; module skeleton; concrete public signatures incl. how `now` and the
      hierarchy enter; error types.
- [x] One owner for "deny overrides allow"; one owner for "grant covers resource R" (self-or-ancestor); one
      owner for "grant is in force at now"; every entry path (library, CLI) reaches them.
- [x] Deny is a first-class effect, not a missing allow (concept fit).
- [x] Stage-1 preservation: every stage-1 case in DESIGN.md §3.4/§8 gives the same answer for a model with no
      deny, no hierarchy, no window, at any now.
- [x] Deny: role X allows + role Y denies same (A,R) → DENY; same role allows and denies → DENY; deny on
      (write,R) leaves (read,R) allowed; deny on R1 leaves R2; deny-only user → DENY.
- [x] Hierarchy: allow on org-root → allow on doc-42 (depth ≥2); allow on finance + deny on doc-42 → doc-42
      DENY, sibling doc-43 ALLOW; **deny on org-root + allow on doc-42 → DENY** (falsifier: the tempting
      "most specific grant wins" shortcut returns ALLOW and fails); deny on doc-42 does not affect a question
      about finance (no upward flow); a resource not in the hierarchy gets only its exact grants; a group is
      itself askable; cycle, self-parent, two parents → rejected at build.
- [x] Time: window [t0,t1): now=t0 applies, now=t1 does not, now<t0 does not; open-ended bounds; from ≥ to
      rejected at build; naive datetime rejected (model and question); same instant in different offsets
      behaves identically; expired deny no longer blocks an allow; not-yet-valid allow does not allow.
- [x] Interactions: time-bounded deny on a group vs permanent allow on a leaf; same (effect,A,R) with two
      windows → each applies in its own window; exact duplicates idempotent.
- [x] Model (grants + hierarchy) immutable; replacement whole-swap; no torn read between hierarchy and grants.
- [x] File format extended at the edge only; core imports no json/argparse; datetime parsing placement justified.
- [x] Answer still allow/deny only (A5).

**Preserve:** goals.md A1–A6; DESIGN.md A7–A9; substrate; stage-1 seams (strings at the seam, immutable
model, edges → core).

**Do not optimize for:** wildcards, role inheritance, ABAC/conditions, explanations, admin API, caching,
performance, stages not revealed.

## Worker handoff

Panel package (identical except axis) sent to three Workers; raw drafts at .aims/panel/2026-09-23-stage2/.

## Open assumptions (stated per substrate.md standing instruction; filed in goals.md and DESIGN.md §12)

- B1 deny wins everywhere on the path; specificity never lets an allow beat a deny.
- B2 hierarchy is a tree (one parent), declared in the model; undeclared resource = its own root.
- B3 windows half-open, either bound optional, tz-aware datetimes only; from ≥ to rejected.
- B4 `now` is required on every question; CLI defaults it to the wall clock.
- B5 windows apply to allow and deny alike; roles and assignments are not time-bounded.

## Open Guide TODO

- [x] Merge panel drafts; file ADR 0003.
- [x] Mandatory revise round.
- [x] Write DESIGN.md (stage 2) and update goals.md (B1–B5 filed there).
- [ ] (Deferred, out of scope) implementation objective.

## Last evaluated result

met — stage-2 merged panel design re-measured after one revise round: 6 findings resolved (_Hierarchy invariant
on every construction path via __post_init__; per-question iterative lineage walk instead of O(n²) precompute;
precise AST fitness forms; _CycleError removed; single file grant spelling; consistency pass). Every exit
criterion has an owner (DESIGN.md §5), a trace (§9) and a test (§10). Decision filed: decisions/0003.
