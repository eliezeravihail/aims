# Manipulation check: which label is which method

**Guess:** X = aims, Y = OpenSpec

**Confidence:** 97%

## Cues

### Y matches OpenSpec's artifact layout and vocabulary
- File markers name the standard OpenSpec change folder: `<!-- file: proposal.md -->`, `<!-- file: specs/feed-ranking/spec.md -->`, `<!-- file: specs/ranking-config/spec.md -->`, `<!-- file: design.md -->` and `<!-- file: tasks.md -->`.
- The proposal uses OpenSpec's section headings: "## Why", "## What Changes", "## Capabilities", "### New Capabilities", "### Modified Capabilities" and "## Impact".
- The specs are written as deltas: "# Spec Delta", "## ADDED Requirements" and, in stage 2, "## MODIFIED Requirements".
- Requirements use RFC-style SHALL and are followed by scenarios in WHEN/THEN form, for example "### Requirement: …", "#### Scenario: …" and "- **WHEN** … - **THEN** …".
- The design uses OpenSpec's design.md template: "## Context", "## Goals / Non-Goals", "## Decisions", "## Risks / Trade-offs", "## Migration Plan".
- tasks.md is a numbered checkbox list: "- [ ] 1.1 Create the `feed_ranking` package …".

### X reads like it was driven by a written set of design principles
- It cites a principles document directly: "design-principles §13 is conditional, so the direct form reads as the rule" (X-stage-2, around line 591).
- The same principle-style ideas come up again and again: "each rule has exactly one owner", "Rule → owner → entry paths", "a second owner" and "Three facts, each with one owner, make a mixed or invalid ranking unrepresentable".
- Its section names sound like steps in a method: "Change axes the shape absorbs, and those it deliberately doesn't", "Seams and the types that cross them", "What was cut (subtractive pass) and concept fit" and, in stage 2, "Re-trace: every reader of a changed shape".
- It has none of OpenSpec's artifacts: no proposal, no spec deltas, no SHALL requirements, no WHEN/THEN scenarios and no tasks checklist.

The remaining 3% covers the chance that the scrubbing or the setup was adversarial, for example if the OpenSpec agent was also given a principles document. The structural cues are strong enough that I don't expect that.
