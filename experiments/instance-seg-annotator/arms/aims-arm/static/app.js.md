---
title: "app.js"
date: 2026-08-13
hash: "sha256:d9e5f06f6fba4a444fb6e5705aeb997074f06af1817b77b7632651ea3806dfad"
---
## Decisions
- **Owns in-memory state, navigation, and wiring only** — no drawing math (that is `canvas.js`) and no URLs
  (that is `api.js`).
- **Navigation auto-saves when dirty** (`navigate` PUTs before moving) so stepping through the folder never
  silently drops unsaved polygons; there is also an explicit Save (button / Ctrl-Cmd+S).
- **Unknown-class objects render neutral, not dropped** — the color map is looked up with a fallback, so an
  object whose class was removed from the list still shows (goals.md: membership is not a validity rule).
- **"Export tiles" is a thin trigger** — it saves if dirty, prompts for tile size / overlap / dataset name
  (defaults 1024 / 128 / "dataset"), POSTs to `/api/export`, and flashes the summary. All tiling/format
  logic is server-side; the button carries no geometry knowledge.

## Discussions
- Autosave-on-navigate was chosen over a "you have unsaved changes" prompt: for a single-user local tool the
  cost of a stray save is nil and losing work is the real risk.
