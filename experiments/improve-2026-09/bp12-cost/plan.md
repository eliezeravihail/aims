---
title: "BP12 — a second clean cost datapoint: full-aims vs plain on one design+build task"
date: 2026-09-20
status: pre-registered before either arm ran
---

# Why

The campaign's only clean cost measurement is BP1 (~1.85× tokens, ~3.7× wall, on a 3-stage build). SYNTHESIS
lists cost (the paper's main downside, quoted 2.5–3×) as undermeasured. BP12 adds a **second datapoint** on a
different, single-shot product: run a **full-aims** arm (skill invoked, records filed, review run) and a
**plain** arm ("build it well") on the **same** card, and record each arm's **tokens** and **wall-clock** from
its subagent handback. Both are scored against the already-validated calendar hidden suite (11 tests) so the
cost is reported alongside correctness.

# Design

- Card: the BP10 booking-calendar card (half-open `[start,end)`, `book`/`is_free`) — validated hidden tests
  exist (`../bp10-correctness-baserate/hidden/test_calendar.py`, 11 tests).
- **arm-aims:** one opus agent using the real aims method (reads `skills/aims-guide/SKILL.md`, files
  co-located records, runs the review) → `arm-aims/calendar.py` (+ records).
- **arm-plain:** one opus agent, code only, "build it well" → `arm-plain/calendar.py`.
- Metrics: `subagent_tokens` and `duration_ms` from each handback (the cost); hidden-suite pass count (the
  correctness check that the premium bought — or didn't).

# Pre-registered expectation

Given every prior correctness result: **both arms pass 11/11** (correctness tie), and aims costs materially
more (BP1 ballpark ~1.5–2×+ tokens). The datapoint's value is the **ratio**, not a winner — a second point to
say whether BP1's 1.85× is representative or product-specific. n=1 per arm; reported as a single ratio with the
BP1 point, not a mean. Nulls/ties recorded as such.
