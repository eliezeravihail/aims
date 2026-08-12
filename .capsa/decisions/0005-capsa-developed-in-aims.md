---
title: "capsa is developed inside aims; the standalone repo is retired"
date: 2026-08-12
code: vendor/capsa/PROVENANCE.md
hash: "sha256:c3c99759c3f35399883425db013f6734c05c4bd76f3e8088dc986cfc196a9aec"
---

Context: capsa began as a standalone format repo; aims is now its only consumer and driver.

Decision: capsa lives under vendor/capsa/ and is developed here; aims relaxes its required-field sets
to the lean profile (docs/format-profile.md). The invariant that keeps it safe: an aims capsule stays
a readable capsa capsule.

Consequences: no external upstream to sync, no vendor-vs-depend tension. The original repo link is
historical attribution only.
