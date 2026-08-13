"""Image discovery and inspection.

Responsible for: knowing which files in the data folder are annotatable
images, reading their pixel dimensions, and turning an untrusted filename
from the URL into a safe path inside the data folder (never outside it).
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from . import config


class UnsafeFilenameError(ValueError):
    """Raised when a requested filename tries to escape the data folder."""


class ImageNotFoundError(FileNotFoundError):
    """Raised when a requested image does not exist in the data folder."""


def is_image_file(path: Path) -> bool:
    """True if ``path`` is a file with a recognised image extension."""
    return path.is_file() and path.suffix.lower() in config.IMAGE_EXTENSIONS


def list_image_names(data_dir: Path) -> List[str]:
    """Return image filenames in the data folder, sorted case-insensitively.

    Only the top level is scanned (the annotation sub-folder is skipped by
    virtue of not containing image extensions). Missing folders yield [].
    """
    if not data_dir.is_dir():
        return []
    names = [p.name for p in data_dir.iterdir() if is_image_file(p)]
    return sorted(names, key=str.lower)


def safe_image_path(data_dir: Path, name: str) -> Path:
    """Resolve ``name`` to a path inside ``data_dir``, or raise.

    Rejects any name that contains path separators or otherwise resolves
    outside the data folder (defence against ``../`` traversal).
    """
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        raise UnsafeFilenameError(name)
    candidate = (data_dir / name).resolve()
    if candidate.parent != data_dir.resolve():
        raise UnsafeFilenameError(name)
    if candidate.suffix.lower() not in config.IMAGE_EXTENSIONS:
        raise UnsafeFilenameError(name)
    return candidate


def get_dimensions(path: Path) -> Tuple[int, int]:
    """Return ``(width, height)`` in pixels for the image at ``path``."""
    with Image.open(path) as im:
        return im.width, im.height


def resolve_existing(data_dir: Path, name: str) -> Path:
    """Safe-resolve ``name`` and confirm the file exists, or raise."""
    path = safe_image_path(data_dir, name)
    if not is_image_file(path):
        raise ImageNotFoundError(name)
    return path
