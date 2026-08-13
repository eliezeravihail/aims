"""Coordinate-transform invariance: the core structural guarantee.

Proves that annotation geometry, once expressed in image space, is unaffected by
any viewport transform (zoom/pan) — exit criterion 2.
"""

import math

import pytest

from app.coords import (
    ViewportTransform,
    image_to_viewport,
    viewport_to_image,
)
from app.model import AnnotationDocument, Instance

# A spread of non-trivial transforms: identity, zoom-in, zoom-out, pan, both.
TRANSFORMS = [
    ViewportTransform(1.0, 0.0, 0.0),
    ViewportTransform(3.7, 0.0, 0.0),
    ViewportTransform(0.25, 0.0, 0.0),
    ViewportTransform(1.0, 140.0, -87.0),
    ViewportTransform(2.5, -300.0, 512.0),
    ViewportTransform(0.13, 999.0, -1234.0),
]

VERTS = [(0.0, 0.0), (12.5, 480.0), (1919.0, 1079.0), (37.2, 6.9)]


@pytest.mark.parametrize("t", TRANSFORMS)
def test_round_trip_recovers_image_coords(t):
    """viewport_to_image(image_to_viewport(p)) == p for every transform."""
    for p in VERTS:
        vp = image_to_viewport(p, t)
        back = viewport_to_image(vp, t)
        assert math.isclose(back[0], p[0], abs_tol=1e-9)
        assert math.isclose(back[1], p[1], abs_tol=1e-9)


def test_stored_document_coords_invariant_to_viewport():
    """Applying viewport transforms never mutates stored image-space vertices.

    This is the exit-criterion-2 assertion: the persisted geometry is defined in
    original-image pixels and does not depend on zoom/pan.
    """
    doc = AnnotationDocument(
        image="x.png", width=1920, height=1080,
        instances=(Instance("building", tuple(VERTS)),),
    )
    stored = doc.to_dict()["instances"][0]["vertices"]

    for t in TRANSFORMS:
        # Simulate the display pipeline: image -> viewport for painting.
        _painted = [image_to_viewport(v, t) for v in doc.instances[0].vertices]
        # The stored/persisted coordinates are untouched by any transform.
        assert doc.to_dict()["instances"][0]["vertices"] == stored


def test_pointer_input_lands_in_image_space():
    """A fixed image point clicked under different zoom/pan resolves identically.

    If a user zooms/pans and clicks the SAME image feature, the recorded vertex
    is the same image-pixel coordinate regardless of transform.
    """
    image_pt = (640.0, 360.0)
    recorded = set()
    for t in TRANSFORMS:
        viewport_click = image_to_viewport(image_pt, t)  # where that feature appears
        recorded_pt = viewport_to_image(viewport_click, t)  # what we store
        recorded.add((round(recorded_pt[0], 6), round(recorded_pt[1], 6)))
    assert recorded == {(640.0, 360.0)}


def test_transforms_are_immutable():
    """zoomed()/panned() return new transforms; the original is never mutated."""
    t = ViewportTransform(1.0, 0.0, 0.0)
    t2 = t.zoomed(2.0, center=(100.0, 100.0))
    t3 = t.panned(10.0, -5.0)
    assert t == ViewportTransform(1.0, 0.0, 0.0)
    assert t2.scale == 2.0 and t2 is not t
    assert (t3.tx, t3.ty) == (10.0, -5.0)


def test_rejects_nonpositive_scale():
    with pytest.raises(ValueError):
        ViewportTransform(0.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        ViewportTransform(-1.0, 0.0, 0.0)
