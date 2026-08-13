"""End-to-end HTTP round-trip through the real FastAPI app (exit criteria 1, 5).

Skipped automatically if fastapi/Pillow are unavailable, so the pure-module
suite still runs in a minimal environment.
"""

import importlib

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("PIL")
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    images_dir = tmp_path / "images"
    ann_dir = tmp_path / "annotations"
    images_dir.mkdir()
    ann_dir.mkdir()
    Image.new("RGB", (800, 600), (30, 30, 30)).save(images_dir / "scene.png")

    monkeypatch.setenv("INPUT_DIR", str(images_dir))
    monkeypatch.setenv("ANNOTATIONS_DIR", str(ann_dir))

    import app.config as config
    importlib.reload(config)
    import app.main as main
    importlib.reload(main)
    return TestClient(main.app)


def test_list_and_meta(client):
    assert client.get("/api/images").json()["images"] == ["scene.png"]
    meta = client.get("/api/images/scene.png/meta").json()
    assert (meta["width"], meta["height"]) == (800, 600)


def test_save_then_reload_identical(client):
    doc = {
        "image": "scene.png", "width": 800, "height": 600,
        "instances": [
            {"class_id": "building", "vertices": [[10, 10], [100, 10], [100, 100]]},
            {"class_id": "vehicle", "vertices": [[200, 200], [250, 200], [250, 260], [200, 260]]},
        ],
    }
    r = client.put("/api/annotations/scene.png", json=doc)
    assert r.status_code == 200
    back = client.get("/api/annotations/scene.png").json()
    assert back["instances"] == doc["instances"]
    assert {i["class_id"] for i in back["instances"]} == {"building", "vehicle"}


def test_invalid_polygon_rejected_over_http(client):
    doc = {"image": "scene.png", "width": 800, "height": 600,
           "instances": [{"class_id": "building", "vertices": [[0, 0], [1, 1]]}]}
    assert client.put("/api/annotations/scene.png", json=doc).status_code == 422


def test_unknown_class_rejected_over_http(client):
    doc = {"image": "scene.png", "width": 800, "height": 600,
           "instances": [{"class_id": "ghost", "vertices": [[0, 0], [1, 0], [1, 1]]}]}
    assert client.put("/api/annotations/scene.png", json=doc).status_code == 422


def test_unsaved_image_returns_empty_document(client):
    back = client.get("/api/annotations/scene.png").json()
    assert back["instances"] == []
