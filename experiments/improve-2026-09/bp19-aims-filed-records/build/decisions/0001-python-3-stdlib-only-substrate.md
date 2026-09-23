---
title: "Python 3 with the standard library only"
date: 2026-09-22
---

**Context.** The substrate — language and foundational dependencies — was fixed by the task card
("a Python module, no external dependencies"), so it is a grounded product fact, not a choice left
open. Everything in this product stands on it.

**Decision.** Python 3, standard library only. Hashing comes from `hashlib`; tests from `unittest`.

**Consequences.**
- The percentage bucket may **not** use the built-in `hash()`: string hashing is salted per process
  (`PYTHONHASHSEED`), which would silently re-shuffle every user's cohort on restart and break the
  product's central guarantee. A cryptographic digest from `hashlib` is used instead, and the
  derivation is published rather than treated as an internal detail.
- A faster non-cryptographic hash (mmh3, xxhash — the usual choice for bucketing) is unavailable.
  Acceptable: one SHA-256 of a short string per rule evaluation, and no performance requirement was
  stated.
- No flag-vendor SDK is adopted; distributing or storing rules is out of scope (`goals.md`).

**Alternatives.** A third-party hashing library (rejected: violates the substrate) and a hosted
feature-flag SDK (rejected: it would replace the product, not support it).
