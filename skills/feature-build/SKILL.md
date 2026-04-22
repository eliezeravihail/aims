---
name: feature-build
description: |
  The design → implement → verify protocol for building a feature from a
  prose description. Optionally consumes a `test_plan` from test-strategy
  so the code satisfies every target scenario. Loaded by: the
  `implementer` worker in `/agents-experts`, and the single worker in
  `/experts` when the request is a feature build.
---

# Feature build

Turn a feature description into production code — not a prototype, not
stubs, not examples. If the request cannot be delivered in a single dispatch
without decomposition, return `abort` and let the Router route elsewhere.

## Preconditions

- `skills/project-context` loaded. Respect the project's existing layout and conventions. Do not invent a new convention when one exists.
- `feature_description` is the spec. If a `test_plan` (from `skills/test-strategy` in design mode) is also present, treat every `scenario` in it as a contract the code must satisfy.
- `constraints` (if present) — file formats, external interfaces, stdlib / language limits. Honour literally.
- `retry_hint` (if present) — a prior attempt failed review; address it directly.

## 1. Design

- State the data model, control flow, and file layout **before** writing code.
- Record it in `design_summary` — one paragraph, ≤ 6 sentences.
- If `test_plan` is present, verify the design can satisfy every `scenario` in it.
- If the spec is under-specified, pick the simplest reasonable interpretation and record it explicitly in `design_summary`. Do not silently expand scope.

## 2. Implement

- Start with the smallest runnable surface (a single CLI entrypoint with one command; a single function that works for the happy path) and grow.
- Prefer the **standard library**. Use third-party deps only when the feature genuinely requires it and the `constraints` allow it.
- Use clear, descriptive identifiers; no comments that repeat the code. Write a comment only when a non-obvious invariant or constraint needs stating.
- **No placeholder stubs, no `TODO`, no `...` in production code.**
- **No half-implementations.** If a declared feature cannot be completed, return a `retry` envelope with a specific reason instead of shipping a stub.

## 3. Verify end-to-end

- Run the feature yourself. A CLI should start, accept input, produce output, persist state, and read it back.
- `verification` must be a concrete command a reviewer can paste — not a description.
- Do **not** author tests yourself — `skills/test-authoring` (or its agent) handles that downstream.

## Content rules

- **Stay in scope.** Build exactly the feature described. Do not add unrequested features (notifications, colour output, configs) even if they seem helpful.
- **Respect `constraints` literally.** "Text files" means text files, not SQLite — even if SQLite is "better".
- **No dependencies without explicit permission.** `requirements.txt` and equivalents count as shipping a dependency.
- **Deterministic CLI behaviour**: clear exit codes, stderr/stdout separation, argument parsing robustness.

## Pre-submit checklist

Apply `skills/quality-analysis`'s rubric. Specifically:

- `design_summary` describes an implementation that can actually satisfy every `test_plan` entry (if a plan was provided).
- Every declared feature in `feature_description` is implemented (not stubbed).
- `created_files` lists every file you wrote, with no extras.
- `verification` is a single concrete command (or short shell pipeline) that exercises the happy path end-to-end.
- You stayed within `effects: [read-fs, write-fs]`. No network, no external API calls.
- No placeholder code, no commented-out blocks, no unmarked `TODO` / `FIXME`.
- You did NOT author test files.

## When to `retry` or `abort`

- `retry` — inputs are insufficient or contradictory. Ask for what's missing.
- `abort` — the feature as described cannot be delivered in a single dispatch. Emit a precise reason so the Router can re-route to a decomposed pipeline.
