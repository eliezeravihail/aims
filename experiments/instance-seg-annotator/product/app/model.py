"""Annotation data model + validation + canonical (de)serialization. Pure.

This module is the single owner of what an annotation *is*. It knows nothing
about display (canvas, colors-as-rendering), viewport transforms, HTTP, tiling,
or export. It imports only the standard library, so a Stage-2 consumer (tiling +
dataset export) can `from app.model import AnnotationDocument` and read
instance geometry in original-image pixels without pulling in any UI/HTTP code.

Coordinate contract: every vertex is an (x, y) pair in ORIGINAL-IMAGE PIXELS.
Nothing here is aware that a viewport or zoom level exists.

`ClassDef.color` is stored project data (a hex string), not rendering logic;
this module never interprets or draws it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Serialization is deliberately hand-rolled (plain dict/list of builtins) rather
# than delegated to a library, so the on-disk shape is owned here and stays
# byte-stable independent of any third-party version.

Vertex = tuple[float, float]

SCHEMA_VERSION = 1


class ValidationError(ValueError):
    """Raised when an instance or document violates the annotation contract."""


@dataclass(frozen=True)
class ClassDef:
    """One annotation class: a stable id, a human name, a display color.

    `color` is opaque project data (e.g. "#e6194b"); the model never renders it.
    """

    id: str
    name: str
    color: str

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "color": self.color}

    @staticmethod
    def from_dict(d: dict) -> "ClassDef":
        return ClassDef(id=str(d["id"]), name=str(d["name"]), color=str(d["color"]))


@dataclass(frozen=True)
class ClassList:
    """The fixed-per-project set of classes. Owns the 'is this class valid?' rule."""

    classes: tuple[ClassDef, ...]

    def ids(self) -> set[str]:
        return {c.id for c in self.classes}

    def contains(self, class_id: str) -> bool:
        return class_id in self.ids()

    def to_list(self) -> list[dict]:
        return [c.to_dict() for c in self.classes]

    @staticmethod
    def from_list(items: list[dict]) -> "ClassList":
        seen: set[str] = set()
        out: list[ClassDef] = []
        for it in items:
            c = ClassDef.from_dict(it)
            if c.id in seen:
                raise ValidationError(f"duplicate class id: {c.id!r}")
            seen.add(c.id)
            out.append(c)
        return ClassList(tuple(out))


@dataclass(frozen=True)
class Instance:
    """One polygon instance: ordered image-pixel vertices + a class id.

    A polygon needs at least 3 vertices to enclose an area.
    """

    class_id: str
    vertices: tuple[Vertex, ...]

    def to_dict(self) -> dict:
        return {
            "class_id": self.class_id,
            "vertices": [[float(x), float(y)] for (x, y) in self.vertices],
        }

    @staticmethod
    def from_dict(d: dict) -> "Instance":
        verts = tuple((float(p[0]), float(p[1])) for p in d["vertices"])
        return Instance(class_id=str(d["class_id"]), vertices=verts)


@dataclass(frozen=True)
class AnnotationDocument:
    """All annotations for one source image, in image-pixel coordinates.

    `image` is the source image filename; `width`/`height` are its original
    pixel dimensions; `instances` may be empty (a valid 'nothing here' save).
    """

    image: str
    width: int
    height: int
    instances: tuple[Instance, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "image": self.image,
            "width": int(self.width),
            "height": int(self.height),
            "instances": [ins.to_dict() for ins in self.instances],
        }

    @staticmethod
    def from_dict(d: dict) -> "AnnotationDocument":
        return AnnotationDocument(
            image=str(d["image"]),
            width=int(d["width"]),
            height=int(d["height"]),
            instances=tuple(Instance.from_dict(i) for i in d.get("instances", [])),
        )


# --- validation -----------------------------------------------------------

MIN_POLYGON_VERTICES = 3


def validate_instance(ins: Instance, classes: ClassList) -> None:
    """Raise ValidationError unless `ins` is a well-formed, in-class polygon."""
    if len(ins.vertices) < MIN_POLYGON_VERTICES:
        raise ValidationError(
            f"polygon needs >= {MIN_POLYGON_VERTICES} vertices, got {len(ins.vertices)}"
        )
    for x, y in ins.vertices:
        if not (_finite(x) and _finite(y)):
            raise ValidationError(f"non-finite vertex: {(x, y)!r}")
    if not classes.contains(ins.class_id):
        raise ValidationError(f"unknown class id: {ins.class_id!r}")


def validate_document(doc: AnnotationDocument, classes: ClassList) -> None:
    """Raise ValidationError unless every instance is valid. Zero instances is OK."""
    if doc.width <= 0 or doc.height <= 0:
        raise ValidationError(f"image size must be positive, got {doc.width}x{doc.height}")
    for ins in doc.instances:
        validate_instance(ins, classes)


def _finite(v: float) -> bool:
    return v == v and v not in (float("inf"), float("-inf"))
