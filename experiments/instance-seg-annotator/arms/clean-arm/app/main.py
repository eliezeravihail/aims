"""FastAPI application: HTTP surface and static-file serving.

Thin by design — every route delegates to the images/storage modules and
returns their results. No business logic lives here.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask

from . import config, export, images, storage
from .models import Annotation, ClassList, ImageInfo

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="Instance Segmentation Annotator")


def _data_dir() -> Path:
    return config.get_data_dir()


# --------------------------------------------------------------------------- #
# Images
# --------------------------------------------------------------------------- #

@app.get("/api/images", response_model=list[ImageInfo])
def list_images() -> list[ImageInfo]:
    """List annotatable images in the data folder, with per-image object counts."""
    data_dir = _data_dir()
    result: list[ImageInfo] = []
    for name in images.list_image_names(data_dir):
        path = data_dir / name
        width, height = images.get_dimensions(path)
        result.append(
            ImageInfo(
                name=name,
                width=width,
                height=height,
                object_count=storage.object_count(data_dir, name),
            )
        )
    return result


@app.get("/api/images/{name}/file")
def get_image_file(name: str) -> FileResponse:
    """Serve the raw image bytes."""
    data_dir = _data_dir()
    try:
        path = images.resolve_existing(data_dir, name)
    except images.UnsafeFilenameError:
        raise HTTPException(status_code=400, detail="invalid image name")
    except images.ImageNotFoundError:
        raise HTTPException(status_code=404, detail="image not found")
    return FileResponse(path)


@app.get("/api/images/{name}/annotation", response_model=Annotation)
def get_annotation(name: str) -> Annotation:
    """Return saved annotation for an image (empty if never annotated)."""
    data_dir = _data_dir()
    try:
        return storage.load_annotation(data_dir, name)
    except images.UnsafeFilenameError:
        raise HTTPException(status_code=400, detail="invalid image name")
    except images.ImageNotFoundError:
        raise HTTPException(status_code=404, detail="image not found")


@app.put("/api/images/{name}/annotation", response_model=Annotation)
def put_annotation(name: str, annotation: Annotation) -> Annotation:
    """Save annotation for an image."""
    data_dir = _data_dir()
    try:
        images.resolve_existing(data_dir, name)
    except images.UnsafeFilenameError:
        raise HTTPException(status_code=400, detail="invalid image name")
    except images.ImageNotFoundError:
        raise HTTPException(status_code=404, detail="image not found")
    if annotation.image != name:
        raise HTTPException(status_code=400, detail="image name mismatch")
    return storage.save_annotation(data_dir, annotation)


# --------------------------------------------------------------------------- #
# Tiled dataset export
# --------------------------------------------------------------------------- #

@app.get("/api/export")
def export_dataset(
    tile_size: int = Query(export.DEFAULT_TILE_SIZE, ge=1),
    overlap: int = Query(export.DEFAULT_OVERLAP, ge=0),
) -> FileResponse:
    """Cut every image + its annotations into overlapping tiles and return a
    zipped COCO instance-segmentation dataset ready for a training pipeline."""
    try:
        cfg = export.TileConfig(tile_size=tile_size, overlap=overlap)
        zip_path = export.export_zip(_data_dir(), cfg)
    except ValueError as exc:  # invalid tile/overlap geometry
        raise HTTPException(status_code=400, detail=str(exc))
    # Remove the temp working directory once the response has been sent.
    cleanup = BackgroundTask(shutil.rmtree, zip_path.parent, ignore_errors=True)
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=zip_path.name,
        background=cleanup,
    )


# --------------------------------------------------------------------------- #
# Classes
# --------------------------------------------------------------------------- #

@app.get("/api/classes", response_model=ClassList)
def get_classes() -> ClassList:
    """Return the configurable class list."""
    return storage.load_classes(_data_dir())


@app.put("/api/classes", response_model=ClassList)
def put_classes(class_list: ClassList) -> ClassList:
    """Replace the class list."""
    return storage.save_classes(_data_dir(), class_list)


# --------------------------------------------------------------------------- #
# Frontend (mounted last so /api routes take precedence)
# --------------------------------------------------------------------------- #

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
