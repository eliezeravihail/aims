---
title: "Pilot plan — feature-based identification app (plants → minerals), aims vs OpenSpec"
date: 2026-09-17
---

# Pilot: feature-based identification (plants, then minerals) — aims vs OpenSpec

A build pilot under [`../PROTOCOL.md`](../PROTOCOL.md): two arms design the **same** product across two
staged reveals; the final architectures are judged **blind** on the single source
([`../../skills/aims-guide/references/design-principles.md`](../../skills/aims-guide/references/design-principles.md)
§0–§14) with the scoring layer in `references/measurement.md` and the fixed Step-0 inventory
([`inventory.md`](inventory.md)).

## The one axis it stresses

Adding a **second identifiable domain (minerals) with a feature schema disjoint from plants**, over an app
whose data is **ingested from an external source (Wikipedia)**. This is the change-absorption axis: does a
stage-1 design absorb the second domain as an **extension at a seam**, or does it **reopen** the
plant-specific core? It directly exercises §0 (module seams / published types / small parts), §4 (disjoint
feature modeling), §6/§7 (OCP + the schema/representation-evolution owner), and §1 (identification
correctness on partial input, no-match/many-match, and a numeric-range feature vs a categorical one).

## The two arms

| | aims arm | OpenSpec arm |
|---|---|---|
| Prompt | the stage card **+** "follow the `aims-guide` skill (§0–§14, design as the goal, one review-and-revise round)" | the stage card **+** "follow a spec-first (OpenSpec) discipline: write the requirements/spec, then derive the architecture from it" |
| Continuity | stage 2 run by a **fresh** builder given only the stage-1 design + card 2 | same — fresh builder, stage-1 design + card 2 |

(A no-method **plain** control may be added; the primary contest requested is aims vs OpenSpec.)

## Stages (frozen; stage 2 hidden during stage 1)

- [`cards/stage-1.md`](cards/stage-1.md) — identify ~500 Israeli plant species by observed features.
- [`cards/stage-2.md`](cards/stage-2.md) — also identify common minerals (disjoint features); don't break plants.

## Judging

One neutral, blind judge per the final designs (labels shuffled, method names stripped), scoring §0–§14 as
chapters (items = sub-checks), most-severe-first fix-list, per `measurement.md`. The **stage-2 reopen** and
the **numeric-range-feature correctness probe** are the load-bearing structural checks. n = 1; the value is
the reading, not a leaderboard.
