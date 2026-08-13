"""Persist annotation documents to disk as JSON. The one owner of on-disk I/O.

Depends on the pure model for shape/validation; adds nothing about display or
transport. One image <-> one JSON file, keyed by the image filename.

Byte-stability contract: `dumps` is deterministic (sorted keys, fixed indent,
trailing newline) so save -> load -> save round-trips to identical bytes. This
is what makes idempotent saves testable.
"""

from __future__ import annotations

import json
from pathlib import Path

from .model import AnnotationDocument, ClassList, validate_document


def dumps(doc: AnnotationDocument) -> str:
    """Serialize a document to canonical, byte-stable JSON text."""
    return json.dumps(doc.to_dict(), sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def loads(text: str) -> AnnotationDocument:
    """Parse canonical JSON text back into a document."""
    return AnnotationDocument.from_dict(json.loads(text))


def annotation_path(annotations_dir: Path, image_name: str) -> Path:
    """Map a source image filename to its annotation file path.

    Uses the image filename stem so 'city_01.png' -> 'city_01.json'. The stem is
    taken from the basename only; any directory parts are stripped to keep writes
    inside `annotations_dir`.
    """
    stem = Path(image_name).name
    stem = Path(stem).stem
    return Path(annotations_dir) / f"{stem}.json"


def save(annotations_dir: Path, doc: AnnotationDocument, classes: ClassList) -> Path:
    """Validate then write `doc`. Returns the path written. Overwrites atomically."""
    validate_document(doc, classes)
    path = annotation_path(annotations_dir, doc.image)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(dumps(doc), encoding="utf-8")
    tmp.replace(path)
    return path


def load(annotations_dir: Path, image_name: str) -> AnnotationDocument | None:
    """Read the document for an image, or None if none has been saved."""
    path = annotation_path(annotations_dir, image_name)
    if not path.exists():
        return None
    return loads(path.read_text(encoding="utf-8"))
