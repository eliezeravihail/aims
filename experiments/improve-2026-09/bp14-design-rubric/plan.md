---
title: "BP14 — the CORRECT measure: score DESIGN against an explicit metric list, not tests"
date: 2026-09-21
status: the measurement-method correction
---

# The correction (per direct instruction)

Good design is NOT measured by tests — tests only check behavior, and behavior is achievable by any design, so
tests can be circumvented (BP13 part-1 proved even a "does it extend?" behavioral probe is gameable). Design
quality is measured by **scoring the design directly against an explicit list of quality metrics** (a rubric),
read from the code. Tests, if used at all, are only a correctness GATE — never the measure of design.

# Method

- **The metric list (1-5 each):** OCP/extensibility · single-responsibility/one-owner · cohesion ·
  coupling/information-hiding · concept-fit/rich-domain · absence-of-type-switch · DRY/single-source-of-truth ·
  appropriate-abstraction · readability. (These are standard SE design metrics; they are also what aims' review
  lens §0-§14 encodes — so the correct evaluation of aims IS a design rubric, not a test.)
- **Demonstration:** a blind judge scores TWO designs that pass the IDENTICAL test suite — one polymorphic
  (design A), one type-switch (design B) — against the list, from the code alone. If the rubric SEPARATES them
  though tests are identical, that proves the rubric (not tests) is the design-quality instrument.
- Mapping sealed in MAPPING-SECRET.txt (A=polymorphic, B=type-switch); judge is blind to it and to methodology.

# Why this matters for the whole campaign

Every "correctness tie" was a test-pass (floor) measurement — not a design measurement. The design comparison
must be re-read on this rubric. This round establishes the instrument; the arms should be re-scored on it.
