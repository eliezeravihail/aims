"""Cut a source image's annotations into overlapping tiles. Pure, no I/O.

The one owner of *tile geometry*: given an image size and (tile size, overlap),
it lays out the grid of overlapping tiles, remaps instance vertices into each
tile's local pixel space, and clips polygons to the tile bounds. It consumes the
annotation model as-is (`from .model import AnnotationDocument`) and produces the
same model back — a tile is just an image + instances in *that tile's* pixel
space, so a per-tile result is itself an `AnnotationDocument`. Nothing here reads
or writes files, opens images, or knows the export format; that is `export.py`.

Coordinate contract:
- Input geometry is in ORIGINAL-IMAGE pixels (the model's contract).
- A tile has a top-left origin `(x0, y0)` in original-image pixels and a size
  `(width, height)`. Tile-local pixel coordinates are `(x - x0, y - y0)`, so the
  image-space point `(x0, y0)` lands at tile-local `(0, 0)`.

Clipping is Sutherland-Hodgman against the axis-aligned tile rectangle
`[0, width] x [0, height]` in tile-local space:
- an instance fully inside a tile is copied unchanged;
- an instance straddling a tile border is clipped to the border;
- an instance fully outside a tile does not appear in that tile;
- because tiles overlap, a border instance can appear (clipped) in more than one
  tile.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .model import AnnotationDocument, Instance, Vertex

# A clipped polygon whose enclosed area is at or below this (square pixels) is a
# degenerate sliver (a line or point produced by clipping exactly along a border)
# and is dropped rather than emitted as an instance.
_MIN_AREA = 1e-9


@dataclass(frozen=True)
class Tile:
    """One tile's placement in original-image pixel space.

    `x0, y0` is the top-left origin; `width, height` the tile size in pixels
    (clamped so the tile never extends past the image edge). `col, row` are the
    tile's grid indices. Immutable, so a layout can never be edited under geometry
    already remapped against it.
    """

    x0: int
    y0: int
    width: int
    height: int
    col: int
    row: int


def _origins(extent: int, tile: int, stride: int) -> list[int]:
    """Start offsets covering `extent` with windows of `tile`, step `stride`.

    Windows are clamped to lie fully within `[0, extent]`. The final window is
    always anchored to the far edge (`extent - tile`) so the whole image is
    covered even when `extent` is not a whole number of strides. If the image is
    smaller than a tile, a single window at 0 is returned.
    """
    if extent <= tile:
        return [0]
    last = extent - tile
    out: list[int] = []
    x = 0
    while x < last:
        out.append(x)
        x += stride
    out.append(last)
    return out


def tile_grid(image_width: int, image_height: int, tile_size: int, overlap: int) -> list[Tile]:
    """Lay out overlapping tiles over an `image_width` x `image_height` image.

    `tile_size` is the square tile edge in pixels; `overlap` is how many pixels
    adjacent tiles share (stride = `tile_size - overlap`). Tiles are clamped to
    the image, so a tile is at most `tile_size` on a side and never smaller than
    the image when the image is smaller than a tile.
    """
    if tile_size <= 0:
        raise ValueError(f"tile_size must be positive, got {tile_size}")
    if overlap < 0:
        raise ValueError(f"overlap must be >= 0, got {overlap}")
    if overlap >= tile_size:
        raise ValueError(f"overlap ({overlap}) must be < tile_size ({tile_size})")
    if image_width <= 0 or image_height <= 0:
        raise ValueError(f"image size must be positive, got {image_width}x{image_height}")

    stride = tile_size - overlap
    tw = min(tile_size, image_width)
    th = min(tile_size, image_height)
    xs = _origins(image_width, tw, stride)
    ys = _origins(image_height, th, stride)

    tiles: list[Tile] = []
    for row, y0 in enumerate(ys):
        for col, x0 in enumerate(xs):
            tiles.append(Tile(x0=x0, y0=y0, width=tw, height=th, col=col, row=row))
    return tiles


def remap_vertex(v: Vertex, tile: Tile) -> Vertex:
    """Translate an image-space vertex into `tile`-local pixel coordinates."""
    return (v[0] - tile.x0, v[1] - tile.y0)


def clip_polygon(vertices: tuple[Vertex, ...], width: float, height: float) -> tuple[Vertex, ...]:
    """Clip a polygon to the rectangle [0, width] x [0, height] (tile-local).

    Sutherland-Hodgman against the four tile edges. Returns the clipped polygon's
    vertices (possibly empty if the polygon lies entirely outside the rectangle).
    Input vertices are assumed to be in tile-local space already.
    """
    # Each edge is a half-plane keep-test + segment/edge intersection.
    def clip_edge(poly: list[Vertex], keep, intersect) -> list[Vertex]:
        if not poly:
            return poly
        out: list[Vertex] = []
        prev = poly[-1]
        prev_in = keep(prev)
        for cur in poly:
            cur_in = keep(cur)
            if cur_in:
                if not prev_in:
                    out.append(intersect(prev, cur))
                out.append(cur)
            elif prev_in:
                out.append(intersect(prev, cur))
            prev, prev_in = cur, cur_in
        return out

    def lerp(a: Vertex, b: Vertex, t: float) -> Vertex:
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    poly: list[Vertex] = list(vertices)
    # left: x >= 0
    poly = clip_edge(poly, lambda p: p[0] >= 0.0,
                     lambda a, b: lerp(a, b, (0.0 - a[0]) / (b[0] - a[0])))
    # right: x <= width
    poly = clip_edge(poly, lambda p: p[0] <= width,
                     lambda a, b: lerp(a, b, (width - a[0]) / (b[0] - a[0])))
    # top: y >= 0
    poly = clip_edge(poly, lambda p: p[1] >= 0.0,
                     lambda a, b: lerp(a, b, (0.0 - a[1]) / (b[1] - a[1])))
    # bottom: y <= height
    poly = clip_edge(poly, lambda p: p[1] <= height,
                     lambda a, b: lerp(a, b, (height - a[1]) / (b[1] - a[1])))
    return tuple(poly)


def polygon_area(vertices: tuple[Vertex, ...]) -> float:
    """Absolute enclosed area of a polygon via the shoelace formula."""
    n = len(vertices)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) * 0.5


def tile_instance(ins: Instance, tile: Tile) -> Instance | None:
    """Remap + clip one instance into `tile`. None if it does not survive.

    Returns None when the clipped polygon is absent (instance fully outside the
    tile) or degenerate (a sliver clipped exactly along a border with < 3
    vertices or ~zero area). The class id is carried through unchanged.
    """
    local = tuple(remap_vertex(v, tile) for v in ins.vertices)
    clipped = clip_polygon(local, float(tile.width), float(tile.height))
    if len(clipped) < 3 or polygon_area(clipped) <= _MIN_AREA:
        return None
    return Instance(class_id=ins.class_id, vertices=clipped)


def tile_name(image: str, tile: Tile) -> str:
    """Stable per-tile identifier derived from the source image stem + origin."""
    stem = Path(image).stem
    return f"{stem}_x{tile.x0}_y{tile.y0}"


def tile_document(doc: AnnotationDocument, tile: Tile) -> AnnotationDocument:
    """Build the per-tile `AnnotationDocument` for one tile (tile-local pixels).

    `image` is the tile's identifier; `width/height` are the tile size; instances
    are the source instances remapped and clipped into this tile (those fully
    outside are omitted). A tile with no surviving instances yields a valid empty
    document.
    """
    kept: list[Instance] = []
    for ins in doc.instances:
        t = tile_instance(ins, tile)
        if t is not None:
            kept.append(t)
    return AnnotationDocument(
        image=tile_name(doc.image, tile),
        width=tile.width,
        height=tile.height,
        instances=tuple(kept),
    )


def tile_all(
    doc: AnnotationDocument, tile_size: int, overlap: int
) -> list[tuple[Tile, AnnotationDocument]]:
    """Tile a whole document: the grid + each tile's local, clipped document."""
    grid = tile_grid(doc.width, doc.height, tile_size, overlap)
    return [(tile, tile_document(doc, tile)) for tile in grid]
