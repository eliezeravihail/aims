"""List source images from the input folder and read their pixel dimensions.

The one owner of 'what images exist and how big are they'. Uses Pillow only to
read dimensions; it never decodes pixels for the model. Kept separate from
storage (annotations) because images are read-only inputs on a different volume.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

# Formats a browser <img>/canvas can display and Pillow can size.
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


def list_images(input_dir: Path) -> list[str]:
    """Return sorted image filenames (basenames) directly under `input_dir`."""
    d = Path(input_dir)
    if not d.is_dir():
        return []
    return sorted(
        p.name
        for p in d.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
    )


def image_size(input_dir: Path, name: str) -> tuple[int, int]:
    """Return (width, height) in original pixels for one image."""
    path = _safe_image_path(input_dir, name)
    with Image.open(path) as im:
        return int(im.width), int(im.height)


def image_file(input_dir: Path, name: str) -> Path:
    """Resolve an image name to a path, guarding against directory traversal."""
    return _safe_image_path(input_dir, name)


def _safe_image_path(input_dir: Path, name: str) -> Path:
    base = Path(name).name  # strip any directory components
    path = Path(input_dir) / base
    if not path.is_file():
        raise FileNotFoundError(f"no such image: {base!r}")
    if path.suffix.lower() not in IMAGE_SUFFIXES:
        raise FileNotFoundError(f"not an allowed image: {base!r}")
    return path
