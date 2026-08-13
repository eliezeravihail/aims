---
title: "images.py"
date: 2026-08-13
hash: "sha256:478d9997929bf6e84df4711c8c43a241fa7764b3c93c21f9bff9cfb075ebf069"
---
## Decisions
- **The only place Pillow is imported.** The rest of the app depends on a `(width, height)` tuple and a
  "crop this box to that file" operation, not on an image library, so Pillow is replaceable by editing
  this one module (architecture.md: confined dependency).
- `probe_size` opens the image lazily (no pixel decode needed) purely to read its true dimensions.
- **`crop_to_file` is the export path's only pixel operation** — it crops a tile box out of a source
  image and saves it, keeping the export's tile-image production behind this same Pillow seam. The box is
  `(x0,y0,x1,y1)` right/bottom-exclusive (PIL crop convention, shared with `tiling`); the destination
  suffix selects the output encoding.

## Discussions
- Reading PNG/JPEG headers with the stdlib was considered to drop the dependency entirely; rejected because
  Pillow is the sanctioned, robust reader across both formats and the substrate already includes it.
