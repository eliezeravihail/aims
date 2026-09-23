---
title: "BP8 result — aims-lite (principle injection) did NOT lower the shortcut rate on a weak model: 2/6 = 2/6"
date: 2026-09-20
---

# BP8 — does the aims-lite principle line transfer to a weak executor?

BP3 showed the **derive-don't-store** principle transfers via one sentence — on **opus**. BP7 showed the
**concept-fit** shortcut (an `isinstance` type-branch engine) is taken **2/6** by plain **haiku** builds. BP8
asks the improvement-critical question directly: does prepending the aims-lite principle block — including the
explicit concept-fit line *"model each distinct concept as its own first-class type with a uniform interface,
rather than branching on a type tag"* — **lower** that 2/6 on haiku?

## Result — no effect (2/6 → 2/6)

| arm (haiku, 6 builds each) | type-branch (shortcut) | polymorphic | branch rate |
|---|---|---|---|
| **plain** (BP7 baseline, no hint) | runs 2, 5 | 1,3,4,6 | **2/6** |
| **lite** (concept-fit principle block) | runs 2, 6 | 1,3,4,5 | **2/6** |

The principle injection made **no measurable difference**: the same fraction of haiku builds (2 of 6) still
centralized all discount logic in an `isinstance` if-elif chain inside `Engine.total`, the exact type-code
shortcut the concept-fit principle names and tells them to avoid. (Fisher exact 2/6 vs 2/6 → p = 1.0; both
underpowered — but there is *zero* signal of reduction, not a small one.)

## What this means — deflating for cheap delivery, and it points at the review

BP3 and BP8 together draw a sharp line:

- **The principle transferred on a strong model (BP3, opus): yes.** A capable executor, handed one sentence,
  acted on it and reproduced the method's structural choice.
- **The principle did NOT transfer on a weak model (BP8, haiku): no.** The same class of one-line guidance,
  made explicit, changed nothing — haiku ignored or failed to operationalize the abstract principle exactly as
  often as with no hint.

This is the opposite of convenient. aims-lite (principle-in-prompt) appears to help **only where the executor
is already capable enough to barely need it** (opus, where the base shortcut rate is already ~0), and to do
**nothing on the weak executor where the edge is largest** (haiku, 33% shortcut rate). A principle the model
can ignore is not a substitute for a step that inspects the output. That is precisely what aims' **mandatory
review** is — it reads the built code and rejects the type-branch — and it is the part a prompt line cannot
replicate on a model that doesn't self-apply guidance.

**So the honest improvement reading flips:** the campaign's earlier "aims-lite may capture most of the benefit
cheaply" (BP3) is a **strong-model-only** finding. On weak executors — the tier where the method's edge is
biggest — the cheap principle injection bought nothing here; the method's value there is the *review that
checks the artifact*, not the *advice in the prompt*.

## Honest limits + the decisive follow-up (BP9)

n=6 per arm, one card, one model, one axis; the null is real but small-sample. The decisive next test is
already visible: take the 2 branched haiku builds and run an **aims review pass** over them — if the review
catches the type-branch and drives the fix where the principle line did not, that confirms *review > principle
injection on weak executors* and locates aims' irreducible value. That is BP9. Recorded as: **aims-lite is not
a weak-model substitute for the method's review** (n small; no signal of benefit).
