# Goals

## Primary goal

A single-user, locally-run tool to annotate a folder of images for **instance segmentation**: open it
in a browser, and for each image draw one outline (polygon) around each individual object and give that
object a class label. Work is saved to disk and restored when the image is reopened. It runs entirely
from a container pointed at a folder on the user's own machine.

## Use scenarios

- The user runs `docker compose up` with a host folder of PNG/JPEG photos mounted in. They open the tool
  in a browser, see the first image, and draw a polygon around each object (a car, a tree, a building),
  picking that object's class from a configurable list. Several objects of several classes can appear in
  one image. They save, step to the next image, and repeat. Reopening a previously-annotated image shows
  its polygons exactly as left.
- Before annotating, the user edits the class list (add/remove/rename a class, pick a color) so the
  classes match their images.
- The user's images are very large satellite scenes (thousands of px per side). After annotating in the
  usual full-image way, they click **Export tiles**, pick a tile size and overlap, and the tool cuts
  every image into overlapping tiles, clips each annotation to each tile it lands in, and writes a
  standard COCO instance-segmentation dataset (tile images + `annotations.json`) a training pipeline can
  consume — without changing how full-image annotation works.

## Non-goals

Deliberately not designed for (build for today only):

- Image formats other than PNG and JPEG; non-photo imagery.
- Shape types other than polygons (bounding boxes, brush masks, semantic fill).
- Multi-user, accounts, authentication, cloud storage, concurrent editing.
- Recursing into nested subfolders of the image directory (flat listing only).
- Undo/redo history, autosave, or annotation versioning.

## Decisions & insights

- **One outline per object, class per object.** The product records a set of independent objects per
  image, each an outline plus a class name — not a per-pixel semantic map. Instance identity is "one
  polygon = one object", chosen because the user's mental model is "draw around each thing".
- **Class-list membership is not an annotation-validity rule.** A saved object carries its class *name*
  as a plain string. The store does not reject an object whose class is absent from the current list,
  because the class list is user-editable and mutable; coupling saved work's validity to the current
  config would silently invalidate prior annotations when the list is edited. The UI renders an
  unknown-class object in a neutral color.
- **Authoritative image dimensions come from the image, not the client.** Coordinates are meaningful
  only against the true pixel size, so the server probes it; a client-supplied size is never trusted.
- **Tiled export is an added, read-only-to-annotations path.** Cutting large images into overlapping tiles
  and writing a COCO dataset never alters the stored full-image annotations (they stay full-image pixel
  space); tiling and boundary-clipping happen only at export time. Objects crossing a tile edge are
  clipped per tile, and overlap lets a near-edge object survive in more than one tile. See
  `decisions/0002-coco-tiled-export.md`.
