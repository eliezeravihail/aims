"""Application configuration.

The only thing this tool needs to be told is *where the data lives*: the
folder on the user's disk that holds their images and receives their saved
annotations. Everything else is derived from that.
"""

from __future__ import annotations

import os
from pathlib import Path

# Name of the sub-folder (created inside the user's data folder) where we keep
# annotation sidecar files and the class list. Kept dot-prefixed so it stays
# out of the way of the user's own image files.
ANNOTATION_DIRNAME = ".annotations"

# The class list is stored as a single file inside the annotation folder.
CLASSES_FILENAME = "classes.json"

# Image extensions we recognise. The product brief scopes this to PNG + JPEG.
IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg"})


def get_data_dir() -> Path:
    """Return the folder the tool reads images from and writes annotations to.

    Configured via the DATA_DIR environment variable (the container mounts the
    user's chosen folder there). Falls back to ``./data`` for local runs.
    """
    raw = os.environ.get("DATA_DIR", "data")
    return Path(raw).expanduser().resolve()
