# Framework Evaluation Plan — next feature pilot

When you next ask the framework to build a feature, run this checklist
alongside the task. The point is to measure the framework's behaviour
itself, not just whether the feature works. Every pilot so far exposed a
specific weakness; the hypotheses below were designed against each one.
Confirm or refute.

## Which mode to test?

The framework now has two invocation modes:

- **`/experts`** (lean, default) — single dispatch with skills preloaded. Strong baselines.
- **`/agents-experts`** (pipeline) — decomposed Router → Planner → workers → Validator. Weak baselines.

**Every pilot report must state which command ran.** Pilots on the same
task across both modes are valuable for comparison but are not required
— if you only run one mode, say so and note which.

## Before you start

### 1. Choose the feature
Pick a bounded deliverable a capable model can plausibly produce end-to-end.
Rule of thumb from the TODO pilot: if the user's request fits in one English
sentence without "and also" / "with tests" / "plus", it is likely `holistic`.

### 2. Write three things down, separately, before dispatch
- **Spec.** The user-visible contract in prose.
- **Expected scope classification.** What *should* the Router choose? (`trivial` / `simple` / `holistic` / `complex`.)
- **Invariants.** The list of properties the deliverable must preserve (e.g. "ids never reused after full drain"). This is the strategist's job, but you write it first so you can grade the strategist.

Store these in `tests/pilot_<name>/pre_run.md`. Do NOT show them to any agent.

### 3. Identify the baseline
- If `holistic`: baseline = single Opus dispatch with the spec.
- If `complex`: baseline = single Opus dispatch with the spec (still worth running, for the cost floor).
- If `simple` / `trivial`: baseline = single Sonnet dispatch; the pipeline should not be meaningfully better.

## During the run

### 4. Capture per-stage telemetry
For both sides (baseline and pipeline), record:
- tokens in / out per dispatch
- tool_uses per dispatch
- wall-clock duration per dispatch
- envelope shape conformance per worker (did the worker emit the canonical `{ok, outputs}`?)
- for the pipeline: which workers ran, in what order, with what bindings
- for the pipeline: verdict scores, suggested_actions, retries_per_step

These go into `tests/pilot_<name>/trace.jsonl`. The harness tracer already
emits this for the Python side; for live Agent-tool dispatches, paste the
per-dispatch usage block into the trace.

### 5. Do not intervene
Let each side finish on its own. The goal is to measure what the framework
produces unguided. Mid-run "corrections" invalidate the comparison.

## After the run

### 6. Run the invariant check
The invariants you wrote in step 2 become the grading sheet. For each one:
- Did the baseline satisfy it? How do you know (what test, what command)?
- Did the pipeline satisfy it? Same question.
- Was there a test in either artifact that would catch a future regression of this invariant? (Not just "the feature works today" — does the test suite *know* about this invariant?)

The TODO pilot failed on exactly this axis: the strategist didn't enumerate
the drain-then-add invariant, so the tester didn't test it, so the bug
shipped. The invariant check catches cases the strategist missed.

### 7. Hypotheses to grade (one paragraph each in the report)

**H1: Router scope classification.** Did the Router pick the expected
scope? If not, was its rationale defensible or was it drift?
- *If it drifted*: is the rule in `agents/_router.md` §4 ambiguous for this
  case? Can you add one disambiguating sentence that would have fixed it?

**H2: Router tool discipline.** How many tool calls did the Router make
in its pre-exec dispatch? Target: zero. Anything non-zero means the
prompt hardening is leaking again (see cookiecutter vs TODO pilots —
it fixed, then regressed).

**H3: Envelope shape compliance.** How many worker dispatches returned a
non-canonical envelope shape? Target: zero. On the TODO pilot, 2 of 3
Sonnet workers drifted. If it persists, we need one-shot examples in
every worker body (this is in the recommendation list but not done yet).

**H4: Validator correctness.** If the pipeline ran: did the Validator
catch every invariant failure, or only some? A Validator that passes a
broken artifact is worse than no Validator — it launders errors.

**H5: Holistic vs Complex routing.** If the task was `holistic`, did the
baseline win or did the pipeline win? The hypothesis from the TODO pilot
is that `holistic` → baseline wins. Challenge it: maybe some holistic
tasks *do* benefit from the pipeline. If pipeline wins here, what made
this task different?

