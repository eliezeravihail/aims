"""Image pixels — the one place Pillow is used.

Confines the image library to this module so the rest of the app depends on a ``(width, height)`` size
and a "crop this box to that file" operation, not on Pillow. Replacing the image library means replacing
only this module.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image


def probe_size(path: Path) -> tuple[int, int]:
    """Return an image's true pixel ``(width, height)`` without loading pixel data."""
    with Image.open(path) as img:
        return int(img.width), int(img.height)


def crop_to_file(src: Path, box: tuple[int, int, int, int], dest: Path) -> None:
    """Crop ``box`` (x0, y0, x1, y1; right/bottom exclusive) out of ``src`` and save it to ``dest``.

    The one place pixel data is decoded/encoded. Keeps every image-library call in this module so the
    export path depends on this seam, not on Pillow. ``dest``'s suffix selects the output encoding.
    """
    with Image.open(src) as img:
        img.crop(box).save(dest)
