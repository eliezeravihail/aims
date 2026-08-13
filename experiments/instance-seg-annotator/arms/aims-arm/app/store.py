"""Workspace store — the single owner of the mounted data folder.

Everything that touches the filesystem lives here: image discovery, the on-disk annotation format, the
class-config file, and path safety (mapping a client-supplied image id to a real file strictly inside the
data root). No other module reads or writes the folder. The seam this module exposes is the ``Workspace``
object; its payloads are pydantic models and plain filenames, never disk paths.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .images import probe_size
from .models import Annotation, AnnotationObject, ClassDef, ClassList

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
ANNOTATIONS_DIRNAME = ".annotations"
EXPORTS_DIRNAME = ".exports"
CLASSES_FILENAME = "classes.json"

# Seeded on first run so the tool is usable immediately; fully editable thereafter.
DEFAULT_CLASSES = [
    ClassDef(name="car", color="#3273dc"),
    ClassDef(name="tree", color="#48c774"),
    ClassDef(name="building", color="#ffdd57"),
]


class ImageNotFound(Exception):
    """Requested image id does not resolve to a real image inside the data root."""


class BadExportName(Exception):
    """Requested export dataset name is not a safe single directory name."""


class Workspace:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.annotations_dir = self.root / ANNOTATIONS_DIRNAME

    # ── path safety (single owner) ───────────────────────────────────────────
    def image_path(self, image_id: str) -> Path:
        """Resolve a client image id to a real image file strictly inside the data root.

        Rejects anything that is not a bare filename living directly in the root with an allowed
        extension: path separators, ``..``, absolute paths, nested ids, and non-existent files all raise
        ``ImageNotFound``. This is the one gate between untrusted ids and the filesystem.
        """
        # A valid id is exactly its own basename — no directory component of any kind.
        if not image_id or image_id != Path(image_id).name:
            raise ImageNotFound(image_id)
        if Path(image_id).suffix.lower() not in IMAGE_EXTENSIONS:
            raise ImageNotFound(image_id)
        candidate = (self.root / image_id).resolve()
        # Defense in depth: the resolved path must still sit directly in the root.
        if candidate.parent != self.root or not candidate.is_file():
            raise ImageNotFound(image_id)
        return candidate

    # ── image discovery ──────────────────────────────────────────────────────
    def list_images(self) -> list[str]:
        """Filenames of PNG/JPEG images directly in the data root, sorted. Empty folder -> []."""
        if not self.root.is_dir():
            return []
        names = [
            p.name
            for p in self.root.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        ]
        return sorted(names)

    # ── export destination (path safety, single owner) ───────────────────────
    def export_dir(self, name: str) -> Path:
        """Resolve+create a fresh export dataset directory ``<root>/.exports/<name>`` and return it.

        Path safety is this store's job: ``name`` must be a bare directory name (no separators, ``..``,
        absolute path, or dotfile) so an export can never write outside the mounted root. What the
        *contents* and layout of that directory are is the export module's concern, not this store's.
        """
        cleaned = name.strip()
        if (
            not cleaned
            or cleaned != Path(cleaned).name
            or cleaned in (".", "..")
            or cleaned.startswith(".")
        ):
            raise BadExportName(name)
        dest = (self.root / EXPORTS_DIRNAME / cleaned).resolve()
        if dest.parent != (self.root / EXPORTS_DIRNAME).resolve():
            raise BadExportName(name)  # defense in depth
        dest.mkdir(parents=True, exist_ok=True)
        return dest

    # ── annotations ──────────────────────────────────────────────────────────
    def _annotation_file(self, image_id: str) -> Path:
        return self.annotations_dir / f"{image_id}.json"

    def read_annotation(self, image_id: str) -> Annotation:
        """Load an image's annotations, or an empty record with true dimensions if none exist yet."""
        path = self.image_path(image_id)  # validates id + existence
        width, height = probe_size(path)
        ann_file = self._annotation_file(image_id)
        if ann_file.is_file():
            stored = json.loads(ann_file.read_text(encoding="utf-8"))
            ann = Annotation.from_stored(stored)
            # Dimensions are authoritative from the image, not from the stored record.
            ann.width, ann.height = width, height
            ann.image = image_id
            return ann
        return Annotation(image=image_id, width=width, height=height, objects=[])

    def write_annotation(self, image_id: str, objects: list[AnnotationObject]) -> Annotation:
        """Persist an image's objects. Dimensions are probed here, never taken from the client."""
        path = self.image_path(image_id)  # validates id + existence
        width, height = probe_size(path)
        ann = Annotation(image=image_id, width=width, height=height, objects=objects)
        self.annotations_dir.mkdir(exist_ok=True)
        _atomic_write_json(self._annotation_file(image_id), ann.model_dump_stored())
        return ann

    # ── class config ─────────────────────────────────────────────────────────
    def read_classes(self) -> ClassList:
        """Load the class list, seeding a default file on first run."""
        path = self.root / CLASSES_FILENAME
        if not path.is_file():
            default = ClassList(classes=list(DEFAULT_CLASSES))
            self.write_classes(default.classes)
            return default
        stored = json.loads(path.read_text(encoding="utf-8"))
        return ClassList(classes=[ClassDef(**c) for c in stored.get("classes", [])])

    def write_classes(self, classes: list[ClassDef]) -> ClassList:
        self.root.mkdir(parents=True, exist_ok=True)
        cl = ClassList(classes=classes)
        _atomic_write_json(
            self.root / CLASSES_FILENAME,
            {"classes": [c.model_dump() for c in cl.classes]},
        )
        return cl


def _atomic_write_json(path: Path, data: dict) -> None:
    """Write JSON so the target file is never left half-written (temp + os.replace)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, path)
