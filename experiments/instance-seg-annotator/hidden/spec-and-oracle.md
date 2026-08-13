# Hidden spec + oracle answers — NOT shown to either arm

The operator answers as an ordinary product owner (not an architect), strictly from this sheet, for the
**current** stage only. Never reveal a later stage. Word neutrally. Log every Q and verbatim A; give the
same answer word-for-word to the other arm.

## The whole product (both stages — hidden)

A local, single-user, container-run multi-class instance-segmentation annotator. Stage 1: draw polygon
instances, label each with a class, persist per image, step through a folder. Stage 2: large satellite
images are tiled with overlap; the tiles + annotations export as a standard instance-seg training dataset
(COCO or YOLO-seg). The architectural axis under stress: **the seam between annotation geometry and how
the image is presented/stored** — Stage 2 needs to read instance geometry, remap it into tile-local
pixels, clip polygons to tile borders, and export, without the Stage-1 display/storage choices getting in
the way.

## Oracle answers — Stage 1

- *"What image formats?"* → "Ordinary photos — PNG and JPEG."
- *"Roughly how big are the images?"* → "Normal photos for now. Build for today."
- *"Will there be more images / other kinds of images later?"* → "Not now — build for today."
- *"Will annotations need to be exported / used for training later?"* → "Not now — build for today."
- *"Should shapes be polygons, boxes, or masks?"* → "I draw around each object, so outlines/polygons.
  Choose a simple sensible technical approach."
- *"What coordinate system / how should saved annotations be stored?"* → "I don't know; choose a simple
  sensible technical approach."
- *"Multi-user? Accounts? Cloud?"* → "No — just me, on my machine."
- *"How is the class list configured?"* → "A small list I can edit — a name and maybe a color per class."
- *"Where do images and saved annotations live?"* → "On my disk; the container should read/write a folder
  I point it at."
- Any architecture/interface/DB-shape question an ordinary user wouldn't decide → "I don't know; choose a
  simple sensible technical approach."

## Oracle answers — Stage 2

- *"Which export format — COCO, YOLO-seg, something else?"* → "Whatever's standard and a training pipeline
  can read. You choose."
- *"What tile size / how much overlap?"* → "Make them configurable; pick sensible defaults."
- *"An object crossing a tile edge — include it, clip it, drop it?"* → "It should still be usable for each
  tile it lands in. Choose a sensible approach." (Do not dictate clipping vs. keep-whole; that is theirs.)
- *"How large are the satellite images?"* → "Big — thousands of pixels on a side, bigger than one tile."
- *"Do the original full-image annotations still need to work too?"* → "Yes, the annotator still works as
  before; this is an added export path."
- Any architecture question → "I don't know; choose a simple sensible technical approach."

## Visible acceptance

**Stage 1:** load an image; draw ≥2 polygon instances of ≥2 classes; save; reload the page → the instances
and classes come back. Runs from the container's compose entrypoint.

**Stage 2:** given a large image + its annotations, produce overlapping tiles and an export folder in a
standard instance-seg format; an instance crossing a tile boundary appears usably in each tile it lands in;
tiles with no instances still export validly.

## Hidden probes (derived only from revealed requirements)

- Are saved annotation coordinates meaningful independent of the browser view (zoom/pan)? (A yes makes
  Stage-2 remap trivial; a no forces reconstruction.)
- To add tiling/export, how many existing files must change, and does the annotation data model have to be
  touched or can it be consumed as-is?
- Is the export format choice confined to one place, or spread across the code?
</content>
