---
title: "tiling.py"
date: 2026-08-13
hash: "sha256:240fa7b7c5e0969d1a7aeac69d9032c31760ed35ff85cdc655524294d4357a0f"
---
## Insights
- Pure geometry with no Pillow, filesystem, or HTTP dependency — the export path's testable core. Every
  edge the export must handle (straddling, fully-outside, overlap-duplication, remap correctness) is
  provable here in isolation (`tests/test_tiling.py`), without images or a server.
- Coordinates in and out are original-image pixel space (the store's persisted space); only `remap`
  moves a polygon into tile-local space, and only after clipping. This keeps the one place that changes
  coordinate frame explicit and testable.

## Decisions
- **Tiles step by `stride = tile_size - overlap`; the final tile on each axis is clamped flush to the
  image edge** so the grid always fully covers the image. Consequence: the last tile may overlap its
  neighbour by more than the requested overlap. Chosen over emitting a thin partial remainder tile,
  which would produce non-uniform tiny tiles at the edge. An image smaller than a tile on an axis yields
  one tile spanning that axis.
- **`overlap` must satisfy `0 <= overlap < tile_size`** (else tiles never advance) — enforced in
  `tile_boxes` defensively; the request-level owner is `export.ExportOptions`.
- **Polygon clipping is Sutherland–Hodgman against the tile rectangle** (a convex window), returning the
  intersection polygon. An object straddling an edge is cut at the edge; an object fully outside clips to
  `[]`; a result with < 3 vertices is treated as "not in this tile" (`[]`). This is why the same border
  object, under overlap, legitimately appears clipped in more than one tile.
- **Box convention is `(x0, y0, x1, y1)` with right/bottom exclusive** — the PIL crop convention — so a
  box passes straight to `images.crop_to_file` without translation.

## Discussions
- Sutherland–Hodgman on a rectangle can leave collinear/duplicate vertices along the cut edge; harmless
  for COCO polygons, so no post-simplification is done. A general polygon-polygon clipper (Weiler–Atherton)
  was unnecessary because the clip window is always an axis-aligned rectangle.
