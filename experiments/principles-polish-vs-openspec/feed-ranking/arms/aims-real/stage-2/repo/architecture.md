---
title: "architecture"
date: 2026-09-23
---
The architecture (stage 2) is specified in full in [DESIGN.md](DESIGN.md), which is authoritative until
the code exists. The rationale and the per-axis harvest are in
[decisions/0001](decisions/0001-stage1-architecture.md) (stage 1) and
[decisions/0002](decisions/0002-stage2-eligibility-diversity.md) (eligibility and diversity). This record
keeps only what the code will not say about itself.

## Boundary
A pure core (`numbers`, `signals`, `weights`, `request`, `ranking`) sits inside a thin shell (`service`,
`config_file`, `cli`). The core never imports the shell.

## Invariants that hold by construction rather than by a check
- Only valid `Weights` exist.
- Each request reads the current weights once.
- A reload assigns only after a complete load.
- A `FeedRequest` that exists is valid, including its ineligible candidates. So eligibility, a method of
  `FeedRequest`, can never run before validation.
- The run limit receives `Candidate`s, which carry no score, so it cannot read or change a score.

## Invariants held by convention, and guarded only by tests
Each of these silently breaks a product rule if violated. No type or import rule prevents it.
- **Weights are read once per request.** Adding a second read of `FeedService._weights` inside a request,
  or a mutator on `Weights`, breaks "one version per request". No test is guaranteed to catch it.
- **`ranking` reads candidates only through `FeedRequest.eligible_candidates()`.** Reading
  `request.candidates` there silently brings blocked and muted items back. It is guarded by the "blocked
  top-score item is absent" test on paths D, L and C.
- **`_limit_author_runs` uses only position and author.** Comparing ids or signals there would make it a
  second owner of rank order. It is guarded by the "each position = earliest placeable remaining item"
  property test.

## Deliberately not change axes
- The signal set, the formula, per-user weights (stage 1).
- The diversity key (author), the run limit 2, the set of eligibility rules, storing the lists (stage 2).

Each is a fixed shape, and the cost of changing it is accepted (DESIGN.md §2).

## Numeric traps that pass ordinary tests
- Use `copy_negate`, never unary minus, on scores.
- Do all score arithmetic and `normalize` in `EXACT`, never the ambient context.
- Never convert with `Decimal(float)` (DESIGN.md §6).
