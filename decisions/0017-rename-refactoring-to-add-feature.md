---
title: "rename the brownfield task from 'refactoring' to 'add-feature' — the name now matches the work"
date: 2026-09-18
---

**Context.** 0015 introduced a brownfield task and (following the classic term) called it the `refactoring`
Kind, with `/aims-refactor` and `refactoring-principles.md`. That name is **wrong for the work it names.**
*Refactoring* is, by definition, a **behaviour-preserving clean-up** — it fixes and tidies, it does not add
anything. But the common task here is **adding a feature to, or adapting, existing code**, which **changes
behaviour**. Calling a behaviour-changing task "refactoring" is a category error, and it misleads both the
operator (who reaches for the wrong command) and the review (which would expect behaviour to be preserved).

**Decision.** Rename the brownfield task to **`add-feature`**, everywhere: the Kind (`design` |
`implementation` | `add-feature` | `experiment`), the command **`/aims-add-feature`**, and the checklist
**`add-feature-principles.md`**. *Refactoring* keeps its true, narrow meaning — a behaviour-preserving
clean-up — as a **sub-case** of an add-feature change (often its first move: "make the change easy, then make
the easy change"), graded on its own terms by §11 of the checklist. Files renamed
(the old `aims-refactor` command → `commands/aims-add-feature.md`; the old `refactoring-principles`
reference → `references/add-feature-principles.md`); all shipped surfaces
(SKILL, objective-selection, review-panel, review, state-template, the plugin manifests, the README), the
`tests/coherence.sh` Kind matcher, and the docs site updated to match. This ADR supersedes the **naming** of
0015/0016 only; their substance (the checklist's content, the before/after-review measure, consistency over
dogma) stands unchanged.

**Consequences.** The command a developer types now says what it does — add a feature to existing code — and
the review applies the right lens by a correctly-named Kind. Rejected alternative: keep "refactoring" as the
umbrella — it is the established word, but it actively misdescribes a behaviour-changing task, which is the
whole point of giving this task its own name. The historical experiment directories
(`experiments/refactoring-*`) keep their names as dated artifacts; the shipped method is what changed.
