---
title: "dependencies"
date: 2026-08-13
---

## Confined, replaceable choices (behind seams)

Distinct from the pervasive `base-dependencies.md` substrate — each of these is owned by one module and
meant to be swappable without reaching across the codebase.

- **On-disk annotation format — JSON, owned by `app/storage.py`.** One annotation document per source
  image, serialized by `model.to_dict()` with sorted keys for byte-stable output. Confined: the model
  defines the *shape*; storage owns *how it lands on disk*. A different container format (e.g. one combined
  file, or a database) would change only `storage.py`.
- **Default class list — `app/classes.default.json`, loaded by `app/config.py`.** Project data, not code;
  replaced per project via the mounted config. name + color + id per class.
- **Dataset export format (Stage 2) — COCO instance segmentation, owned by `app/export.py`.** It reads
  `AnnotationDocument` (per tile) and writes the tile images + a single `annotations.json`. All
  COCO-specific detail is confined to `export.py`; swapping to YOLO-seg touches only that module.
  (system: `decisions/0004-coco-instance-segmentation-export.md`.)
</content>
