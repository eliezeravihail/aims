"""Dataset export — the single owner of turning the annotated workspace into a tiled training dataset.

This is the added export path (goals.md non-goal "exporting to a training format" is lifted for this
capability). It composes three seams and owns only the glue and the on-disk *dataset* shape:

- **tiling** (`app.tiling`) — where the tiles are and how a polygon is clipped/remapped (pure geometry);
- **image pixels** (`app.images.crop_to_file`) — the Pillow-confined crop-and-save of each tile image;
- **the workspace** (`app.store.Workspace`) — image discovery, image bytes, annotations, and the
  path-safe export destination directory.

The export **format** (COCO instance segmentation) lives here and nowhere else: `_build_coco` is the one
place the COCO document shape is known, so swapping to another training format (e.g. YOLO-seg) touches
this module alone. Every large image is tiled with overlap; each object is clipped to each tile it lands
in, so a border object is cut sensibly per tile and, thanks to overlap, may appear in more than one tile.
Tiles with no objects are exported too (valid empty images — useful background, and required to cover the
whole image).
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from .images import crop_to_file
from .store import Workspace
from .tiling import clip_polygon, polygon_area, polygon_bbox, remap, tile_boxes

DEFAULT_TILE_SIZE = 1024
DEFAULT_OVERLAP = 128
IMAGES_SUBDIR = "images"
ANNOTATIONS_FILENAME = "annotations.json"


class ExportOptions(BaseModel):
    """Configurable export parameters. Overlap must be smaller than the tile so tiles advance."""

    tile_size: int = Field(default=DEFAULT_TILE_SIZE, gt=0)
    overlap: int = Field(default=DEFAULT_OVERLAP, ge=0)
    name: str = "dataset"

    @field_validator("name")
    @classmethod
    def _name_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("export name must not be empty")
        return v

    @field_validator("overlap")
    @classmethod
    def _overlap_below_tile(cls, v: int, info) -> int:
        tile = info.data.get("tile_size", DEFAULT_TILE_SIZE)
        if v >= tile:
            raise ValueError("overlap must be smaller than tile_size")
        return v


class ExportSummary(BaseModel):
    """What an export produced. ``path`` is the dataset directory inside the mounted data root."""

    name: str
    path: str
    format: str = "coco"
    source_images: int  # full images tiled
    tiles: int          # tile images written
    instances: int      # clipped object instances across all tiles


def export_dataset(ws: Workspace, options: ExportOptions) -> ExportSummary:
    """Tile every image in the workspace and write a COCO dataset under ``.exports/<name>/``."""
    dest = ws.export_dir(options.name)
    images_dir = dest / IMAGES_SUBDIR
    images_dir.mkdir(exist_ok=True)

    categories, cat_id = _categories(ws)
    coco_images: list[dict] = []
    coco_annotations: list[dict] = []
    source_count = 0

    for image_id in ws.list_images():
        source_count += 1
        ann = ws.read_annotation(image_id)
        src = ws.image_path(image_id)
        stem = Path(image_id).stem
        suffix = Path(image_id).suffix or ".png"
        for (x0, y0, x1, y1) in tile_boxes(ann.width, ann.height, options.tile_size, options.overlap):
            tile_name = f"{stem}__x{x0}_y{y0}{suffix}"
            crop_to_file(src, (x0, y0, x1, y1), images_dir / tile_name)
            image_record_id = len(coco_images) + 1
            coco_images.append(
                {
                    "id": image_record_id,
                    "file_name": f"{IMAGES_SUBDIR}/{tile_name}",
                    "width": x1 - x0,
                    "height": y1 - y0,
                }
            )
            for obj in ann.objects:
                poly = [(p.x, p.y) for p in obj.polygon]
                clipped = clip_polygon(poly, (x0, y0, x1, y1))
                if not clipped:
                    continue  # object does not land in this tile
                local = remap(clipped, x0, y0)
                bx, by, bw, bh = polygon_bbox(local)
                flat = [c for pt in local for c in pt]
                coco_annotations.append(
                    {
                        "id": len(coco_annotations) + 1,
                        "image_id": image_record_id,
                        "category_id": cat_id(obj.cls),
                        "segmentation": [flat],
                        "bbox": [bx, by, bw, bh],
                        "area": polygon_area(local),
                        "iscrowd": 0,
                    }
                )

    coco = _build_coco(coco_images, coco_annotations, categories)
    (dest / ANNOTATIONS_FILENAME).write_text(json.dumps(coco, indent=2), encoding="utf-8")

    return ExportSummary(
        name=options.name,
        path=str(dest),
        source_images=source_count,
        tiles=len(coco_images),
        instances=len(coco_annotations),
    )


def _categories(ws: Workspace):
    """Category list (from the class config) plus a resolver that appends unseen classes on demand.

    Class-list membership is not an annotation-validity rule (goals.md), so an object whose class is not
    in the config still needs a category id; it is appended the first time it is seen.
    """
    names: list[str] = [c.name for c in ws.read_classes().classes]
    ids: dict[str, int] = {name: i + 1 for i, name in enumerate(names)}

    def cat_id(name: str) -> int:
        if name not in ids:
            ids[name] = len(ids) + 1
            names.append(name)
        return ids[name]

    def categories() -> list[dict]:
        return [{"id": ids[name], "name": name} for name in names]

    return categories, cat_id


def _build_coco(images: list[dict], annotations: list[dict], categories) -> dict:
    """The one place the COCO instance-segmentation document shape is assembled."""
    return {
        "info": {"description": "Tiled instance-segmentation dataset", "format": "coco"},
        "images": images,
        "annotations": annotations,
        "categories": categories(),
    }
