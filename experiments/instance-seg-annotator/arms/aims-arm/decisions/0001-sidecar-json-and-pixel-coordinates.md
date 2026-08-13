---
title: "Sidecar JSON per image; polygons in original-image pixel coordinates"
date: 2026-08-13
status: accepted
---

## Context

Annotations must persist per image on a user-mounted folder and be restored exactly on reopen. Two
choices an ordinary user would not make had to be settled: **where/how annotations are stored** and
**what coordinate system polygon vertices use**.

## Decision

**Storage:** one JSON sidecar per image under a `.annotations/` subdirectory of the mounted data root,
named `<image-filename>.json`. Each record is `{image, width, height, objects}`, where each object is
`{class: str, polygon: [[x, y], ...]}`. Writes are atomic (temp file + `os.replace`). The class list is a
separate `classes.json` at the data root.

**Coordinates:** polygon vertices are stored in **original-image pixel space** (origin top-left, x right,
y down), as plain numbers — not display/canvas coordinates and not normalized `[0, 1]`.

## Rationale

- Per-image sidecars are human-readable, isolate each image (no monolithic index to corrupt or lock),
  and are trivially loaded on reopen by filename. A `.annotations/` dotdir keeps the user's own image
  folder visually uncluttered while staying inside the one folder they mounted.
- Pixel coordinates in the source image's own space are **lossless and display-independent**: window
  size, zoom, and canvas resolution never change stored values, and no reconstruction math runs on read.
  Normalized `[0,1]` was considered; rejected because it is harder to read/debug by hand and buys nothing
  here since the true image size is always known and stored alongside.
- The image's true dimensions are stored in the record (probed server-side via Pillow), so a polygon is
  always interpretable without opening the image, and a mismatch is detectable.

## Consequences

- The frontend must own the single display↔image transform (`canvas.js`) so only image-space coordinates
  ever leave the browser.
- Storage format is confined behind `app/store.Workspace`; replacing it touches one module.
- Deleting an image leaves an orphan sidecar; harmless and ignored (non-goal to garbage-collect).
