# Dependencies

Confined, replaceable dependencies (the foundational substrate is in `base-dependencies.md`).

- **Pillow** — reads true image pixel dimensions for PNG/JPEG and crops tile images for export. Confined
  to `app/images.py` (`probe_size`, `crop_to_file`); the store, export, and HTTP layers depend on a
  `(width, height)` tuple and a crop-to-file operation, not on Pillow. Replaceable there alone.
- **uvicorn** — ASGI server that runs the FastAPI app (the container CMD and local dev entrypoint). A
  runtime host, not referenced from application code.
- **pytest** — test runner (dev only). Not shipped in the runtime image.

FastAPI and pydantic are foundational, not confined — see `base-dependencies.md`.
