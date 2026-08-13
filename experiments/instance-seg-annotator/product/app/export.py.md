---
title: "export.py"
date: 2026-08-13
hash: "sha256:11f53314bebcb939e02122d1a95fd1e66bf75bf100195d386431b405a31105ef"
---

## Insights
- COCO's `segmentation` is a flat list of polygon vertices in **pixel** space — a direct match for our
  polygon instances (no normalization, no per-image side files that YOLO-seg needs), and it writes as a
  single deterministic `annotations.json`, mirroring the project's byte-stable JSON ethos (`storage.py`).
- `bbox` and `area` derive from the same clipped polygon, so no extra source of truth is introduced.

## Decisions
- The **single owner** of the export format *and* the tile raster crop + all output-folder I/O. Consumes
  `tiling.tile_all()` for geometry and Pillow for the crop; writes tile images + the COCO file.
  (system: `decisions/0004-coco-export-format.md`; confined choice: `dependencies.md`.)
- All COCO-specific detail is confined here: categories, `segmentation`/`bbox`/`area` shaping, the
  string-class-id → 1-based-integer category map, the JSON write. `tiling.py` and `model.py` know nothing
  of COCO. Swapping to YOLO-seg would touch only this file.
- Carries the thin CLI (`python -m app.export`).

## Discussions
- The tile raster crop (Pillow, I/O) lives here rather than in `tiling.py` so that tiling stays a pure
  geometry module and this stays the one I/O owner — one pure owner + one I/O owner, not two half-pure
  modules.
</content>
