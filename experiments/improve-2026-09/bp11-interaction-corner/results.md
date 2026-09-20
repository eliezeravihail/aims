---
title: "BP11 result — even a designed INTERACTION corner does not induce a slip on a strong model: 0/6; correctness has no pilot-scale target"
date: 2026-09-20
---

# BP11 — the high-context test: does an interaction corner induce a correctness slip?

BP10 found no correctness bug on *single* clear corners and named the untested regime: a builder slipping under
**interaction load**. BP11 built exactly that — a layered access evaluator with **two stated principles that
conflict on a corner** (P1 most-specific-wins vs P2 deny-wins-at-tie), where the common simplification "deny
always wins" silently violates P1 on a **specific ALLOW under a broader DENY**. The card even gave the
*opposite* example (specific-DENY-beats-broad-ALLOW) to make "deny wins" look safe. Tested on **opus** (a strong
model) to ask whether interaction load slips even a capable builder.

## Result — 0/6; every build resolved the corner correctly

| plain opus build | full suite | interaction corner (`specific_allow_under_broad_deny`) |
|---|---|---|
| run-1 … run-6 | **10/10 each** | **passed, all 6** — all returned `ALLOW` |

All six independently implemented "most specific wins, DENY only as the equal-specificity tie-break" — none
collapsed it to "deny always wins." Their traces agree: for `[("a","DENY"),("a/b/c","ALLOW")]` on `a/b/c/d`,
the depth-3 ALLOW is strictly more specific than the depth-1 DENY, so `ALLOW`. **Bug rate 0/6.** With no bug,
Part B (does the aims review catch it?) correctly did not run.

## What this settles (the correctness thread, closed at pilot scale)

BP11 is the fourth independent null on aims' **correctness** claim, and the strongest, because it was
*engineered* to induce a slip and still didn't:

- I1 (plant→mineral input-space) — null;
- I4 (half-open touch-point, opus) — null;
- BP10 (two error-prone corners, haiku) — 0/12;
- **BP11 (a two-principle interaction designed to bait "deny wins", opus) — 0/6.**

The honest conclusion is now firm: **at the scale a blind small-module A/B can reach, there is no correctness
deficit for aims to repair — even a deliberately conflicting interaction is resolved correctly by a capable
model.** aims' demonstrable, measurable value is **trajectory/structural** (variance reduction on the early
design choice; §5/§8 caught by the review). Its **correctness** claim is not *disproven* — it plausibly lives in
the regime BP10/BP11 cannot build: a **genuinely large, noisy, multi-concern task** where attention is divided
and a human-or-model builder actually slips. But that regime is **beyond pilot scale**, and no small blind A/B —
however cleverly the corner is chosen — reproduces the slip. That is the boundary, stated plainly.

## Consequence for the campaign

Combined with BP1–BP9, the picture is complete for what pilots can show:
- **Correctness:** ties everywhere; no pilot-scale target (I1/I4/BP10/BP11).
- **Trajectory:** a real, modest, non-compounding edge = variance reduction on the early structural choice,
  sized by the shortcut base rate (model-dependent), delivered by the **review** (not by prompt-principles on a
  weak model).

The remaining open questions — the record layer at code-opaque scale, cost at larger scope, and the
correctness claim in a genuinely high-context task — are the ones a **dedicated, non-pilot** evaluation must
carry. n=6, opus, one interaction corner; null recorded as null, Part B not fabricated.
