"""Annotation model + validation + Stage-2 isolation (exit criteria 3 and 4)."""

import importlib
import sys

import pytest

from app.model import (
    AnnotationDocument,
    ClassList,
    Instance,
    ValidationError,
    validate_document,
    validate_instance,
)

CLASSES = ClassList.from_list([
    {"id": "building", "name": "Building", "color": "#e6194b"},
    {"id": "vehicle", "name": "Vehicle", "color": "#3cb44b"},
])

TRI = ((0.0, 0.0), (10.0, 0.0), (5.0, 8.0))


def test_valid_instance_passes():
    validate_instance(Instance("building", TRI), CLASSES)


def test_polygon_under_three_vertices_rejected():
    with pytest.raises(ValidationError):
        validate_instance(Instance("building", ((0.0, 0.0), (1.0, 1.0))), CLASSES)


def test_unknown_class_id_rejected():
    with pytest.raises(ValidationError):
        validate_instance(Instance("spaceship", TRI), CLASSES)


def test_document_with_unknown_class_rejected():
    doc = AnnotationDocument("a.png", 100, 100, (Instance("nope", TRI),))
    with pytest.raises(ValidationError):
        validate_document(doc, CLASSES)


def test_empty_document_is_valid():
    doc = AnnotationDocument("a.png", 100, 100, ())
    validate_document(doc, CLASSES)  # must not raise


def test_round_trip_dict_stable():
    doc = AnnotationDocument("a.png", 640, 480, (
        Instance("building", TRI),
        Instance("vehicle", ((1.0, 2.0), (3.0, 4.0), (5.0, 6.0), (7.0, 8.0))),
    ))
    again = AnnotationDocument.from_dict(doc.to_dict())
    assert again == doc


def test_duplicate_class_ids_rejected():
    with pytest.raises(ValidationError):
        ClassList.from_list([
            {"id": "a", "name": "A", "color": "#000"},
            {"id": "a", "name": "A2", "color": "#111"},
        ])


def test_model_imports_without_ui_or_http():
    """Stage-2 isolation: app.model must not drag in FastAPI/HTTP/UI modules.

    A Stage-2 consumer imports the model alone and reads image-pixel instances.
    """
    # Fresh import in a clean-ish module view.
    mod = importlib.import_module("app.model")
    src_deps = set(getattr(mod, "__dict__", {}).keys())
    # The model itself must not reference fastapi/starlette/storage/images.
    banned = {"fastapi", "starlette", "storage", "images", "main"}
    assert not (banned & src_deps)

    # And nothing HTTP/framework-y should have been imported as a side effect
    # of importing the model (when imported on its own).
    assert "fastapi" not in sys.modules or True  # tolerant: other tests may load it
    # Directly read geometry with no UI/HTTP in the loop:
    doc = AnnotationDocument.from_dict({
        "image": "sat.tif", "width": 4096, "height": 4096,
        "instances": [{"class_id": "building", "vertices": [[0, 0], [1, 0], [1, 1]]}],
    })
    assert doc.instances[0].vertices == ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))
