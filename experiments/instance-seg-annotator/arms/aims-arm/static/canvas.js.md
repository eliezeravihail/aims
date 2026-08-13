---
title: "canvas.js"
date: 2026-08-13
hash: "sha256:c1f5b0ec3c220d42fd1713b30c112392d892a4d39c9339532bbde6ce1ab56cbd"
---
## Insights
- This module is the **single owner of the display↔image coordinate transform**. `_toImage` /`_toCanvas`
  and the `_scale`/`_ox`/`_oy` letterbox fit are all here, so nothing that leaves this module (into `app.js`
  or the server) is ever in canvas/display pixels — polygons are always image-space (architecture.md
  invariant; decisions/0001).

## Decisions
- **Coordinates are clamped to `[0,imgW]×[0,imgH]` and rounded on input** (`_toImage`), so a click just
  outside the letterboxed image still yields an in-bounds integer vertex.
- **The image is fit with letterboxing** (`min` scale, centered) rather than stretched, so aspect ratio is
  preserved and the transform is uniform in x and y (a single `_scale`).
- **Selection/deletion of finished objects is NOT here** — it lives in the sidebar (`app.js`). This module
  only draws and builds the in-progress polygon, keeping it focused on rendering + the transform.

## Discussions
- Point-in-polygon hit-testing on the canvas was considered for click-to-select and deliberately cut: the
  sidebar list makes deletion unambiguous and removes a whole interaction mode from the canvas.
