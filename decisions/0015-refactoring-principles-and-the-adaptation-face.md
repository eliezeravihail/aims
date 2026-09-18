---
title: "a add-feature-principles document and the refactoring Kind's adaptation face"
date: 2026-09-18
---

**Context.** aims had a full principles document for *first-time design* (`design-principles.md`) driving the
`design` lens, but the `refactoring` Kind carried only a four-line lens in `review-panel.md` ("behavior
preserved, smell gone") and **no principles document**. That thin definition also excluded the most common
real change: **adapting existing code to a new requirement** — where behavior *does* change and the existing
structure must be reshaped to absorb it. The standalone-review Step-0 even named the gap ("a refactor that
also adds behavior") but only said "pick the dominant lens." Changing existing code is a different task from
greenfield design: its dominant risks are silent behavior drift, changing code you don't understand,
scattering a rule while patching it, and bolting the requirement on instead of absorbing it — none of which a
blank-file checklist targets. The `experiments/principles-polish-vs-openspec/` pilot sharpened this: aims
wins first-round *design*, but the failure that has actually beaten aims (`experiments/judging-rubric/
regrade-results.md`, the cart-discount→line-allocation S4) is a *change-time* correctness miss invisible to a
survival reading.

**Decision.**
1. **Ship `references/add-feature-principles.md`** — the brownfield companion to `design-principles.md`, the
   professional checklist for changing code that already exists. Its preconditions are change-specific:
   characterize-before-touch (§1), behavior preserved out of scope (§4), one owner survives the change (§5),
   and re-trace the full input space the change implies (§6). Its organizing move is Beck's *make the change
   easy, then make the easy change* (§0): a behavior-preserving refactor that creates the seam, then the
   behavior-changing step at that seam, kept distinguishable. It builds on `design-principles.md` for any new
   structure the change creates rather than repeating it.
2. **The `refactoring` Kind now covers both faces of changing existing code** — a pure refactor (behavior
   preserved) and an **adaptation** (a new requirement absorbed). Its lens in `review-panel.md` fills against
   `add-feature-principles.md`, and `objective-selection.md` gains the *Adapt existing code to a new
   requirement* pattern. No fourth Kind is added: the state-template Kind list and the coherence lens-check
   stay as they are (the lens header remains `### refactoring`).
3. **A dedicated command, `/aims-add-feature`**, is the front door for a change to existing code: it learns the
   code and characterizes its behavior first (not the greenfield usage-scenario/substrate flow), chooses one
   `refactoring` objective, files the records (superseding decisions in place), and stops for review. `/aims-build`
   and `/aims-review` then apply the refactoring lens by Kind.

**Consequences.** A change request now has a home that matches its risks, and the review measures it against
the right checklist instead of the design form alone. The greenfield `/aims-plan` flow is no longer
stretched over brownfield work. Rejected alternatives: (a) *enrich the design form to cover changes* — it
would blur two genuinely different tasks into one rubric; (b) *add a separate `adaptation` Kind* — more
machinery (a fourth Kind, lens, template entry) for a distinction the `refactoring` lens can carry with a
named sub-mode; (c) *a command-only orchestration with no principles doc* — leaves "what a correct change is"
unstated, which is the very gap this closes.
