"""Persistence of annotations and the class list.

Storage shape (all inside the user's data folder):

    <data>/<image>.jpg               the user's images
    <data>/.annotations/<image>.jpg.json   one sidecar per annotated image
    <data>/.annotations/classes.json       the configurable class list

Sidecar JSON files are chosen deliberately: they are human-readable, diffable,
survive being copied around next to the images, and need no database or schema
migration for a single-user local tool. Writes are atomic (temp file + rename)
so an interrupted save can never corrupt existing work.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import List

from . import config, images
from .models import Annotation, AnnotationObject, ClassDef, ClassList

# Seed classes offered the first time the tool runs against a fresh folder.
_DEFAULT_CLASSES = [
    ClassDef(name="car", color="#e6194b"),
    ClassDef(name="tree", color="#3cb44b"),
    ClassDef(name="building", color="#4363d8"),
]


def _annotation_dir(data_dir: Path) -> Path:
    return data_dir / config.ANNOTATION_DIRNAME


def _ensure_annotation_dir(data_dir: Path) -> Path:
    d = _annotation_dir(data_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _atomic_write_json(path: Path, payload: dict) -> None:
    """Write JSON to ``path`` atomically (never leave a half-written file)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# --------------------------------------------------------------------------- #
# Annotations
# --------------------------------------------------------------------------- #

def annotation_path(data_dir: Path, image_name: str) -> Path:
    """Path of the sidecar for ``image_name`` (does not check existence)."""
    return _annotation_dir(data_dir) / f"{image_name}.json"


def load_annotation(data_dir: Path, image_name: str) -> Annotation:
    """Load saved annotation for an image.

    If none exists yet, return an empty annotation carrying the image's true
    pixel dimensions, so the frontend always has a valid coordinate frame.
    """
    path = annotation_path(data_dir, image_name)
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        return Annotation.model_validate(data)

    img_path = images.resolve_existing(data_dir, image_name)
    width, height = images.get_dimensions(img_path)
    return Annotation(image=image_name, width=width, height=height, objects=[])


def save_annotation(data_dir: Path, annotation: Annotation) -> Annotation:
    """Persist an annotation. An empty object list deletes the sidecar."""
    path = annotation_path(data_dir, annotation.image)
    if not annotation.objects:
        if path.is_file():
            path.unlink()
        return annotation
    _ensure_annotation_dir(data_dir)
    _atomic_write_json(path, annotation.model_dump())
    return annotation


def object_count(data_dir: Path, image_name: str) -> int:
    """Number of saved objects for an image (0 if never annotated)."""
    path = annotation_path(data_dir, image_name)
    if not path.is_file():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    return len(data.get("objects", []))


# --------------------------------------------------------------------------- #
# Class list
# --------------------------------------------------------------------------- #

def _classes_path(data_dir: Path) -> Path:
    return _annotation_dir(data_dir) / config.CLASSES_FILENAME


def load_classes(data_dir: Path) -> ClassList:
    """Load the class list, seeding sensible defaults on first run."""
    path = _classes_path(data_dir)
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        return ClassList.model_validate(data)
    defaults = ClassList(classes=list(_DEFAULT_CLASSES))
    save_classes(data_dir, defaults)
    return defaults


def save_classes(data_dir: Path, class_list: ClassList) -> ClassList:
    """Persist the class list."""
    _ensure_annotation_dir(data_dir)
    _atomic_write_json(_classes_path(data_dir), class_list.model_dump())
    return class_list
