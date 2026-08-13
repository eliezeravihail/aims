# Base Dependencies

The foundational substrate — the pervasive base the whole product stands on. Fixed at day zero (imposed
as a shared constraint for this build). Kept minimal.

## Foundational substrate

- **Python 3 + FastAPI** — the backend language and web framework. Every server-side object is a FastAPI
  route, dependency, or a plain object wired into one; replacing it rewrites the whole server. FastAPI
  brings **pydantic**, which the product adopts as its domain-model + validation layer (so the type that
  crosses the HTTP seam and the type the store serializes are one and the same). FastAPI/pydantic types
  are therefore permitted to cross public seams.

- **Vanilla JavaScript + HTML5 canvas** — the entire frontend, served as static files with **no build
  step, no framework, no bundler**. The canvas 2D context is the pervasive drawing substrate for image
  display and polygon interaction; every UI concern stands on the DOM + canvas directly.

- **Pillow** — used for the one thing stdlib does not do robustly across PNG/JPEG: reading an image's
  true pixel dimensions. Foundational-adjacent (it is the sanctioned image library) but its use is
  deliberately confined to a single size-probe seam; see `dependencies.md`.

- **Docker + docker compose** — the only supported way to run the tool. The container mounts the user's
  image folder and runs the FastAPI app under uvicorn; there is no hand-installed path.

Not adopted: **numpy**. Although available in the substrate for "image work", polygon annotation needs no
per-pixel array math — dimensions and vertex lists suffice — so pulling it in would be a dependency with
no present force. Reconsider only if pixel-level operations (mask rasterization, area) ever become goals.
