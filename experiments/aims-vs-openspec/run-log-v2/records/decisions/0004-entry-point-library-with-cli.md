---
title: "0004 — Entry point: library with a thin CLI"
date: 2026-09-16
---

## Status
Accepted.

## Context
The task permits a library-with-CLI or a local HTTP endpoint. The substrate forbids network and
persistence; the product is a pure compute over a cart.

## Decision
The product is a **library** whose entry point is `price(cart, catalog) -> PricedCart`. A **thin CLI**
adapter reads a cart (JSON on stdin/arg), calls the library, writes the `PricedCart` (JSON on stdout).
All pricing rules live in the library; the CLI holds none.

## Consequences
- Fully testable without a transport; nothing to stand up.
- A future HTTP endpoint is another thin adapter over the same `price()` — no rule moves.

## Alternatives rejected
- A local HTTP endpoint as the primary surface — adds a server for no present need and sits awkwardly
  with "no network"; deferred to an adapter if ever wanted.
