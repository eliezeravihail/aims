"""Stage-2 COCO export: dataset folder, tile images, and the annotations file.

Exercises the format owner end to end: tile PNGs are written and sized to the
tile, the COCO file references them, category ids map from the project class
list, empty tiles export as valid images with zero annotations, and the JSON is
deterministic.
"""

import json

from PIL import Image

from app.export import build_coco, export_dataset
from app.model import AnnotationDocument, ClassList, Instance
from app.tiling import tile_all

CLASSES = ClassList.from_list([
    {"id": "building", "name": "Building", "color": "#e6194b"},
    {"id": "vehicle", "name": "Vehicle", "color": "#3cb44b"},
])


def _make_source(path, w, h):
    Image.new("RGB", (w, h), (20, 40, 60)).save(path)


def _doc(w, h):
    return AnnotationDocument("sat.png", w, h, (
        # inside the first tile
        Instance("building", ((10.0, 10.0), (60.0, 10.0), (60.0, 60.0), (10.0, 60.0))),
        # straddles the vertical tile border near x=100
        Instance("vehicle", ((90.0, 30.0), (130.0, 30.0), (130.0, 70.0), (90.0, 70.0))),
    ))


def test_build_coco_maps_categories_and_shapes():
    doc = _doc(200, 200)
    tiles = tile_all(doc, tile_size=100, overlap=20)
    coco = build_coco(tiles, CLASSES)
    assert {c["name"] for c in coco["categories"]} == {"Building", "Vehicle"}
    cat_ids = {c["name"]: c["id"] for c in coco["categories"]}
    # every annotation references a real image and a mapped integer category
    img_ids = {im["id"] for im in coco["images"]}
    for ann in coco["annotations"]:
        assert ann["image_id"] in img_ids
        assert ann["category_id"] in cat_ids.values()
        assert ann["iscrowd"] == 0
        assert len(ann["segmentation"]) == 1
        assert len(ann["segmentation"][0]) % 2 == 0  # flat x,y pairs
        assert len(ann["bbox"]) == 4
        assert ann["area"] > 0
    # one image entry per tile
    assert len(coco["images"]) == len(tiles)


def test_export_writes_folder_with_tiles_and_annotations(tmp_path):
    src = tmp_path / "sat.png"
    _make_source(src, 200, 200)
    doc = _doc(200, 200)
    out = tmp_path / "dataset"

    summary = export_dataset(doc, src, CLASSES, out, tile_size=100, overlap=20)

    assert (out / "annotations.json").is_file()
    img_dir = out / "images"
    pngs = sorted(p.name for p in img_dir.glob("*.png"))
    assert len(pngs) == summary.tiles

    coco = json.loads((out / "annotations.json").read_text())
    # every referenced file exists and is a real image of the tile's size
    for im in coco["images"]:
        p = img_dir / im["file_name"]
        assert p.is_file()
        with Image.open(p) as opened:
            assert opened.size == (im["width"], im["height"])


def test_empty_tiles_export_validly(tmp_path):
    src = tmp_path / "sat.png"
    _make_source(src, 300, 300)
    # single small instance in the top-left corner only
    doc = AnnotationDocument("sat.png", 300, 300, (
        Instance("building", ((10.0, 10.0), (40.0, 10.0), (40.0, 40.0))),
    ))
    out = tmp_path / "dataset"
    summary = export_dataset(doc, src, CLASSES, out, tile_size=100, overlap=0)

    assert summary.empty_tiles > 0
    coco = json.loads((out / "annotations.json").read_text())
    # empty tiles still have image entries and their PNGs; they carry 0 annotations
    imgs_with_anns = {a["image_id"] for a in coco["annotations"]}
    all_img_ids = {im["id"] for im in coco["images"]}
    empty_img_ids = all_img_ids - imgs_with_anns
    assert empty_img_ids
    for im in coco["images"]:
        assert (out / "images" / im["file_name"]).is_file()


def test_export_annotations_are_deterministic(tmp_path):
    src = tmp_path / "sat.png"
    _make_source(src, 200, 200)
    doc = _doc(200, 200)

    out1 = tmp_path / "d1"
    out2 = tmp_path / "d2"
    export_dataset(doc, src, CLASSES, out1, tile_size=100, overlap=20)
    export_dataset(doc, src, CLASSES, out2, tile_size=100, overlap=20)
    assert (out1 / "annotations.json").read_bytes() == (out2 / "annotations.json").read_bytes()
