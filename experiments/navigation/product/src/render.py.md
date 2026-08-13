---
title: "render.py"
date: 2026-08-12
hash: "sha256:d0237aa5c8db56888e3fbdca99003892715b9eb95e9513df46bc5c8a5d96185e"
---
## Insights
- An earlier version made to_svg() async to support a "live preview" and added an internal frame cache.
  Under concurrent requests the cache returned a half-rendered SVG for the wrong maze — a silent,
  hard-to-reproduce bug. Lesson: to_svg MUST stay a pure, synchronous function of its argument, with no
  internal state and no I/O. New drawing options must be plain parameters, never cached state.
## Decisions
- to_svg(maze, ...) is a pure synchronous function: input maze -> output svg. No async, no I/O, no
  module-level or instance cache. (Supersedes the earlier async+cache attempt.)
## Discussions
- Considered memoizing by maze id; rejected — see the insight above.
