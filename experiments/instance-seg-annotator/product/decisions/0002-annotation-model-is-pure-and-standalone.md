---
title: "0002 — the annotation model is a pure, standalone module"
date: 2026-08-13
status: accepted
---

## Context
The product will grow a Stage-2 tiling + dataset-export path. If the annotation model were entangled
with HTTP handlers, canvas code, or the on-disk format, that path could not be added without dragging in
(or rewriting) UI/transport concerns.

## Decision
`app/model.py` is the single owner of what an annotation *is* (instance, document, class list) plus its
validation and canonical serialization, and it imports **only the standard library**. It references
nothing about display, viewport, transport, tiling, or export. A consumer can
`from app.model import AnnotationDocument` in isolation (asserted in
`tests/test_model.py::test_model_imports_without_ui_or_http`).

`ClassDef.color` is kept in the model as **opaque project data** (a hex string the model never
interprets or draws), so the class list stays a single owner of the "is this class valid?" rule without
splitting its identity across a separate presentation module. Only the frontend reads the color to paint.

## Consequences
- Stage 2 plugs into `AnnotationDocument` as a pure addition — the seam is the model, not the app.
- The on-disk *format* is confined behind `app/storage.py` (see `dependencies.md`), swappable without
  touching the model.
</content>
