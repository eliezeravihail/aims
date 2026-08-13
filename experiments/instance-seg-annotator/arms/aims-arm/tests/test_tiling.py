import pytest

from app.tiling import (
    clip_polygon,
    polygon_area,
    polygon_bbox,
    remap,
    tile_boxes,
)


# ── tile layout ──────────────────────────────────────────────────────────────
def test_image_smaller_than_tile_is_one_tile_of_image_size():
    assert tile_boxes(300, 200, 1024, 128) == [(0, 0, 300, 200)]


def test_tiles_overlap_by_the_configured_amount():
    # tile 100, overlap 20 -> stride 80. width 260 -> origins 0,80,160 and clamp to 160 (260-100).
    boxes = tile_boxes(260, 100, 100, 20)
    xs = sorted({b[0] for b in boxes})
    assert xs == [0, 80, 160]
    # neighbours share 20 px: tile at 0 ends at 100, tile at 80 starts at 80 -> 20 overlap.
    assert 100 - 80 == 20


def test_tiles_cover_the_whole_image_final_tile_clamped_to_edge():
    boxes = tile_boxes(250, 100, 100, 20)  # stride 80: 0,80,160; last needs clamp to 150
    xs = sorted({b[0] for b in boxes})
    assert xs[-1] == 150  # 250 - 100, flush to the right edge
    assert max(b[2] for b in boxes) == 250  # right edge reached -> full coverage


def test_grid_is_product_of_axes():
    boxes = tile_boxes(200, 200, 100, 0)  # stride 100 -> 2x2
    assert len(boxes) == 4
    assert set(boxes) == {(0, 0, 100, 100), (100, 0, 200, 100),
                          (0, 100, 100, 200), (100, 100, 200, 200)}


@pytest.mark.parametrize("tile,overlap", [(0, 0), (-5, 0), (100, 100), (100, 150), (100, -1)])
def test_invalid_tile_or_overlap_rejected(tile, overlap):
    with pytest.raises(ValueError):
        tile_boxes(500, 500, tile, overlap)


# ── clipping + remap ─────────────────────────────────────────────────────────
def _square(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def test_object_fully_inside_tile_is_unchanged():
    poly = _square(10, 10, 40, 40)
    clipped = clip_polygon(poly, (0, 0, 100, 100))
    assert set(clipped) == set(poly)


def test_object_fully_outside_tile_clips_to_nothing():
    poly = _square(200, 200, 260, 260)
    assert clip_polygon(poly, (0, 0, 100, 100)) == []


def test_object_straddling_a_boundary_is_cut_at_the_edge():
    # square from x=80..120 straddles the right edge of a tile ending at x=100.
    poly = _square(80, 20, 120, 60)
    clipped = clip_polygon(poly, (0, 0, 100, 100))
    xs = [p[0] for p in clipped]
    assert max(xs) == 100  # cut exactly at the tile edge
    assert min(xs) == 80   # the inside part is kept


def test_remap_of_a_known_point_is_correct():
    # A point at image (130, 90) inside a tile with origin (100, 50) -> tile-local (30, 40).
    assert remap([(130, 90)], 100, 50) == [(30, 40)]


def test_clip_then_remap_puts_the_straddler_in_tile_local_space():
    poly = _square(80, 20, 120, 60)
    box = (0, 0, 100, 100)
    local = remap(clip_polygon(poly, box), box[0], box[1])
    # inside part x in [80,100] -> local [80,100]; unchanged origin here, but the far edge is 100.
    assert max(p[0] for p in local) == 100
    # a right-neighbour tile at origin 80 sees the same object shifted into its space.
    box2 = (80, 0, 180, 100)
    local2 = remap(clip_polygon(poly, box2), box2[0], box2[1])
    assert min(p[0] for p in local2) == 0   # x=80 -> local 0
    assert max(p[0] for p in local2) == 40  # x=120 -> local 40


def test_area_and_bbox_of_a_unit_square():
    sq = _square(0, 0, 10, 10)
    assert polygon_area(sq) == 100.0
    assert polygon_bbox(sq) == (0, 0, 10, 10)
