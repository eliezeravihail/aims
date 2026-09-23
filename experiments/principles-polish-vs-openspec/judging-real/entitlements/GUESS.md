# Manipulation check: method attribution

**Guess:** X = **OpenSpec**, Y = **aims**

**Confidence:** 97%

## Cues for X = OpenSpec

X follows OpenSpec's change-proposal format and artifact set closely:

- **File layout.** The files are `proposal.md`, `specs/<capability>/spec.md`, `design.md` and `tasks.md`, joined with `<!-- file: ... -->` markers. This is the OpenSpec change directory.
- **Proposal headings.** `## Why`, `## What Changes`, `## Capabilities` → `### New Capabilities` / `### Modified Capabilities`, and `## Impact`. This is the OpenSpec proposal template.
- **Spec deltas.** `# Spec Delta`, `## ADDED Requirements`, `## MODIFIED Requirements`, and `### Requirement: ...` with `#### Scenario: ...`. Each scenario uses bold `- **WHEN** ... - **THEN** ...` bullets and RFC-style `SHALL` / `SHALL NOT`. These are the OpenSpec delta conventions.
- **Stage 2 as a delta.** Stage 2 updates specs in place ("The 'no hierarchy' clause of the exact-pair requirement is replaced") and lists `Modified Capabilities`.
- **Archive path.** "Stage 1 is described in `the-method/changes/archive/2026-09-23-entitlements-decision-service/design.md`". The `changes/archive/<date>-<change-name>/` path is OpenSpec's archive layout. The directory name was scrubbed to "the-method", but the rest of the path was not.
- **Design and tasks templates.** `design.md` has the sections `## Context`, `## Goals / Non-Goals`, `## Decisions`, `## Risks / Trade-offs` (with `[risk] -> mitigation` bullets) and `## Migration Plan`. `tasks.md` uses numbered `- [ ] 1.1` checkboxes. Both match the OpenSpec templates.

## Cues for Y = aims (the principles-driven method)

Y keeps citing a numbered set of principles and a review ritual built on them:

- **Numbered principles.** It cites sections of a principles document: "Subtractive pass (§7)", "Naming pass (§3)", "Concept-fit pass (§4)", "Interface-calibration check (§5)", "§0 says speak the published domain type at a seam", "§1 correctness, §5 one-owner, §0/§11 core-purity", "§7 falsifier: name the Stage-1 axis it serves".
- **Method vocabulary.** "the-method-single arm", "Produced by the-method: plan phase (objective + filed records) + the one mandatory design review-and-revise round", "the Guide chose the substrate", "a Worker could start sprint 1 from it", "no S3/S4 finding open", "Full scored profile withheld here per the build-time projection".
- **Durable records.** It files its own records rather than OpenSpec artifacts: `goals.md`, `base-dependencies.md`, `dependencies.md`, `architecture.md`, `decisions/0001-substrate.md`, `decisions/0002-...`, `decisions/0003-stage2-precedence.md`, `review.md`, `decisions/0011`.
- **Design-principle language.** "Tell-Don't-Ask", "connascence of position → of name/type", "ports-&-adapters boundary", "pure functional core", "value-correct ceremony", and "a boolean with a label" (named as the canonical ceremony the subtractive pass targets).
- **Self-assessment sections.** Stage 2 includes `## 5. SURVIVAL` and `## 6. Cost` tables that judge the stage-1 bet. These come from the method's own reflection step, not from an OpenSpec template.
- **No OpenSpec structure.** Y has no proposal, spec deltas, SHALL/WHEN/THEN scenarios or tasks checklist.

## Why not 100%

The scrubbing replaced both method names with "the-method" (X's archive path, and Y's text throughout), so no single token proves the attribution. Even so, X's artifact structure and Y's principle citations are very hard to explain the other way round.
