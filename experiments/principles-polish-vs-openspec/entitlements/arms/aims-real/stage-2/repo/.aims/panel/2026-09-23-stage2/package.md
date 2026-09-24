ROLE
You are a design Worker — a senior engineer as capable as the Guide. The design is the deliverable. This is a
DESIGN-ONLY task: produce an architecture document, not implementation code (signatures, interface sketches and
a few illustrative lines are welcome). Do not redefine priorities; if evidence invalidates the objective, report it.

DESIGN GOAL (the objective — a quality outcome, not a feature)
Evolve the existing stage-1 architecture (read /home/user/aims-rerun/entitlements/DESIGN.md, goals.md,
substrate.md, decisions/0002-*.md) so that the stage-2 decision has exactly ONE owner for the combining rule
(deny overrides allow) and one owner for each clause that feeds it (does a grant cover this resource? is it in
force at this instant?), with deny modelled as a first-class effect, the resource hierarchy consistent by
construction, and every stage-1 answer preserved where the new features are absent.
The hard decision at its core: where the precedence rule lives once three independent dimensions
(user's roles × the resource's ancestor path × time) feed one decision; how deny is represented so it can
outrank an allow from any role at any level; who owns the hierarchy and its invariants; how "now" crosses the seam.

BEHAVIOR IT MUST SATISFY (the product change, verbatim, plus resolved readings)
1. Explicit deny. A grant may be an allow or an explicit deny. An explicit deny for (A,R) applied to any of U's
   roles overrides any allow — even an allow from a different role. (Deny wins.)
2. Resource inheritance. Resources form a hierarchy: a resource may belong to a group (doc-42 is in folder
   finance, which is in org-root). A grant on a group applies to every resource beneath it, unless a more
   specific grant on a descendant says otherwise. A deny anywhere on the path still wins over an allow.
3. Time-bounded grants. A grant may carry a validity window [from, to). Outside its window the grant does not
   apply. The decision is made relative to a supplied "now".
The stage-1 question and its answer for a simple role→permission grant are unchanged where these features are absent.

Resolved readings (product assumptions, stated per the product owner's standing instruction in substrate.md;
treat as grounded):
- B1 Deny wins everywhere on the path. Given (2)'s last sentence, "more specific grant says otherwise" can only
  ever make a group-allowed resource denied; a more specific ALLOW never beats a deny on an ancestor.
  Effective rule: DENY if any in-force deny from any of U's roles covers (A,R) via R or an ancestor; else ALLOW
  if any in-force allow does; else DENY.
- B2 The hierarchy is a tree: each resource has at most one parent group; a group is itself a resource (it can
  be asked about and can belong to a group). It is part of the supplied model (A1: supplied whole, replaced
  whole). Cycles, self-parent and two parents are model errors rejected at build (A3 spirit). A resource not
  mentioned in the hierarchy is its own root: only its exact grants apply. Inheritance flows down only: a deny
  on doc-42 does not affect a question about finance.
- B3 Windows are half-open [from, to); either bound may be absent (open-ended); a grant with no window is always
  in force. Datetimes must be timezone-aware (naive → error, in model and in question); comparison is by
  instant. from >= to is a model error.
- B4 "now" is supplied on every question (required; the library never reads the clock). The CLI, as the
  imperative shell, may default it to the wall clock and accept an explicit override.
- B5 Windows apply to allow and deny alike. Roles and user→role assignments are not time-bounded.
- Actions have no hierarchy (A4 unchanged). The answer stays allow/deny only (A5). Set semantics (A6) apply to
  grants as whole values (effect, action, resource, window).

Adversarial cases the design must visibly handle (each is an exit criterion):
- deny: role X allows + role Y denies same (A,R) → DENY; same role allows+denies → DENY; deny (write,R) leaves
  (read,R) allowed; deny on R1 leaves R2; user holding only deny grants → DENY.
- hierarchy: allow on org-root → allow on doc-42 (depth ≥ 2); allow finance + deny doc-42 → doc-42 DENY, sibling
  doc-43 ALLOW; deny org-root + allow doc-42 → DENY (the "most specific wins" shortcut would say ALLOW — it is
  wrong here); deny doc-42 does not affect (A, finance); unlisted resource gets exact grants only; group
  askable directly; cycle / self-parent / two parents rejected.
- time: window [t0,t1): now=t0 in force, now=t1 not, now<t0 not; open bounds; from >= to rejected; naive
  datetimes rejected in model and question; same instant in different UTC offsets behaves identically; an
  expired deny no longer blocks an allow; a not-yet-valid allow does not allow.
- interactions: a time-bounded deny on a group vs a permanent allow on a leaf (both sides of the window); the
  same (effect,A,R) with two windows applies in each; exact duplicates idempotent.
- stage-1 preservation: every stage-1 case in DESIGN.md §3.4/§8 answers identically for a model with no deny, no
  hierarchy, no window, at any now.
- model (grants + hierarchy) immutable; replacement whole-swap; no torn read between hierarchy and grants.

WHY NOW
A newly received product change. The stage-1 design deliberately named `decide` and the role clause as the owner
a deny/hierarchy stage would reopen; this round decides how that reopen lands.

WHAT "GOOD" AIMS AT
The standard is /home/user/aims-rerun/entitlements/.claude/skills/aims-guide/references/design-principles.md —
the target, not a checklist. Pay particular attention to: §5 one owner per rule (and "a rule that gains a case
keeps its single owner"); §4 concept fit (an explicit deny is NOT a missing allow); §1 trace the full input space
(each new axis crossed with each existing rule); §7 YAGNI/subtractive. Because this evolves an existing design,
also honor .../references/add-feature-principles.md where it applies (build on recorded decisions, supersede
rather than silently contradict; preserve out-of-scope behavior exactly; absorb, don't accrete).

TESTING
State the test plan (test-first; every decision, including ones already believed correct, has a test;
behavior through public seams; no coverage targets).

RELEVANT CONTEXT / PRESERVE / NON-GOALS
- Substrate: Python 3.11+, stdlib only, single process, no persistence.
- Preserve: A1–A9; strings at the seam for identifiers; immutable model built by one constructor; edges (JSON,
  CLI) call the core; core imports no I/O; public surface minimal.
- Non-goals: wildcards, action hierarchy, role inheritance, time-bounded assignments, ABAC/conditions,
  explanations, admin API, caching/performance, anything not revealed.
- The modules, classes and interfaces are YOURS to choose. You may keep, reshape or supersede stage-1 choices —
  say which and why.

RETURN TO GUIDE
- Write your full design document to: /home/user/aims-rerun/entitlements/.aims/panel/2026-09-23-stage2/worker-<AXIS>.md
  (AXIS given below). Do not edit any other file.
- It must contain: module skeleton; public API signatures; the internal model; where each rule lives (a table);
  JSON file format changes; CLI changes; the adversarial cases traced through the design; test plan; assumptions
  you added; what you deliberately did not build; a short account of key decisions and the alternatives rejected.
- Before returning, run the subtractive pass on your own design: for every type/guard/abstraction you added,
  name the present force that requires it; remove what has none.
- Final reply: 5–10 lines summarizing the design and result (met | partially_met | invalidated | blocked), plus
  any new facts or risks.
