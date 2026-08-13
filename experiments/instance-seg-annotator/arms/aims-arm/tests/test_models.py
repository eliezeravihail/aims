import math

import pytest
from pydantic import ValidationError

from app.models import AnnotationObject, Point


def _tri():
    return [Point(x=0, y=0), Point(x=10, y=0), Point(x=5, y=8)]


def test_polygon_needs_three_vertices():
    with pytest.raises(ValidationError):
        AnnotationObject(cls="car", polygon=[Point(x=0, y=0), Point(x=1, y=1)])


def test_three_vertices_ok():
    obj = AnnotationObject(cls="car", polygon=_tri())
    assert len(obj.polygon) == 3


def test_class_name_must_be_nonempty():
    with pytest.raises(ValidationError):
        AnnotationObject(cls="   ", polygon=_tri())


def test_non_finite_coordinate_rejected():
    with pytest.raises(ValidationError):
        Point(x=math.inf, y=0)


def test_stored_roundtrip_uses_class_key():
    obj = AnnotationObject(cls="tree", polygon=_tri())
    stored = obj.model_dump_stored()
    assert stored["class"] == "tree"
    assert stored["polygon"] == [[0, 0], [10, 0], [5, 8]]
    back = AnnotationObject.from_stored(stored)
    assert back.cls == "tree" and len(back.polygon) == 3
