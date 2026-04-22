---
name: debug-methodology
description: |
  The reproduce → isolate → fix → verify → test-gap protocol for bug work.
  Loaded by: the `debugger` worker agent (in `/agents-experts` pipeline) and
  any single-worker dispatch in `/experts` (lean) when the Router classifies
  the request as bug work. Produces a causal root_cause, a minimum fix, a
  concrete verification command, and a list of test_gaps for the downstream
  tester to close.
---

# Debug methodology

A bug that reached production is, by definition, a test gap. This protocol
exists to turn that failure into three durable artifacts: a **causal** root
cause, a **minimal** fix, and a **complete** list of gaps that would have
caught it.

Skip any of the five phases and the resulting envelope will fail quality
review — reviewers look for all five.

## Preconditions

- `skills/project-context` already loaded (via its Read procedure). Locate
  the module named in the bug description / codebase hint using the cached
  layout before any filesystem scan. If the cache is missing, emit
  `advisory: "project-context-missing"` in the envelope and let the
  Executor bootstrap.
- `retry_hint` (if present) describes a prior failure — address it directly;
  do not repeat the same approach.

## 1. Reproduce
- Produce a **minimal, deterministic** reproduction. Smallest input, fewest steps, clearest failure.
- If the bug is non-deterministic, say so in `root_cause` and capture the pattern (race, timing, environment).
- If you cannot reproduce after reasonable effort, return a `retry` envelope asking for more information — do not guess.

## 2. Isolate
- Narrow the cause to the smallest region of code that, when changed, makes the bug go away.
- Use Grep/Glob to trace call sites. Use Bash to run targeted tests. Use Read to inspect code paths.
- Form a concrete hypothesis **before** editing.

## 3. Fix
- Edit the **minimum** number of files. No drive-by refactors. No "while I'm here" cleanup.
- Do not introduce dependencies, feature flags, or abstractions the bug fix doesn't require.
- If the fix requires > ~30 lines, consider whether this is really scope-complex and should have gone through Planner — if so, `abort` with reason.
- Do not add error handling for cases that cannot occur. Do not suppress errors to make tests pass.

## 4. Verify
- Run the reproduction against the fixed code. It must now succeed (or fail in the expected non-bug way).
- Run adjacent tests that could plausibly regress.
- Capture the **exact command(s)** for the `verification` field. Not "run the tests"; the exact invocation (`pytest tests/test_auth.py::test_offline_config -v`).

## 5. Test-gap analysis
Answer: **"what test, if it had existed, would have caught this?"**

For each gap, emit one `TestTarget` (shape in `agents/_schema.md` §9) with
`origin: "bug-driven"`:

```json
{
  "test_type": "unit|integration|e2e|property|regression",
  "target":    "<module / function / endpoint / UI flow>",
  "scenario":  "<specific input / state / timing the bug exploited>",
  "origin":    "bug-driven",
  "priority":  "critical|high|medium|low",
  "rationale": "<one-line justification>"
}
```

Honesty rules:
- If an **existing** test failed to catch the bug, describe *why* (wrong assertion, wrong input, mocked away the very thing that broke). That counts as a gap.
- If the bug is of a kind where **no test would have caught it** (e.g., typo in a user-facing string), return `test_gaps: []` and explain in `root_cause`. Do not invent gaps to look thorough.
- Do not write the tests yourself. This protocol identifies gaps; the `tester` agent (downstream in the pipeline, or a second phase in lean mode) fills them.

## Content rules

- **Root cause must be causal, not symptomatic.** "The function threw NullPointerException" is not a root cause. "`f()` assumes `config.port` is set, but the production config omits it when `mode=offline`" is a root cause.
- **Report your reproduction**, even if the fix is one line. The reviewer needs to know the failure was real.
- **Do not silently expand scope.** If you find a second bug while fixing the first, mention it in `root_cause` as a known adjacency — don't fix it in this pass.

## Pre-submit checklist

Before emitting your envelope, apply `skills/quality-analysis`'s rubric.
Specifically:

- Reproduction was established (not skipped).
- `root_cause` is causal.
- `fix.files` lists every file changed, no extras.
- `verification` is a concrete command.
- `test_gaps` present — concrete list OR empty with justification in `root_cause`.
- You did NOT write tests yourself.
- You stayed within `effects: [read-fs, write-fs]`. No web calls, no external APIs, no git push.
- You did not modify unrelated code.

## When to `retry` or `abort`

- `retry` — you could not establish reproduction from the input; ask for more.
- `abort` — the bug crosses concerns, requires infra changes, or cannot be fixed in isolation. Emit a precise reason.
