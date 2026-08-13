# Pilot — instance-segmentation annotator (aims arm vs. clean arm, blind-judged)

A **build pilot** run under [`../PROTOCOL.md`](../PROTOCOL.md): a real, container-run product is built by two
arms across a staged evolution nobody is told about in advance, then judged **blind** by separate judges.
This is an experiment, not a demonstration — there is a control arm and an independent judge.

## The product & the axis
A local, single-user, container-run **multi-class instance-segmentation** annotator. The one architectural
axis its evolution stresses: **the seam between annotation geometry and how the image is presented/stored.**
Stage 2 (below) is exactly what a good seam must absorb without a tear-open.

## The staged reveal (neither arm sees Stage 2 while doing Stage 1)
- **Stage 1** ([`cards/stage-1.md`](cards/stage-1.md)) — a general annotator: load an image from a folder,
  draw polygon instances, label each with a configurable class, save/reload, step through images, run from
  a container. *No hint that anything else is coming.*
- **Stage 2** ([`cards/stage-2.md`](cards/stage-2.md)) — the evolution: large **satellite** images arrive;
  cut them into **overlapping tiles** and **export a training dataset** in a standard instance-seg format.

The hidden spec + oracle answers (used to answer product questions without leaking the future) are in
[`hidden/spec-and-oracle.md`](hidden/spec-and-oracle.md).

## The two arms (only variable = aims method + co-located records)
- **aims arm** ([`arms/aims-arm/`](arms/aims-arm/)) — built following the `aims-guide` skill; files
  co-located records. Its **Stage 2 is run by a fresh session** given the product + records + the Stage-2
  card, told to navigate the records to find the seam — *not* told where it is. (This is the Q2 test.)
- **clean arm** ([`arms/clean-arm/`](arms/clean-arm/)) — built by an equally capable agent told only "build
  it well", free to plan/refactor; no method, no records. Its Stage 2 is a fresh session given only the
  code.

Both arms share an identical substrate (Python/FastAPI + vanilla-canvas + Docker) and identical stage
cards + oracle answers. The extra reasoning the aims arm spends **is the treatment**; cost is recorded, not
equalized.

## What is judged (separately — never merged into one score)
- **Q1 — direction:** is the aims arm's **final architecture** better than the clean arm's, after the
  unstated evolution? Judged blind (anonymized X/Y) against
  [`../../skills/aims-guide/references/design-principles.md`](../../skills/aims-guide/references/design-principles.md)
  by **two opposite-disposition judges** (invariant-ownership vs. YAGNI). A verdict must turn on a
  structural property (can the annotation model be consumed by tiling without edits? is the export format
  one owner or scattered?), not a removable blemish; every load-bearing claim carries a reproduction or
  `file:line`.
- **Q2 — continuity:** did the aims arm's **fresh Stage-2 session** actually find and use the seam by
  navigating the records (vs. re-deriving / rewriting the model)?
- **Product** & **Cost** recorded separately.

See [`results.md`](results.md) for the readings and the honest limits.
</content>
