---
title: "substantive judging — by consequence, not smell-catalogue"
date: 2026-09-16
---

# Why this exists
The first design-quality reading (`run-log/judge-reports/quality-*.md`) was a smell-catalogue judged by
taste: two opposite-disposition judges both fixated on the same technical point (tax folded into the
explanation ledger) and ranked aims third, letting one localized decision outrank a leaner architecture.
The operator's critique: a local problem is nothing against a better architecture, and judging must be
substantive, not technical. This is the redesigned judging.

# The rubric (`RUBRIC.md`)
Judge by **consequence**: M1 change-absorption (the survival count), M2 accidental complexity (machinery
the problem did not force), M3 blast radius of three pre-registered future changes. A fault is placed on a
**Cartesian severity plane** (M4): X = hiddenness (visible→latent), Y = change-required-to-fix
(additive→architectural); severity grows monotonically along both, the origin corner is negligible, the
hidden-and-architectural corner is a design failure. A fault may move the ranking only in proportion to how
far it sits toward that corner.

# Two substantive judges, opposite verdicts — recorded honestly
- **verdict-1**: **P (aims-v2) wins.** Best M1 (5 vs 8/9), least accidental complexity (shared catalog,
  no per-market-file/routing-guard cluster), M3 close. Treated the tax-in-ledger fault as consequence-free
  and barred it.
- **verdict-2 (adversarial)**: **flips to Q (plain).** The tax fault is NOT consequence-free — it bites the
  pre-registered C-next-1 (per-product reduced rate) and an invented "second stacked tax": once tax
  composition changes, aims must reopen the discount ledger and INV-7 where plain/OpenSpec keep it closed.
  The fault is pervasive (result.py + pricing.py + market.py + the `Explanation.final==gross` seam). And
  M1 is only partly comparable — ~2–3 of aims-v2's survival lead is "fewer seams / did less," not "absorbs
  change better."

# Placing aims-v2's fault on the operator's Cartesian plane
- **Y (change to fix): high / architectural** — reshapes a core seam and the ownership of INV-7.
- **X (hiddenness): high** — numbers are correct on every current case; the cost is latent and surfaces
  only under a future tax-composition change (per-product rates is pre-registered). Looks clean, passes
  every test, hides its price until later.
So by the operator's own model the fault sits in the **hidden-and-architectural (severe) corner** — it is
a genuine design weakness, not a dismissible local blemish. The earlier "visible + correct = not terrible"
read was too shallow.

# Honest bottom line
Close — a P/Q wash, not a rout. aims-v2 is genuinely leaner and absorbs the *already-seen* evolution
better (M1). But applying the substantive rubric and the operator's severity model rigorously, its one
fault — tax folded into the explanation ledger — is real design weakness (latent cost, architectural fix),
and on the forward-looking measure it tips the edge to the plain arm. This does not restore aims to a win;
it explains, correctly this time, *why* the tax decision matters even though every number is right: it is
the method's "explanation is the single source of truth" doctrine over-applied to a concept (tax) that is
a decomposition, not a movement. That doctrine — not §2 — is the next lever for the method.

# Caveats
aims-only re-run (plain/OpenSpec designs are the v1 ones); n=1; the M1 non-comparability discount above;
judges on Opus. The substantive rubric was authored by the operator's session, so verdict-1's pro-aims
lean was correctly stress-tested by verdict-2 rather than trusted.
