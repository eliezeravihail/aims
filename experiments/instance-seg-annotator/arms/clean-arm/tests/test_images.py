"""Tests for image discovery, safe path resolution and dimension reading."""

from __future__ import annotations

import pytest

from app import images
from tests.conftest import make_image


def test_list_image_names_filters_and_sorts(data_dir):
    make_image(data_dir / "b.png")
    make_image(data_dir / "A.jpg", fmt="JPEG")
    make_image(data_dir / "c.jpeg", fmt="JPEG")
    (data_dir / "notes.txt").write_text("ignore me")
    (data_dir / "sub").mkdir()  # directories are not images

    names = images.list_image_names(data_dir)
    assert names == ["A.jpg", "b.png", "c.jpeg"]  # case-insensitive sort


def test_list_image_names_missing_dir(tmp_path):
    assert images.list_image_names(tmp_path / "nope") == []


def test_get_dimensions(data_dir):
    make_image(data_dir / "img.png", size=(30, 20))
    assert images.get_dimensions(data_dir / "img.png") == (30, 20)


@pytest.mark.parametrize("bad", ["../evil.png", "a/b.png", "..", ".", "", "sub\\x.png"])
def test_safe_image_path_rejects_traversal(data_dir, bad):
    with pytest.raises(images.UnsafeFilenameError):
        images.safe_image_path(data_dir, bad)


def test_safe_image_path_rejects_non_image_extension(data_dir):
    with pytest.raises(images.UnsafeFilenameError):
        images.safe_image_path(data_dir, "notes.txt")


def test_safe_image_path_accepts_plain_name(data_dir):
    p = images.safe_image_path(data_dir, "photo.jpg")
    assert p.parent == data_dir.resolve()
    assert p.name == "photo.jpg"


def test_resolve_existing_raises_when_missing(data_dir):
    with pytest.raises(images.ImageNotFoundError):
        images.resolve_existing(data_dir, "ghost.png")
