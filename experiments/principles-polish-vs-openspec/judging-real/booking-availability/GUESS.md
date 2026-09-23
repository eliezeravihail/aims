# Manipulation check: which label is which method

## Guess

- **X = aims** (the method driven by a written set of design principles)
- **Y = OpenSpec** (the spec-driven workflow tool)

## Confidence

**97%**

## Cues

### Y matches OpenSpec's file layout and syntax

- **The file set is OpenSpec's change folder.** Y is split into `<!-- file: proposal.md -->`, `<!-- file: specs/slot-availability/spec.md -->`, `<!-- file: design.md -->` and `<!-- file: tasks.md -->`. That is the proposal, spec delta, design and tasks set of an OpenSpec change.
- **The proposal uses OpenSpec's template headings.** They are `## Why`, `## What Changes`, `## Capabilities` (with `### New Capabilities` and `### Modified Capabilities`) and `## Impact`.
- **The spec uses delta syntax.** The headings are `# Spec Delta`, `## ADDED Requirements` and, in stage 2, `## MODIFIED Requirements`.
- **Requirements and scenarios follow OpenSpec's format.** Requirements are written as `### Requirement: ...` with SHALL wording. Scenarios are written as `#### Scenario: ...` with `- **WHEN** ... - **THEN** ...`.
- **Some commands and paths are OpenSpec's, with only the name scrubbed.**
  - `the-method validate add-booking-availability --strict` and `the-method validate add-buffer-notice-granularity --strict` match OpenSpec's `validate --strict` command.
  - "Stage 1 is archived at `the-method/changes/archive/2026-09-23-add-booking-availability/design.md`" follows OpenSpec's `changes/archive/<date>-<change-id>/` layout.
- **The design doc and task list use OpenSpec's scaffolding.**
  - `design.md` has the sections `## Context`, `## Goals / Non-Goals`, `## Decisions`, `## Risks / Trade-offs` and `## Migration Plan`.
  - `tasks.md` is a numbered checkbox list, for example `- [ ] 1.1 ...`.

### X reads like a principles-driven method

- **It cites numbered principles throughout.** Examples are "Domain model — value objects (§4)", "Seams and crossing types (§0/§5)", "§5 one-owner-per-rule", "(§7 falsifier: no present X-item forces it)" and "the §4 cram risk".
- **Its review rounds use named passes from a principles checklist.** They are "the **subtractive pass**" and "The **concept-fit pass** (run on the design, before code)". The rounds are also "Measured with the assessment form; building projection (fix-list, most-severe-first, no aggregate)" and include "One mandatory design review-and-revise round".
- **Its vocabulary sounds like a design philosophy, not a spec template.** Examples are "*Deleting it damages no current ownership*", "the pervasiveness test finds only the language foundational", "value-correct-but-concept-substituted shape" and "no inert member".
- **Its durable records don't fit OpenSpec's layout.** They are `goals.md`, `architecture.md`, `base-dependencies.md`, `decisions/0001–0003` and `.method/state.md`. X also mentions "Kind: design" and "stepped `/the-method-plan`". Nothing in X uses proposal, spec-delta or task formats, or SHALL/WHEN/THEN.

### Why not 100%

The two formats line up so closely with the two methods that the only real doubt is a deliberate swap or disguise. I saw no sign of one.
