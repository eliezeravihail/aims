---
title: "Design knowledge is co-located with the code — the structure is both code graph and knowledge tree"
date: 2026-08-12
---

Context: durable design knowledge could live glued to each source file (fragile), in a central folder
(bloats, read-whole), or in a separate .capsa/ tree that mirrors the code (a parallel tree to keep in
sync). All were rejected.

Decision: a record lives IN the code tree, next to the code it describes — a component's `component.md`
inside its directory, its `decisions/`/`insights/` beside it; cross-cutting records at the repo root.
The one directory structure is both the code graph and the knowledge tree, so understanding and
navigation come from the structure itself. Location is scope; a reader walks from where it works up to
the root. Supersedes the earlier separate-.capsa-tree design.

Consequences: no parallel tree to sync — move a directory and its records move with it. A concern that
cannot be given its own directory is an architecture smell, not a record to scatter.
