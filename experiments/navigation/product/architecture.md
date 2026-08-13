---
title: "architecture"
date: 2026-08-12
---
## Boundaries & seams
- generator: builds a maze (grid). render: turns a finished maze into SVG. store: persists saved mazes.
  server: serves pages.
- render must not know how the maze was generated or how it is stored.
