---
id: 2
title: "Fast balance via an invalidate-on-post memo of the derivation, not a stored field"
status: accepted
date: 2026-08-12
tags: [ledger, invariant, performance]
supersedes: []
refines: [1]
anchors:
- {path: "src/ledger.py", hash: "sha256:698be97c04bb873506f554bd46b3ab7657aca6c1e38fd2c7f8a795e0d903a5bc"}
---

## Context
`Ledger.balance()` is hot (called very frequently) and was O(n) in entries on every read. Decision 1
established that balance is derived from the append-only entries and must never become a second source
of truth (see insight `insights/dev/stored-balance-drift`). We needed reads fast without breaking that
invariant.

## Decision
Add a per-account balance **memo** (`self._balance_memo`) that caches the *derivation* from the
entries. `balance()` returns the cached value when warm (O(1)); on a miss it re-derives by summing the
entries (O(n)) and stores the result. `post()` invalidates the memo for the posted account
(`pop(account)`), so the next read re-derives. The memo is fully reconstructible from the entries and
is dropped on every write, so it cannot silently drift — it is a cache, never an independently mutated
balance field. The entries remain the single source of truth.

## Consequences
- Reads are O(1) on the hot path; the first read after each post pays the O(n) re-derivation once.
- Invariant preserved: no incremental running total is maintained; the memo can be cleared at any time
  and rebuilds to the same value.
- `statement(account)` returns the account's entries plus its closing balance, both derived from the
  entries (it reuses `balance()`, so it benefits from the memo).

## Alternatives considered
- Incrementally updating a stored running balance inside `post()` — rejected: this is exactly the
  independently-mutated field that drifted before (insight `stored-balance-drift`, decision 1).
