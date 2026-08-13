import pytest

from app.models import AnnotationObject, ClassDef, Point
from app.store import ImageNotFound, Workspace
from conftest import make_image


def _tri():
    return [Point(x=1, y=2), Point(x=30, y=4), Point(x=15, y=50)]


def test_empty_folder_lists_nothing(tmp_path):
    assert Workspace(tmp_path).list_images() == []


def test_lists_only_png_jpeg_sorted(tmp_path):
    make_image(tmp_path / "b.png")
    make_image(tmp_path / "a.jpg")
    (tmp_path / "notes.txt").write_text("x")
    (tmp_path / "readme.md").write_text("x")
    assert Workspace(tmp_path).list_images() == ["a.jpg", "b.png"]


def test_missing_annotations_returns_empty_with_true_dims(tmp_path):
    make_image(tmp_path / "img.png", size=(120, 80))
    ann = Workspace(tmp_path).read_annotation("img.png")
    assert ann.objects == []
    assert (ann.width, ann.height) == (120, 80)


def test_save_then_reload_roundtrips_polygons(tmp_path):
    make_image(tmp_path / "img.png", size=(120, 80))
    ws = Workspace(tmp_path)
    ws.write_annotation("img.png", [AnnotationObject(cls="car", polygon=_tri())])
    reloaded = ws.read_annotation("img.png")
    assert len(reloaded.objects) == 1
    obj = reloaded.objects[0]
    assert obj.cls == "car"
    assert [[p.x, p.y] for p in obj.polygon] == [[1, 2], [30, 4], [15, 50]]


def test_dimensions_are_authoritative_from_image_not_stored(tmp_path):
    make_image(tmp_path / "img.png", size=(120, 80))
    ws = Workspace(tmp_path)
    ws.write_annotation("img.png", [])
    # Corrupt the stored dims; read must correct them from the real image.
    f = tmp_path / ".annotations" / "img.png.json"
    f.write_text(f.read_text().replace('"width": 120', '"width": 999'))
    assert ws.read_annotation("img.png").width == 120


def test_unknown_class_is_accepted_and_stored(tmp_path):
    # class-list membership is NOT an annotation-validity rule.
    make_image(tmp_path / "img.png")
    ws = Workspace(tmp_path)
    ws.write_classes([ClassDef(name="car", color="#123456")])
    ws.write_annotation("img.png", [AnnotationObject(cls="spaceship", polygon=_tri())])
    assert ws.read_annotation("img.png").objects[0].cls == "spaceship"


@pytest.mark.parametrize("bad", ["../secret.png", "/etc/passwd", "sub/img.png", "..", "nope.png"])
def test_path_safety_rejects_bad_ids(tmp_path, bad):
    make_image(tmp_path / "img.png")
    (tmp_path.parent / "secret.png").write_bytes(b"x")  # a real file just outside the root
    ws = Workspace(tmp_path)
    with pytest.raises(ImageNotFound):
        ws.image_path(bad)


def test_non_image_extension_rejected(tmp_path):
    (tmp_path / "notes.txt").write_text("x")
    with pytest.raises(ImageNotFound):
        Workspace(tmp_path).image_path("notes.txt")


def test_classes_seeded_on_first_read(tmp_path):
    ws = Workspace(tmp_path)
    classes = ws.read_classes().classes
    assert [c.name for c in classes] == ["car", "tree", "building"]
    assert (tmp_path / "classes.json").is_file()


def test_classes_write_then_read(tmp_path):
    ws = Workspace(tmp_path)
    ws.write_classes([ClassDef(name="road", color="#000000")])
    assert [c.name for c in ws.read_classes().classes] == ["road"]
