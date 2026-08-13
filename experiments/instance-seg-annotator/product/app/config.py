"""Runtime configuration: mount paths and the project class list.

Reads environment (with sane defaults for local dev) and loads the class list
from a JSON file. The class list is a *confined* choice — a project config file,
swappable — so it lives on disk, not baked into code.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .model import ClassList

# Default mount points inside the container (see docker-compose.yml).
INPUT_DIR = Path(os.environ.get("INPUT_DIR", "/data/images"))
ANNOTATIONS_DIR = Path(os.environ.get("ANNOTATIONS_DIR", "/data/annotations"))
CLASSES_FILE = Path(os.environ.get("CLASSES_FILE", str(Path(__file__).parent / "classes.default.json")))

# Fallback class list if no file is present at all.
_FALLBACK = [
    {"id": "building", "name": "Building", "color": "#e6194b"},
    {"id": "vehicle", "name": "Vehicle", "color": "#3cb44b"},
    {"id": "vegetation", "name": "Vegetation", "color": "#4363d8"},
]


def load_class_list() -> ClassList:
    """Load the project class list from CLASSES_FILE, else the built-in fallback."""
    if CLASSES_FILE.exists():
        items = json.loads(CLASSES_FILE.read_text(encoding="utf-8"))
    else:
        items = _FALLBACK
    return ClassList.from_list(items)
