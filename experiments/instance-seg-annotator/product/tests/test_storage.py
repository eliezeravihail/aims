"""Persistence: byte-stable, idempotent round-trips (exit criteria 1 and 4)."""

import pytest

from app.model import AnnotationDocument, ClassList, Instance, ValidationError
from app.storage import dumps, load, save

CLASSES = ClassList.from_list([
    {"id": "building", "name": "Building", "color": "#e6194b"},
    {"id": "vehicle", "name": "Vehicle", "color": "#3cb44b"},
])

TRI = ((0.0, 0.0), (10.0, 0.0), (5.0, 8.0))
QUAD = ((1.0, 2.0), (3.0, 4.0), (5.0, 6.0), (7.0, 8.0))


def make_doc():
    return AnnotationDocument("scene_01.png", 1920, 1080, (
        Instance("building", TRI),
        Instance("vehicle", QUAD),
    ))


def test_draw_two_instances_save_reload_identical(tmp_path):
    """Exit criterion 1: draw >=2 instances, distinct classes, save/reload equal."""
    doc = make_doc()
    save(tmp_path, doc, CLASSES)
    back = load(tmp_path, "scene_01.png")
    assert back == doc
    assert {i.class_id for i in back.instances} == {"building", "vehicle"}


def test_save_is_idempotent_byte_stable(tmp_path):
    """save -> load -> save produces byte-identical JSON."""
    doc = make_doc()
    p = save(tmp_path, doc, CLASSES)
    bytes1 = p.read_bytes()
    reloaded = load(tmp_path, "scene_01.png")
    save(tmp_path, reloaded, CLASSES)
    bytes2 = p.read_bytes()
    assert bytes1 == bytes2


def test_dumps_deterministic():
    d1 = dumps(make_doc())
    d2 = dumps(AnnotationDocument.from_dict(make_doc().to_dict()))
    assert d1 == d2


def test_empty_document_saves_and_loads(tmp_path):
    doc = AnnotationDocument("empty.png", 640, 480, ())
    save(tmp_path, doc, CLASSES)
    back = load(tmp_path, "empty.png")
    assert back == doc
    assert back.instances == ()


def test_load_missing_returns_none(tmp_path):
    assert load(tmp_path, "never_saved.png") is None


def test_save_rejects_invalid_before_writing(tmp_path):
    bad = AnnotationDocument("bad.png", 100, 100, (Instance("building", ((0.0, 0.0), (1.0, 1.0))),))
    with pytest.raises(ValidationError):
        save(tmp_path, bad, CLASSES)
    # nothing written
    assert load(tmp_path, "bad.png") is None


def test_annotation_path_keyed_by_stem(tmp_path):
    doc = AnnotationDocument("nested/name.jpeg", 10, 10, ())
    p = save(tmp_path, doc, CLASSES)
    assert p.name == "name.json"
    assert p.parent == tmp_path
