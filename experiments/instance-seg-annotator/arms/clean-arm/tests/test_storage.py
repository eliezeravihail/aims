"""Tests for annotation + class-list persistence."""

from __future__ import annotations

from app import config, storage
from app.models import Annotation, AnnotationObject, ClassDef, ClassList
from tests.conftest import make_image


def _sample_annotation(name="img.png"):
    return Annotation(
        image=name,
        width=64,
        height=48,
        objects=[
            AnnotationObject(id="o1", label="car", points=[[1, 1], [10, 1], [10, 10]]),
        ],
    )


def test_load_annotation_defaults_to_empty_with_dimensions(data_dir):
    make_image(data_dir / "img.png", size=(64, 48))
    ann = storage.load_annotation(data_dir, "img.png")
    assert ann.objects == []
    assert (ann.width, ann.height) == (64, 48)


def test_save_then_load_round_trip(data_dir):
    make_image(data_dir / "img.png", size=(64, 48))
    storage.save_annotation(data_dir, _sample_annotation())

    loaded = storage.load_annotation(data_dir, "img.png")
    assert len(loaded.objects) == 1
    obj = loaded.objects[0]
    assert obj.label == "car"
    assert obj.points == [[1, 1], [10, 1], [10, 10]]


def test_sidecar_lives_in_annotation_subfolder(data_dir):
    make_image(data_dir / "img.png")
    storage.save_annotation(data_dir, _sample_annotation())
    sidecar = data_dir / config.ANNOTATION_DIRNAME / "img.png.json"
    assert sidecar.is_file()


def test_saving_empty_objects_deletes_sidecar(data_dir):
    make_image(data_dir / "img.png")
    storage.save_annotation(data_dir, _sample_annotation())
    sidecar = storage.annotation_path(data_dir, "img.png")
    assert sidecar.is_file()

    empty = Annotation(image="img.png", width=64, height=48, objects=[])
    storage.save_annotation(data_dir, empty)
    assert not sidecar.is_file()


def test_object_count(data_dir):
    make_image(data_dir / "img.png")
    assert storage.object_count(data_dir, "img.png") == 0
    storage.save_annotation(data_dir, _sample_annotation())
    assert storage.object_count(data_dir, "img.png") == 1


def test_classes_seed_defaults_on_first_load(data_dir):
    classes = storage.load_classes(data_dir)
    names = [c.name for c in classes.classes]
    assert names == ["car", "tree", "building"]
    # And they are now persisted.
    assert (data_dir / config.ANNOTATION_DIRNAME / config.CLASSES_FILENAME).is_file()


def test_classes_round_trip(data_dir):
    new = ClassList(classes=[ClassDef(name="dog", color="#ABCDEF")])
    storage.save_classes(data_dir, new)
    loaded = storage.load_classes(data_dir)
    assert [c.name for c in loaded.classes] == ["dog"]
    assert loaded.classes[0].color == "#abcdef"  # normalised lower-case
