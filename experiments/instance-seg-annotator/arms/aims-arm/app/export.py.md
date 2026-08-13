---
title: "export.py"
date: 2026-08-13
hash: "sha256:fa0123decba9d13bc67f7a0a09f0cb8fdff84af591d825a5e37d3915641158b8"
---
## Insights
- The single owner of the added export path: it composes three existing seams — `tiling` (geometry),
  `images.crop_to_file` (Pillow-confined pixel crop), `store.Workspace` (image discovery, bytes,
  annotations, path-safe destination) — and owns only the glue plus the on-disk *dataset* shape.
- The annotation domain model (`models.py`) is untouched: export *reads* `Annotation`/`AnnotationObject`
  and needs no new field or rule there. Its own request/response types (`ExportOptions`/`ExportSummary`)
  live here because they are the export concern, not annotation validity.

## Decisions
- **Format is COCO instance segmentation, and `_build_coco` is its one locus.** Chosen because it is the
  de-facto standard consumed directly by segmentation training pipelines (Detectron2, MMDetection, …):
  a single `annotations.json` (`images` / `annotations` / `categories`) plus an `images/` folder of tile
  crops. Swapping to another format (e.g. YOLO-seg) touches only `_build_coco` and the write. See
  `decisions/0002`.
- **Every tile is emitted, including tiles with no objects** — valid empty COCO images. Required for full
  image coverage and useful as background samples; also the "empty tile exports validly" edge.
- **A clipped object becomes one COCO annotation per tile it lands in.** `segmentation` is the remapped
  tile-local polygon (flat `[x,y,...]`), `bbox`/`area` computed from it (`tiling.polygon_bbox/area`),
  `iscrowd=0`. Overlap therefore duplicates a border object across neighbouring tiles by design.
- **Categories come from the class config, and an unknown class is appended on first sight** — mirrors
  the product rule that class-list membership is not an annotation-validity rule (goals.md): an object
  whose class is not configured still gets a category id.
- **The destination directory is obtained from `store.export_dir(name)`** (path safety stays the store's
  job); the *layout inside* it (`images/`, `annotations.json`) is this module's. All images across all
  source images share one dataset.

## Discussions
- Tile filenames encode the source stem and origin (`<stem>__x{ox}_y{oy}.<ext>`) so a tile is traceable
  back to its image and position; ids in the COCO doc are plain 1-based counters.
- Export writes `annotations.json` directly (not through the store's private atomic-writer) — a derived
  artifact in a store-sandboxed directory, not part of the mounted annotation workspace. See the design
  tension noted in `architecture.md` (export destination ownership).
