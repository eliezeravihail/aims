---
title: "BP13 — measure DESIGN QUALITY, not test-pass: do green-but-rigid builds break under a surprise change?"
date: 2026-09-21
status: pre-registered before the surprise change ran
---

# The correction this experiment makes

The campaign's "correctness ties" were measured by hidden pytest — which is a **floor, not the target**. A
capable model makes the tests pass with *any* design, good or bad; passing tests says nothing about whether the
design is correct, flexible, and good. aims' whole purpose is the design quality that tests don't see. BP13
measures **that** directly.

# The setup that isolates design quality from test-pass

Take **4 builds that all already PASS the floor tests (12/12 stage-1)** but are **badly designed** — the
type-switch / anemic-rules builds from BP7/BP9 (`isinstance` dispatch in the engine; the aims review already
flagged all four as structurally rigid in BP9, S3). By the test metric they are indistinguishable from a good
design. The question: is the review's design-quality verdict *real*?

**Test it with a surprise change the builds never anticipated:** add the stacking policy (priority +
exclusivity) — the same change BP7's *polymorphic* opus arms absorbed by **extending at a seam (0 reopens)**.
Apply it to each type-switch build with a strong model (opus), so any rewrite is forced by the **design**, not
model weakness.

# Metrics — all design-quality, none is "did tests pass"

- **reopened-owner:** did `Engine.total` / the dispatch get **rewritten** (the type-switch forced restructuring)
  or **extended at a seam** (per-rule logic untouched)? Measured from the stage-1→after diff (snapshots).
- **floor regression (gate only, not the outcome):** the change must not break the 12 stage-1 tests, and must
  satisfy the 7 stage-2 tests — so the comparison is design-shape at equal correctness.
- **blind structural read:** the diff shape (rewrite vs seam-extension) read off the code.

# Pre-registered prediction

The type-switch design has **no per-rule seam**: discount logic lives inside the engine's `isinstance` branches,
so threading priority + exclusivity means **restructuring the dispatch loop** — a reopen — even for opus. So:
- type-switch builds (BP13): **reopen** `Engine.total` (≥3/4 expected).
- polymorphic builds (BP7 opus arms, control): **extended at a seam, 0 reopens** (already observed).

If so, the result is decisive: **all builds were equal on tests, but the review's design verdict predicted which
absorb change cleanly and which must be rewritten** — i.e., aims measures a real design-quality difference that
functional tests are blind to. If the type-switch builds *also* extend cleanly, the review over-flagged and the
design difference is cosmetic (recorded honestly). n=4; nulls recorded as nulls.
