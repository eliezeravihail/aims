---
title: "model.py"
date: 2026-08-13
hash: "sha256:df8c960c7f253bd85056171bc7700a61aa2c6fefb2406f11df47692bda1c7121"
---

## Insights
- Keeping this module stdlib-only and standalone is what makes Stage 2 a pure addition: a tiling/export
  consumer does `from app.model import AnnotationDocument` and reads instance geometry in image space
  with no UI/HTTP in the loop (`tests/test_model.py::test_model_imports_without_ui_or_http`).
- Hand-rolled `to_dict`/`from_dict` (plain builtins) rather than a serialization library — so the on-disk
  shape is owned here and stays byte-stable regardless of any third-party version.

## Decisions
- The **single owner** of what an annotation is (instance / document / class list) + validation +
  canonical serialization. Imports only the stdlib; references nothing about display, viewport, HTTP,
  tiling, or export. (system: `decisions/0002-annotation-model-is-pure-and-standalone.md`)
- All vertices are in **original-image pixels** (contract, not a display artifact).
- Validation rules (append-only intent): polygon needs **≥ 3 vertices**; vertices must be finite; class
  id must be in the project `ClassList`; a document with **zero instances is valid**; image size must be
  positive.
- `ClassDef.color` is **opaque project data** (a hex string), stored but never interpreted or drawn here.
  This keeps the class list a single owner of validity without splitting its identity into a separate
  presentation module; only the frontend reads the color.

## Discussions
- Colors are inherently presentation, yet the class list (with colors) is also the validation authority.
  Splitting colors out would have fractured the class list across two owners and duplicated its identity.
  Resolved by treating color as *data the model carries but never acts on*, rather than display *logic*.
</content>
