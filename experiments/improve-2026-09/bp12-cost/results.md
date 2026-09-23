---
title: "BP12 result — a second cost datapoint: aims ≈2.3× tokens / ≈12× wall on a single-shot task; correctness tie"
date: 2026-09-20
---

# BP12 — full-aims vs plain, measured cost on one design+build task

Same card (the booking calendar), two arms, scored against the validated calendar hidden suite (11 tests).
Cost read straight from each arm's subagent handback.

| arm | tokens | wall-clock | tool calls | correctness | footprint |
|---|---|---|---|---|---|
| **plain** | **42,109** | **~21 s** | 3 | **11/11** | calendar.py only |
| **aims** | **98,680** | **~254 s** | 23 | **11/11** | calendar.py (96 lines) + 141 lines of records (goals/arch/base-deps/ADR/companion) + own tests |
| **ratio** | **2.34×** | **≈12.1×** | 7.7× | tie | records are the extra artifact |

# Reading

- **Correctness: a tie (11/11 each).** The fifth correctness tie of the campaign — both arms handled the
  half-open boundary; the premium bought no correctness here (there was none to buy).
- **Token premium ≈2.34×.** Beside BP1's **1.85×** (a 3-stage build), the two clean datapoints bracket
  **≈1.85–2.34×** — real, and a little **below** the paper's quoted 2.5–3×. The premium buys the design
  ceremony (sharpen → design → review) and the durable co-located records (here 141 lines of goals/arch/ADR/
  companion the plain arm doesn't produce).
- **Wall premium is the striking one, and it is task-size-dependent.** ~12× here vs ~3.7× in BP1. The reason
  is mechanical: aims' ceremony is a **largely fixed overhead** (sharpen, records, review, its own tests) that
  a plain arm skips. On a **small** task the plain arm finishes in one shot (~21 s, 3 tool calls) so the fixed
  ceremony dominates the ratio; on a **larger/multi-stage** task the implementation work amortizes the
  ceremony and the wall ratio falls (BP1's 3.7×). So the wall-clock premium is **worst on small tasks** and
  shrinks as the task grows — a useful, non-obvious characterization.

# What it adds to the campaign

- The cost premium is now **two datapoints, not one**: **≈1.85–2.34× tokens**, wall **3.7–12×** (task-size
  dependent, worst when small). This is the price of the trajectory edge and the records — paid **every** build,
  including the ~5/6 where (per BP6/BP7) a plain builder would have chosen the extensible design anyway and the
  trajectory edge is therefore zero.
- Put with the trajectory findings, the honest cost/benefit sharpens: aims charges ~2× tokens on **every**
  build to buy an avoided reopen on the **minority** where the shortcut would be taken (plus durable records).
  Whether that trades well depends on the shortcut base rate for the executor and how much the records are
  worth downstream — exactly the mixed-tier calculus the method already frames. n=2 on cost (BP1 + BP12);
  reported as a range, not a mean.