**H6: Cost ratio is rising or falling.** Track pipeline tokens / baseline
tokens across pilots:
- LCS (pipeline, trivial):       5.3× (tokens)
- cookiecutter (pipeline, medium): 4.1× (tokens) / 0.93× ($)
- TODO (pipeline, feature): 6.8× (tokens)
- contacts (pipeline, holistic → baseline): 2.23× (tokens)
- **cookiecutter (lean, medium): 1.13× (tokens) / 0.15× ($)** — dual-mode committed
Target: **lean-mode ratio** should hold ≤ 1.5× in $ across tasks. Pipeline-mode
ratio should drop only when the Router makes a better scope choice, not when
we hack the pipeline itself.

### 8. Update the evidence, not the docs
When a hypothesis resolves, add one row to the scorecard — do not rewrite
the thesis. The framework has survived precisely because each pilot
produced a committed, auditable result that future pilots have to grapple
with. Don't erase history.

## Recommended changes if you need to act

From pilot data, these are the known deferred fixes. Do any of them land
if the next pilot confirms a hypothesis:

| Hypothesis failed | Action |
|-------------------|--------|
| H1 — Router picked wrong scope | Add a disambiguating rule to `agents/_router.md` §4 with the specific example |
| H2 — Router drifted | Tighten the prompt: add explicit "do not analyse the request" and/or reduce `tools:` to `[]` if no reads are actually needed |
| H3 — Envelope drift | Add a one-shot envelope example to the failing worker's body (~3 lines per worker) |
| H4 — Validator laundered a bug | Tighten `_router.md` decision table: `passed: true + suggested_action != "accept"` → `retry`, not `accept` |
| H5 — Holistic lost to pipeline | Revise the `holistic` classification rule with the specific reason the task was coordination-heavy after all |
| H6 — Cost ratio up | The framework grew overhead somewhere; bisect dispatches against the previous pilot's numbers |
| H7 — Convention drift | Strengthen `skills/project-context` to capture conventions (style, error patterns, test layout), not just module layout |
| H8 — Discovery scales super-linearly | The cache is under-producing — add per-module summaries or a second layer |
| H9 — Cache does not earn its keep | Either fix the cache format (workers aren't consulting it) or retire it |
| H10 — New tests diverge from existing style | Bind `codebase_hint: "tests/"` to the tester step in `_planner.md` |
| H11 — No merge-conflict detection | New Executor preflight that reads `git status` + diffs against tracked branches, emits `advisory: "in-flight-conflict"` |
| H12 — Slow convergence on known-root-cause bug | Add a `hypothesis:` input to the debugger so a familiar user can short-circuit the reproduce phase |
| H13 — No CoWork-session awareness | Executor preflight: `git fetch --all` + detect divergent branches touching target files, emit `advisory: "cowork-in-flight"` |
| H14 — Shared-cache race undetected | Project-context skill: re-hash `CLAUDE.md` / `.claude.md` before each worker; emit `project-context-stale` on change |

## Reporting template

```
# Pilot <name> — <one-line>

## Pre-run notes
- Spec:       ...
- Expected:   scope = ...
- Invariants: [...]

## Headline result
| Dimension       | Baseline | Pipeline |
| Scope           | n/a      | ...      |
| Correct on invariants | ... | ... |
| Tokens          | ...      | ...      |
| Duration        | ...      | ...      |

## Hypotheses
- H1: ...
- H2: ...
- H3: ...
- H4: ...
- H5: ...
- H6: ...

## Evidence committed
- tests/pilot_<name>/pre_run.md
- tests/pilot_<name>/baseline/...
- tests/pilot_<name>/pipeline/...
- tests/pilot_<name>/trace.jsonl
```

## Automation hook (optional, for later)

The harness already has `harness.tracer` emitting per-step JSONL. A future
enhancement: a `harness/eval_pilot.py` script that reads a `pre_run.md`,
runs both sides, computes the hypothesis grades mechanically, and emits
the report template pre-filled. Not required for the next pilot — do it
manually first, automate when the manual workflow stabilises.

## Scenario B — bug fix / feature in `the target framework` via Claude Code **CoWork** sessions

**Status**: pending. Trigger = the next time the user (Eliezer) hits a
bug in `the target framework` or decides to add a feature there. The user
will update this section with the actual task at trigger time.

All three prior pilots were sterile: standalone repos, no history, no
parallel work in flight, solo user. The one context the framework has
**not** been tested in is the one it will actually live in. The user is
developing `the target framework` inside a Claude Code **CoWork** session —
Claude Code's multi-session workspace feature — while this routing
framework lives in a separate session. The pilot runs against
`the target framework` as the target codebase, with another Claude Code
session in the same CoWork potentially touching the same tree in
parallel. Coordination between sessions is exclusively through the git
tree; neither session sees the other's context. Shared state consists of
the committed code, `CLAUDE.md`, and `.claude.md`.

This is not a human-coworker scenario. The "coworker" — if any is active
during the pilot — is a second Claude Code instance inside the same
CoWork. Both sessions read the same `CLAUDE.md` and `.claude.md`. Both
produce markdown + code. Neither has visibility into the other's
session context — only whatever lands on disk or in a commit.

### What's different from scenarios A (the sterile pilots)

| Axis | Sterile pilot | CoWork pilot (`the target framework`) |
|------|---------------|-----------------------------------|
| User's prior familiarity with the codebase | zero — you read the spec | high — you have context the pipeline doesn't |
| Repository size | hundreds of LOC | thousands to hundreds of thousands |
| Conventions | none enforced | strong, enforced by `the target framework`'s own `CLAUDE.md` |
| In-flight work | none | possibly a second CoWork session on a separate branch |
| Shared state | none | `CLAUDE.md`, `.claude.md`, and the git tree |
| Coordination surface | none | git only (branches, commits, possibly the same file) |
| Test infrastructure | tiny | established fixtures, helpers, CI hooks |
| Stakes | a pilot | real merge-conflict risk if a parallel CoWork session is active |

### Pre-run notes (in addition to §2 above)

Before dispatching anything:

1. **Task statement.** One sentence from the user: bug to fix or feature to add. Written at trigger time, not in advance.
2. **Git snapshot.** From inside `the target framework`'s checkout: `git rev-parse HEAD`, `git log --oneline -20`, `git branch -a`. Store in `pre_run.md`. Any fix the pipeline proposes will be diffed against this snapshot.
3. **CoWork session map.** List any other active CoWork session working on `the target framework` — its branch name, its recent commits, the files it has touched (`git log --name-only <their-branch>..HEAD`). If none, record "none active". This is the surface where merge conflict can actually happen.
4. **Shared-context snapshot.** Capture the current state of `the target framework`'s `CLAUDE.md` and `.claude.md` at dispatch time. If either changes mid-run (because a parallel session updated it), that's a race worth recording.
5. **Convention inventory (one page).** The unwritten rules you already know that the pipeline should pick up from `the target framework`'s `CLAUDE.md` / `.claude.md`: naming, module layout, test-file patterns, logging style, error-raising style, commit-message convention. Write them down so you can grade whether the framework followed them.
6. **Your own mental fix sketch.** One paragraph: what you would do if you fixed this yourself. The framework's output gets graded against this, not just against "did tests pass".

### Additional hypotheses (continuing from H1–H6 above)

**H7: Convention conformance.** Did the fix match `the target framework`'s
style — naming, error patterns, import order, test-file naming? Grade
by diffing the fix's stylistic choices against 3 neighboring files
(pick randomly before dispatch; no cherry-picking afterward).
- *Fails if*: the fix introduces a new pattern when an existing one would have worked.
- *Implied action*: strengthen `skills/project-context` to capture
  conventions (not just module layout).
- **CoWork nuance**: both sessions read the same `CLAUDE.md`. If they
  diverge on style, the convention was under-specified in the shared
  instructions — that's where to fix it, not in either session's prompt.

**H8: Scaling cost vs. codebase size.** Tokens spent on discovery
(reads, greps, globs) vs. LOC of the repository. Compare against the
TODO pilot ratio (tiny repo) and the cookiecutter pilot ratio (medium).
- *Fails if*: discovery tokens scale super-linearly with LOC — indicates
  the `.claude.md` cache is not shielding the workers.
- *Implied action*: the Bootstrap procedure in `skills/project-context`
  is under-producing; either add a per-module summary or add a second
  cache layer.

**H9: `.claude.md` earn-its-keep test.** Run the fix twice: once with
`.claude.md` present, once without. Measure Grep/Glob/Read tool calls
across workers.
- *Fails if*: the difference is < 30%. The cache exists to reduce
  discovery; if it doesn't, it's dead weight.
- *Implied action*: either fix the cache format (maybe it lacks the fields
  workers actually consult), or retire it.

**H10: Test-pattern recognition.** Compare 1 new test the tester wrote
to 3 existing tests in the same module.
- *Fails if*: the new test uses different fixtures, different assertion
  style, different import shape than existing tests in that module.
- *Implied action*: feed the test_strategist the existing test layout,
  not just the production code layout. Update `_planner.md` to bind a
  `codebase_hint: "tests/"` explicitly in the tester step.

**H11: Merge-conflict inference.** Does the framework detect that one of
the files it wants to touch is being edited on a coworker's open PR?
(If it doesn't touch git at all to check, that's the answer.)
- *Fails if*: the framework proposed edits to a file with an in-flight
  change and had no awareness.
- *Implied action*: add a preflight step in the Executor that consults
  `git status --porcelain` and `git diff main...HEAD` across tracked
  branches, surfaces the overlap to Router/Planner as
  `advisory: "in-flight-conflict"`. This is a new capability, not a tweak.

**H12: Prior-knowledge disadvantage.** You already know the bug's root
cause; the framework doesn't. Measure: how long until the pipeline
converges on the same hypothesis you'd have formed? (Tokens + wall-clock
to the first correct root-cause statement in the debugger envelope.)
- *Fails if*: the pipeline burns more than 2× the time it would take you
  to just explain the cause and ask for a fix.
