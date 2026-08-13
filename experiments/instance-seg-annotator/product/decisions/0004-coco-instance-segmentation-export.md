---
title: "0004 — tiled export uses COCO instance segmentation, confined to export.py"
date: 2026-08-13
status: accepted
---

## Context
Stage 2 exports a training dataset from large satellite images cut into overlapping tiles. A standard
instance-segmentation format is needed. Candidates: COCO instance segmentation and YOLO-seg.

## Decision
Export **COCO instance segmentation**. Its `segmentation` field is a flat list of polygon vertices in
pixel space — a direct match for our polygon instances, with no normalization and no per-image side
files (which YOLO-seg requires). It writes as a single deterministic `annotations.json`, consistent with
the project's byte-stable JSON persistence (`storage.py`). The format is a **confined choice**: every
COCO-specific detail lives only in `app/export.py`; `app/tiling.py` and `app/model.py` are format-blind.

## Consequences
- Tiling stays a pure geometry module (`tiling.py`); export owns the format + the raster crop + I/O.
- Swapping to YOLO-seg (or adding it) touches only `export.py`.
- This realizes the Stage-2 plan recorded in `dependencies.md` ("Dataset export format … a confined
  choice behind its own module").
</content>
