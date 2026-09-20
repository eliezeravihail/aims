---
title: "BP8 — does aims-lite (principle injection) lower the shortcut base rate on a weak model?"
date: 2026-09-20
status: pre-registered before any lite arm ran
---

# The question the campaign now points at

BP6/BP7 established that aims' trajectory edge = variance reduction on an early structural choice, sized by the
**shortcut base rate**, which is model-dependent: on **haiku**, the concept-fit shortcut (an `isinstance`
type-branch engine instead of first-class rules) was taken **2/6** plain builds (BP7 `baserate/`). BP3 showed
the *derive* principle transfers via one sentence on opus. The open, directly-actionable improvement question:

**Does a lightweight principle injection ("aims-lite" — a few high-yield principles as a short prompt, no
skill/records/review) lower the shortcut rate on a weak model?** If yes, aims-lite is a real, cheap delivery
mode worth recommending: it would buy most of the trajectory edge (fewer reopens) at plain cost, without the
~1.85× method premium.

# Design (a clean base-rate A/B, same product/model as BP7's probe)

- **Product/card:** identical BP7 concept-fit stage-1 card (three promo rule kinds + engine). Model: **haiku**
  (the tier where the shortcut actually appears).
- **plain baseline:** reuse BP7 `baserate/` — **2/6 TYPE-BRANCH** (runs 2,5), 4/6 polymorphic. (Copied here
  for the record; not re-run.)
- **lite arm:** **6 fresh haiku builds** of the same card, each with the aims-lite principle block prepended:
  - concept-fit ("model each distinct concept as its own first-class type with a uniform interface, rather
    than branching on a type tag");
  - one owner; full input space; subtractive.
- **Metric (pre-registered):** fraction of lite builds that write the **type-branch** engine (isinstance/
  type-tag if-elif) vs first-class polymorphic rules. Classified by reading each engine directly (grep
  `isinstance(rule` in the engine), not by prose.

# Pre-registered predictions

- If aims-lite transfers the concept-fit discipline: lite branch rate **< 2/6**, ideally 0/6.
- If the principle doesn't stick on a weak model (haiku may not act on abstract guidance): lite ≈ plain (~2/6)
  → aims-lite is **not** enough on a weak executor, and the method's machinery (or at least worked examples)
  is doing more than a principle line. Either result is informative and recorded honestly.
- Null-aware: n=6 per arm, one card, one model. A 2/6 → 0/6 shift is suggestive, not proof (Fisher exact on
  2/6 vs 0/6 is p≈0.45 — underpowered); report the raw counts and the wide uncertainty, don't oversell.

# Guardrails

Correctness is not the metric here (all BP7 builds passed the spec); this isolates the **structural-choice
rate**. Builds that fail to satisfy the API are re-run or excluded with a note. Nulls recorded as nulls.
