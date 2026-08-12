---
title: "Cut the memory-tree subsystem; the capsule + one read hook replace it"
date: 2026-08-12
code: hooks/staleness_read.py
hash: "sha256:d51809594e168fafdde9b5d9d345bc6ae9291703e9c0428313271d4659b7677f"
---

Context: pre-capsa aims maintained a memory tree with marker/consolidation/lint/doctor machinery and
several hooks (docs/adr/0006-0012, 0018-0019, 0024, 0027-0030 are the frozen history).

Decision: remove the whole subsystem. capsa's placement-addressed, one-record-per-file grammar makes
relevance structural (a tree walk), not computed, so there is no mutable store to keep coherent. The
only active machinery becomes one advisory read-time staleness hook.

Consequences: ~1200 lines of shell and eight hooks deleted; documentation stays current by
construction (method discipline) + detected drift (the anchor), not background maintenance.
