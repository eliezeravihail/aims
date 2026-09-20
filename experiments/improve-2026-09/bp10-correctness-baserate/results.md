---
title: "BP10 result — no correctness deficit to fix on clear specs: 0/12 bugs across two error-prone corners (even on haiku)"
date: 2026-09-20
---

# BP10 — does the shortcut ever cause a WRONG answer (aims' headline claim)?

Every prior build pilot found correctness **ties** — aims' measured edge was always *trajectory*, never
*correct-vs-wrong*. aims' headline claim, though, is **correctness in the result** (the plant→mineral loss).
BP10 went looking for a **correctness** difference: pick corners a real fraction of quick builds should get
**wrong**, measure the plain (haiku) bug rate, and — if bugs appear — test whether aims' §1 full-input-space
trace / review catches them. Two determinate, classically error-prone corners:

| sub-probe | the corner | naive-wrong version | plain haiku result |
|---|---|---|---|
| **A — interval boundary** | half-open `[start,end)`; touching bookings don't overlap | closed-interval overlap (`<=`) wrongly rejects the adjacent booking | **6/6 correct** (11/11 each; touch-point 4/4 each) |
| **B — remainder allocation** | `split(n,k)` parts must sum **exactly** to `n` | `[n//k]*k` drops the remainder → sum < n | **6/6 correct** (8/8 each; every build distributed the remainder) |

**Bug rate: 0/12.** Not one plain haiku build shipped the corner bug on either probe. All six interval builds
used the strict half-open predicate (`start < e and s < end`); all six allocation builds distributed the
remainder (`[q+1]*r + [q]*(k-r)` and equivalents), summing exactly.

# Part B is moot — and that is the finding

There was **no bug to catch**, so the "does aims' review catch it?" arm does not run — recording it would be
fabricating a failure that did not occur. The honest result is the **null itself**: on a **clearly-specified**
corner, a capable model — *even the cheap one* — does not lose correctness. This is the third independent
confirmation (with I1's plant→mineral null and I4's half-open-touch null on opus) of a single, robust boundary:

**aims has no correctness deficit to repair on clean small specs, because the base is already right.** The
method's correctness claim is real only where a builder actually *slips* — and a slip is not what a clear spec
on a tractable module induces, at either model tier tested. The plant→mineral loss that motivated the whole
correctness thread was a **slip under specific conditions** (plausibly larger/noisier context, ambiguity, or
distraction across many concerns), not a systematic failure a small blind A/B can reproduce.

# What this pins down for the campaign

Put beside the trajectory results, BP10 sharpens the honest shape of aims' value to a single sentence:

> On tractable, clearly-specified work, aims' benefit is **structural/trajectory** (variance reduction on the
> early design choice — avoided reopens), **not correctness**; correctness ties because a capable model is
> already correct, and aims cannot win a correctness contest that has no loser.

Where aims' correctness claim could still be real — and what BP10 **cannot** reach — is exactly where I1/I4/BP10
cannot go: **under-specified or high-context conditions where a builder slips**, which require a bigger, noisier
task than a single blind small-module corner. That, with the record-layer-at-opacity question, is the campaign's
standing frontier. n=12 builds, two corners, haiku; nulls recorded as nulls, Part B honestly not run.
