---
title: "a refactoring review is a before/after delta on the target's grain — consistency overrides the checklist"
date: 2026-09-18
---

**Context.** `refactoring-principles.md` (0015) graded a change against its own checklist, like a design
review. Two things that reading missed, both surfaced while validating the document on real and synthetic
adaptations:

1. **The bar is relative, not absolute.** What matters is not how the changed module scores against the ideal
   in the abstract, but whether *this* module got **worse** — and, because rot is cumulative, the **trajectory
   across a sequence** of adaptations (each step "works" while the architecture degrades — the mechanism
   behind the historical checkout S4).
2. **Consistency with the target can outrank a principle.** A module has an established style and level of
   abstraction. A change that imports a *foreign* style — value objects onto bare-int code, a class hierarchy
   onto a flat functional module — is itself a **regression** (it makes the module inconsistent), even when it
   scores higher against `design-principles.md`. The greenfield rule ("too little structure is the graver
   risk") does not transfer unchanged to a codebase already written a certain way.

**Decision.**
1. **The refactoring measure is an explicit before/after review** on the **target's own terms**: read design
   quality before and after; the bar is **no regression, ideally a small improvement**; across successive
   changes, watch the **trajectory**. Recorded at the top of `refactoring-principles.md` and in the
   `### refactoring` lens of `review-panel.md`.
2. **Match the target's grain — consistency over dogma.** Adapt to the existing code's style and abstraction
   *even where it contradicts a principle in `refactoring-principles.md` or `design-principles.md`*; when the
   two disagree on the same change, the grain wins and the deviation is recorded as deliberate. The goal is
   **no new mess**, not conformance to the list.

**Consequences.** The refactoring lens now grades a *delta on the target*, not a rewrite toward an ideal, and
explicitly penalizes both the plain arm's accretion (rot) **and** an over-eager arm that imposes ceremony a
flat module never needed (inconsistency). Rejected alternative: keeping the absolute checklist grade — it
would reward a foreign-style "cleaner" rewrite that a maintainer of the target would reject, and it cannot see
cumulative rot. This refines 0015; it does not reverse it (the checklist still names what to look for; this
decides how it is weighed against the target).
