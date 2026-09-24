# Manipulation check — method guess

**Guess:** X = OpenSpec, Y = aims

**Confidence:** 97%

## Cues

### X looks like OpenSpec
- It is split into OpenSpec's standard change artifacts, with file markers: `<!-- file: proposal.md -->`, `<!-- file: specs/slot-availability/spec.md -->`, `<!-- file: design.md -->`, `<!-- file: tasks.md -->`.
- The proposal uses OpenSpec's template headings: "## Why", "## What Changes", "## Capabilities / ### New Capabilities / ### Modified Capabilities", "## Impact".
- The spec is written as deltas: "# Spec Delta", "## ADDED Requirements" in stage 1, then "## MODIFIED Requirements" and "## ADDED Requirements" in stage 2.
- Requirements use RFC-style wording and a fixed scenario format: "### Requirement: …", "The system SHALL …", "#### Scenario: …", "- **WHEN** … - **THEN** …".
- design.md follows OpenSpec's template: "## Context", "## Goals / Non-Goals", "## Decisions", "## Risks / Trade-offs", "## Open Questions".
- tasks.md is a numbered checkbox list: "- [ ] 1.1 …".
- The final task is "`the-method validate add-booking-availability --strict`". This is `openspec validate <change> --strict` with the tool name scrubbed.

### Y looks like aims
- It keeps pointing to a numbered set of principles that is not in the file: "That is feature envy (§8)", "§5 says to let an unactionable programming error fall rather than wrap it", "(§4, illegal states unrepresentable)", "Under the §7 tie-break", "§11 concurrency", "§14 security", "§13 performance".
- It has a section titled "8.4 Principles that do not apply at this scale".
- It runs passes that come from a checklist: "8.5 Subtractive pass (rerun on this revision)" with a "Present force | Verdict" table, and "8.6 Concept-fit pass (rerun)". It also says "No inert stand-ins remain."
- It uses principle-style wording throughout: "present force", "The falsifier for this decision", code-smell names ("primitive obsession", "data clump", "lazy class", "shotgun surgery", "inappropriate intimacy"), and "make the change easy, then make the easy change" (stage 2, §10).
- It shows signs of a review loop: "Splits decided in the panel", "fix-list item 2/3/7", "Correction to the earlier merge", and "Revise round" rows in stage 2.
- It cites its own decision records: "decision 0002", "decisions/0003", "decisions/0004 §7".
- It ends with a verdict against the goal: "## 11. Result — **met**, against the design goal".
- It is a single self-contained architecture document, not OpenSpec's proposal/spec/tasks file set.

I have some doubt only because the scrubbing could in principle hide a reversed setup. But the OpenSpec file layout and delta syntax in X are too specific to mistake.
