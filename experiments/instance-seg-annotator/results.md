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

_(filled in after the evolution: how tiling + export plugged into the Stage-1 seam, what the Stage-2
session read vs. re-derived, test output, records filed.)_

## Verdict

_(did the directed boundary hold; was Stage 2 additive; did the records carry the design forward.)_
</content>
