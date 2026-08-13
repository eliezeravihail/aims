---
title: "base-dependencies"
date: 2026-08-13
---

## The substrate (day-zero, foundational)

Chosen at grounding as the pervasive base the whole product rests on. These are *base* dependencies —
they are everywhere and not casually replaceable — as distinct from confined `dependencies.md` choices.

- **Python 3 + FastAPI** — the local backend (serves the app, the image bytes, and the annotation
  read/write API). Standard, small, async-capable, trivially containerized.
- **Pillow + numpy** — image inspection (dimensions) now; the raster work (tiling, clipping) in Stage 2.
- **Vanilla-JS + HTML5 Canvas** frontend — no build step, no framework. The annotator is a canvas that
  draws an image and polygon overlays; a framework would be pure weight here.
- **Docker + docker compose** — the run surface. The product is *defined* as "runs from a container";
  a mounted volume is where images come from and annotations go.

## Why these are base (not confined)

The API shape, the canvas drawing model, and the container boundary are load-bearing across every
feature. Confined choices (e.g. the on-disk annotation *format*, an export format in Stage 2) live in
`dependencies.md` and are meant to be swappable behind a seam.
</content>
</invoke>
