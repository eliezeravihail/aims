"""FastAPI app: serve the frontend, image bytes, class list, and annotation I/O.

The transport/HTTP owner. It wires the pure modules (model, storage) to disk
(images, storage) and the browser. It holds no annotation logic of its own:
geometry rules live in model, persistence in storage, transforms in coords (JS
side). Every save goes through storage.save, which validates via the model.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config, images, storage
from .model import AnnotationDocument, ValidationError

app = FastAPI(title="Instance Segmentation Annotator", version="1.0")

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/api/config")
def get_config() -> JSONResponse:
    """Return the project class list (name + color per class)."""
    return JSONResponse({"classes": config.load_class_list().to_list()})


@app.get("/api/images")
def get_images() -> JSONResponse:
    """List available source image filenames."""
    return JSONResponse({"images": images.list_images(config.INPUT_DIR)})


@app.get("/api/images/{name}/meta")
def get_image_meta(name: str) -> JSONResponse:
    """Return original-pixel dimensions for one image."""
    try:
        w, h = images.image_size(config.INPUT_DIR, name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="image not found")
    return JSONResponse({"image": name, "width": w, "height": h})


@app.get("/api/images/{name}/raw")
def get_image_raw(name: str) -> FileResponse:
    """Serve raw image bytes for the canvas to draw."""
    try:
        path = images.image_file(config.INPUT_DIR, name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="image not found")
    return FileResponse(path)


@app.get("/api/annotations/{name}")
def get_annotations(name: str) -> JSONResponse:
    """Load saved annotations for an image; empty document if none saved yet."""
    doc = storage.load(config.ANNOTATIONS_DIR, name)
    if doc is None:
        try:
            w, h = images.image_size(config.INPUT_DIR, name)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="image not found")
        doc = AnnotationDocument(image=name, width=w, height=h, instances=())
    return JSONResponse(doc.to_dict())


@app.put("/api/annotations/{name}")
def put_annotations(name: str, body: dict) -> JSONResponse:
    """Validate and persist annotations for an image (image-pixel coords)."""
    body = {**body, "image": name}  # the URL is authoritative for the image name
    try:
        doc = AnnotationDocument.from_dict(body)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"malformed document: {exc}")
    try:
        storage.save(config.ANNOTATIONS_DIR, doc, config.load_class_list())
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return JSONResponse(doc.to_dict())


# Frontend (mounted last so /api/* wins).
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
