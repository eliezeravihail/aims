"""Tests for the pure tile geometry: grid layout, coordinate remap, clipping."""

from __future__ import annotations

import pytest

from app import tiling
from app.tiling import Tile


# --------------------------------------------------------------------------- #
# plan_tiles
# --------------------------------------------------------------------------- #

def test_single_tile_when_image_smaller_than_tile():
    tiles = tiling.plan_tiles(100, 80, tile_size=256, overlap=32)
    assert len(tiles) == 1
    t = tiles[0]
    # Tile is clamped down to the image; no padding.
    assert (t.x, t.y, t.width, t.height) == (0, 0, 100, 80)


def test_grid_covers_whole_image_with_overlap():
    # 100 wide, 60px tiles, 20px overlap -> step 40 -> x origins {0, 40}.
    tiles = tiling.plan_tiles(100, 50, tile_size=60, overlap=20)
    xs = sorted({t.x for t in tiles})
    assert xs == [0, 40]
    # Every tile is full-size; the last one is clamped to end at the image edge.
    assert all(t.width == 60 for t in tiles)
    assert max(t.x + t.width for t in tiles) == 100  # right edge fully covered


def test_last_tile_clamped_not_run_off_the_edge():
    # 100 wide, 64px tiles, 0 overlap -> naive origins {0, 64}; 64+64=128 > 100,
    # so the last origin clamps to 100-64 = 36.
    tiles = tiling.plan_tiles(100, 64, tile_size=64, overlap=0)
    xs = sorted({t.x for t in tiles})
    assert xs == [0, 36]


def test_overlap_must_be_smaller_than_tile():
    with pytest.raises(ValueError):
        tiling.plan_tiles(100, 100, tile_size=50, overlap=50)


# --------------------------------------------------------------------------- #
# Coordinate remap
# --------------------------------------------------------------------------- #

def test_to_local_remaps_a_known_point():
    tile = Tile(row=0, col=1, x=36, y=0, width=64, height=64)
    # A point at (50, 10) in the original image lands at (14, 10) in the tile.
    assert tile.to_local([50, 10]) == [14, 10]


# --------------------------------------------------------------------------- #
# Polygon clipping
# --------------------------------------------------------------------------- #

def test_polygon_fully_inside_tile_is_translated_only():
    tile = Tile(row=0, col=0, x=40, y=40, width=60, height=60)
    square = [[50, 50], [70, 50], [70, 70], [50, 70]]
    local = tiling.clip_polygon_to_tile(square, tile)
    assert local == [[10, 10], [30, 10], [30, 30], [10, 30]]


def test_polygon_fully_outside_tile_is_absent():
    tile = Tile(row=0, col=0, x=0, y=0, width=60, height=50)
    faraway = [[80, 10], [90, 10], [90, 30], [80, 30]]
    assert tiling.clip_polygon_to_tile(faraway, tile) == []


def test_polygon_straddling_boundary_is_clipped_per_tile():
    # Object spans x=50..70. Left tile covers x[0,60); right tile x[40,100).
    left = Tile(row=0, col=0, x=0, y=0, width=60, height=50)
    right = Tile(row=0, col=1, x=40, y=0, width=60, height=50)
    obj = [[50, 10], [70, 10], [70, 30], [50, 30]]

    left_local = tiling.clip_polygon_to_tile(obj, left)
    right_local = tiling.clip_polygon_to_tile(obj, right)

    # Present in BOTH tiles (overlap keeps the border object usable in each).
    assert left_local and right_local
    # Left tile keeps x 50..60 -> local 50..60.
    assert max(p[0] for p in left_local) == 60
    assert min(p[0] for p in left_local) == 50
    # Right tile (origin x=40) keeps the whole object -> local x 10..30.
    assert min(p[0] for p in right_local) == 10
    assert max(p[0] for p in right_local) == 30


def test_polygon_only_grazing_an_edge_is_absent():
    # Object entirely at x>=60, touching the left tile's x=60 edge with 0 area.
    tile = Tile(row=0, col=0, x=0, y=0, width=60, height=50)
    obj = [[60, 10], [70, 10], [70, 30], [60, 30]]
    assert tiling.clip_polygon_to_tile(obj, tile) == []


def test_polygon_area_shoelace():
    assert tiling.polygon_area([[0, 0], [10, 0], [10, 10], [0, 10]]) == 100.0
