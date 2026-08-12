---
title: "Let the directory structure carry both the code graph and the knowledge tree"
date: 2026-08-12
hash: "sha256:4e52fcbc684ed17a5a37507deb8f78b3caf544805c2873683048dcd73036c9c8"
---

The dead ends were: notes glued to a source file (fragile), a central folder (bloats), and a separate
.capsa/ tree mirroring the code (a parallel tree to sync). The clean idea is to keep design records
IN the code tree, next to the code — so the one structure is both the code graph and the knowledge
tree. Scope, navigation, and the anchor target all come from *where the record sits*: no path field, no
mirror, and moving a directory moves its knowledge with it. A concern that cannot be given its own
directory is telling you the architecture, not the format, needs fixing.
