import json

import pytest

from app.export import ExportOptions, export_dataset
from app.models import AnnotationObject, ClassDef, Point
from app.store import BadExportName, Workspace
from conftest import make_image


def _poly(pts):
    return [Point(x=x, y=y) for (x, y) in pts]


def _load(dest):
    return json.loads((dest / "annotations.json").read_text())


def test_large_image_is_tiled_with_overlap_and_dataset_is_coco(tmp_path):
    make_image(tmp_path / "big.png", size=(250, 100))
    ws = Workspace(tmp_path)
    summary = export_dataset(ws, ExportOptions(tile_size=100, overlap=20, name="ds"))
    dest = tmp_path / ".exports" / "ds"
    coco = _load(dest)
    # 250x100 with tile 100 / stride 80 -> x origins 0,80 then clamp to 150 -> 3 x-tiles, 1 y-tile.
    assert summary.tiles == len(coco["images"]) == 3
    # every tile image file exists on disk.
    for img in coco["images"]:
        assert (dest / img["file_name"]).is_file()
    assert {"images", "annotations", "categories"} <= set(coco)


def test_object_straddling_boundary_appears_clipped_in_each_tile_it_lands_in(tmp_path):
    make_image(tmp_path / "big.png", size=(250, 100))
    ws = Workspace(tmp_path)
    # A square 80..120 straddles the boundary between the tile at x=0 (ends 100) and x=80 (starts 80).
    ws.write_annotation("big.png", [AnnotationObject(cls="car", polygon=_poly(
        [(80, 20), (120, 20), (120, 60), (80, 60)]))])
    export_dataset(ws, ExportOptions(tile_size=100, overlap=20, name="ds"))
    coco = _load(tmp_path / ".exports" / "ds")
    # overlap makes the border object land in more than one tile.
    assert len(coco["annotations"]) >= 2
    # every clipped instance is a valid polygon (>=3 vertices -> >=6 flat coords) inside its tile.
    for ann in coco["annotations"]:
        seg = ann["segmentation"][0]
        assert len(seg) >= 6
        img = next(i for i in coco["images"] if i["id"] == ann["image_id"])
        xs = seg[0::2]
        ys = seg[1::2]
        assert min(xs) >= 0 and max(xs) <= img["width"]
        assert min(ys) >= 0 and max(ys) <= img["height"]


def test_object_absent_from_tiles_it_does_not_touch(tmp_path):
    make_image(tmp_path / "big.png", size=(250, 100))
    ws = Workspace(tmp_path)
    # object lives only in the far-left tile (x 10..40).
    ws.write_annotation("big.png", [AnnotationObject(cls="car", polygon=_poly(
        [(10, 10), (40, 10), (40, 40), (10, 40)]))])
    export_dataset(ws, ExportOptions(tile_size=100, overlap=20, name="ds"))
    coco = _load(tmp_path / ".exports" / "ds")
    # tiles whose x-origin is >= 40 (e.g. 80,150) must carry no annotation for this object.
    left_tile_ids = {
        i["id"] for i in coco["images"] if i["file_name"].endswith("x0_y0.png")
    }
    for ann in coco["annotations"]:
        assert ann["image_id"] in left_tile_ids  # only the left tile has it
    assert len(coco["annotations"]) == 1


def test_empty_tiles_are_exported_validly(tmp_path):
    make_image(tmp_path / "big.png", size=(250, 100))
    ws = Workspace(tmp_path)  # no annotations at all
    summary = export_dataset(ws, ExportOptions(tile_size=100, overlap=20, name="ds"))
    coco = _load(tmp_path / ".exports" / "ds")
    assert summary.instances == 0
    assert coco["annotations"] == []
    assert len(coco["images"]) == 3  # tiles still emitted, images on disk
    for img in coco["images"]:
        assert (tmp_path / ".exports" / "ds" / img["file_name"]).is_file()


def test_remapped_point_is_in_tile_local_coordinates(tmp_path):
    make_image(tmp_path / "big.png", size=(250, 100))
    ws = Workspace(tmp_path)
    # a triangle wholly inside the second tile (origin x=80): vertices at image x 130,170,150.
    ws.write_annotation("big.png", [AnnotationObject(cls="car", polygon=_poly(
        [(130, 20), (170, 20), (150, 60)]))])
    export_dataset(ws, ExportOptions(tile_size=100, overlap=20, name="ds"))
    coco = _load(tmp_path / ".exports" / "ds")
    # find the tile at origin x=80 and confirm its instance's first vertex is (130-80, 20-0)=(50,20).
    tile80 = next(i for i in coco["images"] if i["file_name"].endswith("x80_y0.png"))
    ann = next(a for a in coco["annotations"] if a["image_id"] == tile80["id"])
    seg = ann["segmentation"][0]
    assert (seg[0], seg[1]) == (50, 20)


def test_unknown_class_gets_a_category(tmp_path):
    make_image(tmp_path / "img.png", size=(120, 80))
    ws = Workspace(tmp_path)
    ws.write_classes([ClassDef(name="car", color="#123456")])
    ws.write_annotation("img.png", [AnnotationObject(cls="spaceship", polygon=_poly(
        [(1, 1), (40, 1), (20, 40)]))])
    export_dataset(ws, ExportOptions(tile_size=1024, overlap=128, name="ds"))
    coco = _load(tmp_path / ".exports" / "ds")
    names = {c["name"] for c in coco["categories"]}
    assert "spaceship" in names and "car" in names


def test_multiple_source_images_share_one_dataset(tmp_path):
    make_image(tmp_path / "a.png", size=(120, 80))
    make_image(tmp_path / "b.png", size=(120, 80))
    ws = Workspace(tmp_path)
    summary = export_dataset(ws, ExportOptions(name="ds"))
    assert summary.source_images == 2
    assert summary.tiles == 2  # each small image is a single tile


@pytest.mark.parametrize("bad", ["../evil", "sub/ds", "/abs", ".", "..", ".hidden"])
def test_export_name_path_safety(tmp_path, bad):
    ws = Workspace(tmp_path)
    with pytest.raises(BadExportName):
        ws.export_dir(bad)


def test_export_stays_inside_the_data_root(tmp_path):
    make_image(tmp_path / "img.png", size=(120, 80))
    ws = Workspace(tmp_path)
    dest = ws.export_dir("ds")
    assert str(dest).startswith(str(tmp_path.resolve()))


def test_overlap_must_be_below_tile_size():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ExportOptions(tile_size=100, overlap=100)


def test_empty_export_name_rejected():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ExportOptions(name="  ")
