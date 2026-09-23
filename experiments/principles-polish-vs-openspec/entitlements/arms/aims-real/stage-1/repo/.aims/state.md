# aims Guide State

## Mode

auto

## Loop cursor

ready-to-choose-next (stage-1 design met; operator scope is design only — stop before implementation)

## Current objective

**Kind:** design

**Objective:** A buildable architecture for the stage-1 decision service in which the grant rule ("any of U's
roles grants (A,R)") has exactly one owner, the entitlement model is an immutable domain object that is
consistent by construction, and the source of the model (in-code, file for the CLI) is a replaceable edge
that never leaks into the decision core.

**Why now:** opening round of a new product; nothing exists. Feasibility is not in doubt.

**Exit criteria:**
- [ ] Buildable: Python 3.11 stdlib, module skeleton, concrete public signatures, error types.
- [ ] One owner for the grant rule; every entry path (library call, CLI) reaches it.
- [ ] Cases: unknown user → deny; user with roles none of which grant → deny; two roles, only the second grants → allow; (write, R) granted but (read, R) asked → deny; (read, R1) granted but (read, R2) asked → deny; user with zero roles → deny; role granting nothing → valid.
- [ ] Case-sensitivity: `Read` ≠ `read`; `doc-42` ≠ `DOC-42`.
- [ ] Malformed question (empty string, non-string) → error at the boundary, not deny.
- [ ] Inconsistent model (assignment to undefined role) → rejected when the model is built/loaded, never at query time.
- [ ] Duplicate assignments/grants idempotent.
- [ ] Model immutable after construction; replacing it is whole-model swap; concurrent queries see one consistent model (no torn read) — falsifier: a reload that mutates the live model in place fails this.
- [ ] File format parsing confined to an edge; the core never imports json/argparse.
- [ ] Deny is the absence of any grant — no inert "deny" machinery for a stage that has no deny rules.

**Preserve:** goals.md assumptions A1–A6; substrate.

**Do not optimize for:** future stages (wildcards, hierarchy, explicit deny, ABAC), performance tuning, admin API, pattern count.

## Worker handoff (drafted — do not execute before the build command)

See the panel prompts sent in this round (identical except the axis block).

## Open assumptions (unproven — carried, not filed)

- None beyond goals.md A1–A6 (filed as stated assumptions).

## Open Guide TODO

- [x] Merge panel drafts into one design (DESIGN.md); ADR 0002 to file after revision.
- [x] Mandatory revise round on the merged design.
- [x] Write DESIGN.md.
- [ ] (Deferred, out of this session's scope) implementation objective conforming to DESIGN.md.

## Last evaluated result

met — merged panel design re-measured after one revise round: all 6 findings resolved (str-subclass normalization, inert _Role.name removed, precise single-owner map, two-phase error policy, consistency fixes, exit-criteria trace + 2 added tests). Every exit criterion has an owner (DESIGN.md §3/§7) and a test (§8). Decision filed: decisions/0002.
