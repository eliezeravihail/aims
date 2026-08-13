"""Export a tiled image + annotations as a COCO instance-segmentation dataset.

The one owner of the *export format*. It reads an `AnnotationDocument` (image-space
geometry) via the pure `tiling` module, crops each tile out of the source image
(Pillow), and writes a training dataset folder: tile PNGs plus a single COCO
`annotations.json`. Swapping the format (e.g. to YOLO-seg) touches only this
module — everything the format needs is confined here.

Why COCO instance segmentation (over YOLO-seg):
- Its `segmentation` field is a flat list of polygon vertex coordinates in *pixel*
  space, a direct match for our polygon instances — no normalization or per-image
  side files. One `annotations.json` describes the whole dataset, so the write
  stays a single deterministic artifact (mirroring the project's byte-stable
  JSON ethos). `bbox` and `area` are derived from the same polygon.
- Category ids: COCO wants integer category ids, our model uses string class ids.
  The mapping (string class id -> 1-based integer) is built here from the project
  `ClassList` order and written into `categories`; it never leaks into the model.

Layout written under `out_dir`:
    out_dir/
      images/<tile>.png       one PNG per tile
      annotations.json        COCO dataset (images, annotations, categories)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from . import images as images_mod
from . import storage
from .model import AnnotationDocument, ClassList
from .tiling import polygon_area, tile_all


@dataclass(frozen=True)
class ExportSummary:
    """What an export produced, for callers/CLI to report."""

    out_dir: Path
    tiles: int
    instances: int
    empty_tiles: int


def _categories(classes: ClassList) -> tuple[list[dict], dict[str, int]]:
    """COCO categories + a stable string-class-id -> integer-category-id map."""
    cats: list[dict] = []
    mapping: dict[str, int] = {}
    for i, c in enumerate(classes.classes, start=1):
        mapping[c.id] = i
        cats.append({"id": i, "name": c.name, "supercategory": ""})
    return cats, mapping


def _bbox(vertices: tuple[tuple[float, float], ...]) -> list[float]:
    """COCO bbox [x, y, width, height] from a polygon's vertices."""
    xs = [x for x, _ in vertices]
    ys = [y for _, y in vertices]
    x0, y0 = min(xs), min(ys)
    return [x0, y0, max(xs) - x0, max(ys) - y0]


def _segmentation(vertices: tuple[tuple[float, float], ...]) -> list[list[float]]:
    """COCO polygon segmentation: one flat [x0, y0, x1, y1, ...] ring."""
    flat: list[float] = []
    for x, y in vertices:
        flat.extend((x, y))
    return [flat]


def build_coco(
    tiles: list[tuple[object, AnnotationDocument]], classes: ClassList
) -> dict:
    """Assemble the COCO dataset dict from per-tile documents. Pure (no I/O).

    `tiles` is a list of (tile, tile_document) pairs as produced by
    `tiling.tile_all`; only the documents' geometry is read here.
    """
    cats, cat_id = _categories(classes)
    coco_images: list[dict] = []
    annotations: list[dict] = []
    ann_id = 1
    for image_id, (_tile, doc) in enumerate(tiles, start=1):
        coco_images.append({
            "id": image_id,
            "file_name": f"{doc.image}.png",
            "width": doc.width,
            "height": doc.height,
        })
        for ins in doc.instances:
            annotations.append({
                "id": ann_id,
                "image_id": image_id,
                "category_id": cat_id[ins.class_id],
                "segmentation": _segmentation(ins.vertices),
                "bbox": _bbox(ins.vertices),
                "area": polygon_area(ins.vertices),
                "iscrowd": 0,
            })
            ann_id += 1
    return {"images": coco_images, "annotations": annotations, "categories": cats}


def export_dataset(
    doc: AnnotationDocument,
    source_image: Path,
    classes: ClassList,
    out_dir: Path,
    tile_size: int,
    overlap: int,
) -> ExportSummary:
    """Tile `source_image` + `doc` and write a COCO dataset under `out_dir`.

    Crops each tile from the source image and writes it as a PNG under
    `out_dir/images/`, then writes one COCO `annotations.json`. Empty tiles are
    exported as valid images carrying zero annotations.
    """
    tiles = tile_all(doc, tile_size, overlap)

    out_dir = Path(out_dir)
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    empty = 0
    with Image.open(source_image) as im:
        src = im.convert("RGB")
        for tile, tdoc in tiles:
            crop = src.crop((tile.x0, tile.y0, tile.x0 + tile.width, tile.y0 + tile.height))
            crop.save(img_dir / f"{tdoc.image}.png")
            if not tdoc.instances:
                empty += 1

    coco = build_coco(tiles, classes)
    # Deterministic, byte-stable output (mirrors storage.py's ethos).
    (out_dir / "annotations.json").write_text(
        json.dumps(coco, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    total_instances = sum(len(t.instances) for _tile, t in tiles)
    return ExportSummary(
        out_dir=out_dir,
        tiles=len(tiles),
        instances=total_instances,
        empty_tiles=empty,
    )


def _main(argv: list[str] | None = None) -> int:
    """CLI: export one annotated source image as a COCO tile dataset.

    Wires the confined pieces (config paths, storage, images) to the pure tiler
    and this format owner. Kept thin — all format logic is above.
    """
    import argparse

    from . import config

    parser = argparse.ArgumentParser(description="Export a tiled COCO instance-seg dataset.")
    parser.add_argument("image", help="source image filename (in the input dir)")
    parser.add_argument("out", help="output dataset folder")
    parser.add_argument("--tile-size", type=int, required=True, help="square tile edge, pixels")
    parser.add_argument("--overlap", type=int, default=0, help="tile overlap, pixels (default 0)")
    parser.add_argument("--input-dir", default=None, help="override input image dir")
    parser.add_argument("--annotations-dir", default=None, help="override annotations dir")
    args = parser.parse_args(argv)

    input_dir = Path(args.input_dir) if args.input_dir else config.INPUT_DIR
    ann_dir = Path(args.annotations_dir) if args.annotations_dir else config.ANNOTATIONS_DIR

    source = images_mod.image_file(input_dir, args.image)
    w, h = images_mod.image_size(input_dir, args.image)
    doc = storage.load(ann_dir, args.image)
    if doc is None:
        doc = AnnotationDocument(image=args.image, width=w, height=h, instances=())

    summary = export_dataset(
        doc=doc,
        source_image=source,
        classes=config.load_class_list(),
        out_dir=Path(args.out),
        tile_size=args.tile_size,
        overlap=args.overlap,
    )
    print(
        f"exported {summary.tiles} tiles "
        f"({summary.instances} instances, {summary.empty_tiles} empty) -> {summary.out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
