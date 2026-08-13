---
title: "storage.py"
date: 2026-08-13
hash: "sha256:73140c7dc2f7d35ae64c062f44ff0a6de40dd0679c304400fccc584e6b63bccb"
---

## Insights
- Byte-stable serialization (sorted keys, fixed indent, trailing newline) is what makes idempotent saves
  *testable*: save → load → save round-trips to identical bytes (`tests/test_storage.py`).
- Writes are atomic (write a `.tmp` sibling, then `replace`) so a crash mid-write can't leave a truncated
  annotation file.

## Decisions
- The **single owner** of on-disk annotation I/O. Depends on the pure model for shape/validation; adds
  nothing about display or transport. The on-disk **format is a confined choice** here (`dependencies.md`)
  — swapping it (combined file, DB) touches only this module, not the model.
- One image ↔ one JSON file, keyed by the image filename **stem** (`city_01.png` → `city_01.json`);
  directory parts are stripped so writes stay inside `annotations_dir`.

## Discussions
- Considered a single combined annotations file; kept per-image files for simplicity and so stepping
  through a folder maps one image to one small file. Revisit if cross-image queries ever matter.
</content>
