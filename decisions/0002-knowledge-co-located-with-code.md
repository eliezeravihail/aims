---
title: "Design knowledge is co-located with the code — the structure is both code graph and knowledge tree"
date: 2026-08-12
---

Context: durable design knowledge could live glued to a source file, in a central folder, or in a
separate tree that mirrors the code (a parallel tree to keep in sync). All were rejected.

Decision: knowledge lives IN the code tree, in two homes. **File-level** — a source file's knowledge is
in a same-named companion beside it (`render.py` → `render.py.md`), holding its Insights / Decisions /
Discussions; read the whole companion when you touch the file. **System-level** — cross-cutting records
at the root (`goals.md`, `architecture.md`, `base-dependencies.md`, `dependencies.md`, ADRs under
`decisions/`). The one directory structure is both the code graph and the knowledge tree; knowledge is
reached by navigating to the file or the root record, never by reading the whole project.

Consequences: no parallel tree — renaming a source file and its companion together stays in sync with
nothing to update.
