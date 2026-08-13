---
title: "tiling.py"
date: 2026-08-13
hash: "sha256:af4fe04c0627ae8a842fafa68046eccf28cbdce1fd46482548d1c902fc3263d8"
---

## Insights
- Reusing `AnnotationDocument` as the **per-tile representation** (a tile *is* an image + instances in
  that tile's pixel space) avoided inventing a parallel "tile annotations" type — so tiling plugged into
  the Stage-1 seam with no new geometry type and no model change (`git diff` on the model was empty).
- Polygon clipping to the tile rectangle is **Sutherland–Hodgman** (four half-plane passes). Results with
  < 3 vertices or ~zero area (border slivers) are dropped, which gives the three required behaviors for
  free: fully-outside → no instance, fully-inside → copied, straddling → clipped.

## Decisions
- The **single owner** of tile geometry: overlapping-grid layout, coordinate remap to tile-local pixels,
  and polygon clipping. **Pure — no I/O** (the raster crop lives in `export.py`; see its Discussions).
  Imports only stdlib + `app.model`.
- Tile layout: square `tile_size`, `stride = tile_size − overlap`; the final origin is anchored to the
  far edge (`extent − tile`) so the whole image is covered; tiles are clamped inside the image; an image
  smaller than a tile yields one tile of the image's size. `overlap ≥ tile_size` is rejected.
- Remap contract: tile-local `(x,y) = (image_x − x0, image_y − y0)`, so image-space `(x0,y0)` → local
  `(0,0)`.

## Discussions
- The raster crop is conceptually "tiling" but is I/O; keeping the geometry pure meant the crop belongs
  to `export.py` (the I/O owner) while this module computes only tile *placement* + clipped geometry.
</content>
