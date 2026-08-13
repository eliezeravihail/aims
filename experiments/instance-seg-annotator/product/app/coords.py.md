---
title: "coords.py"
date: 2026-08-13
hash: "sha256:975d01bb86f269ca028dbd0ebc65cf71e413ab92c17b800d8176668b1f5453eb"
---

## Insights
- The zoom/pan-invariance of saved annotations is **structural, not incidental**: because persisted
  geometry is whatever the caller holds in image space, and a transform only affects the round-trip used
  to read pointer input and paint, a transform change *cannot* mutate a stored coordinate. Verified in
  `tests/test_coords.py` (`test_stored_document_coords_invariant_to_viewport`,
  `test_pointer_input_lands_in_image_space`).

## Decisions
- This is the **single owner** of image↔viewport math; pure, no I/O, no framework imports. (system:
  `decisions/0001-annotations-in-image-pixel-space.md`)
- `ViewportTransform` is **immutable** — `zoomed()`/`panned()` return new instances — so a transform can
  never be edited in place under stored geometry.
- The transform is uniform scale + translation only. **No rotation/shear**: an instance-seg annotator
  pans and zooms, it does not rotate the canvas. If rotation is ever needed, it is a new decision here.
- `viewport_to_image()` is the **single funnel** every pointer sample must pass through before becoming a
  vertex. Do not add a second path from screen coordinates to geometry.

## Discussions
- A build step could let one file serve both Python and the browser; rejected (base-deps forbid a
  frontend build). `app/static/coords.js` mirrors this file instead — this file stays authoritative and
  tested. See `decisions/0003-frontend-mirrors-coords-no-build-step.md`.
</content>
