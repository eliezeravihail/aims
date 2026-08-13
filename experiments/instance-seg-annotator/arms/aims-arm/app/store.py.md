---
title: "store.py"
date: 2026-08-13
hash: "sha256:16e18d19dfd3d5a5a06e68107f58643a22bb8a2695ba1759eea3f17a7da70474"
---
## Insights
- `Workspace` owns path safety and the mounted *annotation workspace* (images, sidecars, `classes.json`).
  Keeping that filesystem+format concern here is what lets storage change (sidecar JSON → anything)
  behind one seam. The tiled export writes a *derived* dataset into a store-sandboxed `.exports/<name>/`
  directory; the store owns *where* it may write (`export_dir`), the export module owns *what* goes in it.
- Image dimensions are re-probed on every read/write and overwrite whatever a stored record claims; a
  corrupted or client-supplied size can never win (see `test_store.test_dimensions_are_authoritative...`).

## Decisions
- **Path safety has one gate**: `image_path` accepts an id only if it equals its own basename, has a
  PNG/JPEG extension, resolves directly inside `self.root`, and is a real file — otherwise `ImageNotFound`.
  Traversal, absolute, and nested ids are rejected here and nowhere else (guarded by `test_store` params).
- **On-disk format is `{image,width,height,objects}` with polygons as compact `[[x,y],...]`** in a
  `.annotations/<image>.json` sidecar; the model↔disk mapping lives in `models.py` (`*_stored`), keeping
  the file shape decoupled from the model's field layout. See `decisions/0001`.
- **Writes are atomic** (`_atomic_write_json`: temp + `os.replace`) so a crash never leaves a half-written
  annotation or class file.
- **Class-list membership is not enforced on annotation write** — an object with an unknown class is stored
  as-is (goals.md), so editing the class list never invalidates saved work.
- **`export_dir(name)` is the export destination's path-safety gate** — same discipline as `image_path`:
  `name` must be a bare directory name (no separators, `..`, absolute, or dotfile) so an export can never
  write outside the mounted root. It resolves+creates `<root>/.exports/<name>/`; anything else raises
  `BadExportName` (guarded by `test_export` params).

## Discussions
- A single monolithic index file was rejected in favor of per-image sidecars: isolation, no global lock,
  trivial reopen-by-filename. Cost: orphan sidecars when an image is deleted — accepted (non-goal to GC).
