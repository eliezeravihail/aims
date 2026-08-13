# Instance Segmentation Annotator (Stage 1)

A local, single-user web tool for **multi-class instance-segmentation** annotation.
Load an image, draw polygon instances, assign each a class, and save the
annotations to disk as JSON. Runs from a container.

## Run it

```bash
# 1. Put images in the input folder, create the output folder:
mkdir -p data/images data/annotations
cp /path/to/your/*.png data/images/

# 2. Build and serve:
docker compose up --build

# 3. Open the app:
#    http://localhost:8000
```

### Where things mount

| Purpose            | Host folder (edit in `docker-compose.yml`) | Container path        |
|--------------------|--------------------------------------------|-----------------------|
| Input images       | `./data/images` (read-only)                | `/data/images`        |
| Annotation output  | `./data/annotations`                       | `/data/annotations`   |
| Class list (opt.)  | your JSON file                             | `/srv/app/classes.default.json` |

Annotations are written one JSON file per image, keyed by the image's filename
stem: `data/images/scene_01.png` → `data/annotations/scene_01.json`.

### Classes

The project class list (name + color per class) is a JSON file. The built-in
default is `app/classes.default.json`. Override it by mounting your own file over
that path, or by setting `CLASSES_FILE`.

## Using the canvas

- **Left-click**: add a polygon vertex.
- **Enter** or **Finish polygon** / **double-click**: close the current polygon
  (needs ≥ 3 vertices) and add it as an instance with the selected class.
- **Esc** or **Cancel**: discard the in-progress polygon.
- **Middle-drag**: pan. **Wheel**: zoom. **Fit**: reset the view.
- Sidebar lists instances; click to select, ✕ to delete.
- **Save**: persists to disk. **‹ / ›**: step between images. Reloading restores.

Zoom and pan are display-only: annotations are always stored in original-image
pixels, never in screen coordinates.

## Design: the annotation ↔ presentation boundary

Two pure, I/O-free modules form the seam a later Stage 2 (tiling + dataset
export) plugs into without a rewrite:

- **`app/model.py`** — the annotation data model. An *instance* is ordered
  image-pixel vertices + a class id; a *document* is image ref + size +
  instances. It imports only the standard library — no display, transport,
  tiling, or export. A Stage-2 module can `from app.model import
  AnnotationDocument` and read instance geometry in isolation.
- **`app/coords.py`** — the only place that maps between image space and the
  viewport (zoom/pan). `viewport_to_image()` is the funnel every pointer sample
  passes through before becoming a vertex, so stored coordinates are always in
  image pixels and are invariant to zoom/pan.

Everything else is an owner of exactly one concern: `storage.py` (JSON on disk),
`images.py` (list images / read sizes), `config.py` (mounts + class list),
`main.py` (HTTP transport), and the frontend (`static/`, rendering + input).

## Stage 2: export a tiled training dataset

Large source images (e.g. satellite scenes) can be cut into **overlapping tiles**
and exported as a **COCO instance-segmentation** dataset. Annotations are remapped
into each tile's local pixel space and polygons are clipped to the tile bounds (an
instance straddling a border is clipped; one fully outside a tile is dropped; with
overlap, a border instance can appear in more than one tile).

```bash
# tile size + overlap are in source-image pixels
python -m app.export sat.png ./dataset --tile-size 512 --overlap 64
```

This writes a dataset folder:

```
dataset/
  images/<tile>.png     one PNG crop per tile
  annotations.json      COCO (images, annotations, categories)
```

By default it reads the source image from the input dir and its annotations from
the annotations dir (same mounts as the app); override with `--input-dir` /
`--annotations-dir`. Tiles with no instances still export as valid images with
zero annotations. Tiling geometry lives in `app/tiling.py` (pure); the COCO format
is confined to `app/export.py` — swapping formats touches only that module.

## Tests

```bash
pip install -r requirements.txt
pytest                # from this directory
```

`tests/test_coords.py` proves the zoom/pan invariance; `tests/test_model.py`
proves validation and Stage-2 import isolation; `tests/test_storage.py` proves
byte-stable idempotent saves; `tests/test_api.py` exercises the full HTTP stack.
