---
description: "aims — plan a change to code that ALREADY EXISTS: a pure refactor, or an adaptation that absorbs a new requirement. Learns the code and characterizes its behavior first, chooses one refactoring/adaptation objective, files the records, and stops for review. Does not use the greenfield design flow."
---

Enter the `aims-guide` skill and run the **PLAN phase for a `refactoring` objective** — a change to existing
code, not a new product. Follow `references/refactoring-principles.md` (the brownfield checklist),
`references/objective-selection.md` (the `refactoring` Kind and the *Adapt existing code to a new
requirement* pattern), `references/discovery.md` ("Entering an existing codebase"), `references/modes.md`
(stepped mode), and `references/design-record.md`.

**Changing existing code is a different task from first-time design — do not run the greenfield flow.** There
is no usage-scenario-from-nothing and no substrate to choose; the code is ground truth. Concretely:

- Set `Mode: stepped` in `.aims/state.md` (create it from `assets/state-template.md` if absent).
- **Learn the code first** (`references/discovery.md`, "Entering an existing codebase"): the real seams, the
  records in force (the companion of each file you will touch, the root records, the decisions), and the
  implementation of **every case your change claims to touch, preserve, or unify**.
- **Characterize the behavior you must preserve** (`refactoring-principles.md` §1) — the paths the change is
  near, and everything out of scope that must stay bit-for-bit identical. If load-bearing behavior is
  genuinely unknown, the first objective is to characterize it, not to edit blind.
- **Resolve any open product decision** by asking the user one concrete question at a time.
- Choose the single **`refactoring` objective** now and **declare its Kind `refactoring`** (it sets the
  review lens — `refactoring-principles.md`, not the design form alone). Frame it as the two moves where they
  apply: **make the change easy** (a behavior-preserving refactor that creates the seam) **then make the easy
  change** (add the new behavior at that seam) — as separable steps. Draft a bounded Worker handoff per
  `references/worker-handoff.md`. Write both into `state.md`; set the Loop cursor to `planned:awaiting-build`.
- **File the round's durable records in the code tree** (`references/design-record.md`): supersede a decision
  **in place** (never silently contradict a recorded invariant); record what behavior is being preserved and
  what is changing, the seam the change lands at, and the interactions it implies. **Anchor each companion on
  filing** with `python3 .aims/anchor.py <companion>`. `decisions/` are append-only.
- **Stop here. Do not delegate and do not write implementation code.** **Present a plan report** — the
  objective, the behavior being preserved vs changed, the seam, the refactor-then-change decomposition, the
  interactions to re-trace, and the exit criteria — so the user can inspect it before anything is built. Then
  tell them to run `/aims-build`, and `/aims-review` (which apply the `refactoring` lens by Kind).

$ARGUMENTS
