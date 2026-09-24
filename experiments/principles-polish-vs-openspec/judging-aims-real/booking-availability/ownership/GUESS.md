# Manipulation check: method attribution

**Guess:** X = OpenSpec, Y = aims

**Confidence:** 97%

## Cues

### X looks like OpenSpec
- The artifact layout is OpenSpec's change folder: `<!-- file: proposal.md -->`, `<!-- file: specs/slot-availability/spec.md -->`, `<!-- file: design.md -->`, `<!-- file: tasks.md -->`.
- The proposal uses OpenSpec's template headings: "## Why", "## What Changes", "## Capabilities / ### New Capabilities / ### Modified Capabilities", "## Impact", and the placeholder "<!-- none: no existing specs -->".
- The spec uses OpenSpec's delta format: "# Spec Delta", "## ADDED Requirements", and in stage 2 "## MODIFIED Requirements". Each requirement is "### Requirement: …" with SHALL wording and "#### Scenario:" blocks in "**WHEN** / **THEN**" form.
- The design uses OpenSpec's design.md template: "Context", "Goals / Non-Goals", "Decisions", "Risks / Trade-offs", "Open Questions". Risks are written as "[risk] → mitigation".
- tasks.md is a numbered checklist ("- [ ] 1.1 …"). The last task is "`the-method validate add-booking-availability --strict`", which is `openspec validate <change> --strict` with the name scrubbed. It also refers to a change id.

### Y looks like aims (principle-driven)
- It cites a numbered principles document throughout: "§5 says to let an unactionable programming error fall", "feature envy (§8)", "§5, information hiding", "illegal states unrepresentable (§4)", "Under the §7 tie-break", "§11 concurrency", "§14 security", "§13 performance", and "8.4 Principles that do not apply at this scale".
- It runs named principle passes: "Subtractive pass (rerun on this revision)" with a keep/cut table, and "Concept-fit pass (rerun)" ending "No inert stand-ins remain."
- It uses code-smell vocabulary as its reasoning: "primitive obsession", "data clump", "lazy class", "shotgun surgery", "inappropriate intimacy", "anemic bag".
- It describes a review process and decision log: "Splits decided in the panel", "fix-list item 2/3/7", "Correction to the earlier merge", "decision 0002", and in stage 2 "decisions/0003", "Supersessions".
- It is written as one self-contained architecture document with a "Rule → owner" table, falsifiers ("The falsifier for this decision: …"), and a final "Result: **met**" verdict against the design goal. It has no proposal/spec/tasks split.
- Stage 2 has "Build order — make the change easy, then make the easy change", which is another principle-style heading.

The remaining 3% covers the chance that the labels were deliberately planted or crossed. The structural cues are strong and consistent across both stages.
