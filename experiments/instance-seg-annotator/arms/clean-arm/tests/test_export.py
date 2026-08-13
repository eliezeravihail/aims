"""Tests for the tiled COCO dataset export: module orchestration + HTTP route."""

from __future__ import annotations

import io
import json
import zipfile

from app import export, storage
from app.export import TileConfig
from app.models import Annotation, AnnotationObject
from tests.conftest import make_image


def _annotate_car(data_dir, name="sat.png", size=(200, 100)):
    """An image with one 20x20 'car' object at x=50..70, y=10..30."""
    make_image(data_dir / name, size=size)
    storage.save_annotation(
        data_dir,
        Annotation(
            image=name,
            width=size[0],
            height=size[1],
            objects=[
                AnnotationObject(
                    id="o1",
                    label="car",
                    points=[[50, 10], [70, 10], [70, 30], [50, 30]],
                )
            ],
        ),
    )


def _build(data_dir, tmp_path, tile_size=60, overlap=20):
    out = tmp_path / "out"
    coco = export.build_dataset(
        data_dir, out, TileConfig(tile_size=tile_size, overlap=overlap)
    )
    return out, coco


def test_build_writes_tiles_and_coco_json(data_dir, tmp_path):
    _annotate_car(data_dir)
    out, coco = _build(data_dir, tmp_path)

    # A COCO annotations.json exists and parses.
    parsed = json.loads((out / "annotations.json").read_text())
    assert parsed["images"] and parsed["categories"]
    # Every image entry has a real PNG on disk.
    for img in coco["images"]:
        assert (out / img["file_name"]).is_file()


def test_categories_follow_class_list_order(data_dir, tmp_path):
    _annotate_car(data_dir)
    _, coco = _build(data_dir, tmp_path)
    # Default seeded classes are car, tree, building -> ids 1,2,3.
    by_name = {c["name"]: c["id"] for c in coco["categories"]}
    assert by_name["car"] == 1 and by_name["tree"] == 2 and by_name["building"] == 3


def test_straddling_object_appears_in_each_tile_it_lands_in(data_dir, tmp_path):
    _annotate_car(data_dir)
    _, coco = _build(data_dir, tmp_path)
    # The object spans the col0/col1 boundary, so it is clipped into exactly the
    # two tiles it overlaps (and no others).
    assert len(coco["annotations"]) == 2
    assert {a["category_id"] for a in coco["annotations"]} == {1}


def test_coordinate_remap_is_correct_in_a_tile(data_dir, tmp_path):
    _annotate_car(data_dir)
    _, coco = _build(data_dir, tmp_path)
    # In the tile whose origin is (40, 0) the object sits fully inside, so its
    # bbox is the object shifted by (-40, 0): [10, 10, 20, 20].
    bboxes = [a["bbox"] for a in coco["annotations"]]
    assert [10.0, 10.0, 20.0, 20.0] in bboxes


def test_empty_tiles_export_validly(data_dir, tmp_path):
    _annotate_car(data_dir)
    _, coco = _build(data_dir, tmp_path)
    annotated_ids = {a["image_id"] for a in coco["annotations"]}
    empty_ids = {img["id"] for img in coco["images"]} - annotated_ids
    # There ARE tiles with no object, and each is still a valid image entry
    # with a real bitmap on disk.
    assert empty_ids
    for img in coco["images"]:
        if img["id"] in empty_ids:
            assert (tmp_path / "out" / img["file_name"]).is_file()


def test_image_with_no_annotation_still_tiles(data_dir, tmp_path):
    make_image(data_dir / "blank.png", size=(150, 90))
    _, coco = _build(data_dir, tmp_path)
    assert coco["images"]              # tiles were produced
    assert coco["annotations"] == []  # but nothing to label


def test_export_zip_contains_dataset(data_dir):
    _annotate_car(data_dir)
    zip_path = export.export_zip(data_dir, TileConfig(tile_size=60, overlap=20))
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert any(n.endswith("annotations.json") for n in names)
    assert any(n.endswith(".png") for n in names)


# --------------------------------------------------------------------------- #
# HTTP route
# --------------------------------------------------------------------------- #

def test_export_endpoint_returns_zip(client, data_dir):
    _annotate_car(data_dir)
    r = client.get("/api/export", params={"tile_size": 60, "overlap": 20})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        coco = json.loads(zf.read(next(n for n in zf.namelist() if n.endswith("annotations.json"))))
    assert len(coco["annotations"]) == 2


def test_export_endpoint_rejects_bad_overlap(client, data_dir):
    _annotate_car(data_dir)
    r = client.get("/api/export", params={"tile_size": 60, "overlap": 60})
    assert r.status_code == 400
