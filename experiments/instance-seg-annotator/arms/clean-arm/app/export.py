"""Export a tiled training dataset from the annotated images.

This is the orchestration layer for the tiling export path. It reads images and
their saved annotations, lays overlapping tiles over each one
(:mod:`app.tiling`), crops the tile bitmaps with Pillow, clips every object into
each tile it touches, and feeds the result to the format writer
(:mod:`app.coco`). The finished dataset is packaged as a single ``.zip`` so it
downloads in one click and unpacks straight into a training pipeline.

Nothing here changes how the annotator stores or serves full-image annotations;
it only *reads* them. The output layout is::

    <name>_tiles/
      images/
        <stem>_r0_c0.png
        <stem>_r0_c1.png
        ...
      annotations.json        # COCO instance segmentation

Empty tiles (no object overlaps them) are still written as images and still get
a COCO ``images`` entry — they are valid, label-free training samples.
"""

from __future__ import annotations

import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from PIL import Image

from . import images, storage
from .coco import CocoDatasetBuilder
from .tiling import Tile, clip_polygon_to_tile, plan_tiles

# Sensible defaults for satellite imagery: 512 px tiles with 64 px of overlap,
# so an object within ~64 px of a boundary is captured whole by a neighbour.
DEFAULT_TILE_SIZE = 512
DEFAULT_OVERLAP = 64


@dataclass(frozen=True)
class TileConfig:
    """How to cut an image into tiles. Validated by :mod:`app.tiling`."""

    tile_size: int = DEFAULT_TILE_SIZE
    overlap: int = DEFAULT_OVERLAP


def _tile_file_name(stem: str, tile: Tile) -> str:
    """Deterministic, sortable tile filename: ``<stem>_r<row>_c<col>.png``."""
    return f"{stem}_r{tile.row}_c{tile.col}.png"


def build_dataset(
    data_dir: Path,
    out_dir: Path,
    config: TileConfig,
    image_names: Optional[List[str]] = None,
) -> dict:
    """Build the tiled COCO dataset under ``out_dir`` and return its COCO dict.

    ``image_names`` defaults to every image in ``data_dir``. Each source image
    is tiled independently; tiles from all images share one ``annotations.json``
    so the whole folder exports as a single dataset.
    """
    out_images = out_dir / "images"
    out_images.mkdir(parents=True, exist_ok=True)

    builder = CocoDatasetBuilder()
    # Seed categories from the user's class list so category ids follow class
    # order, independent of which labels happen to appear on the first tile.
    for cls in storage.load_classes(data_dir).classes:
        builder.register_category(cls.name)

    names = image_names if image_names is not None else images.list_image_names(data_dir)
    for name in names:
        img_path = images.resolve_existing(data_dir, name)
        annotation = storage.load_annotation(data_dir, name)
        stem = Path(name).stem

        with Image.open(img_path) as im:
            im = im.convert("RGB")
            tiles = plan_tiles(im.width, im.height, config.tile_size, config.overlap)
            for tile in tiles:
                file_name = _tile_file_name(stem, tile)
                im.crop(tile.box).save(out_images / file_name, "PNG")
                image_id = builder.add_image(
                    f"images/{file_name}", tile.width, tile.height
                )
                for obj in annotation.objects:
                    local = clip_polygon_to_tile(obj.points, tile)
                    if local:
                        builder.add_annotation(image_id, obj.label, local)

    coco = builder.to_dict()
    (out_dir / "annotations.json").write_text(
        _dumps(coco), encoding="utf-8"
    )
    return coco


def export_zip(
    data_dir: Path,
    config: TileConfig,
    image_names: Optional[List[str]] = None,
    dataset_name: str = "dataset_tiles",
) -> Path:
    """Build the dataset and pack it into a ``.zip``; returns the zip path.

    The zip lives in a fresh temp directory the caller is responsible for
    cleaning up (the HTTP layer streams it, then removes the directory).
    """
    workdir = Path(tempfile.mkdtemp(prefix="tile-export-"))
    build_dir = workdir / dataset_name
    build_dataset(data_dir, build_dir, config, image_names)

    zip_path = workdir / f"{dataset_name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(build_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(build_dir.parent))
    return zip_path


def _dumps(obj: dict) -> str:
    import json

    return json.dumps(obj, indent=2, ensure_ascii=False)
