---
title: "base-dependencies"
date: 2026-09-22
---

- **Language:** Python 3, standard library only. Fixed by the task card, not defaulted — see
  `decisions/0001-python-3-stdlib-only-substrate.md`.
- **Framework:** none. The module is a plain library: callers construct rules and a resolver.
- **Foundational dependencies:** the standard library only — `hashlib` in particular is part of the
  substrate rather than an incidental helper, because the "same user, same answer, forever"
  guarantee is a published contract expressed in terms of SHA-256.

**Confined dependencies: none**, so there is no `dependencies.md` — that record exists only once a
replaceable dependency sits behind a boundary.
