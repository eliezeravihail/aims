"""Tiling geometry — the single owner of how a large image is cut into overlapping tiles and how a
polygon is clipped and remapped into a tile's local pixel space.

Pure geometry: no Pillow, no filesystem, no HTTP. It speaks in plain numbers and vertex lists so it is
trivially testable and reusable. Two responsibilities:

- **Tile layout** (`tile_boxes`): given an image size, a tile size, and an overlap, produce the set of
  tile boxes that fully cover the image, overlapping by the requested amount.
- **Polygon clipping** (`clip_polygon` + `remap`): cut a polygon (in original-image pixel space) to a
  tile box and translate it into that tile's local coordinates. An object straddling a tile edge is cut
  at the edge and kept for that tile; an object fully outside a tile clips to nothing.

Coordinates in and out are original-image pixel space (the store's persisted space); only `remap`
translates into tile-local space, and only after clipping.
"""
from __future__ import annotations

Point = tuple[float, float]
Box = tuple[int, int, int, int]  # (x0, y0, x1, y1) — right/bottom exclusive, PIL crop convention.


def tile_boxes(width: int, height: int, tile_size: int, overlap: int) -> list[Box]:
    """The tile boxes covering a ``width``x``height`` image with ``overlap`` px shared between neighbours.

    Tiles step by ``stride = tile_size - overlap``. Every tile is exactly ``tile_size`` on a side except
    when the image is smaller than a tile on an axis, in which case that axis spans the whole image (one
    tile). The final tile on an axis is clamped so its far edge meets the image edge, guaranteeing full
    coverage; that last tile may therefore overlap its neighbour by more than ``overlap``.
    """
    if tile_size <= 0:
        raise ValueError("tile_size must be positive")
    if not 0 <= overlap < tile_size:
        raise ValueError("overlap must satisfy 0 <= overlap < tile_size")
    xs = _origins(width, tile_size, tile_size - overlap)
    ys = _origins(height, tile_size, tile_size - overlap)
    boxes: list[Box] = []
    for oy in ys:
        th = min(tile_size, height)
        for ox in xs:
            tw = min(tile_size, width)
            boxes.append((ox, oy, ox + tw, oy + th))
    return boxes


def _origins(dim: int, tile: int, stride: int) -> list[int]:
    """Left/top origins of tiles along one axis of length ``dim``."""
    if dim <= tile:
        return [0]
    origins = list(range(0, dim - tile + 1, stride))
    if origins[-1] != dim - tile:
        origins.append(dim - tile)  # clamp final tile flush to the far edge (full coverage).
    return origins


def clip_polygon(polygon: list[Point], box: Box) -> list[Point]:
    """Clip a polygon to an axis-aligned rectangle, returning the intersection polygon in image space.

    Sutherland–Hodgman against the four half-planes of ``box`` (a convex window). Returns ``[]`` when the
    polygon lies entirely outside the box or the intersection is degenerate (< 3 vertices). Vertices are
    still in original-image coordinates; call :func:`remap` to move them into tile-local space.
    """
    x0, y0, x1, y1 = box
    pts = list(polygon)
    # Each edge: an inside-test and the coordinate at which to interpolate the crossing point.
    pts = _clip_edge(pts, lambda p: p[0] >= x0, axis=0, at=x0)  # left
    pts = _clip_edge(pts, lambda p: p[0] <= x1, axis=0, at=x1)  # right
    pts = _clip_edge(pts, lambda p: p[1] >= y0, axis=1, at=y0)  # top
    pts = _clip_edge(pts, lambda p: p[1] <= y1, axis=1, at=y1)  # bottom
    return pts if len(pts) >= 3 else []


def _clip_edge(pts, inside, axis: int, at: float):
    """Clip a vertex ring against one axis-aligned half-plane (Sutherland–Hodgman step)."""
    if not pts:
        return []
    out: list[Point] = []
    n = len(pts)
    for i in range(n):
        cur = pts[i]
        prev = pts[i - 1]
        cur_in = inside(cur)
        prev_in = inside(prev)
        if cur_in:
            if not prev_in:
                out.append(_intersect(prev, cur, axis, at))
            out.append(cur)
        elif prev_in:
            out.append(_intersect(prev, cur, axis, at))
    return out


def _intersect(a: Point, b: Point, axis: int, at: float) -> Point:
    """Point where segment a→b crosses the line ``coord[axis] == at`` (axis: 0=x, 1=y)."""
    other = 1 - axis
    denom = b[axis] - a[axis]
    t = 0.0 if denom == 0 else (at - a[axis]) / denom
    crossed = a[other] + t * (b[other] - a[other])
    return (at, crossed) if axis == 0 else (crossed, at)


def remap(polygon: list[Point], ox: int, oy: int) -> list[Point]:
    """Translate a polygon from image space into the tile-local space of a tile at origin ``(ox, oy)``."""
    return [(x - ox, y - oy) for (x, y) in polygon]


def polygon_bbox(polygon: list[Point]) -> tuple[float, float, float, float]:
    """Axis-aligned bounding box of a polygon as ``(x, y, width, height)``."""
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


def polygon_area(polygon: list[Point]) -> float:
    """Absolute area of a simple polygon via the shoelace formula."""
    n = len(polygon)
    s = 0.0
    for i in range(n):
        x0, y0 = polygon[i]
        x1, y1 = polygon[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2.0
