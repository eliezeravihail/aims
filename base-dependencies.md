---
title: "base-dependencies"
date: 2026-09-16
---

The foundational substrate for aims itself — the base every part stands on, whose replacement would
rewrite essentially everything (`SKILL.md` step 1). aims mandates this record for any product it designs;
this is aims dogfooding the rule on itself.

## Substrate

- **Language:** Python 3 (standard library only) for the two tools, and **bash** for the hooks/tests.
- **Framework:** none. aims is a Claude Code **plugin** — markdown skills + commands + two small scripts;
  the Claude Code plugin/skill/hook contract is the only platform it stands on.
- **Foundational dependencies:** none beyond the Python standard library and a POSIX shell. This is a
  fixed decision, not a default — see `decisions/0004-stdlib-only-no-runtime-deps.md`.

## Confined dependencies

**None.** aims has no heavy, replaceable dependency behind a boundary, so there is no root
`dependencies.md` — the confined-dependency record exists only when such a dependency does. Adding one
(a runtime library, a model, a data tool) would be a substrate decision to record here, or a confined one
to record in a new `dependencies.md`.
