---
id: 1
title: "Design is the goal handed to the Worker, not a review after the fact"
status: accepted
date: 2026-08-12
tags: [method, thesis]
---

## Context
An implementing agent optimizes toward whatever goal it is handed. Hand it a feature ticket and design
quality becomes whatever survives shipping.

## Decision
The Guide hands the Worker a design/quality objective with the feature as a constraint, and measures
the returned design — direction and measurement, not coercion.

## Consequences
Good design is produced at construction time, not policed afterward. Inherited from Balash; it is the
reason aims exists.

## Alternatives considered
A post-hoc review/lint gate — rejected: it measures after the design is already whatever the feature
goal made it.
