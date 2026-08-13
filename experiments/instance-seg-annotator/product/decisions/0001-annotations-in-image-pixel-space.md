---
title: "0001 — annotations are defined and persisted in original-image pixel space"
date: 2026-08-13
status: accepted
---

## Context
An instance-segmentation annotator zooms and pans. If annotation geometry were stored in viewport
(screen) coordinates, every zoom/pan would corrupt the meaning of the data, and a later consumer
(tiling, dataset export) would have to reverse-engineer the display transform to recover true pixels.

## Decision
All annotation vertices are stored in **original-image pixel coordinates**. The viewport transform
(`app/coords.py`) exists only to interpret pointer input and to paint. `coords.viewport_to_image()` is
the single funnel every pointer sample passes through before it becomes a vertex; `ViewportTransform` is
immutable. The annotation model (`app/model.py`) contains no reference to a viewport, scale, or canvas.

## Consequences
- Saved coordinates are zoom/pan-invariant by construction (asserted in `tests/test_coords.py`).
- A Stage-2 tiling/export consumer reads geometry directly in image space — no display knowledge needed.
- The frontend must carry a faithful mirror of the transform math (`app/static/coords.js`); see 0003.
</content>
