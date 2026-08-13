"""HTTP layer — translates HTTP to Workspace calls and back, and serves the static UI + raw images.

Holds no filesystem or format knowledge: image discovery, path safety, and the on-disk format all live
in ``app.store.Workspace``; validity lives in ``app.models``. This module only wires them to routes.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .export import ExportOptions, export_dataset
from .models import AnnotationWrite, ClassList
from .store import BadExportName, ImageNotFound, Workspace

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def create_app(data_root: Path) -> FastAPI:
    app = FastAPI(title="Instance Segmentation Annotator")
    ws = Workspace(data_root)

    @app.get("/api/images")
    def list_images() -> dict:
        return {"images": ws.list_images()}

    @app.get("/api/images/{image_id}/raw")
    def image_raw(image_id: str) -> FileResponse:
        try:
            return FileResponse(ws.image_path(image_id))
        except ImageNotFound:
            raise HTTPException(status_code=404, detail="image not found")

    @app.get("/api/images/{image_id}/annotations")
    def get_annotations(image_id: str) -> dict:
        try:
            return ws.read_annotation(image_id).model_dump_stored()
        except ImageNotFound:
            raise HTTPException(status_code=404, detail="image not found")

    @app.put("/api/images/{image_id}/annotations")
    def put_annotations(image_id: str, body: AnnotationWrite) -> dict:
        try:
            return ws.write_annotation(image_id, body.objects).model_dump_stored()
        except ImageNotFound:
            raise HTTPException(status_code=404, detail="image not found")

    @app.post("/api/export")
    def export(options: ExportOptions) -> dict:
        try:
            return export_dataset(ws, options).model_dump()
        except BadExportName:
            raise HTTPException(status_code=422, detail="invalid export name")

    @app.get("/api/classes")
    def get_classes() -> dict:
        return {"classes": [c.model_dump() for c in ws.read_classes().classes]}

    @app.put("/api/classes")
    def put_classes(body: ClassList) -> dict:
        saved = ws.write_classes(body.classes)
        return {"classes": [c.model_dump() for c in saved.classes]}

    # Static UI last, mounted at root so /api/* wins.
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


def _data_root_from_env() -> Path:
    return Path(os.environ.get("ANNOTATOR_DATA_DIR", "/data"))


# Container / uvicorn entrypoint: `uvicorn app.main:app`.
app = create_app(_data_root_from_env())
