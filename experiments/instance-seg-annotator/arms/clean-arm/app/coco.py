"""COCO instance-segmentation dataset assembly.

This module is the *only* place that knows the on-disk shape of the exported
dataset. Everything else (tiling geometry, cropping, zipping) works in plain
image-pixel coordinates and hands finished tiles + clipped polygons to the
:class:`CocoDatasetBuilder`. To support a different training format later
(e.g. YOLO segmentation .txt files), add a sibling builder with the same
``add_image`` / ``add_annotation`` / ``to_dict`` surface — nothing outside this
module needs to change.

Why COCO: it is the de-facto standard for instance segmentation and is read
directly by the common training stacks (Detectron2, MMDetection, and the many
tools that consume ``instances_*.json``). Its polygon ``segmentation`` field
maps one-to-one onto our polygons, so no lossy conversion is required.

Shape produced (a single ``annotations.json``)::

    {
      "info": {...}, "licenses": [],
      "images":      [{"id", "file_name", "width", "height"}, ...],
      "annotations": [{"id", "image_id", "category_id",
                       "segmentation": [[x1,y1,x2,y2,...]],
                       "bbox": [x,y,w,h], "area", "iscrowd": 0}, ...],
      "categories":  [{"id", "name", "supercategory"}, ...]
    }
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Sequence

from .tiling import polygon_area

Polygon = Sequence[Sequence[float]]


def _round_pt(v: float) -> float:
    """Trim float noise from clipped coordinates while staying sub-pixel exact."""
    return round(v, 2)


class CocoDatasetBuilder:
    """Accumulates images, annotations and categories into a COCO dict.

    Categories are assigned stable 1-based ids in the order labels are first
    registered; seed them up-front from the class list via :meth:`register_category`
    so ids follow the user's class order regardless of which tile is seen first.
    """

    def __init__(self, description: str = "Tiled instance-segmentation dataset") -> None:
        self._images: List[dict] = []
        self._annotations: List[dict] = []
        self._category_ids: Dict[str, int] = {}
        self._description = description
        self._next_image_id = 1
        self._next_ann_id = 1

    # -- categories --------------------------------------------------------- #

    def register_category(self, label: str) -> int:
        """Return the category id for ``label``, assigning a new one if unseen."""
        if label not in self._category_ids:
            self._category_ids[label] = len(self._category_ids) + 1
        return self._category_ids[label]

    # -- images + annotations ---------------------------------------------- #

    def add_image(self, file_name: str, width: int, height: int) -> int:
        """Register one tile image; returns its COCO image id."""
        image_id = self._next_image_id
        self._next_image_id += 1
        self._images.append(
            {"id": image_id, "file_name": file_name, "width": width, "height": height}
        )
        return image_id

    def add_annotation(self, image_id: int, label: str, polygon: Polygon) -> int:
        """Register one clipped object on a tile. ``polygon`` is tile-local."""
        category_id = self.register_category(label)
        flat: List[float] = []
        xs: List[float] = []
        ys: List[float] = []
        for x, y in polygon:
            fx, fy = _round_pt(x), _round_pt(y)
            flat.extend((fx, fy))
            xs.append(fx)
            ys.append(fy)
        x0, y0 = min(xs), min(ys)
        bbox = [x0, y0, max(xs) - x0, max(ys) - y0]
        ann_id = self._next_ann_id
        self._next_ann_id += 1
        self._annotations.append(
            {
                "id": ann_id,
                "image_id": image_id,
                "category_id": category_id,
                "segmentation": [flat],
                "bbox": bbox,
                "area": round(polygon_area(polygon), 2),
                "iscrowd": 0,
            }
        )
        return ann_id

    # -- output ------------------------------------------------------------- #

    def to_dict(self) -> dict:
        """Materialise the full COCO dataset dictionary."""
        categories = [
            {"id": cid, "name": name, "supercategory": ""}
            for name, cid in sorted(self._category_ids.items(), key=lambda kv: kv[1])
        ]
        return {
            "info": {
                "description": self._description,
                "date_created": datetime.now(timezone.utc).isoformat(),
            },
            "licenses": [],
            "images": list(self._images),
            "annotations": list(self._annotations),
            "categories": categories,
        }
