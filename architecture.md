---
title: "architecture"
date: 2026-08-12
---

## Boundaries & seams
- **skills/aims-guide** — the design method (produces knowledge). **knowledge/** — where knowledge is
  written and how drift is detected (format + anchor tool + read hook). The method calls the tool; it
  does not embed hashing.
- `knowledge/anchor.py` (write) and `knowledge/staleness_hook.py` (read) share the derivation +
  hashing so read-time and write-time always agree; the hook imports the tool.

## Invariants
- Design knowledge is co-located: a source file's knowledge is in its same-named companion; system-wide
  knowledge is a root record. Nothing stores a path — pairing is by name.
- The read hook is advisory: never blocks, fail-open.
