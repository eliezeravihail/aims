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
- **Dataset export format (Stage 2, forthcoming) — will be a confined choice** behind its own module
  (e.g. COCO / YOLO-seg). It reads `AnnotationDocument` and writes the chosen format; swapping formats
  touches only that module.
</content>
