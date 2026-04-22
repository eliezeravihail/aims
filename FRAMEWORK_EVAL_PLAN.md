# Framework Evaluation Plan — next feature pilot

When you next ask the framework to build a feature, run this checklist
alongside the task. The point is to measure the framework's behaviour
itself, not just whether the feature works. Every pilot so far exposed a
specific weakness; the hypotheses below were designed against each one.
Confirm or refute.

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
- LCS (trivial):       5.3×
- cookiecutter (complex): 4.1×
- TODO (holistic, feature): 6.8×
Target: the ratio should drop over time as the framework matures. If it
rises, something regressed.

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

## The one meta-rule

**Prefer contradicting evidence over confirming evidence.** If a pilot
matches what we already believe, it tells us nothing new. If it refutes
a belief, that is the only way this framework gets better. Pick tasks
that challenge current assumptions, not tasks that re-validate them.
