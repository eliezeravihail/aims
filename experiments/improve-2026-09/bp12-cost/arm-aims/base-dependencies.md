---
title: "base-dependencies"
date: 2026-09-20
---
## Insights
- The foundational substrate is deliberately minimal: this is a single self-contained module.

## Decisions
- **Language:** Python 3 (`from __future__ import annotations`; `X | None` union syntax; `dataclasses`).
- **Framework:** none.
- **Foundational dependencies:** the Python standard library only — `dataclasses` for the value object,
  `unittest` for tests. No third-party packages. This is a hard product constraint from the spec.

## Discussions
- The spec fixed "no external dependencies," so the substrate was given rather than chosen. There is
  nothing pervasive enough besides the language itself to count as foundational here.
