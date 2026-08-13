"""Domain models — the single owner of "what is a valid annotation".

These pydantic models are the one shape shared across the HTTP seam (request/response bodies) and the
store's on-disk serialization. Validity rules live here and nowhere else: a polygon needs >=3 finite
vertices; an object needs a non-empty class name. The store decides where/how to persist; these decide
what is well-formed.
"""
from __future__ import annotations

import math

from pydantic import BaseModel, Field, field_validator


class Point(BaseModel):
    x: float
    y: float

    @field_validator("x", "y")
    @classmethod
    def _finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("coordinate must be a finite number")
        return v


class AnnotationObject(BaseModel):
    """One annotated instance: an outline (polygon) plus its class name."""

    # The JSON key is "class" (a Python keyword); the attribute is "cls". populate_by_name also
    # accepts "cls" directly (used by internal construction).
    cls: str = Field(alias="class")
    polygon: list[Point]

    model_config = {"populate_by_name": True}

    @field_validator("cls")
    @classmethod
    def _class_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("class name must not be empty")
        return v

    @field_validator("polygon")
    @classmethod
    def _polygon_is_a_shape(cls, v: list[Point]) -> list[Point]:
        if len(v) < 3:
            raise ValueError("a polygon outline needs at least 3 vertices")
        return v

    def model_dump_stored(self) -> dict:
        return {"class": self.cls, "polygon": [[p.x, p.y] for p in self.polygon]}

    @classmethod
    def from_stored(cls, d: dict) -> "AnnotationObject":
        return cls(cls=d["class"], polygon=[Point(x=p[0], y=p[1]) for p in d["polygon"]])


class Annotation(BaseModel):
    """The full annotation record for one image: its true dimensions plus its objects.

    ``width``/``height`` are authoritative (probed from the image by the server); a client-supplied
    value is ignored on write.
    """

    image: str
    width: int
    height: int
    objects: list[AnnotationObject] = []

    def model_dump_stored(self) -> dict:
        return {
            "image": self.image,
            "width": self.width,
            "height": self.height,
            "objects": [o.model_dump_stored() for o in self.objects],
        }

    @classmethod
    def from_stored(cls, d: dict) -> "Annotation":
        return cls(
            image=d["image"],
            width=d["width"],
            height=d["height"],
            objects=[AnnotationObject.from_stored(o) for o in d.get("objects", [])],
        )


class AnnotationWrite(BaseModel):
    """The write payload: objects only. Dimensions are the server's to determine."""

    objects: list[AnnotationObject] = []


class ClassDef(BaseModel):
    """A configurable class: a name and a display color."""

    name: str
    color: str = "#ff3860"

    @field_validator("name")
    @classmethod
    def _name_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("class name must not be empty")
        return v


class ClassList(BaseModel):
    classes: list[ClassDef] = []
