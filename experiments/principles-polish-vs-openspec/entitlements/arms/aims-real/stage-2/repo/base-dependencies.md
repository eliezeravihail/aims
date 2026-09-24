---
title: "base-dependencies"
date: 2026-09-23
---
- **Python 3.11+, standard library only** — fixed by the product owner in `substrate.md` (not chosen here).
  Every module stands on it. Only stdlib types and the design's own published domain types cross seams.
- No UI, network, database or persistence; single process. Entry point: a library API plus a small CLI.
