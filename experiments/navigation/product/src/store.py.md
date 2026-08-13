---
title: "store.py"
date: 2026-08-12
hash: "sha256:a71e2d7f406f5508efad8a3ac847f6b4f2e89f53e0402b5b34e6475ae188025a"
---
## Insights
- store keeps a module-level _CACHE for speed; callers MUST clear the entry after a write or a stale
  SVG can be served. This caching rule is specific to storage and lives only here.
## Decisions
- save() writes through _CACHE. Persistence concerns belong to store alone.
## Discussions
-
