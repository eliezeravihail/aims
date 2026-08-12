---
id: 1
title: "Balance is derived from the append-only entries, never stored"
status: accepted
date: 2026-08-12
tags: [ledger, invariant]
anchors:
- {path: "src/ledger.py", hash: "sha256:2ee9c3536bd3a040f4b69bc20df2f63e6be3c16a12625619f4a8078101ad41b5"}
---

## Context
An account balance could be kept as a running field updated on each post, or derived by summing the
entries on read.

## Decision
Balance is **derived** on read (`Ledger.balance` sums the entries). The append-only entries list is the
single source of truth. No stored/cached balance field exists, by design.

## Consequences
Reads are O(n) in entries. This is accepted: correctness over speed. If balance reads ever need to be
faster, the fix must NOT introduce a second source of truth (see insight
`insights/dev/stored-balance-drift`).

## Alternatives considered
A stored running balance — rejected: see the recorded drift bug.
