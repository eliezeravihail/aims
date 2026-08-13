---
title: "Project norm: the plugin's code is stdlib-only, no runtime dependencies"
date: 2026-08-12
---

A capsule-wide convention (a root record, no anchor — it applies uniformly to all of aims' code). Every
script aims ships — Python tools, bash hooks — uses only the standard library and POSIX shell; no
third-party runtime dependency. Keeps aims installable into any project without a package step. If it
ever needs enforcing, that is an opt-in linter, not a passive record.
