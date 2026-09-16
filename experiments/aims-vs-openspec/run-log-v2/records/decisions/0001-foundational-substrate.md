---
title: "0001 — Foundational substrate"
date: 2026-09-16
---

## Status
Accepted.

## Context
Day-zero substrate — the base whose replacement rewrites everything — must be fixed by the owner, not
guessed. Here the product owner fixed it directly in the request.

## Decision
- Language: **Python 3.11+**.
- **Standard library only**; a new runtime dependency must be argued for in the design.
- `decimal.Decimal` is the money base and part of the permitted seam vocabulary; `float` is forbidden
  for money.
- No UI, no network, no database, no persistence; single process; single currency.

## Consequences
- The definitions-file parser is a stdlib module (`json`), not a third-party library.
- No core application framework exists to lean on; the design is plain modules + domain types.

## Alternatives rejected
- Choosing a web framework / HTTP server as the substrate — excluded by "no network" and by the entry
  point being a library (ADR 0004).
