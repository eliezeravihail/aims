# Manipulation check — method guess

**Guess:** X = OpenSpec, Y = aims

**Confidence:** 97%

## Cues

### X looks like OpenSpec
- X is split into the standard OpenSpec change artifacts, each marked with a file header: `<!-- file: proposal.md -->`, `<!-- file: specs/access-decision/spec.md -->`, `<!-- file: specs/entitlement-model/spec.md -->`, `<!-- file: design.md -->`, `<!-- file: tasks.md -->`.
- The proposal uses OpenSpec's template headings: `## Why`, `## What Changes`, `## Capabilities` / `### New Capabilities` / `### Modified Capabilities`, `## Impact`.
- The specs are written as OpenSpec deltas: `# Spec Delta`, `## ADDED Requirements`, and in stage 2 `## MODIFIED Requirements`.
- Requirements use OpenSpec's form: `### Requirement: ...` with `SHALL` / `SHALL NOT`, then `#### Scenario:` blocks written as `**WHEN** ... **THEN** ...`.
- The design uses the OpenSpec design.md template: `## Context`, `## Goals / Non-Goals`, `## Decisions`, `## Risks / Trade-offs`, `## Migration Plan`. It ends with a numbered, checklist-style `# Tasks`.

### Y looks like aims (a principles-driven method)
- Y cites a principles document directly: "(§13 of the principles is conditional and no requirement is stated)".
- Y uses vocabulary that reads like a named set of design principles: "seam", "### 2.1 Calibration of each seam" with a "Floor (what the consumer needs) | Ceiling (what every producer can supply)" table, "*concept fit*", "Falsifier for this ...", "the imperative shell", "one type per distinct handling", "sole owner of the file format", "## 7. Where each rule lives", "the one owner of 'a supplied instant'".
- Y refers to a separate `goals.md` with numbered assumptions (A1–A6, B1–B5) and to `base-dependencies.md`. Neither is an OpenSpec artifact.
- Y's front matter reads "status: final — panel-merged, revised after one mandatory review round". It also mentions "The genericity draft proposed ...". Both suggest a multi-lens review process, not an OpenSpec proposal/specs/tasks flow.
- Y has no proposal/specs/tasks split and no ADDED/MODIFIED deltas or WHEN/THEN scenarios. It is one architecture record.

The remaining 3% covers the chance that the scrubbing swapped the formats on purpose. The structural cues are strong and consistent across both stages.
