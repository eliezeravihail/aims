"""Pydantic schemas — the shapes that cross the API boundary.

Coordinate convention (single source of truth for the whole app):
every polygon point is an ``[x, y]`` pair in the *original image's* pixel
space, x rightward from the left edge, y downward from the top edge. This is
display-independent: zoom, window size and canvas scaling never change a
stored coordinate.
"""

from __future__ import annotations

import re
from typing import List

from pydantic import BaseModel, Field, field_validator

# A hex colour like #a1b2c3 (used for class swatches in the UI).
_HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{6})$")

# A 2-element [x, y] point in image-pixel coordinates.
Point = List[float]


class ClassDef(BaseModel):
    """One label the user can assign to an object: a name and a swatch colour."""

    name: str = Field(min_length=1, max_length=64)
    color: str = Field(default="#e6194b")

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("class name must not be empty")
        return v

    @field_validator("color")
    @classmethod
    def _check_color(cls, v: str) -> str:
        if not _HEX_COLOR.match(v):
            raise ValueError("color must be a #rrggbb hex string")
        return v.lower()


class ClassList(BaseModel):
    """The user's configurable set of classes."""

    classes: List[ClassDef] = Field(default_factory=list)

    @field_validator("classes")
    @classmethod
    def _unique_names(cls, v: List[ClassDef]) -> List[ClassDef]:
        seen = set()
        for c in v:
            key = c.name.lower()
            if key in seen:
                raise ValueError(f"duplicate class name: {c.name}")
            seen.add(key)
        return v


class AnnotationObject(BaseModel):
    """A single annotated object: one closed polygon plus its class label."""

    id: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=64)
    points: List[Point]

    @field_validator("points")
    @classmethod
    def _valid_polygon(cls, v: List[Point]) -> List[Point]:
        if len(v) < 3:
            raise ValueError("a polygon needs at least 3 points")
        for p in v:
            if len(p) != 2:
                raise ValueError("each point must be [x, y]")
        return v


class Annotation(BaseModel):
    """Everything saved for one image: the objects drawn on it.

    ``width``/``height`` record the pixel frame the points live in, so a
    consumer never has to open the image to interpret a coordinate.
    """

    image: str
    width: int = Field(ge=1)
    height: int = Field(ge=1)
    objects: List[AnnotationObject] = Field(default_factory=list)


class ImageInfo(BaseModel):
    """Directory-listing entry for one image."""

    name: str
    width: int
    height: int
    object_count: int
