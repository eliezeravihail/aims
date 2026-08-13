"""Shared fixtures: an isolated data folder and a TestClient bound to it."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image


def make_image(path: Path, size=(64, 48), color=(120, 30, 30), fmt="PNG") -> None:
    """Write a solid-colour test image to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, fmt)


@pytest.fixture
def data_dir(tmp_path, monkeypatch) -> Path:
    """A fresh data folder, wired into the app via the DATA_DIR env var."""
    d = tmp_path / "data"
    d.mkdir()
    monkeypatch.setenv("DATA_DIR", str(d))
    return d


@pytest.fixture
def client(data_dir):
    """FastAPI TestClient reading/writing the isolated data folder."""
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        yield c
