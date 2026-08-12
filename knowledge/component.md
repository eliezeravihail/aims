---
title: "knowledge (co-located records + staleness)"
date: 2026-08-12
shape: "sha256:d05dde9a447430412d68331dfde0567308618834a449ef51677a597b18d8faa4"
---

## Purpose
The durable-knowledge substrate: the record format (format.md), the write-time anchor stamper
(anchor.py), and the read-time staleness advisory (staleness_hook.py).

## Boundaries & seams
anchor.py (write) and staleness_hook.py (read) share their derivation + hashing so the two always
agree; the hook imports the tool. A record's anchor target is derived from the record's location, so
neither stores a path.

## Invariants
- The read hook is advisory: never blocks, fail-open.
- Design records (component.md, decisions/, insights/) are excluded from every anchor, so editing
  knowledge never trips its own anchor.
