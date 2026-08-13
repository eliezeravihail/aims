"""Stage-2 tiling geometry: grid layout, coordinate remap, polygon clipping.

Pure-geometry exit criteria: an instance straddling a tile border is clipped to
the tile; an instance fully outside a tile is absent; overlap lets a border
instance appear (clipped) in more than one tile; a known image-space point lands
at the right tile-local pixel; empty tiles yield valid empty documents.
"""

import pytest

from app.model import AnnotationDocument, Instance
from app.tiling import (
    Tile,
    clip_polygon,
    polygon_area,
    remap_vertex,
    tile_all,
    tile_document,
    tile_grid,
    tile_instance,
)


# --- grid layout ----------------------------------------------------------

def test_grid_single_tile_when_image_smaller_than_tile():
    grid = tile_grid(100, 80, 256, 32)
    assert len(grid) == 1
    t = grid[0]
    assert (t.x0, t.y0, t.width, t.height) == (0, 0, 100, 80)


def test_grid_overlap_produces_shared_stride():
    # 512 wide, 256 tile, 64 overlap -> stride 192: origins 0,192,256(clamped edge)
    grid = tile_grid(512, 256, 256, 64)
    xs = sorted({t.x0 for t in grid})
    assert xs == [0, 192, 256]
    # every tile is a full 256-square, clamped inside the image
    for t in grid:
        assert t.width == 256 and t.height == 256
        assert t.x0 + t.width <= 512 and t.y0 + t.height <= 256


def test_grid_far_edge_is_covered():
    grid = tile_grid(500, 500, 200, 0)
    xs = sorted({t.x0 for t in grid})
    # last origin anchored to far edge so pixel 499 is inside some tile
    assert xs[-1] == 300
    assert max(t.x0 + t.width for t in grid) == 500


def test_grid_rejects_overlap_ge_tile():
    with pytest.raises(ValueError):
        tile_grid(100, 100, 64, 64)


# --- coordinate remap -----------------------------------------------------

def test_remap_origin_lands_at_tile_local_zero():
    tile = Tile(x0=300, y0=200, width=256, height=256, col=1, row=1)
    assert remap_vertex((300.0, 200.0), tile) == (0.0, 0.0)


def test_remap_known_point():
    tile = Tile(x0=300, y0=200, width=256, height=256, col=1, row=1)
    # image-space (350, 260) is 50 px right, 60 px down from the tile origin
    assert remap_vertex((350.0, 260.0), tile) == (50.0, 60.0)


# --- polygon clipping -----------------------------------------------------

def test_polygon_fully_inside_is_unchanged():
    poly = ((10.0, 10.0), (40.0, 10.0), (40.0, 40.0), (10.0, 40.0))
    assert clip_polygon(poly, 100.0, 100.0) == poly


def test_polygon_straddling_border_is_clipped_to_bounds():
    # square from x=80..120 against a 100-wide tile -> clipped to x<=100
    poly = ((80.0, 10.0), (120.0, 10.0), (120.0, 40.0), (80.0, 40.0))
    clipped = clip_polygon(poly, 100.0, 100.0)
    assert clipped  # non-empty
    assert max(x for x, _ in clipped) == 100.0
    assert min(x for x, _ in clipped) == 80.0
    # area halved (40x30 -> 20x30)
    assert polygon_area(clipped) == pytest.approx(20.0 * 30.0)


def test_polygon_fully_outside_clips_to_empty():
    poly = ((200.0, 200.0), (250.0, 200.0), (225.0, 260.0))
    assert clip_polygon(poly, 100.0, 100.0) == ()


# --- per-instance tiling --------------------------------------------------

def test_instance_fully_outside_tile_is_none():
    tile = Tile(x0=0, y0=0, width=100, height=100, col=0, row=0)
    ins = Instance("building", ((200.0, 200.0), (250.0, 200.0), (225.0, 260.0)))
    assert tile_instance(ins, tile) is None


def test_instance_inside_tile_is_remapped():
    tile = Tile(x0=100, y0=100, width=100, height=100, col=1, row=1)
    ins = Instance("building", ((110.0, 110.0), (150.0, 110.0), (130.0, 150.0)))
    out = tile_instance(ins, tile)
    assert out is not None
    assert out.class_id == "building"
    assert out.vertices == ((10.0, 10.0), (50.0, 10.0), (30.0, 50.0))


def test_border_instance_appears_clipped_in_two_overlapping_tiles():
    """Overlap means a border-straddling instance survives in >1 tile."""
    # one 200x100 image, 120-tile, 40 overlap -> x origins 0 and 80, both cover x~=100
    doc = AnnotationDocument("sat.tif", 200, 100, (
        Instance("building", ((90.0, 30.0), (130.0, 30.0), (130.0, 70.0), (90.0, 70.0))),
    ))
    tiled = tile_all(doc, tile_size=120, overlap=40)
    hits = [(tile, tdoc) for tile, tdoc in tiled if tdoc.instances]
    # instance at x=90..130 falls inside both the x0=0 (0..120) and x0=80 (80..200) tiles
    assert len(hits) >= 2
    # and in the x0=0 tile it is clipped (x<=120), i.e. width < original 40
    left = next(td for t, td in hits if t.x0 == 0)
    max_local_x = max(x for ins in left.instances for x, _ in ins.vertices)
    assert max_local_x == pytest.approx(120.0)  # clipped to tile-local right edge


# --- document-level -------------------------------------------------------

def test_tile_document_names_and_sizes():
    doc = AnnotationDocument("scene_01.png", 300, 200, ())
    tile = Tile(x0=100, y0=50, width=128, height=128, col=1, row=0)
    tdoc = tile_document(doc, tile)
    assert tdoc.image == "scene_01_x100_y50"
    assert (tdoc.width, tdoc.height) == (128, 128)


def test_empty_tile_yields_valid_empty_document():
    doc = AnnotationDocument("sat.tif", 400, 400, (
        Instance("building", ((10.0, 10.0), (40.0, 10.0), (40.0, 40.0))),
    ))
    tiled = tile_all(doc, tile_size=100, overlap=0)
    # the far-corner tile has no instances but is still present and valid
    empties = [td for _t, td in tiled if not td.instances]
    assert empties, "expected some empty tiles"
    for td in empties:
        assert td.instances == ()
        assert td.width > 0 and td.height > 0
