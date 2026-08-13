"""End-to-end tests of the HTTP API via FastAPI's TestClient."""

from __future__ import annotations

from tests.conftest import make_image


def test_list_images(client, data_dir):
    make_image(data_dir / "a.png")
    make_image(data_dir / "b.jpg", fmt="JPEG")

    r = client.get("/api/images")
    assert r.status_code == 200
    body = r.json()
    assert [i["name"] for i in body] == ["a.png", "b.jpg"]
    assert body[0]["width"] > 0 and body[0]["height"] > 0
    assert body[0]["object_count"] == 0


def test_get_image_file(client, data_dir):
    make_image(data_dir / "a.png")
    r = client.get("/api/images/a.png/file")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")


def test_get_image_file_missing(client, data_dir):
    r = client.get("/api/images/ghost.png/file")
    assert r.status_code == 404


def test_get_image_file_traversal_rejected(client, data_dir):
    r = client.get("/api/images/..%2f..%2fetc%2fpasswd/file")
    assert r.status_code in (400, 404)


def test_annotation_default_is_empty(client, data_dir):
    make_image(data_dir / "a.png", size=(64, 48))
    r = client.get("/api/images/a.png/annotation")
    assert r.status_code == 200
    body = r.json()
    assert body == {"image": "a.png", "width": 64, "height": 48, "objects": []}


def test_put_then_get_annotation(client, data_dir):
    make_image(data_dir / "a.png", size=(64, 48))
    payload = {
        "image": "a.png",
        "width": 64,
        "height": 48,
        "objects": [
            {"id": "o1", "label": "car", "points": [[1, 1], [20, 2], [15, 30]]},
            {"id": "o2", "label": "tree", "points": [[5, 5], [6, 5], [6, 6], [5, 6]]},
        ],
    }
    r = client.put("/api/images/a.png/annotation", json=payload)
    assert r.status_code == 200

    r2 = client.get("/api/images/a.png/annotation")
    body = r2.json()
    assert len(body["objects"]) == 2
    assert body["objects"][0]["label"] == "car"

    # Object count reflected in the listing.
    listing = client.get("/api/images").json()
    assert listing[0]["object_count"] == 2


def test_put_annotation_name_mismatch(client, data_dir):
    make_image(data_dir / "a.png")
    payload = {"image": "b.png", "width": 64, "height": 48, "objects": []}
    r = client.put("/api/images/a.png/annotation", json=payload)
    assert r.status_code == 400


def test_put_annotation_rejects_degenerate_polygon(client, data_dir):
    make_image(data_dir / "a.png")
    payload = {
        "image": "a.png",
        "width": 64,
        "height": 48,
        "objects": [{"id": "o1", "label": "car", "points": [[1, 1], [2, 2]]}],
    }
    r = client.put("/api/images/a.png/annotation", json=payload)
    assert r.status_code == 422  # fewer than 3 points


def test_put_annotation_missing_image(client, data_dir):
    payload = {"image": "ghost.png", "width": 64, "height": 48, "objects": []}
    r = client.put("/api/images/ghost.png/annotation", json=payload)
    assert r.status_code == 404


def test_classes_get_seeds_defaults(client, data_dir):
    r = client.get("/api/classes")
    assert r.status_code == 200
    assert [c["name"] for c in r.json()["classes"]] == ["car", "tree", "building"]


def test_classes_put_and_get(client, data_dir):
    payload = {"classes": [{"name": "boat", "color": "#123456"}]}
    r = client.put("/api/classes", json=payload)
    assert r.status_code == 200
    assert client.get("/api/classes").json()["classes"][0]["name"] == "boat"


def test_classes_put_rejects_duplicates(client, data_dir):
    payload = {"classes": [{"name": "x", "color": "#111111"}, {"name": "X", "color": "#222222"}]}
    r = client.put("/api/classes", json=payload)
    assert r.status_code == 422


def test_classes_put_rejects_bad_color(client, data_dir):
    payload = {"classes": [{"name": "x", "color": "red"}]}
    r = client.put("/api/classes", json=payload)
    assert r.status_code == 422


def test_index_html_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Segmentation Annotator" in r.text
