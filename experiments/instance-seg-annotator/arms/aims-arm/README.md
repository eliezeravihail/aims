# Instance Segmentation Annotator

A small, single-user tool to annotate a folder of images for instance segmentation. Open it in a
browser, draw a polygon outline around each object, give each object a class, save, and step through the
folder. Everything runs from a container pointed at a folder on your machine.

## Run

```bash
IMAGES_DIR=/path/to/your/images docker compose up
```

Then open <http://localhost:8000>. If `IMAGES_DIR` is unset, `./sample-images` is used.

Only PNG and JPEG images (directly in the folder) are shown. Your work is written **inside that same
folder**:

- `.annotations/<image>.json` — one sidecar per image (polygons in original-image pixel coordinates).
- `classes.json` — your editable class list (name + color).

## Use

- Pick a class from the class bar. Click on the image to place polygon vertices; press **Enter** (or
  double-click) to close the outline (needs ≥3 vertices). **Esc** cancels, **Backspace** removes the last
  vertex.
- Delete an object from the **Objects** sidebar.
- **Save** (or Ctrl/Cmd+S). Navigating with **‹ Prev / Next ›** (or ← / →) auto-saves first.
- **Edit classes** to add/rename/recolor/remove classes, then **Save classes**.

## Export a tiled training dataset

For large images (e.g. satellite scenes), **Export tiles** cuts every image into overlapping tiles and
writes a standard **COCO instance-segmentation** dataset a training pipeline can consume. Pick a tile
size (default 1024) and overlap (default 128); each annotation is clipped to each tile it lands in
(objects crossing a tile edge are cut sensibly, and overlap keeps a near-edge object in more than one
tile). The dataset is written **inside the mounted folder** at:

```
.exports/<name>/
  images/<image>__x{ox}_y{oy}.png   # one crop per tile
  annotations.json                   # COCO: images / annotations / categories
```

The endpoint is `POST /api/export` with `{"tile_size", "overlap", "name"}`. Full-image annotation is
unchanged; export never alters stored annotations.

## Develop / test

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
uvicorn app.main:app --reload    # ANNOTATOR_DATA_DIR=./sample-images uvicorn ...
```

## Layout

- `app/models.py` — domain models; the single owner of annotation validity.
- `app/store.py` — the Workspace store; single owner of the mounted folder, on-disk format, path safety.
- `app/images.py` — Pillow-confined image size probe + tile crop.
- `app/tiling.py` — pure tiling geometry: overlapping tile boxes, polygon clip + remap.
- `app/export.py` — the added export path; owns the COCO tiled-dataset format.
- `app/main.py` — FastAPI HTTP layer; wires routes to the store, serves the UI and raw images.
- `static/` — vanilla-JS frontend: `api.js` (URLs), `canvas.js` (display↔image transform + drawing),
  `app.js` (state + navigation).

Design records: `goals.md`, `architecture.md`, `base-dependencies.md`, `dependencies.md`, `decisions/`.
