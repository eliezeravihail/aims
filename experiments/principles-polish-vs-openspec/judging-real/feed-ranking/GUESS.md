# Manipulation check — method guess

**Guess:** X = aims, Y = OpenSpec

**Confidence:** 97%

## Cues

### Y looks like OpenSpec (its standard change-folder layout and spec-delta syntax)
- File markers match OpenSpec's change-folder layout exactly: `<!-- file: proposal.md -->`, `<!-- file: specs/feed-ranking/spec.md -->`, `<!-- file: specs/ranking-config/spec.md -->`, `<!-- file: design.md -->`, `<!-- file: tasks.md -->`.
- The proposal uses OpenSpec's template headings: "## Why", "## What Changes", "## Capabilities", "### New Capabilities", "### Modified Capabilities", "## Impact".
- Spec-delta syntax: "# Spec Delta", "## ADDED Requirements", "## MODIFIED Requirements", "### Requirement: …", "#### Scenario: …" with "- **WHEN** … - **THEN** …", and RFC-style "SHALL".
- Stage 2 flags breaking changes the way OpenSpec does: "**BREAKING (request shape):**".
- It refers to OpenSpec's archive step: "Stage 1 (archived as `2026-09-23-add-feed-ranking`)".
- The design.md template headings are there: "## Context", "## Goals / Non-Goals", "## Decisions", "## Risks / Trade-offs", "## Migration Plan".
- tasks.md is a numbered checkbox list: "- [ ] 1.1 Create the `feed_ranking` package …".

### X looks like aims (design driven by written principles)
- It cites numbered sections of a principles document: "(§5)", "§7 YAGNI", "§0 published-type-across-seam", "§4 primitive obsession", "§1 fail fast", "§7 one-owner-of-representation".
- It uses method vocabulary that doesn't come from any spec template: "Step-0 inventory", "Rules / invariants (R)", "Change axes (X)", "Foundational substrate", "pervasiveness test", "subtractive pass", "concept-fit pass", "value-correct cram".
- It follows a fixed method loop: "the one mandatory design review-and-revise round", "One measure → return-findings → revise round", "Delta-discovery".
- It names a role and a fallback rule: "the Guide chose it under the separated-phase fallback".
- It uses its own record layout: "`goals.md`, `base-dependencies.md`, `dependencies.md`, `architecture.md`", ADRs under `decisions/`, and "Loop status in `.method/state.md`" (the method's name has been scrubbed out of that path). "system records take no anchor" / "companions to anchor" is also method-specific.
- It frames each stage around a design objective and treats the feature as a constraint ("Kind: design … the feature as its constraint"), which is a principles-driven framing.

I see no conflicting cues. The 3% I'm holding back only covers the chance that the scrubbing or labelling was deliberately swapped.
