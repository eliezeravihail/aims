---
title: "architecture"
date: 2026-08-13
---

## The shape

A local, container-run annotator. The browser paints an image on a canvas and lets the user draw polygon
instances; a FastAPI backend serves image bytes and reads/writes annotation JSON on a mounted volume.

## The load-bearing boundary — annotation geometry vs. image presentation/storage

The one seam the whole design is organized around: **annotations live in original-image pixel
coordinates and know nothing about how the image is displayed or delivered.** Presentation (zoom/pan)
and geometry (the annotation model) are separate pure modules:

- `app/coords.py` — the *only* owner of the image↔viewport transform. Pure, no I/O.
- `app/model.py` — the *only* owner of what an annotation *is* (instance = ordered image-pixel vertices +
  class id; document = image ref + size + instances) and its validation. Stdlib-only; imports nothing
  about display, viewport, HTTP, tiling, or export.

The rule that makes the boundary real: **every pointer sample passes through
`coords.viewport_to_image()` before it can become a vertex**, so nothing downstream of that call ever
holds a screen coordinate. `ViewportTransform` is immutable, so a transform can never be edited under
stored geometry. Saved coordinates are therefore zoom/pan-invariant *structurally*, not by convention —
asserted in `tests/test_coords.py`.

## Owners (one concern each)

| Module | Owns |
|---|---|
| `app/coords.py` | image↔viewport math (pure) |
| `app/model.py` | annotation data model + validation + canonical (de)serialization (pure) |
| `app/storage.py` | annotation JSON read/write on disk (the confined on-disk *format* seam) |
| `app/images.py` | which images exist + their pixel dimensions |
| `app/config.py` | runtime mount paths + loading the project class list |
| `app/main.py` | HTTP transport only — wires pure modules to disk and browser, holds no annotation logic |
| `app/static/coords.js` | frontend transform (a faithful mirror of `coords.py`) |
| `app/static/app.js` | canvas rendering + pointer interaction only |
| `app/tiling.py` (Stage 2) | tile geometry — overlapping-grid layout, coordinate remap, polygon clipping (pure) |
| `app/export.py` (Stage 2) | export-format owner — tile raster crop + COCO dataset write (the confined format + I/O) |

## The change axis this is built for

The product *evolves* toward large satellite images cut into overlapping tiles + dataset export
(Stage 2). That work is a raster/coordinate operation over the **same image-pixel space** the
annotations already live in, and the on-disk format is confined behind `storage.py`. So Stage 2 is
designed to be a **pure addition**: a new module does `from app.model import AnnotationDocument`, reads
instance geometry in image space, tiles/clips/exports — touching neither the annotation model nor the
UI. The seam it plugs into is `AnnotationDocument`.

**Stage 2 landed exactly this way.** `app/tiling.py` + `app/export.py` were added; `model.py`,
`coords.py`, and the UI were byte-untouched (empty tracked diff). A tile's result *is itself* an
`AnnotationDocument` (image + instances in that tile's pixel space), so no parallel geometry type was
introduced. Export is COCO instance segmentation, confined to `export.py` (`decisions/0004`).
</content>
