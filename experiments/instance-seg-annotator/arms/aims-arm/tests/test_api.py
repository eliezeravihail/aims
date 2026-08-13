import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from conftest import make_image


@pytest.fixture
def client(tmp_path):
    make_image(tmp_path / "a.png", size=(120, 80))
    make_image(tmp_path / "b.jpg", size=(64, 64))
    return TestClient(create_app(tmp_path))


def _tri():
    return [{"x": 1, "y": 2}, {"x": 30, "y": 4}, {"x": 15, "y": 50}]


def test_list_images(client):
    assert client.get("/api/images").json() == {"images": ["a.png", "b.jpg"]}


def test_empty_folder_lists_empty(tmp_path):
    c = TestClient(create_app(tmp_path))
    assert c.get("/api/images").json() == {"images": []}


def test_get_annotations_empty_not_404(client):
    r = client.get("/api/images/a.png/annotations")
    assert r.status_code == 200
    body = r.json()
    assert body["objects"] == [] and body["width"] == 120 and body["height"] == 80


def test_put_then_get_roundtrip(client):
    payload = {"objects": [{"class": "car", "polygon": _tri()}]}
    assert client.put("/api/images/a.png/annotations", json=payload).status_code == 200
    body = client.get("/api/images/a.png/annotations").json()
    assert body["objects"][0]["class"] == "car"
    assert body["objects"][0]["polygon"] == [[1, 2], [30, 4], [15, 50]]


def test_put_rejects_degenerate_polygon(client):
    payload = {"objects": [{"class": "car", "polygon": [{"x": 0, "y": 0}, {"x": 1, "y": 1}]}]}
    assert client.put("/api/images/a.png/annotations", json=payload).status_code == 422


def test_put_rejects_empty_class(client):
    payload = {"objects": [{"class": "  ", "polygon": _tri()}]}
    assert client.put("/api/images/a.png/annotations", json=payload).status_code == 422


def test_unknown_image_404(client):
    assert client.get("/api/images/nope.png/annotations").status_code == 404
    assert client.get("/api/images/a.png/raw").status_code == 200


def test_traversal_id_404(client):
    # FastAPI path parsing keeps this from matching; either way it must never serve outside root.
    assert client.get("/api/images/..%2F..%2Fetc%2Fpasswd/raw").status_code == 404


def test_raw_image_served(client):
    r = client.get("/api/images/a.png/raw")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")


def test_classes_get_seeds_default(client):
    names = [c["name"] for c in client.get("/api/classes").json()["classes"]]
    assert names == ["car", "tree", "building"]


def test_classes_put(client):
    r = client.put("/api/classes", json={"classes": [{"name": "road", "color": "#111111"}]})
    assert r.status_code == 200
    assert [c["name"] for c in r.json()["classes"]] == ["road"]


def test_index_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Annotator" in r.text


def test_export_endpoint_produces_summary(client):
    client.put("/api/images/a.png/annotations",
               json={"objects": [{"class": "car", "polygon": _tri()}]})
    r = client.post("/api/export", json={"tile_size": 1024, "overlap": 128, "name": "run1"})
    assert r.status_code == 200
    body = r.json()
    assert body["format"] == "coco"
    assert body["source_images"] == 2  # a.png + b.jpg
    assert body["tiles"] == 2          # both images fit in one tile
    assert body["instances"] == 1


def test_export_defaults_applied(client):
    r = client.post("/api/export", json={})
    assert r.status_code == 200
    assert r.json()["tiles"] == 2


def test_export_bad_overlap_422(client):
    r = client.post("/api/export", json={"tile_size": 100, "overlap": 100})
    assert r.status_code == 422


def test_export_bad_name_422(client):
    r = client.post("/api/export", json={"name": "../escape"})
    assert r.status_code == 422
