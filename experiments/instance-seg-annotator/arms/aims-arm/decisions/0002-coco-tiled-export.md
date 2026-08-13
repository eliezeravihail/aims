---
title: "Tiled dataset export in COCO instance-segmentation format"
date: 2026-08-13
status: accepted
---

## Context

Source imagery is now very large satellite images (thousands of px per side) — too big to annotate or
train on whole. The tool must cut a source image and its annotations into smaller tiles that **overlap**
by a configurable amount (so objects near a tile edge are not lost) and export a folder a segmentation
training pipeline can consume. This is an **added export path**; full-image annotation still works
exactly as before. Two choices an ordinary user would not make had to be settled: the **export format**
and how an object **crossing a tile boundary** is handled.

## Decision

**Format: COCO instance segmentation.** One dataset directory per export, under a store-sandboxed
`<data-root>/.exports/<name>/`:

```
.exports/<name>/
  images/<stem>__x{ox}_y{oy}.<ext>   # one crop per tile
  annotations.json                    # COCO: images / annotations / categories
```

Each tile is a COCO `image`; each object clipped into a tile is a COCO `annotation` with a polygon
`segmentation` (flat `[x,y,...]` in tile-local pixels), `bbox`, `area`, `iscrowd=0`; categories come
from the class config (unknown classes appended on sight).

**Tiling:** tiles of a configurable `tile_size` (default 1024) step by `stride = tile_size - overlap`
(default overlap 128); the last tile on each axis is clamped flush to the image edge for full coverage.

**Boundary handling:** each object polygon is clipped (Sutherland–Hodgman) to each tile rectangle and
remapped to tile-local coordinates. An object straddling an edge is cut at the edge and kept for that
tile; because tiles overlap, a border object legitimately appears (clipped) in more than one tile; an
object fully outside a tile is absent from it. Tiles with no objects are still exported (valid empty
COCO images).

## Rationale

- **COCO** is the de-facto standard for instance-segmentation training (Detectron2, MMDetection, etc.):
  a single self-describing `annotations.json` plus an image folder, readable off the shelf. YOLO-seg
  (per-image txt, normalized coords) was considered; rejected as less self-describing and less directly
  a "dataset folder" for segmentation. The format is confined to `export._build_coco`, so a later YOLO
  target changes one function.
- **Clipping at the tile edge** yields a valid, trainable polygon per tile with no object silently lost;
  **overlap** is exactly what lets a near-edge object survive whole in a neighbouring tile. Clamping the
  final tile avoids thin degenerate remainder tiles while guaranteeing every pixel is covered.
- Coordinates are remapped into tile-local pixel space only at export time; the stored annotations remain
  full-image pixel space (decisions/0001), so the annotator is unchanged.

## Consequences

- Pillow gains one confined use — cropping a tile to a file (`images.crop_to_file`) — still behind the
  single image seam.
- The export writes a derived artifact into a directory the store sandboxes (`Workspace.export_dir`); the
  store keeps ownership of path safety, the export module owns the dataset layout/format. This is a
  deliberate refinement of "the store is the only thing that touches the filesystem": it owns the mounted
  *annotation workspace*; exports are a separate output tree.
- `models.py` (annotation validity) is untouched; export reads the existing models and defines its own
  `ExportOptions`/`ExportSummary`.
- Orphan exports are never garbage-collected (same stance as orphan sidecars); re-exporting a name
  overwrites files in place.
