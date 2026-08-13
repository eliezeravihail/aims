---
title: "models.py"
date: 2026-08-13
hash: "sha256:af32fd73b7d60546fd433cc46d0ac3577f3f41dc54639ae065c192bdef4b6f9b"
---
## Insights
- These pydantic models are the single owner of "what is a valid annotation". Because the same models are
  the HTTP request bodies, validity is enforced at the boundary for free (a bad PUT is 422 before any code
  in `store.py` runs).

## Decisions
- **A polygon needs ≥3 finite vertices; a class name must be non-empty** — enforced by `field_validator`s
  here, not in the store or the HTTP layer (guarded by `test_models`, `test_api`).
- **The JSON/on-disk key is `class`; the Python attribute is `cls`** via `Field(alias="class")` with
  `populate_by_name=True` (so internal construction by name still works). `class` is a Python keyword and
  cannot be an attribute name.
- **`AnnotationWrite` (objects only) is the write payload**, separate from `Annotation`, so a client cannot
  set the image dimensions — those are the server's to probe (goals.md: authoritative dims).
- **`*_stored` / `from_stored` own the model↔disk shape** (compact `[[x,y]]`), keeping the persisted format
  independent of the model's field layout.

## Discussions
- `Point` as a model (vs a bare `[x,y]` list) was kept because it carries the finite-coordinate invariant;
  storing NaN/inf would corrupt rendering and JSON. The extra type earns its place via that guard.
