# Manipulation check: which label is which method

**Guess:** X = aims, Y = OpenSpec

**Confidence:** 97%

## Cues

### Y has OpenSpec's artifact layout and vocabulary
- The files are stitched together with markers that match OpenSpec's change-folder layout exactly: `<!-- file: proposal.md -->`, `<!-- file: specs/feed-ranking/spec.md -->`, `<!-- file: specs/ranking-config/spec.md -->`, `<!-- file: design.md -->`, `<!-- file: tasks.md -->`.
- The proposal uses OpenSpec's template headings: `## Why`, `## What Changes`, `## Capabilities`, `### New Capabilities`, `### Modified Capabilities`, `## Impact`.
- The specs are written as deltas: `# Spec Delta`, `## ADDED Requirements`, and in stage 2 `## MODIFIED Requirements`.
- Requirements use RFC-style `SHALL` wording, and scenarios use the `#### Scenario:` heading with `- **WHEN** … - **THEN** …` bullets.
- The design uses OpenSpec's `design.md` sections: `## Context`, `## Goals / Non-Goals`, `## Decisions`, `## Risks / Trade-offs`, `## Migration Plan`.
- `tasks.md` is a numbered checkbox list (`- [ ] 1.1 Create the feed_ranking package …`).

### X is organized around design principles, not spec artifacts
- It has no proposal, spec delta, SHALL requirements or task checklist. It is one architecture document.
- Its sections read like the checks a principles-driven method would run: "Change axes the shape absorbs, and those it deliberately doesn't", "Rule → owner → entry paths", "What was cut (subtractive pass) and concept fit", and in stage 2 "Re-trace: every reader of a changed shape".
- It keeps returning to the one-owner rule and to justifying what it kept: "Owner (exactly one)", "Kept, with the force behind each", "a second owner, and a signature that lies", "Arity is Python's rule; values are the product's."
- Its assumptions are framed as choices handed back by a product owner: "the PO handed these choices back; each is a simple default". That fits a method with a written principle about product decisions.

## Why not 100%
Y matches OpenSpec almost exactly, so the only real doubt is whether the scrubbing could have reshaped the structure. It is very unlikely that an aims agent produced OpenSpec's file tree and delta headings.
