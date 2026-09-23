---
title: "architecture"
date: 2026-09-23
---
The stage-1 architecture is specified in full in [DESIGN.md](DESIGN.md), which is authoritative until
the code exists. The rationale and the per-axis harvest are in
[decisions/0001](decisions/0001-stage1-architecture.md). This record keeps only what the code will not
say about itself.

- **Boundary.** A pure core (`numbers`, `signals`, `weights`, `request`, `ranking`) sits inside a thin
  shell (`service`, `config_file`, `cli`). The core never imports the shell.
- **Invariants that hold by construction rather than by a check:**
  - only valid `Weights` exist;
  - each request reads the current weights once;
  - a reload assigns only after a complete load.

  Adding a second read of `FeedService._weights` inside a request, or a mutator on `Weights`, silently
  breaks "one version per request". No test is guaranteed to catch it.
- **Deliberately not change axes in stage 1:** the signal set, the formula, per-user weights. Each is a
  fixed shape, and the cost of changing it is accepted (DESIGN.md §2).
- **Numeric traps that pass ordinary tests.** Use `copy_negate`, never unary minus, on scores. Do all
  score arithmetic and `normalize` in `EXACT`, never the ambient context. Never convert with
  `Decimal(float)` (DESIGN.md §6).
