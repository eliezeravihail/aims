# Manipulation check: guess

**Guess:** X = OpenSpec, Y = aims

**Confidence:** 97%

## Cues

### X looks like OpenSpec
- It uses OpenSpec's artifact layout, including file markers: `<!-- file: proposal.md -->`, `<!-- file: specs/access-decision/spec.md -->`, `<!-- file: design.md -->` and `<!-- file: tasks.md -->`.
- The proposal has OpenSpec's sections: "## Why", "## What Changes", "## Capabilities" with "### New Capabilities" and "### Modified Capabilities" ("None. The project has no existing specs."), and "## Impact".
- The specs are written as deltas: "# Spec Delta", "## ADDED Requirements", and in stage 2 "## MODIFIED Requirements".
- Requirements use SHALL, and each has scenarios in WHEN/THEN form: "### Requirement: … The service SHALL answer **allow** …", "#### Scenario: … - **WHEN** … - **THEN** …".
- design.md follows OpenSpec's template headings: "## Context", "## Goals / Non-Goals", "## Decisions", "## Risks / Trade-offs" (with `[risk] -> mitigation` bullets).
- tasks.md is a numbered checkbox list: "- [ ] 1.1 Create the `entitlements/` package …".

### Y looks like aims (a design method driven by written principles)
- It refers to a principles document: "(§13 of the principles is conditional …)" and "the value-correct cram that design-principles §4 names" (stage 2).
- It uses principle-style vocabulary: "Tell-Don't-Ask", "CQS", "shotgun surgery", "middle man with no rule", "lazy modules", "concept fit", "imperative shell", "Architecture fitness" tests.
- It justifies choices by forces and falsifiers: "Falsifier for this choice: the day one kind of identifier gains a rule of its own…", "Each lacks a present force", "`_Role` earns its place by two present forces, not by a foreseen stage".
- It has a table assigning each rule to one owner ("## 7. Where each rule lives": "Sole owner"), and a seam calibration table with "Floor"/"Ceiling" columns.
- Its front matter and references are not OpenSpec's: `status: final — panel-merged, revised after one mandatory review round; serves as the root architecture record`, `goals.md`, `base-dependencies.md`, and in stage 2 "decisions/0002".
- It has no proposal/specs/tasks structure, and no ADDED/MODIFIED deltas or SHALL scenarios.

The remaining 3% covers the chance that the labels were deliberately swapped or disguised. The structural fingerprints on both sides are strong and point the same way.
