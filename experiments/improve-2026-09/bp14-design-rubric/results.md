---
title: "BP14 result — the rubric IS the instrument: same tests, design scores 43 vs 16"
date: 2026-09-21
---

# BP14 — design quality measured against the metric list (no tests as a measure)

A blind judge scored two designs of the same promo engine — both passing the IDENTICAL hidden suite (22/22) —
against a 9-metric design-quality rubric, from the code alone. Mapping (sealed, then unsealed):
**A = polymorphic, B = type-switch.**

| metric | A (polymorphic) | B (type-switch) |
|---|---|---|
| Open/Closed (OCP) | 5 | 1 |
| single responsibility / one owner | 5 | 2 |
| cohesion | 5 | 2 |
| coupling / information hiding | 4 | 2 |
| concept-fit / rich domain | 5 | 1 |
| absence of type-code switch | 5 | 1 |
| DRY / single source of truth | 5 | 2 |
| appropriate abstraction | 4 | 2 |
| readability | 5 | 3 |
| **TOTAL /45** | **43** | **16** |

# The point, proven

Both designs are **identical by tests** (22/22) and were even indistinguishable by a behavioral change-probe
on the wrong axis (BP13 part-1). The **rubric separates them 43 vs 16.** So:

- **Tests are a floor and can be circumvented** — they do not measure design and never separated these two.
- **Design quality is measured by scoring the design against an explicit metric list** — and that instrument
  cleanly and decisively separates good design from bad.
- This is also the correct way to measure aims itself: aims' review lens (§0-§14 / S1-S4) *is* such a rubric.
  The proper evaluation of aims is "does its output score higher on the design rubric, at correctness parity" —
  not "do the tests pass" (they always do).

# Consequence for the campaign

Every prior "correctness tie" measured the floor. The real aims-vs-plain comparison must be **re-scored on this
rubric**: score aims arms and plain arms' *designs* against the metric list, blind, at correctness-gate parity,
and compare the distributions. That is the outstanding correct measurement.
