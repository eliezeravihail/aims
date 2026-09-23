---
title: "BP9 — does the aims review catch the shortcut that the aims-lite principle could not (on weak-model output)?"
date: 2026-09-20
status: pre-registered before the review ran
---

# The decisive test BP8 set up

BP8 showed the aims-lite **principle-in-prompt** produced no reduction in haiku's concept-fit shortcut rate
(2/6 → 2/6): a weak model ignores abstract advice as often as it takes it. The method's other, heavier lever
is the **mandatory review** — a step that reads the *built artifact* and rejects the shortcut, which a prompt
line cannot do on a model that doesn't self-apply guidance. aims' architecture is explicitly **mixed-tier**: a
cheap Worker builds, a competent Guide reviews. BP9 tests that configuration on exactly the outputs the
principle failed to fix.

# Design

- **Inputs:** the **4 branched builds** — weak-model (haiku) outputs that took the type-branch shortcut (an
  `isinstance` if-elif engine, rules as dumb data): `branched/b1-plain-run2`, `b2-plain-run5` (BP7 plain),
  `b3-lite-run2`, `b4-lite-run6` (BP8 lite). All are functionally correct at stage 1 (pass the spec); the
  shortcut is a *structural* defect (the engine is a second owner of every rule's logic; adding a rule kind or
  the stacking policy reopens it).
- **Treatment:** run the **real aims review instrument** (`skills/aims-guide/references/review.md` — the
  subtractive / concept-fit / one-owner / full-input-space passes) as a competent Guide (opus) over each build.
  The reviewer is given the code and the review reference and asked for findings — **NOT** primed to look for
  the type-branch. Blind to which builds came from plain vs lite.
- **Metrics (pre-registered):**
  1. **Detection:** for each of the 4 builds, does the review independently raise a finding that the engine's
     type-dispatch is a one-owner / concept-fit defect and recommend first-class rules? (yes/no per build)
  2. **Repair (secondary):** applying the review's recommendation, does the engine become polymorphic with the
     spec still passing? (spot-check 1–2 builds; correctness via the BP7 hidden stage-1 tests, 12/12).

# Pre-registered predictions

- If the method's value on weak executors is the review (BP8's implication): detection **4/4** (or 3/4) — a
  competent aims review reliably names the type-branch as a §5 one-owner violation, where the principle line
  changed nothing. That would locate aims' irreducible, non-transferable value: *output inspection*, not advice.
- Null/negative to stay honest: if the review misses it on some builds (the shortcut is defensible at a single
  stage), detection < 3/4 — then even the review doesn't reliably flag a functionally-correct shortcut, and
  aims' edge is narrower than "the review saves you." Recorded either way.

# Guardrails

The type-branch is **not a correctness bug** at stage 1 — a fair review must flag it on *structural* grounds
(one-owner / extensibility), not invent a false correctness failure. A review that only says "looks correct"
counts as a **miss**. n=4; one axis/card. The reviewer uses the shipped instrument as-is (no hand-direction).
