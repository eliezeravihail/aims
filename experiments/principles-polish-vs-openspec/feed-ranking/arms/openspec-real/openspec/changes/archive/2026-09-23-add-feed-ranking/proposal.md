# Proposal

## Why

A user's feed has to be ordered so that the most relevant candidate items appear first. Relevance comes from three
per-item signals (recency, affinity, popularity). How much each signal counts is a business decision that differs
between deployments and changes over time. Operators need to be able to retune it without a code change or release.

## What Changes

- New in-process ranking service. It takes a `user` and a list of candidate items (each with `item_id`, `recency`,
  `affinity` and `popularity` in [0.0, 1.0]) and returns the same candidates ordered by a combined score, highest
  first.
- The combined score is a weighted sum of the three signals. Equal scores are ordered by `item_id` ascending, so
  the result is deterministic.
- The weights are per-deployment configuration: a small JSON file whose path is given to the service. The file is
  validated when it is loaded, and an operator changes weights by editing it and reloading. No code change is
  needed.
- Invalid input is rejected with an explicit error and never silently "fixed". This covers out-of-range signals,
  duplicate item ids, invalid weights and unknown signal names.
- A small CLI wraps the library API for operators and for manual checks.

## Capabilities

### New Capabilities
- `feed-ranking`: scores candidate items from their signals and returns them in a deterministic order. Covers the
  request/response contract, the scoring rule, tie-breaking and input validation.
- `ranking-config`: per-deployment signal weights. Covers the file format, validation rules, how weights are
  loaded and reloaded, and the guarantee that a request is scored with one consistent set of weights.

### Modified Capabilities
<!-- none: no existing specs -->

## Impact

- Greenfield: no existing code or specs are affected.
- Python 3.11+ standard library only (`json`, `dataclasses`, `decimal` optional; see design). No new runtime
  dependencies.
- Public surface: a library function or class API plus a CLI entry point. Nothing is persisted. It runs as a
  single process.
