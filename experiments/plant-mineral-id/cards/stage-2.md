# Stage 2 — evolution card (revealed only after stage 1 is designed)

You are given an existing stage-1 design (below/attached) for the plant-identification app. Evolve it to
also do the following. **Do not rewrite the stage-1 design from scratch** — extend it, and keep the
plant-identification behaviour working exactly as before.

## The new requirement

The app must **also identify common minerals** from their own observed features. In scope: a handful of
common minerals — **quartz, chert (flint), shale, calcite, basalt**.

Minerals are identified by a **different set of features** than plants — for example:

- **Mohs hardness** (a number, often given as a range, e.g. 6.5–7)
- **lustre** (vitreous, dull, earthy, …)
- **colour** and **streak**
- **crystal habit / fracture** (conchoidal fracture, layered/fissile, massive, …)
- **locality** where found

The mineral feature set is **disjoint** from the plant feature set: hardness and streak mean nothing for a
plant; leaf shape means nothing for a mineral.

## Required behaviours

- Identifying a mineral works the way identifying a plant does: the user supplies the features they
  observed (partial input normal), and gets the **consistent minerals, ranked, with an explanation** —
  including no-match and many-match as distinct results, and numeric-range features (hardness) handled the
  same careful way as plant height.
- **Adding minerals must not change or break plant identification** — a plant query behaves exactly as it
  did in stage 1.
- Where the identification machinery is **genuinely shared** between the two domains (matching a set of
  observed features against candidates, ranking, explaining, reporting unknown values), it is **reused**,
  not copied.
- Assume a **third domain is foreseeable** (e.g. birds, by their own features) — the design should absorb it
  the same way, not by another rewrite.

*Build constraint (experiment):* as in stage 1, there is **no live external access** — mineral reference
data is a **small mock/fixture** behind the same ingestion seam. The exercise is the design, not a crawl.

## Deliverable

The evolved architecture and its concrete, typed interfaces, plus a short note on **what stage-1 code
changed and what stayed untouched**.
