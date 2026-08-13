---
title: "results — instance-segmentation annotator (a real aims build)"
date: 2026-08-13
---

## What this experiment is

A real, evolving product built *through* aims: the Guide chooses one design objective at a time and
delegates each to a Worker; the design knowledge is filed as co-located records (companions beside code
+ root `goals.md` / `architecture.md` / `base-dependencies.md` / `decisions/`). Two stages, a genuine
evolution between them, so we can see whether the boundary aims directed at Stage 1 absorbs Stage 2
without a rewrite.

- **Stage 1** — a general multi-class instance-segmentation annotator, container-run.
- **Stage 2** — large satellite images arrive: cut into overlapping tiles, export a training dataset.

The claim under test: directing the *design boundary* (annotation geometry vs. image
presentation/storage) as the Stage-1 objective makes Stage 2 a **pure addition** rather than a
tear-open — and the co-located records let the Stage-2 session continue from the boundary instead of
re-deriving it.

## Stage 1 — result

**What was built** (`product/`): a container-run FastAPI + vanilla-canvas annotator. Pure modules
`app/coords.py` (image↔viewport transform) and `app/model.py` (annotation data model + validation),
`app/storage.py` (byte-stable JSON persistence), `app/images.py`, `app/config.py`, `app/main.py` (HTTP
only), a canvas frontend, `Dockerfile` + `docker-compose.yml`, and a `tests/` suite.

**The directed boundary.** The Stage-1 objective was not a feature ticket — it was a *design outcome*:
draw a durable seam between annotation geometry and image presentation/storage, such that saved
coordinates are in original-image pixels and invariant to zoom/pan. The Worker delivered exactly that:
`ViewportTransform` is immutable, and `coords.viewport_to_image()` is the single funnel every pointer
sample passes through before it can become a vertex, so nothing downstream holds a screen coordinate.
`model.py` imports only the stdlib and references nothing about display/viewport/HTTP/tiling/export.

**Measurement (Guide, re-run honestly).** `python3 -m pytest` → **30 passed in ~0.5s**. The suite
covers every adversarial edge from the objective: <3-vertex reject, unknown-class reject, empty-document
valid save, save→load→save byte-stable idempotence, two-instance distinct-class save/reload identity,
and — the key one — an assertion that applying a viewport transform leaves stored image-space coords
unchanged. The app was also verified booting under uvicorn end-to-end (config/images/save/reload/422).
*One honest gap:* the Docker daemon isn't available in this sandbox, so `docker compose build` couldn't
run live — the compose file validates and the app boots via the same entrypoint the container `CMD`
uses, but a live container run is unverified here.

**Records filed** (co-located): root `architecture.md`, `base-dependencies.md`, `dependencies.md`,
`decisions/0001..0003`; companions `app/coords.py.md`, `app/model.py.md`, `app/storage.py.md` (each
anchored to its source by the aims anchor tool). A tension the Worker surfaced — class *color* is
presentation yet the class list is the validation authority — is recorded in `model.py.md` Discussions
(resolved: color is opaque data the model carries but never acts on).

One design tension worth noting for the next session: the frontend needs the same transform math as the
tested `coords.py`. Rather than add a JS build step (forbidden by `base-dependencies.md`), `coords.js`
is a thin mirror of the authoritative Python — recorded in `decisions/0003`.

## Stage 2 — result

The evolution was delegated to a **fresh Worker session** — a clean continuation. It was *not* told
where the boundary was; it was told to consult the co-located design records to find the seam, and to
add rather than rewrite. This is the actual test of the knowledge layer.

**What the continuation session read to orient itself.** By its own report: `goals.md`, `architecture.md`,
`base-dependencies.md`, `dependencies.md`, the three `decisions/`, and `app/model.py` + its companion
`model.py.md` (plus the existing tests). `architecture.md` names the seam outright — *"a new module does
`from app.model import AnnotationDocument` … the seam it plugs into is `AnnotationDocument`."* The Worker
plugged into exactly that, and reused `AnnotationDocument` as the per-tile representation (a tile *is* an
image + instances in tile-local pixels), so it introduced **no parallel geometry type**.

**What was built** (additively): `app/tiling.py` — pure tile geometry (overlapping-grid layout,
coordinate remap, Sutherland–Hodgman polygon clip; no I/O); `app/export.py` — the confined COCO
export-format owner (tile raster crop + `annotations.json`); plus `tests/test_tiling.py` and
`tests/test_export.py`.

**Measurement (Guide, re-run honestly).**
- `python3 -m pytest` → **48 passed** (30 Stage-1 + 18 new).
- **The key result — was the boundary fought? No.** `git diff` on tracked files since the Stage-1 commit
  is a single README note (the explicitly-permitted export blurb); `app/model.py`, `app/coords.py`, and
  everything under `app/static/` are **byte-identical**. Import check confirms `tiling.py` pulls in only
  stdlib + `app.model`; the format + all I/O sit in `export.py`. The directed seam absorbed the
  evolution as a pure addition.
- Adversarial edges green: straddling instance clipped to bounds; fully-outside instance absent;
  overlap → a border instance appears (clipped) in two tiles; empty tiles export validly; known-point
  coordinate remap correct. CLI verified end-to-end (400×300, tile 200 / overlap 50 → 6 tiles).

**Records filed** (co-located): `architecture.md` updated (owners table + "Stage 2 landed this way"),
`dependencies.md` updated (export format resolved to COCO, confined), `decisions/0004` (COCO export),
anchored companions `app/tiling.py.md` and `app/export.py.md`. The Worker's tension — where the raster
crop belongs (I/O) vs. keeping tiling pure — is recorded in both companions' Discussions.

## Verdict

Both halves of aims showed up in one real, evolving build:

1. **Directing design as the goal worked.** Stage 1's objective was a *design outcome* (the
   annotation-geometry ↔ image-presentation boundary), not a feature ticket. The Worker produced a
   structurally-invariant coordinate boundary at construction time — the zoom/pan invariance is proven by
   a test, not policed after the fact.
2. **The boundary held under a genuine evolution.** Stage 2 (satellite tiling + COCO export) — the exact
   change the boundary was chosen to absorb — landed with **zero edits to the annotation model or UI**.
   That is the design paying off, measured by an empty tracked diff, not asserted.
3. **The co-located records carried the design forward.** A *fresh* session with no memory of Stage 1
   found the intended seam by **navigating the records** (`architecture.md` → `model.py` + companion),
   and continued from the recorded conclusion instead of re-deriving or rewriting it. This is the
   continued-development claim, reproduced on a real product rather than a toy.

**Honest limits.** The two Workers are subagents of one session, not truly independent humans; the
Stage-2 session was *instructed* to read the records (aims' method does this via the SessionStart hook in
a real install, but here it was a prompt). Docker `compose build` could not run live in the sandbox (no
daemon) — the app boots under uvicorn (the container's entrypoint), but a live container run is
unverified. The favorable seam ("a tile is just another `AnnotationDocument`") is partly a credit to the
Stage-1 design choice under test, which is the point — but it means this is one evolution, not a
statistical claim.
</content>
