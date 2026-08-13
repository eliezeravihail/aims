"""Tile geometry: cutting a large image's coordinate space into overlapping
tiles, and clipping annotation polygons to each tile.

This module is deliberately **pure geometry** — no Pillow, no filesystem, no
knowledge of any export format. It answers two questions:

  1. *Where* are the tiles? (:func:`plan_tiles`)
  2. What does an object polygon look like *inside* a given tile, in that
     tile's own pixel coordinates? (:func:`clip_polygon_to_tile`)

Coordinate convention matches the rest of the app: every point is ``[x, y]`` in
the *original image's* pixel space (x rightward, y downward). A tile's local
space has the same axes with its origin shifted to the tile's top-left corner,
so remapping a point is a subtraction (see :meth:`Tile.to_local`).

Objects that straddle a tile boundary are handled by clipping: the part of the
polygon that falls inside the tile is kept (in tile-local coordinates) and the
rest is discarded. Because tiles overlap, a border object is clipped
independently into every tile it touches, so it survives — usably — in each.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

# A point is an [x, y] pair; a polygon is a list of them (matching models.Point).
Point = Sequence[float]
Polygon = List[List[float]]


@dataclass(frozen=True)
class Tile:
    """One tile's placement in the original image.

    ``(x, y)`` is the top-left corner in original-image pixels; ``width`` and
    ``height`` are the tile's pixel size. ``row``/``col`` index the tile in the
    grid (row 0 / col 0 is top-left) and are used to name the tile file.

    The covered region is the half-open box ``[x, x + width) x [y, y + height)``.
    """

    row: int
    col: int
    x: int
    y: int
    width: int
    height: int

    @property
    def box(self) -> Tuple[int, int, int, int]:
        """``(left, upper, right, lower)`` — the crop box (right/lower exclusive)."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def to_local(self, point: Point) -> List[float]:
        """Remap an original-image point into this tile's local pixel space."""
        return [point[0] - self.x, point[1] - self.y]


def _axis_origins(length: int, tile: int, step: int) -> List[int]:
    """Top-left origins along one axis so tiles of size ``tile`` (stepping by
    ``step``) cover ``[0, length)`` with no gaps.

    If the image is no larger than a tile, there is a single origin at 0. The
    final origin is clamped to ``length - tile`` so the last tile ends exactly
    at the image edge rather than running past it — the trade is that the last
    tile overlaps its neighbour by more than ``overlap`` when the image length
    is not an exact multiple of ``step``. Every tile therefore has the full
    ``tile`` size (no undersized edge tiles, no padding).
    """
    if length <= tile:
        return [0]
    origins = list(range(0, length - tile + 1, step))
    last = length - tile
    if origins[-1] != last:
        origins.append(last)
    return origins


def plan_tiles(
    image_width: int,
    image_height: int,
    tile_size: int,
    overlap: int,
) -> List[Tile]:
    """Lay a grid of overlapping tiles over an image.

    Args:
        image_width / image_height: the source image size in pixels.
        tile_size: desired tile edge length in pixels (square tiles).
        overlap: pixels of overlap between adjacent tiles. Must be smaller than
            ``tile_size``; an object within ``overlap`` pixels of a boundary is
            therefore captured whole by at least one tile.

    Returns tiles in row-major order (row 0 top). Tile size is clamped down to
    the image on either axis when the image is smaller than ``tile_size``.
    """
    if tile_size < 1:
        raise ValueError("tile_size must be >= 1")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= tile_size:
        raise ValueError("overlap must be smaller than tile_size")
    if image_width < 1 or image_height < 1:
        raise ValueError("image dimensions must be >= 1")

    step = tile_size - overlap
    tw = min(tile_size, image_width)
    th = min(tile_size, image_height)
    xs = _axis_origins(image_width, tile_size, step)
    ys = _axis_origins(image_height, tile_size, step)

    tiles: List[Tile] = []
    for row, y in enumerate(ys):
        for col, x in enumerate(xs):
            tiles.append(Tile(row=row, col=col, x=x, y=y, width=tw, height=th))
    return tiles


# --------------------------------------------------------------------------- #
# Polygon clipping (Sutherland–Hodgman against an axis-aligned rectangle)
# --------------------------------------------------------------------------- #

def _clip_against_edge(
    poly: Polygon,
    inside,
    intersect,
) -> Polygon:
    """One Sutherland–Hodgman pass: keep the part of ``poly`` on the inside of a
    single half-plane, inserting intersection points where edges cross it."""
    if not poly:
        return []
    out: Polygon = []
    prev = poly[-1]
    prev_in = inside(prev)
    for cur in poly:
        cur_in = inside(cur)
        if cur_in:
            if not prev_in:
                out.append(intersect(prev, cur))
            out.append([cur[0], cur[1]])
        elif prev_in:
            out.append(intersect(prev, cur))
        prev, prev_in = cur, cur_in
    return out


def clip_polygon_to_box(
    points: Polygon,
    box: Tuple[float, float, float, float],
) -> Polygon:
    """Clip a polygon to the rectangle ``box = (left, top, right, bottom)``.

    Uses the Sutherland–Hodgman algorithm against the four rectangle edges. The
    rectangle is convex, so the result is a single polygon (empty if the input
    lies entirely outside). Coordinates stay in the input's space; the caller
    remaps to tile-local space afterwards.
    """
    left, top, right, bottom = box

    def _cross_x(a: Point, b: Point, x: float) -> List[float]:
        # Interpolate the y where segment a->b crosses vertical line X = x.
        t = (x - a[0]) / (b[0] - a[0]) if b[0] != a[0] else 0.0
        return [x, a[1] + t * (b[1] - a[1])]

    def _cross_y(a: Point, b: Point, y: float) -> List[float]:
        # Interpolate the x where segment a->b crosses horizontal line Y = y.
        t = (y - a[1]) / (b[1] - a[1]) if b[1] != a[1] else 0.0
        return [a[0] + t * (b[0] - a[0]), y]

    poly: Polygon = [[p[0], p[1]] for p in points]
    poly = _clip_against_edge(poly, lambda p: p[0] >= left, lambda a, b: _cross_x(a, b, left))
    poly = _clip_against_edge(poly, lambda p: p[0] <= right, lambda a, b: _cross_x(a, b, right))
    poly = _clip_against_edge(poly, lambda p: p[1] >= top, lambda a, b: _cross_y(a, b, top))
    poly = _clip_against_edge(poly, lambda p: p[1] <= bottom, lambda a, b: _cross_y(a, b, bottom))
    return poly


def polygon_area(points: Polygon) -> float:
    """Absolute area of a polygon via the shoelace formula."""
    n = len(points)
    if n < 3:
        return 0.0
    acc = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        acc += x1 * y2 - x2 * y1
    return abs(acc) / 2.0


def clip_polygon_to_tile(points: Polygon, tile: Tile, min_area: float = 1.0) -> Polygon:
    """Clip an object polygon to ``tile`` and return it in tile-local pixels.

    Returns ``[]`` when the object does not have a usable (>= ``min_area``)
    presence inside the tile — i.e. it is outside the tile, or only grazes an
    edge with effectively zero area. Otherwise the returned polygon has at least
    3 vertices, all within ``[0, width] x [0, height]``.
    """
    clipped = clip_polygon_to_box(points, tile.box)
    if len(clipped) < 3 or polygon_area(clipped) < min_area:
        return []
    return [tile.to_local(p) for p in clipped]
