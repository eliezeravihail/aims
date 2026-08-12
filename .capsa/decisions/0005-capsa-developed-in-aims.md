---
id: 5
title: "capsa is developed inside aims; the standalone repo is retired"
status: accepted
date: 2026-08-12
tags: [capsa, vendor]
anchors:
- {path: "vendor/capsa/PROVENANCE.md", hash: "sha256:4811a4878dc2c17beeb7e72f490eb8183d7f967c217bf6f02263e35d5b4b7f94"}
---

## Context
capsa began as a standalone format repo. aims is now its only consumer and driver.

## Decision
capsa lives under vendor/capsa/ and is developed here; edits to the grammar are a reviewed act that
bumps vendor/capsa/VERSION. The invariant that keeps it safe: an aims capsule stays a conforming capsa
capsule, so the format remains readable by any capsa tool.

## Consequences
No external upstream to sync, no vendor-vs-depend tension. The original repo link is historical
attribution only (vendor/capsa/PROVENANCE.md).
