---
title: "Project norm: the plugin's code is stdlib-only, no runtime dependencies"
date: 2026-08-12
---

A capsule-wide convention (no `code:` — it applies uniformly to all of aims' code, present and future,
so it has no single cohesive target; it lives at the root and binds capsule-wide by placement).

Norm: every script aims ships — Python tools, bash hooks — uses only the language standard library and
POSIX shell. No third-party runtime dependency is added. This mirrors capsa's own "passive, zero
dependencies" posture and keeps aims installable into any project without a package step.

If this ever needs *enforcing* rather than stating, that is an opt-in linter over all scripts emitting
capsa `X-` findings — not part of the passive record.
