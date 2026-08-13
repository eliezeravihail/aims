---
title: "main.py"
date: 2026-08-13
hash: "sha256:d3ac39b4adc15c6ceb0718be605e464f5c884e4a3d0982dcfd5fd64bdf309f4d"
---
## Decisions
- **HTTP layer holds no filesystem/format knowledge** — it only translates HTTP to `Workspace`/`export`
  calls and maps `ImageNotFound` → 404, `BadExportName` → 422. Validation 422s otherwise come from the
  pydantic models (`AnnotationWrite`, `ExportOptions`), not from code here.
- **`POST /api/export`** takes an `ExportOptions` body and delegates to `export.export_dataset(ws, ...)`;
  the tiling, clipping, and COCO format all live behind that one call, so this route stays a thin wire.
- **`create_app(data_root)` is a factory**; the module-level `app` reads `ANNOTATOR_DATA_DIR` (default
  `/data`, the container mount). The factory is what makes the API tests run against a `tmp_path` root.
- **Static UI is mounted at `/` last**, after the `/api/*` routes, so API routes take precedence and the
  SPA/static files are the fallback.

## Discussions
- Raw image bytes are served with `FileResponse(ws.image_path(id))` rather than re-encoding through Pillow —
  the store's path-safety gate is the only thing between the client id and the file, and no decode is needed.
