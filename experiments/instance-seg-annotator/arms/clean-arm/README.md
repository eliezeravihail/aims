# Instance Segmentation Annotator

A small, local, browser-based tool for outlining objects in your images and
labelling each one with a class. Everything runs in a container and reads/writes
a folder of images on your own disk — no accounts, no cloud, no build step.

## Run it

Point the tool at the folder that holds your PNG/JPEG images:

```bash
IMAGES_DIR=/path/to/my/images docker compose up
```

Then open <http://localhost:8000> in a browser.

If you omit `IMAGES_DIR`, it uses `./data` next to this file.

## Using it

- The left panel lists every image in the folder. Click one, or step with the
  **Prev / Next** buttons (or the `[` and `]` keys).
- **Draw an object:** click on the image to drop polygon points around it. Click
  the first point again (or press `Enter`) to close the shape. `Esc` cancels;
  `Backspace` removes the last point.
- The new shape takes the **active class** (highlighted in the *Classes* panel).
  Click a class to make it active.
- **Classes** are editable: rename them, pick a colour, add or remove them. The
  list is saved to your folder and reused next time.
- Adjust a shape by selecting it and dragging its vertices. Delete the selected
  shape with the `Delete` key or the × in the *Objects* list. Change a shape's
  class from the dropdown in that list.
- **Zoom** with the mouse wheel, **pan** by dragging with the right mouse button.
- Click **Save** (or `Ctrl/Cmd+S`). Your work is also saved automatically when
  you move to another image, and re-loaded whenever you reopen that image.

## Exporting a tiled training dataset

Satellite images are often too large to annotate or train on whole. Click
**Export tiles…** (top-right) to cut every image *and its annotations* into
smaller, **overlapping** tiles and download them as a training dataset.

You choose the tile size and the overlap (defaults: 512 px tiles, 64 px
overlap). Overlap means an object near a tile edge is captured whole by at least
one neighbouring tile rather than being lost. An object that crosses a tile
boundary is clipped into every tile it touches, so it stays usable in each.

The download is a `.zip` in **COCO instance-segmentation** format — the standard
that Detectron2, MMDetection and most training stacks read directly:

```
dataset_tiles/
  images/
    sat_r0_c0.png        # row 0, col 0
    sat_r0_c1.png
    ...
  annotations.json       # COCO: images, annotations (polygons), categories
```

Categories come from your class list. Tiles with no objects are still exported
as valid, label-free samples. Your original full-image annotations are untouched
— this is a read-only export path.

## Where your work is stored

Inside your image folder, in a `.annotations/` sub-folder:

```
my-images/
  photo1.jpg
  photo2.png
  .annotations/
    classes.json           # your class list
    photo1.jpg.json        # one sidecar per annotated image
```

The sidecars are plain, human-readable JSON. Each object is a polygon whose
points are `[x, y]` pixel coordinates in the original image (top-left origin),
alongside the image's width and height. See `docs`-style notes in
`app/models.py` for the exact schema.

## Development

```bash
pip install -r requirements-dev.txt
python -m pytest                      # run the test suite
uvicorn app.main:app --reload         # run without Docker (uses ./data)
```
