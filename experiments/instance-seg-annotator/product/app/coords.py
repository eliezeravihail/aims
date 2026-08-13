"""Image <-> viewport coordinate transform. Pure, no I/O, no framework imports.

This is the ONLY place that knows how a viewport (zoom + pan) maps to and from
original-image pixel space. Annotations are always defined and persisted in
image space; the viewport transform exists solely for display and pointer input.

Viewport model (2D affine, uniform scale + translation):

    viewport = image * scale + (tx, ty)
    image    = (viewport - (tx, ty)) / scale

`scale` is the zoom factor (viewport pixels per image pixel); (tx, ty) is the
pan offset (viewport pixels). No rotation or shear: an instance-seg annotator
pans and zooms, it does not rotate the canvas.

The invariance guarantee for saved coordinates is structural, not incidental:
the persisted geometry is whatever the caller holds in image space. A viewport
transform only affects the *round trip* used to interpret pointer input and to
paint; it can never mutate an image-space coordinate. `viewport_to_image` is the
single funnel that pointer input passes through before it becomes annotation
geometry, so nothing downstream ever sees viewport units.
"""

from __future__ import annotations

from dataclasses import dataclass

Point = tuple[float, float]


@dataclass(frozen=True)
class ViewportTransform:
    """A display transform: uniform zoom about the origin plus a pan offset.

    Immutable so a transform can never be edited in place under stored geometry.
    """

    scale: float = 1.0
    tx: float = 0.0
    ty: float = 0.0

    def __post_init__(self) -> None:
        if self.scale <= 0:
            raise ValueError(f"scale must be positive, got {self.scale}")

    def zoomed(self, factor: float, center: Point = (0.0, 0.0)) -> "ViewportTransform":
        """Return a new transform zoomed by `factor` about a viewport-space point.

        The image point currently under `center` stays under `center` after the
        zoom (standard zoom-to-cursor). Returns a new transform; never mutates.
        """
        if factor <= 0:
            raise ValueError(f"factor must be positive, got {factor}")
        cx, cy = center
        new_scale = self.scale * factor
        # Keep the image point under `center` fixed:
        #   center = img*new_scale + tx'  and  center = img*scale + tx
        new_tx = cx - (cx - self.tx) * factor
        new_ty = cy - (cy - self.ty) * factor
        return ViewportTransform(new_scale, new_tx, new_ty)

    def panned(self, dx: float, dy: float) -> "ViewportTransform":
        """Return a new transform translated by (dx, dy) viewport pixels."""
        return ViewportTransform(self.scale, self.tx + dx, self.ty + dy)


def image_to_viewport(pt: Point, t: ViewportTransform) -> Point:
    """Map an image-space point to viewport space (for painting)."""
    x, y = pt
    return (x * t.scale + t.tx, y * t.scale + t.ty)


def viewport_to_image(pt: Point, t: ViewportTransform) -> Point:
    """Map a viewport-space point (e.g. a mouse click) to image space.

    This is the funnel every pointer sample passes through before it becomes
    annotation geometry, guaranteeing stored coordinates are in image pixels.
    """
    x, y = pt
    return ((x - t.tx) / t.scale, (y - t.ty) / t.scale)