- *Implied action*: for a familiar-codebase user, add a `hypothesis:`
  input on the debugger so the user can short-circuit the reproduce phase.

**H13: CoWork-session awareness.** If a second CoWork session is active
on `the target framework` at dispatch time, does the pipeline notice?
Today, nothing in the Executor reads git state to detect this; the
preflight only touches `.claude.md`. So the expected answer is "no".
- *Fails if*: the pipeline edits a file the other CoWork session is
  also editing, with no advisory. (This is the interesting failure.)
- *Implied action*: add an Executor preflight step that runs
  `git fetch --all` and checks for divergent branches touching the
  pipeline's target files, surfaces as `advisory: "cowork-in-flight"`.

**H14: Shared-cache race.** Does either `CLAUDE.md` or `.claude.md`
change during the run? (Would indicate a concurrent session wrote to
the shared state mid-pipeline.)
- *Measurement*: hash the two files at dispatch start and at each
  Validator gate; record divergences.
- *Fails if*: the pipeline kept reading a stale cache after the other
  session updated it, leading to decisions based on outdated structure.
- *Implied action*: the project-context skill should re-hash the cache
  before each worker dispatch and emit `advisory: "project-context-
  stale"` if it changed since preflight.

### Report template additions (scenario B only)

```
## Convention conformance (H7)
  3 neighbouring files sampled: [a.py, b.py, c.py]
  Divergences: [list any]
  Verdict: conformed / diverged on {...}

## Scaling (H8)
  Repo LOC: ...
  Discovery tokens: ...
  Tokens / kLOC: ...                   ← compare to prior pilots

## Cache (H9)
  With cache:    Grep=<>, Glob=<>, Read=<>
  Without cache: Grep=<>, Glob=<>, Read=<>
  Delta: <%>

## Test-pattern recognition (H10)
  Sample new test: tests/...
  Sample neighbours: [3 paths]
  Divergences: [list]

## Merge-conflict inference (H11)
  Files the pipeline proposes to edit: [...]
  Files the other CoWork session has touched on its branch: [...]
  Overlap: [...]
  Framework advisory emitted?  yes / no

## Prior-knowledge disadvantage (H12)
  Your ex-ante hypothesis: "<one line>"
  Debugger's root_cause:    "<one line>"
  Match?                    yes / partially / no
  Time to converge:          <tokens, seconds>

## CoWork-session awareness (H13)
  Parallel session active at dispatch?  yes / no / unknown
  Its branch:                           <name or "—">
  Files it edited in flight:            [...]
  Pipeline advisory emitted for overlap? yes / no

## Shared-cache race (H14)
  CLAUDE.md hash at dispatch / at completion: <h1> / <h2>
  .claude.md hash at dispatch / at completion: <h1> / <h2>
  Race observed?                yes / no
  Pipeline decisions affected?  yes / no
```

### The interesting negative result to watch for

A framework that works great on pilots and poorly here is a framework
that **only works in isolation**. That's the most likely failure mode and
the one that would make this pilot the most useful. If the numbers here
are worse than in the sterile pilots, it tells us the framework needs to
become codebase-aware (cache, convention-detection, git-integration)
before it can graduate from "benchmark winner" to "production tool".

## The one meta-rule

**Prefer contradicting evidence over confirming evidence.** If a pilot
matches what we already believe, it tells us nothing new. If it refutes
a belief, that is the only way this framework gets better. Pick tasks
that challenge current assumptions, not tasks that re-validate them.
