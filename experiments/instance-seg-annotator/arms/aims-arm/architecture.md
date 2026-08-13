# Architecture

## Boundaries & seams

Three server responsibilities, one clear seam between them, and a thin frontend that never sees disk.

- **HTTP layer** (`app/main.py`) — owns routing, request/response, and serving static assets + raw image
  bytes. It holds no filesystem or format knowledge; it translates HTTP to store calls and back. Domain
  objects crossing in/out are the pydantic models (`app/models.py`).

- **Workspace store** (`app/store.py`) — the **single owner of the mounted annotation workspace** and of
  **path safety**: the on-disk annotation format, the class-config file, image discovery, mapping a
  client image id to a real file strictly inside the data root (rejecting traversal / absolute / nested
  ids), and sandboxing an export destination directory. The seam is the `Workspace` object's methods
  (`list_images`, `read_annotation`, `write_annotation`, `read_classes`, `write_classes`, `image_path`,
  `export_dir`); the payloads are pydantic models and plain filenames — never disk paths.

- **Image pixels** (`app/images.py`) — the only place Pillow is called: `probe_size(path) -> (w, h)` and
  `crop_to_file(src, box, dest)`. Confines the image library to one module so the rest of the app depends
  on a size and a crop-to-file operation, not on Pillow.

- **Tiling geometry** (`app/tiling.py`) — pure geometry, the single owner of how a large image is cut
  into overlapping tiles (`tile_boxes`) and how a polygon is clipped to a tile and remapped into
  tile-local space (`clip_polygon` / `remap`, plus `polygon_bbox`/`polygon_area`). No Pillow, filesystem,
  or HTTP; the export path's testable core.

- **Dataset export** (`app/export.py`) — the single owner of the **added export path**: composes tiling +
  `images.crop_to_file` + the store to write a tiled COCO instance-segmentation dataset into
  `export_dir`. Owns the COCO format (`_build_coco`) and its own `ExportOptions`/`ExportSummary`; reads
  the existing annotation models without changing them. See `decisions/0002-coco-tiled-export.md`.

- **Frontend** (`static/`) — split by concern: `api.js` (fetch client, the only place URLs live),
  `canvas.js` (**single owner of the display↔image coordinate transform** and all polygon drawing/
  rendering), `app.js` (in-memory state, image navigation, class selection, wiring). The frontend
  addresses images only by filename id; it never constructs or sees a filesystem path.

## Key structural decisions

- **Coordinates are stored in original-image pixel space** as integer-ish `[x, y]` vertex lists — not
  canvas/display coordinates and not normalized `[0,1]`. Rationale: it is lossless, independent of the
  browser window / zoom / canvas size, directly meaningful for debugging, and needs no reconstruction
  math on read. The display↔image transform lives entirely in `canvas.js` (one owner), so what reaches
  the store is always image-space. See `decisions/0001-sidecar-json-and-pixel-coordinates.md`.

- **One sidecar JSON per image, in a `.annotations/` subdir of the data root**, keyed by image filename
  (`photo.jpg` → `.annotations/photo.jpg.json`). Rationale: human-readable, per-image isolation (no big
  index to corrupt), trivially restored on reopen; the dotdir keeps the user's image folder visually
  clean. Writes are atomic (temp file + `os.replace`). See the ADR above.

- **The class list is one `classes.json` at the data root**, editable both by hand and via the UI. It is
  configuration, not annotation, so it lives beside the images at the top level (not in `.annotations/`).

- **pydantic models are the one domain shape** shared across the HTTP seam and the store's
  serialization, so "what is a valid annotation" has a single owner (`app/models.py`): a polygon needs
  ≥3 finite vertices; an object needs a non-empty class name. The store enforces *where/how* to persist;
  the models enforce *what is valid*.

## Invariants

- **Path safety**: every filesystem access derived from a client-supplied name resolves inside the data
  root or is rejected. Single owner: `Workspace.image_path` (image ids) and `Workspace.export_dir`
  (export names). Guarded by `tests/test_store.py` and `tests/test_export.py` (traversal, absolute,
  nested, missing / dotfile names).
- **Coordinates persisted are image-space.** Enforced on the client by `canvas.js` owning the transform;
  validated server-side against probed dimensions being present in the stored record.
- **Annotation validity has one owner** (`app/models.py`), applied at the HTTP boundary on write.
- **Atomic writes**: an annotation/class file is never left half-written (temp + `os.replace`).

## Likely change axes

- **Storage format** (sidecar JSON → other) is confined behind `Workspace`; the ADR records the current
  choice so a replacement has a single locus.
- **Image library** (Pillow) is confined behind `app/images.py`.
- **Export format** (COCO → e.g. YOLO-seg) is confined behind `app/export.py` (`_build_coco`); the tiling
  geometry it stands on is independent (`app/tiling.py`). See `decisions/0002`.

## Design tension: export destination ownership

The store is stated as the sole thing that touches the filesystem for the mounted workspace. The export
writes a *derived* dataset (tile images + `annotations.json`). Resolution: the store keeps ownership of
**path safety** — it validates and creates the destination via `export_dir(name)` — while the **export
module owns the layout and format inside** that sandboxed directory. So the invariant that matters (no
write escapes the data root) stays single-owner in the store, and the new concern (dataset shape) has its
own owner, rather than smearing COCO knowledge into the store.

## Confined dependencies

- **Pillow** — confined to `app/images.py` (`probe_size` reads dimensions; `crop_to_file` crops a tile to
  a file). Replaceable there without touching the store, export, or HTTP layer.
