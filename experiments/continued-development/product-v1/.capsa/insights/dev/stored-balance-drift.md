---
kind: dev
title: "A stored running balance drifted from the entries — do not reintroduce it"
created: 2026-08-12
code_globs: ["src/ledger.py"]
tags: [ledger, bug, invariant]
anchors:
- {path: "src/ledger.py", hash: "sha256:2ee9c3536bd3a040f4b69bc20df2f63e6be3c16a12625619f4a8078101ad41b5"}
---

An earlier prototype kept a `self._balance` field updated inside `post()`. Under an interleaving where
an entry was appended but the field update was skipped on an error path, the stored balance drifted
from the true sum of entries, and the bug was silent — reads returned a plausible-but-wrong number for
weeks. The lesson: with two representations of the same fact, they *will* diverge. Balance must have a
single source of truth (the entries). If speed is ever needed, memoize *derivation from the entries*
(and invalidate on post) — never keep an independently-mutated balance field. This is exactly the
"single home / one representation" rule.
